"""FastAPI service. Run with python -m orbit; private by default."""

from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from threading import Lock
import os, json, sqlite3, secrets, hashlib, shutil, io, csv, socket, time
from urllib.parse import urlsplit
import numpy as np
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import core, models

ROOT = Path(__file__).resolve().parents[1]
MAX_UPLOAD = 256 * 1024**2


class UploadBodyLimit:
    """Bound multipart bodies before the multipart spooler sees them."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/api/upload":
            return await self.app(scope, receive, send)
        from tempfile import SpooledTemporaryFile

        limit = MAX_UPLOAD + 1024**2
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = limit + 1
        if declared > limit:
            return await JSONResponse(
                {"detail": "Upload request exceeds 256 MiB plus multipart overhead."},
                413,
            )(scope, receive, send)
        with SpooledTemporaryFile(max_size=1024**2) as spool:
            total = 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                total += len(chunk)
                if total > limit:
                    return await JSONResponse(
                        {"detail": "Upload request exceeds size limit."}, 413
                    )(scope, receive, send)
                spool.write(chunk)
                if not message.get("more_body", False):
                    break
            spool.seek(0)
            done = False

            async def replay():
                nonlocal done
                if done:
                    return await receive()
                chunk = spool.read(1024**2)
                done = spool.tell() == total
                return {"type": "http.request", "body": chunk, "more_body": not done}

            await self.app(scope, replay, send)


def now():
    return datetime.now(timezone.utc).isoformat()


def create_app(data_dir=None, access_code=None, lan=False, port=8765):
    data = Path(
        data_dir or os.environ.get("ORBIT_DATA_DIR", ROOT / "orbit-data")
    ).resolve()
    for name in ("originals", "captures", "models", "staging"):
        (data / name).mkdir(parents=True, exist_ok=True)
    code = access_code or secrets.token_hex(4).upper()
    sessions = set()
    attempts = {}
    guard = Lock()
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="orbit")
    db = data / "orbit.sqlite3"
    with sqlite3.connect(db) as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS records (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id))"
        )

    def put(kind, row):
        with sqlite3.connect(db) as con:
            con.execute(
                "INSERT OR REPLACE INTO records VALUES (?,?,?)",
                (kind, row["id"], json.dumps(row)),
            )

    def rows(kind):
        with sqlite3.connect(db) as con:
            return [
                json.loads(x[0])
                for x in con.execute(
                    "SELECT body FROM records WHERE kind=? ORDER BY rowid DESC", (kind,)
                )
            ]

    def get(kind, id):
        with sqlite3.connect(db) as con:
            row = con.execute(
                "SELECT body FROM records WHERE kind=? AND id=?", (kind, id)
            ).fetchone()
        if not row:
            raise HTTPException(404, f"{kind} not found.")
        return json.loads(row[0])

    def delete(kind, id):
        with sqlite3.connect(db) as con:
            con.execute("DELETE FROM records WHERE kind=? AND id=?", (kind, id))

    for job in rows("job"):
        if job["status"] in ("queued", "running"):
            job.update(
                status="interrupted",
                message="Server restarted; submit the operation again.",
            )
            put("job", job)

    @asynccontextmanager
    async def lifespan(app):
        yield
        pool.shutdown(wait=True, cancel_futures=True)

    app = FastAPI(
        title="Orbit Wi-Fi Sensing Lab",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.code = code
    app.state.data = data
    app.state.records = rows
    print(
        f"\nOrbit access code: {code}\nLocal workspace: http://127.0.0.1:{port}\nData: {data}\n",
        flush=True,
    )

    @app.middleware("http")
    async def protect(request, call_next):
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).netloc != request.headers.get("host"):
            return JSONResponse(
                {"detail": "Cross-origin requests are not allowed."}, 403
            )
        host = request.url.hostname or ""
        try:
            import ipaddress

            private = (
                ipaddress.ip_address(host).is_private
                or ipaddress.ip_address(host).is_loopback
            )
        except ValueError:
            private = host in ("localhost", "testserver")
        if not private:
            return JSONResponse(
                {"detail": "Use the loopback or private LAN address."}, 400
            )
        if request.url.path.startswith("/api/") and request.url.path not in (
            "/api/health",
            "/api/auth",
        ):
            with guard:
                allowed = request.cookies.get("orbit_session") in sessions
            if not allowed:
                return JSONResponse(
                    {
                        "detail": "Enter the session access code shown in the laptop terminal."
                    },
                    401,
                )
        try:
            response = await call_next(request)
        except Exception:
            # Do not send local paths or stack traces to clients.
            return JSONResponse(
                {"detail": "Operation failed. Check the local server log."}, 500
            )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = (
            "no-store" if request.url.path.startswith("/api/") else "no-cache"
        )
        return response

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, 422)

    @app.get("/api/health")
    def health():
        return {"status": "online", "version": "1.0.0", "local_only": True}

    class Auth(BaseModel):
        code: str = Field(max_length=100)

    @app.post("/api/auth")
    def auth(body: Auth, request: Request):
        host = request.client.host if request.client else "unknown"
        t = time.monotonic()
        with guard:
            prior = [v for v in attempts.get(host, []) if t - v < 60]
            if len(prior) >= 10:
                raise HTTPException(429, "Too many attempts. Wait one minute.")
            if not secrets.compare_digest(body.code.strip().upper(), code.upper()):
                attempts[host] = prior + [t]
                raise HTTPException(401, "Incorrect code. Check the laptop terminal.")
            token = secrets.token_urlsafe(32)
            sessions.add(token)
            attempts.pop(host, None)
        response = JSONResponse({"ok": True})
        response.set_cookie(
            "orbit_session", token, httponly=True, samesite="strict", max_age=12 * 3600
        )
        return response

    @app.post("/api/logout")
    def logout(request: Request):
        with guard:
            sessions.discard(request.cookies.get("orbit_session"))
        response = JSONResponse({"ok": True})
        response.delete_cookie("orbit_session")
        return response

    @app.get("/api/status")
    def status():
        return {
            "datasets": rows("dataset"),
            "captures": rows("capture"),
            "models": rows("model"),
            "runs": rows("run")[:50],
            "jobs": rows("job")[:30],
            "lan": lan,
            "version": "1.0.0",
        }

    def job_start(kind, fn):
        with guard:
            if any(j["status"] in ("queued", "running") for j in rows("job")):
                raise HTTPException(
                    409, "Another operation is running. Wait for it to finish."
                )
            jid = secrets.token_hex(12)
            job = {
                "id": jid,
                "kind": kind,
                "status": "queued",
                "progress": 0,
                "message": "Queued",
                "created": now(),
            }
            put("job", job)

        def progress(message, percent):
            job.update(status="running", message=message, progress=percent)
            put("job", job)

        def work():
            try:
                progress("Starting", 1)
                result = fn(jid, progress)
                job.update(
                    status="completed", progress=100, message="Completed", result=result
                )
            except Exception as exc:
                import logging

                logging.exception("Orbit background operation failed")
                job.update(status="failed", message=str(exc)[:500])
            finally:
                put("job", job)

        pool.submit(work)
        return job

    @app.get("/api/jobs/{id}")
    def job(id: str):
        return get("job", id)

    def import_recording(staged, filename, did, progress):
        dest = data / "captures" / did
        dest.mkdir()
        extracted = dest / "source"
        extracted.mkdir()
        try:
            if filename.lower().endswith(".zip"):
                core.safe_extract(staged, extracted)
            else:
                shutil.copyfile(staged, extracted / "recording.mat")
            mats = sorted(extracted.rglob("*.mat"))
            if not mats:
                raise ValueError("No supported .mat recordings found in the archive.")
            if len(mats) > 100:
                raise ValueError("Import at most 100 recordings per archive.")
            captures = []
            errors = []
            seen = set()
            for i, path in enumerate(mats):
                progress(
                    f"Validating recording {i+1}/{len(mats)}",
                    int(10 + 80 * i / len(mats)),
                )
                try:
                    m = core.metadata(path, extracted)
                    a, invalid, zero = core.read_capture(path, m["bandwidth"])
                    inferred = 20 if a.shape[0] == 256 else 40
                    warnings = []
                    if m["bandwidth"] is None:
                        warnings.append(
                            "Bandwidth absent in config; inferred from supported subcarrier count for inspection only."
                        )
                    if m["modulation"] != "ax":
                        warnings.append(
                            "AX modulation is not verified by config; training/inference unavailable."
                        )
                    if m["present"] is None:
                        warnings.append(
                            "Presence label unavailable; excluded from training."
                        )
                    if invalid.any():
                        warnings.append(
                            f"{int(invalid.sum())} invalid/all-zero packet columns. 20 MHz baseline replaces nonfinite values with zero; 40 MHz uses validity-aware windows."
                        )
                    if not (~invalid).any():
                        raise ValueError("Capture has no valid packet columns.")
                    _, windows, audit = core.feature_windows(a, invalid, inferred)
                    sha = hashlib.sha256(path.read_bytes()).hexdigest()
                    if sha in seen:
                        errors.append(
                            {
                                "file": str(path.relative_to(extracted)),
                                "error": "Duplicate capture content skipped.",
                            }
                        )
                        continue
                    seen.add(sha)
                    cid = secrets.token_hex(12)
                    np.savez_compressed(
                        dest / f"{cid}.npz", amplitude=a, invalid=invalid
                    )
                    captures.append(
                        {
                            "id": cid,
                            "dataset_id": did,
                            "name": str(path.relative_to(extracted)),
                            "path": str(path.relative_to(data)),
                            "cache": str((dest / f"{cid}.npz").relative_to(data)),
                            **{k: v for k, v in m.items() if k != "config"},
                            "bandwidth": inferred,
                            "bandwidth_verified": m["bandwidth"] is not None,
                            "subcarriers": a.shape[0],
                            "packets": a.shape[1],
                            "invalid_packets": int(invalid.sum()),
                            "zero_packets": zero,
                            "valid_fraction": float((~invalid).mean()),
                            "windows": len(windows),
                            "rejected_windows": sum(not w["accepted"] for w in audit),
                            "warnings": warnings,
                            "sha256": sha,
                            "created": now(),
                            "source": "RECORDED DATA",
                        }
                    )
                except Exception as exc:
                    errors.append(
                        {
                            "file": str(path.relative_to(extracted)),
                            "error": str(exc)[:400],
                        }
                    )
            if not captures:
                raise ValueError(
                    "No valid CSI captures. "
                    + "; ".join(e["error"] for e in errors[:3])
                )
            original = data / "originals" / f"{did}{Path(filename).suffix.lower()}"
            shutil.move(str(staged), original)
            dataset = {
                "id": did,
                "name": filename,
                "created": now(),
                "captures": len(captures),
                "errors": errors,
                "sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
                "size": original.stat().st_size,
            }
            # Register atomically so observers never see partial imports.
            with sqlite3.connect(db) as con:
                for kind, row in [("dataset", dataset)] + [
                    ("capture", c) for c in captures
                ]:
                    con.execute(
                        "INSERT INTO records VALUES (?,?,?)",
                        (kind, row["id"], json.dumps(row)),
                    )
            return {"dataset_id": did, "captures": len(captures), "errors": errors}
        except Exception:
            shutil.rmtree(dest, ignore_errors=True)
            raise
        finally:
            staged.unlink(missing_ok=True)

    @app.post("/api/upload")
    async def upload(file: UploadFile = File(...)):
        filename = Path((file.filename or "upload").replace("\\", "/")).name
        if Path(filename).suffix.lower() not in (".mat", ".zip"):
            raise HTTPException(415, "Upload a .mat recording or .zip dataset.")
        did = secrets.token_hex(12)
        staged = data / "staging" / did
        count = 0
        try:
            with staged.open("wb") as out:
                while chunk := await file.read(1024**2):
                    count += len(chunk)
                    if count > MAX_UPLOAD:
                        raise HTTPException(413, "Upload exceeds 256 MiB.")
                    out.write(chunk)
            if not count:
                raise HTTPException(422, "Empty upload.")
            return job_start(
                "import", lambda jid, p: import_recording(staged, filename, did, p)
            )
        except Exception:
            staged.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

    @app.delete("/api/datasets/{id}")
    def remove_dataset(id: str):
        get("dataset", id)
        if any(j["status"] in ("queued", "running") for j in rows("job")):
            raise HTTPException(
                409, "Wait for the current operation before deleting data."
            )
        # IDs are resolved through the database, never interpreted as an arbitrary path.
        for cap in rows("capture"):
            if cap["dataset_id"] == id:
                delete("capture", cap["id"])
        shutil.rmtree(data / "captures" / id, ignore_errors=True)
        for ext in (".mat", ".zip"):
            (data / "originals" / f"{id}{ext}").unlink(missing_ok=True)
        delete("dataset", id)
        return {"ok": True}

    def arrays(id):
        cap = get("capture", id)
        with np.load(data / cap["cache"], allow_pickle=False) as z:
            return cap, z["amplitude"], z["invalid"]

    @app.get("/api/captures/{id}")
    def capture(
        id: str,
        start: int = 0,
        length: int = 1024,
        subcarrier: int = -1,
        window: int = 256,
        hop: int = 128,
    ):
        cap, a, invalid = arrays(id)
        if (
            not 0 <= start < a.shape[1]
            or not 16 <= length <= 8192
            or not -1 <= subcarrier < a.shape[0]
        ):
            raise ValueError("Invalid trace range or subcarrier.")
        if not 16 <= window <= 2048 or not 1 <= hop <= window:
            raise ValueError("Invalid window/hop.")
        end = min(start + length, a.shape[1])
        segment = a[:, start:end]
        trace = np.median(segment, axis=0) if subcarrier < 0 else segment[subcarrier]
        selected = a[:, start : min(start + window, a.shape[1])]
        feats = core.four_features(selected)
        heatstep = max(1, int(np.ceil(segment.shape[1] / 256)))
        scstep = max(1, int(np.ceil(a.shape[0] / 64)))
        custom = []
        for s in range(0, a.shape[1] - window + 1, hop):
            custom.append(
                {
                    "start": s,
                    "end": s + window,
                    "valid_fraction": float((~invalid[s : s + window]).mean()),
                }
            )
            if len(custom) >= 10000:
                break
        return {
            "metadata": cap,
            "packet": list(range(start, end)),
            "trace": trace.tolist(),
            "heatmap": segment[::scstep, ::heatstep].tolist(),
            "heatmap_packet": list(range(start, end, heatstep)),
            "heatmap_subcarrier": list(range(0, a.shape[0], scstep)),
            "invalid_indices": np.flatnonzero(invalid[start:end]).tolist(),
            "feature_vector": feats.tolist(),
            "feature_means": feats.reshape(4, -1).mean(axis=1).tolist(),
            "inspection_windows": custom,
            "feature_window": {
                "start": start,
                "end": min(start + window, a.shape[1]),
                "preprocessing": "inspection only; raw zero-filled baseline",
            },
        }

    class DSPBody(BaseModel):
        capture_id: str | None = None
        operation: str = "moving_average"
        taps: int = Field(default=15, ge=3, le=127)
        window: str = "hann"
        cutoff: float = Field(default=0.1, gt=0, lt=0.5)
        kind: str = "lowpass"
        factor: int = Field(default=2, ge=2, le=8)
        start: int = Field(default=0, ge=0)
        length: int = Field(default=1024, ge=32, le=4096)
        subcarrier: int = Field(default=-1, ge=-1)

    @app.post("/api/dsp")
    def run_dsp(body: DSPBody):
        source = "EDUCATIONAL DEMO"
        x = core.demo_signal(body.length)
        if body.capture_id:
            cap, a, invalid = arrays(body.capture_id)
            if body.start >= a.shape[1] or body.subcarrier >= a.shape[0]:
                raise ValueError("Trace selection outside recording.")
            segment = a[:, body.start : body.start + body.length]
            if segment.shape[1] < 32:
                raise ValueError("Select at least 32 packets.")
            x = (
                np.median(segment, axis=0)
                if body.subcarrier < 0
                else segment[body.subcarrier]
            )
            source = "RECORDED DATA"
        result = core.dsp(
            x,
            **{
                k: v
                for k, v in body.model_dump().items()
                if k not in ("capture_id", "start", "length", "subcarrier")
            },
        )
        result.update(source=source, capture_id=body.capture_id, start=body.start)
        return result

    @app.post("/api/runs")
    def save_run(body: DSPBody):
        result = run_dsp(body)
        row = {
            "id": secrets.token_hex(12),
            "created": now(),
            "kind": "DSP",
            "source": result["source"],
            "settings": body.model_dump(),
            "metrics": result["metrics"],
            "note": result["note"],
        }
        put("run", row)
        return row

    @app.get("/api/captures/{id}/features")
    def features(id: str):
        cap, a, invalid = arrays(id)
        x, windows, audit = core.feature_windows(a, invalid, cap["bandwidth"])
        means = x.reshape(len(x), 4, -1).mean(axis=2) if len(x) else np.empty((0, 4))
        corr = np.nan_to_num(np.corrcoef(means.T), nan=0).tolist() if len(x) > 1 else []
        return {
            "contract": core.contract(cap["bandwidth"]),
            "windows": windows,
            "audit": audit,
            "group_means": means.tolist(),
            "correlation": corr,
        }

    class TrainBody(BaseModel):
        dataset_id: str | None = None
        bandwidth: int = 20
        split: str = "date"
        kinds: list[str] = Field(
            default_factory=lambda: ["lr", "rf", "mlp"], min_length=1, max_length=4
        )
        population: int = Field(default=8, ge=4, le=16)
        generations: int = Field(default=6, ge=1, le=15)
        mutation: float = Field(default=0.03, ge=0, le=0.3)

    @app.post("/api/train")
    def train(body: TrainBody):
        if (
            body.bandwidth not in (20, 40)
            or body.split not in ("date", "capture")
            or any(k not in ("lr", "rf", "mlp", "ga_rf") for k in body.kinds)
        ):
            raise ValueError("Unsupported training configuration.")
        captures = [
            c
            for c in rows("capture")
            if not body.dataset_id or c["dataset_id"] == body.dataset_id
        ]
        # Inferred bandwidth is useful for plots but never sufficient evidence for training.
        captures = [c for c in captures if c.get("bandwidth_verified")]

        def work(jid, p):
            result = models.train(
                captures,
                data,
                data / "models",
                jid,
                body.bandwidth,
                body.split,
                body.kinds,
                body.population,
                body.generations,
                body.mutation,
                p,
            )
            for row in result:
                put("model", row)
            row = {
                "id": jid,
                "kind": "training",
                "created": now(),
                "source": "RECORDED DATA",
                "models": [r["id"] for r in result],
            }
            put("run", row)
            return {"model_ids": row["models"]}

        return job_start("training", work)

    class PredictBody(BaseModel):
        capture_id: str
        model_id: str

    @app.post("/api/predict")
    def predict(body: PredictBody):
        cap = get("capture", body.capture_id)
        get("model", body.model_id)
        if not cap.get("bandwidth_verified"):
            raise ValueError(
                "Bandwidth must be verified by recording config before inference."
            )
        result = models.predict(cap, data, data / "models" / f"{body.model_id}.joblib")
        row = {
            "id": secrets.token_hex(12),
            "created": now(),
            "kind": "inference",
            **result,
        }
        put("run", row)
        return row

    class FuzzyBody(BaseModel):
        variation: float = Field(default=0.4, ge=0, le=1)
        motion: float = Field(default=0.6, ge=0, le=1)
        rules: list[dict] | None = None

    @app.post("/api/fuzzy")
    def fuzzy(body: FuzzyBody):
        return core.fuzzy(**body.model_dump())

    @app.get("/api/evidence")
    def evidence():
        names = [
            "presence_model_comparison_by_bandwidth",
            "ax_bf_simulation_summary",
            "cross_domain_transfer_metrics",
            "sensing_mode_readiness",
            "wifi_sensing_technology_comparison",
            "capture_level_model_predictions",
            "csi_capture_quality_audit",
            "model_validation_fold_details",
        ]
        out = {}
        for name in names:
            with (ROOT / "results" / f"{name}.csv").open(
                encoding="utf-8-sig", newline=""
            ) as f:
                out[name] = list(csv.DictReader(f))
        return out

    @app.get("/api/export/evidence/{name}")
    def export_evidence(name: str):
        allowed = {p.stem: p for p in (ROOT / "results").glob("*.csv")}
        if name not in allowed:
            raise HTTPException(404, "Result not found.")
        return FileResponse(
            allowed[name], filename=f"{name}.csv", media_type="text/csv"
        )

    @app.get("/api/export/run/{id}")
    def export_run(id: str):
        row = get("run", id)
        buffer = io.StringIO()
        records = row.get("windows") or [
            row.get("metrics", {"kind": row["kind"], "source": row["source"]})
        ]
        writer = csv.DictWriter(buffer, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
        return Response(
            buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="orbit-{id}.csv"'},
        )

    @app.get("/api/export/model/{id}")
    def export_model(id: str):
        row = get("model", id)
        return Response(
            json.dumps(row, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="orbit-model-{id}.json"'
            },
        )

    def lan_info():
        addresses = set()
        try:
            for result in socket.getaddrinfo(
                socket.gethostname(), None, socket.AF_INET
            ):
                ip = result[4][0]
                if not ip.startswith("127."):
                    addresses.add(ip)
        except OSError:
            pass
        return {
            "enabled": lan,
            "addresses": (
                [f"http://{ip}:{port}/#/upload" for ip in sorted(addresses)]
                if lan
                else []
            ),
            "local_url": f"http://127.0.0.1:{port}",
            "max_upload_mib": 256,
            "storage": str(data),
            "note": "Same trusted Wi-Fi/LAN required. Start with --lan to enable phone access. Allow Python on private networks in Windows Firewall only.",
        }

    @app.get("/api/server")
    def server():
        return lan_info()

    @app.get("/api/qr")
    def qr():
        addresses = lan_info()["addresses"]
        if not addresses:
            raise HTTPException(409, "LAN mode disabled or no LAN address found.")
        import qrcode
        from qrcode.image.svg import SvgPathImage

        output = io.BytesIO()
        qrcode.make(
            addresses[0], image_factory=SvgPathImage, box_size=8, border=3
        ).save(output)
        return Response(output.getvalue(), media_type="image/svg+xml")

    static = ROOT / "orbit" / "static"
    if static.exists():
        app.mount("/", StaticFiles(directory=static, html=True), name="frontend")
    app.add_middleware(UploadBodyLimit)
    return app
