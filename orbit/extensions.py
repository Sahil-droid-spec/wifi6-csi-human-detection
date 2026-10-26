"""Local-only upload, pairing, simulation and experiment services."""

import hashlib
import io
import json
import os
import secrets
import shutil
import socket
import threading
import time
import zipfile
from pathlib import Path

import numpy as np
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from . import core, lab


class ImportSettings(BaseModel):
    modulation: str = "ax"
    bandwidth: int = 20
    label: str = "unlabelled"
    session: str = "Session 1"
    group: str = "unknown"
    synthetic: bool = False
    packet_rate: float | None = Field(default=None, gt=0, le=100000)


class Transfer(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    size: int = Field(gt=0, le=2 * 1024**3)
    sha256: str = Field(pattern="^[a-f0-9]{64}$")
    settings: ImportSettings = Field(default_factory=ImportSettings)


class Simulation(BaseModel):
    subcarriers: int = 256
    packet_rate: float = 100
    duration: float = 10.24
    noise: float = 0.03
    seed: int = 42
    sessions: int = 6
    days: int = 3
    environment: str = "LOS"
    loss: float = 0.02
    classes: list[str] = Field(default_factory=lambda: list(lab.CLASSES))


class Marker(BaseModel):
    capture_id: str | None = None
    label: str = Field(max_length=80)
    packet: int | None = Field(default=None, ge=0)
    session: str = Field(default="Session 1", max_length=80)


class Watch(BaseModel):
    path: str = Field(max_length=500)
    enabled: bool = False
    settings: ImportSettings = Field(default_factory=ImportSettings)


class Teaching(BaseModel):
    kind: str = "perceptron"
    seed: int = 42
    epochs: int = Field(default=40, ge=5, le=200)
    grid: int = Field(default=4, ge=2, le=8)


class Question(BaseModel):
    question: str = Field(max_length=2000)


GUIDE = [
    (
        "pair phone connect qr server firewall hotspot",
        "Open Connect on the laptop and create a one-time QR. Scan it on your phone on the same Wi-Fi. Keep the local server running. If unreachable, check the private-network firewall prompt, Wi-Fi client isolation or use a trusted phone hotspot. orbit.local depends on mDNS; the numeric LAN URL is the fallback.",
        "Connect",
    ),
    (
        "upload file folder csv numpy npy npz resume",
        "Open Library → Import wizard. Select files or a folder, set real metadata if config.json is absent, then send. Uploads resume by SHA-256 and offset; identical stored files are detected. CSV is a numeric subcarrier-by-packet matrix, with no header. NPZ needs capture, csi or amplitude. Never upload pickled object arrays.",
        "Library",
    ),
    (
        "simulate simulation generate empty still walking moving human",
        "Open Simulation. Empty means no person reflection; one still adds a small breathing-like reflection; one moving adds a changing reflection; two people adds two moving reflections. These are generated channels, not actual motion measurements. Keep the Simulation chip visible.",
        "Simulation",
    ),
    (
        "sc soft genetic ga ann fuzzy learning som adaline perceptron",
        "Soft-computing tools are in Learning Lab. ANN learns nonlinear feature patterns; GA searches feature subsets inside training folds; fuzzy rules combine graded memberships. The Advanced learning page adds perceptron/Adaline/MLP and SOM examples. Pipeline tools can gate quality and fuse model outputs, but those heuristics are not calibrated detection evidence.",
        "Learning Lab",
    ),
    (
        "dsp filter butter fft spectrum pole convolution alias",
        "Signal Studio processes recordings with filters, FFT, spectrogram and multirate tools. Cutoffs use cycles/packet unless a trustworthy packet rate is supplied. The numerical extension page includes pole-zero views, Kaiser FIR and computation counts. Smoother traces do not establish better classification.",
        "Signal Studio",
    ),
    (
        "accuracy confidence prediction held out train validation",
        "Replay defaults to saved held-out predictions. An inference probability is not test accuracy. Use independent recording/date groups and compare capture-majority metrics with their protocol. Final-model inference may include training recordings and is labelled. Small datasets and date/class confounding limit claims.",
        "Replay",
    ),
    (
        "native wifi bf live wall camera video",
        "Live CSI hardware, through-wall detection and native 802.11bf are unverified. Phone videos are lab context, not CSI. Phone upload transfers files to the laptop; it does not capture CSI from an ordinary phone.",
        "Sensing modes",
    ),
]


def install(app, ctx):
    data = ctx["data"]
    rows = ctx["rows"]
    put = ctx["put"]
    get = ctx["get"]
    delete = ctx["delete"]
    job_start = ctx["job_start"]
    import_recording = ctx["import_recording"]
    local = ctx["local_request"]
    now = ctx["now"]
    for name in ["transfers", "simulations", "exports"]:
        (data / name).mkdir(exist_ok=True)
    tokens = {}
    token_urls = {}
    lock = threading.Lock()
    stop = threading.Event()
    observed = {}
    mdns = {}

    def require_local(request):
        if not local(request):
            raise HTTPException(403, "Change this setting from the laptop workspace.")

    def digest(path):
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024**2), b""):
                h.update(chunk)
        return h.hexdigest()

    def prepare(path, name, settings):
        """Normalize supported imports to bounded MAT/config layout before registration."""
        token = secrets.token_hex(12)
        folder = data / "staging" / ("normalize-" + token)
        folder.mkdir()
        try:
            if path.suffix.lower() == ".zip":
                core.safe_extract(path, folder)
            else:
                shutil.copy2(path, folder / Path(name).name)
            config = {
                "modulation": settings.modulation,
                "bandwidth": settings.bandwidth,
                "session": settings.session,
                "date": settings.group,
                "synthetic": settings.synthetic,
                "packet_rate": settings.packet_rate,
                "people": {
                    "present": None
                    if settings.label == "unlabelled"
                    else settings.label == "present"
                },
                "metadata_source": "import wizard",
            }
            if (
                settings.bandwidth not in (20, 40)
                or settings.modulation not in ("ax", "ac", "unknown")
                or settings.label not in ("unlabelled", "present", "absent")
            ):
                raise ValueError("Choose supported bandwidth, modulation and presence label.")
            for source in list(folder.rglob("*")):
                if source.suffix.lower() in (".csv", ".npy", ".npz"):
                    amp = lab.convert_array(
                        source, source.with_suffix(".mat"), 256 if settings.bandwidth == 20 else 512
                    )
                    if amp:
                        config["amplitude_only"] = True
                    source.unlink()
            if not (folder / "config.json").exists():
                (folder / "config.json").write_text(json.dumps(config), encoding="utf8")
            packed = data / "staging" / (token + ".zip")
            lab.archive(folder, packed)
            return packed
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def submit(path, name, settings, origin="phone"):
        actual = digest(path)
        duplicate = next(
            (d for d in rows("dataset") if d.get("upload_sha256", d.get("sha256")) == actual), None
        )
        if duplicate:
            return {"duplicate": True, "dataset_id": duplicate["id"]}

        def work(jid, p):
            normalized = prepare(path, name, settings)
            result = import_recording(
                normalized,
                name if name.endswith(".zip") else name + ".zip",
                secrets.token_hex(12),
                p,
            )
            dataset = get("dataset", result["dataset_id"])
            dataset["upload_sha256"] = actual
            put("dataset", dataset)
            item = {
                "id": secrets.token_hex(12),
                "name": name,
                "dataset_id": dataset["id"],
                "created": now(),
                "origin": origin,
                "status": "Imported",
                "synthetic": dataset.get("synthetic", False),
            }
            put("inbox", item)
            if path.parent == data / "transfers":
                path.unlink(missing_ok=True)
            return result

        return job_start("import", work)

    @app.post("/api/transfers")
    def begin(body: Transfer):
        if Path(body.name.replace("\\", "/")).suffix.lower() not in (
            ".mat",
            ".zip",
            ".csv",
            ".npy",
            ".npz",
        ):
            raise HTTPException(415, "Choose MAT, ZIP, CSV, NPY or NPZ.")
        duplicate = next(
            (d for d in rows("dataset") if d.get("upload_sha256", d.get("sha256")) == body.sha256),
            None,
        )
        if duplicate:
            return {"duplicate": True, "dataset_id": duplicate["id"]}
        for row in rows("transfer"):
            if (
                row["sha256"] == body.sha256
                and row["size"] == body.size
                and row["settings"] == body.settings.model_dump()
                and row.get("status") == "uploading"
            ):
                row["offset"] = (data / "transfers" / row["id"]).stat().st_size
                return row
        active = [r for r in rows("transfer") if r.get("status") == "uploading"]
        if len(active) >= 8 or sum(r["size"] for r in active) + body.size > 6 * 1024**3:
            raise HTTPException(409, "Finish or cancel pending transfers before adding more files.")
        row = {
            "id": secrets.token_hex(12),
            **body.model_dump(),
            "name": Path(body.name.replace("\\", "/")).name,
            "offset": 0,
            "status": "uploading",
            "created": now(),
        }
        (data / "transfers" / row["id"]).touch()
        put("transfer", row)
        return row

    @app.get("/api/transfers/{id}")
    def transfer(id: str):
        row = get("transfer", id)
        p = data / "transfers" / row["id"]
        row["offset"] = p.stat().st_size if p.exists() else row["offset"]
        return row

    @app.put("/api/transfers/{id}")
    async def chunk(id: str, request: Request, offset: int = 0):
        row = get("transfer", id)
        parts = []
        size = 0
        async for part in request.stream():
            size += len(part)
            if size > 4 * 1024**2:
                raise HTTPException(413, "Send chunks no larger than 4 MiB.")
            parts.append(part)
        with lock:
            path = data / "transfers" / row["id"]
            if row["status"] != "uploading" or not path.exists():
                raise HTTPException(409, "Start or resume an active transfer.")
            actual = path.stat().st_size
            if offset != actual:
                raise HTTPException(409, f"Resume at byte {actual}.")
            if actual + size > row["size"]:
                raise HTTPException(413, "Chunk exceeds the declared file size.")
            with path.open("ab") as f:
                f.write(b"".join(parts))
            row["offset"] = actual + size
            put("transfer", row)
        return row

    @app.delete("/api/transfers/{id}")
    def cancel_transfer(id: str):
        row = get("transfer", id)
        (data / "transfers" / row["id"]).unlink(missing_ok=True)
        delete("transfer", id)
        return {"ok": True}

    @app.post("/api/transfers/{id}/complete")
    def complete(id: str):
        row = get("transfer", id)
        path = data / "transfers" / row["id"]
        if row["status"] == "completed":
            return row.get("result", {})
        if not path.exists() or path.stat().st_size != row["size"]:
            raise HTTPException(409, "Finish uploading all bytes before importing.")
        if digest(path) != row["sha256"]:
            raise HTTPException(
                422, "Hash mismatch. Cancel this transfer and reselect the original file."
            )
        result = submit(path, row["name"], ImportSettings(**row["settings"]))
        row.update(status="completed", result=result)
        put("transfer", row)
        return result

    @app.get("/api/inbox")
    def inbox():
        return {
            "items": rows("inbox"),
            "transfers": rows("transfer"),
            "markers": rows("marker"),
            "trash": rows("trash"),
        }

    @app.post("/api/inbox/{id}/ack")
    def acknowledge(id: str):
        row = get("inbox", id)
        row["status"] = "Reviewed"
        put("inbox", row)
        return row

    @app.post("/api/markers")
    def marker(body: Marker):
        if body.capture_id:
            cap = get("capture", body.capture_id)
            if body.packet is not None and body.packet >= cap["packets"]:
                raise ValueError("Select a packet inside this recording.")
        row = {
            "id": secrets.token_hex(12),
            **body.model_dump(),
            "created": now(),
            "synthetic": bool(get("capture", body.capture_id).get("synthetic"))
            if body.capture_id
            else False,
            "meaning": "Manual tap label; wall-clock timestamp, not automatic CSI/video synchronization",
        }
        put("marker", row)
        return row

    @app.post("/api/trash/{id}/restore")
    def restore(id: str):
        item = get("trash", id)
        for kind, row in item["records"]:
            put(kind, row)
        delete("trash", id)
        return {"ok": True}

    @app.post("/api/pair/token")
    def pairing(request: Request, interface: int = 0):
        require_local(request)
        if not ctx["sharing"]["enabled"]:
            raise HTTPException(409, "Switch local-server phone sharing on first.")
        token = secrets.token_urlsafe(32)
        with lock:
            for old in list(tokens):
                if tokens[old] < time.monotonic():
                    tokens.pop(old)
            tokens[token] = time.monotonic() + 120
        addresses = ctx["lan_info"]()["addresses"]
        base = (
            addresses[max(0, min(interface, len(addresses) - 1))].split("/#")[0]
            if addresses
            else f"http://orbit.local:{ctx['port']}"
        )
        token_urls[token] = base + "/#/pair?token=" + token
        return {
            "token": token,
            "url": base + "/#/pair?token=" + token,
            "expires_seconds": 120,
            "qr": "/api/pair/qr/" + token,
        }

    @app.get("/api/pair/qr/{token}")
    def pairing_qr(token: str):
        if tokens.get(token, 0) < time.monotonic():
            raise HTTPException(410, "Create a fresh pairing QR.")
        import qrcode
        import qrcode.image.svg

        buffer = io.BytesIO()
        qrcode.make(token_urls[token], image_factory=qrcode.image.svg.SvgPathImage).save(buffer)
        return Response(buffer.getvalue(), media_type="image/svg+xml")

    @app.post("/api/desktop/claim")
    async def desktop_claim(request: Request):
        require_local(request)
        body = await request.json()
        token = body.get("token", "")
        expected = getattr(app.state, "desktop_bootstrap", None)
        if (
            not isinstance(token, str)
            or not expected
            or not secrets.compare_digest(token, expected)
        ):
            raise HTTPException(401, "Start the native desktop app to connect this window.")
        app.state.desktop_bootstrap = None
        session = secrets.token_urlsafe(32)
        ctx["sessions"].add(session)
        response = JSONResponse({"ok": True})
        response.set_cookie(
            "orbit_session", session, httponly=True, samesite="strict", max_age=12 * 3600
        )
        return response

    @app.post("/api/pair/claim")
    async def claim(request: Request):
        body = await request.json()
        token = body.get("token", "")
        if not isinstance(token, str) or len(token) > 100:
            raise HTTPException(401, "Scan a fresh laptop QR.")
        with lock:
            expiry = tokens.pop(token, 0)
            token_urls.pop(token, None)
            if expiry < time.monotonic():
                raise HTTPException(
                    401, "Pairing QR expired or already used. Create a new one on the laptop."
                )
            session = secrets.token_urlsafe(32)
            ctx["sessions"].add(session)
        put("device", {"id": secrets.token_hex(8), "name": "Paired phone", "created": now()})
        response = JSONResponse({"ok": True})
        response.set_cookie(
            "orbit_session", session, httponly=True, samesite="strict", max_age=12 * 3600
        )
        return response

    @app.get("/api/doctor")
    def doctor():
        return {
            **ctx["lan_info"](),
            "hostname": "orbit.local",
            "mdns_registered": bool(mdns.get("service")),
            "devices": rows("device"),
            "checks": [
                {"name": "Local analysis server", "status": "running"},
                {"name": "Phone sharing", "status": "on" if ctx["sharing"]["enabled"] else "off"},
                {"name": "Same Wi-Fi / hotspot", "status": "Check on both devices"},
                {
                    "name": "Private-network firewall permission",
                    "status": "Allow Orbit/Python on your trusted private network; no automatic firewall changes",
                },
                {
                    "name": "Wi-Fi client isolation",
                    "status": "If school Wi-Fi blocks devices, connect both to a trusted hotspot",
                },
                {
                    "name": "mDNS",
                    "status": "Use numeric LAN address if orbit.local does not resolve",
                },
            ],
        }

    @app.post("/api/watch")
    def watch(body: Watch, request: Request):
        require_local(request)
        path = Path(body.path).expanduser().resolve()
        if body.enabled and not path.is_dir():
            raise ValueError("Choose an existing watch folder on the laptop.")
        if path == data or path.is_relative_to(data):
            raise ValueError("Choose a folder outside Orbit internal storage.")
        row = {"id": "folder", **body.model_dump(), "path": str(path)}
        put("watch", row)
        return row

    @app.get("/api/watch")
    def watch_state(request: Request):
        require_local(request)
        return rows("watch")

    @app.post("/api/simulation")
    def simulation(body: Simulation):
        def work(jid, p):
            folder = data / "simulations" / jid
            folder.mkdir()
            lab.generate(folder, **body.model_dump())
            packed = data / "staging" / (jid + ".zip")
            lab.archive(folder, packed)
            result = import_recording(packed, "Simulation set A.zip", secrets.token_hex(12), p)
            row = get("dataset", result["dataset_id"])
            row["settings"] = body.model_dump()
            put("dataset", row)
            return result

        return job_start("simulation", work)

    @app.get("/api/simulation/{id}/download")
    def download_sim(id: str):
        dataset = get("dataset", id)
        if not dataset.get("synthetic"):
            raise HTTPException(404, "Choose a simulation dataset.")
        path = data / "originals" / (id + ".zip")
        if not path.exists():
            raise HTTPException(
                404,
                "Original archive unavailable in this package. Export a simulation recording instead.",
            )
        return FileResponse(path, filename="Simulation-set-A.zip")

    @app.get("/api/captures/{id}/download")
    def download_capture(id: str):
        cap = get("capture", id)
        target = data / "exports" / (id + ".zip")
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(data / cap["path"], "recording.mat")
            cfg = core.metadata(data / cap["path"], data / "captures" / cap["dataset_id"])["config"]
            cfg["synthetic"] = cap.get("synthetic", False)
            z.writestr("config.json", json.dumps(cfg, indent=2))
        return FileResponse(
            target,
            filename=("Simulation-" if cap.get("synthetic") else "Recorded-") + id[:8] + ".zip",
        )

    @app.post("/api/teaching")
    def teaching(body: Teaching):
        return lab.teaching(**body.model_dump())

    @app.post("/api/guide")
    def guide(body: Question):
        words = set(body.question.lower().split())
        scores = [len(words & set(keys.split())) for keys, answer, page in GUIDE]
        i = int(np.argmax(scores))
        answer, page = (
            (GUIDE[i][1], GUIDE[i][2])
            if scores[i]
            else (
                "Start with Library to import a recording, Simulation for generated examples, Signal Studio for DSP, Learning Lab for models, and Connect for phone pairing. Ask about one of those tasks.",
                "Home",
            )
        )
        return {
            "answer": answer,
            "page": page,
            "source": "Offline rule-based guide; no external AI service, no fabricated analysis",
        }

    @app.get("/api/plan")
    def plan():
        return rows("plan")

    @app.post("/api/plan")
    async def save_plan(request: Request):
        body = await request.json()
        if len(json.dumps(body)) > 64000:
            raise ValueError("Keep the session sheet below 64 KB.")
        row = {"id": body.get("id") or secrets.token_hex(12), "created": now(), "sheet": body}
        put("plan", row)
        return row

    @app.post("/api/pipeline/tune")
    async def tune_pipeline(request: Request):
        from .pipeline import tune

        body = await request.json()
        synthetic = bool(body.get("synthetic", False))
        bw = body.get("bandwidth", 20)
        did = body.get("dataset_id")
        selected = [
            c
            for c in rows("capture")
            if bool(c.get("synthetic")) == synthetic
            and c["bandwidth"] == bw
            and (not did or c["dataset_id"] == did)
        ]

        def work(jid, p):
            result = tune(selected, data, p)
            result.update(id=jid, created=now(), kind="DSP GA tuning")
            put("run", result)
            return result

        return job_start("DSP GA tuning", work)

    @app.post("/api/pipeline/fuse")
    async def fuse(request: Request):
        body = await request.json()
        cap, a, bad = ctx["arrays"](str(body.get("capture_id", "")))
        start = int(body.get("start", 0))
        length = core.contract(cap["bandwidth"])["window"]
        if start < 0 or start >= cap["packets"]:
            raise ValueError("Choose a packet inside the recording.")
        segment = a[:, start : start + length]
        gate = lab.quality_gate(
            float((~bad[start : start + length]).mean()), float(np.median(segment.std(axis=1)))
        )
        if not gate["accept"]:
            return {
                "gate": gate,
                "state": "Window skipped (quality)",
                "synthetic": cap.get("synthetic", False),
                "source": cap["source"],
            }
        chosen = {}
        for m in rows("model"):
            if (
                m["name"] in ("Logistic Regression", "Random Forest", "ANN / MLP")
                and m["contract"] == core.contract(cap["bandwidth"])
                and bool(m.get("synthetic")) == bool(cap.get("synthetic"))
                and m["name"] not in chosen
            ):
                chosen[m["name"]] = m
        values = []
        for m in chosen.values():
            try:
                r = ctx["predict"](
                    ctx["PredictBody"](
                        capture_id=cap["id"], model_id=m["id"], mode=body.get("mode", "held_out")
                    )
                )
                w = next((w for w in r["windows"] if w["start"] == start), None)
                if w:
                    values.append(
                        {
                            "model": m["name"],
                            "score": w["probability"],
                            "validation_protocol": r["validation_protocol"],
                        }
                    )
            except ValueError:
                continue
        if not values:
            raise ValueError(
                "Train compatible LR/RF/ANN models, then select a held-out recording or explicit final-model inference."
            )
        weights = np.array([max(0.05, abs(v["score"] - 0.5) * 2) * gate["score"] for v in values])
        score = float(np.average([v["score"] for v in values], weights=weights))
        return {
            "gate": gate,
            "state": "Prediction",
            "fuzzy_score": score,
            "prediction": int(score >= 0.5),
            "models": values,
            "weights": weights.tolist(),
            "source": cap["source"],
            "synthetic": bool(cap.get("synthetic")),
            "validation_protocol": "Heuristic confidence-membership fusion of "
            + body.get("mode", "held_out")
            + " model outputs; no independently validated fusion accuracy",
            "why": [
                "Low-quality windows abstain",
                "Scores further from 0.5 receive higher membership weight",
                "Weighted graded evidence is thresholded at 0.5; not a calibrated probability",
            ],
        }

    @app.post("/api/fuzzy/designer")
    async def fuzzy_designer(request: Request):
        body = await request.json()
        r = core.fuzzy(
            float(body.get("variation", 0.4)), float(body.get("motion", 0.6)), body.get("rules")
        )
        r["value"] = lab.defuzzify(r["universe"], r["aggregate"], body.get("method", "centroid"))
        r["method"] = body.get("method", "centroid")
        return r

    @app.post("/api/rate")
    async def packet_rate(request: Request):
        body = await request.json()
        t = np.asarray(body.get("timestamps", []), dtype=float)
        if len(t) < 3:
            return {
                "packet_rate": None,
                "protocol": "Unknown without timestamps or trusted capture metadata; no estimate invented",
            }
        if len(t) > 8192 or not np.isfinite(t).all() or np.any(np.diff(t) <= 0):
            raise ValueError("Provide 3–8192 strictly increasing finite timestamps in seconds.")
        delta = np.diff(t)
        return {
            "packet_rate": float(1 / np.median(delta)),
            "relative_jitter": float(np.std(delta) / np.mean(delta)),
            "protocol": "Reciprocal median packet timestamp interval; burst gaps may bias this estimate",
        }

    @app.get("/api/markers/export")
    def export_markers():
        import csv

        buffer = io.StringIO()
        items = rows("marker")
        columns = [
            "id",
            "capture_id",
            "session",
            "label",
            "packet",
            "created",
            "meaning",
            "synthetic",
        ]
        writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(items)
        return Response(
            buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="orbit-manual-markers.csv"'},
        )

    def watcher():
        while not stop.wait(3):
            try:
                configs = rows("watch")
                if not configs or not configs[0]["enabled"]:
                    continue
                config = configs[0]
                folder = Path(config["path"])
                for path in list(folder.iterdir())[:100]:
                    if (
                        not path.is_file()
                        or not path.resolve().is_relative_to(folder.resolve())
                        or path.suffix.lower() not in (".mat", ".zip", ".csv", ".npy", ".npz")
                        or path.stat().st_size > 2 * 1024**3
                    ):
                        continue
                    mark = (path.stat().st_size, path.stat().st_mtime_ns)
                    if observed.get(str(path)) != mark:
                        observed[str(path)] = mark
                        continue
                    key = hashlib.sha256(str(path).encode()).hexdigest()
                    previous = next((r for r in rows("watched") if r["id"] == key), {})
                    if previous.get("mark") == list(mark):
                        continue
                    submit(path, path.name, ImportSettings(**config["settings"]), "watch folder")
                    put("watched", {"id": key, "mark": list(mark)})
                    break
            except Exception:
                continue

    def start():
        threading.Thread(target=watcher, name="orbit-watch-folder", daemon=True).start()
        try:
            from zeroconf import ServiceInfo, Zeroconf

            ips = [a.split("://")[1].split(":")[0] for a in ctx["lan_info"]()["addresses"]]
            if ctx["lan"] and ips and os.environ.get("ORBIT_DISABLE_MDNS") != "1":
                z = Zeroconf()
                info = ServiceInfo(
                    "_http._tcp.local.",
                    "Orbit._http._tcp.local.",
                    addresses=[socket.inet_aton(ip) for ip in ips],
                    port=ctx["port"],
                    server="orbit.local.",
                    properties={"path": "/", "app": "Orbit"},
                )
                z.register_service(info, allow_name_change=True)
                mdns.update(client=z, service=info)
        except Exception:
            pass

    def close():
        stop.set()
        if mdns.get("client"):
            mdns["client"].unregister_service(mdns["service"])
            mdns["client"].close()

    app.state.extensions_start = start
    app.state.extensions_close = close
