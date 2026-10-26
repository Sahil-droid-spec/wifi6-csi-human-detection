"""FastAPI service. Run with python -m orbit; private by default."""

import csv
import hashlib
import io
import json
import os
import secrets
import shutil
import socket
import sqlite3
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import core, models

ROOT = Path(__file__).resolve().parents[1]
MAX_UPLOAD = 2 * 1024**3


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(4 * 1024**2), b""):
            h.update(chunk)
    return h.hexdigest()


class UploadBodyLimit:
    """Bound multipart bodies before the multipart spooler sees them."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") not in (
            "/api/upload",
            "/api/media",
        ):
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
                {"detail": "Upload request exceeds 2 GiB plus multipart overhead."},
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
    data = Path(data_dir or os.environ.get("ORBIT_DATA_DIR", ROOT / "orbit-data")).resolve()
    for name in ("originals", "captures", "models", "staging", "media", "references"):
        (data / name).mkdir(parents=True, exist_ok=True)
    code = access_code or secrets.token_hex(4).upper()
    sessions = set()
    attempts = {}
    guard = Lock()
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="orbit")
    db = data / "orbit.sqlite3"
    with closing(sqlite3.connect(db)) as con, con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS records (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id))"
        )

    def put(kind, row):
        with closing(sqlite3.connect(db)) as con, con:
            con.execute(
                "INSERT OR REPLACE INTO records VALUES (?,?,?)",
                (kind, row["id"], json.dumps(row)),
            )

    def rows(kind):
        with closing(sqlite3.connect(db)) as con, con:
            return [
                json.loads(x[0])
                for x in con.execute(
                    "SELECT body FROM records WHERE kind=? ORDER BY rowid DESC", (kind,)
                )
            ]

    def get(kind, id):
        with closing(sqlite3.connect(db)) as con, con:
            row = con.execute(
                "SELECT body FROM records WHERE kind=? AND id=?", (kind, id)
            ).fetchone()
        if not row:
            raise HTTPException(404, f"{kind} not found.")
        return json.loads(row[0])

    def delete(kind, id):
        with closing(sqlite3.connect(db)) as con, con:
            con.execute("DELETE FROM records WHERE kind=? AND id=?", (kind, id))

    sharing = {"enabled": lan}
    stored = rows("settings")
    if stored:
        sharing["enabled"] = bool(lan and stored[0].get("sharing", True))

    def local_request(request):
        return request.client is not None and request.client.host in (
            "127.0.0.1",
            "::1",
            "testclient",
        )

    for job in rows("job"):
        if job["status"] in ("queued", "running"):
            job.update(
                status="interrupted",
                message="Server restarted; submit the operation again.",
            )
            put("job", job)

    @asynccontextmanager
    async def lifespan(app):
        if hasattr(app.state, "extensions_start"):
            app.state.extensions_start()
        yield
        if hasattr(app.state, "extensions_close"):
            app.state.extensions_close()
        pool.shutdown(wait=True, cancel_futures=True)

    app = FastAPI(
        title="Orbit Wi-Fi Sensing Lab",
        version="2.2.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.instance_id = secrets.token_hex(8)
    app.state.code = code
    app.state.data = data
    app.state.records = rows
    print(
        f"\nOrbit access code: {code}\nLocal workspace: http://127.0.0.1:{port}\nData: {data}\n",
        flush=True,
    )

    @app.middleware("http")
    async def protect(request, call_next):
        if not sharing["enabled"] and not local_request(request):
            return JSONResponse({"detail": "Phone sharing is switched off on the laptop."}, 403)
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).netloc != request.headers.get("host"):
            return JSONResponse({"detail": "Cross-origin requests are not allowed."}, 403)
        host = request.url.hostname or ""
        try:
            import ipaddress

            private = (
                ipaddress.ip_address(host).is_private or ipaddress.ip_address(host).is_loopback
            )
        except ValueError:
            private = host in ("localhost", "testserver") or (host == "orbit.local" and lan)
        if not private:
            return JSONResponse({"detail": "Use the loopback or private LAN address."}, 400)
        if request.url.path.startswith("/api/") and request.url.path not in (
            "/api/health",
            "/api/auth",
            "/api/pair/claim",
            "/api/desktop/claim",
        ):
            with guard:
                allowed = request.cookies.get("orbit_session") in sessions
            if not allowed:
                return JSONResponse(
                    {"detail": "Enter the session access code shown in the laptop terminal."},
                    401,
                )
        try:
            response = await call_next(request)
        except Exception:
            # Do not send local paths or stack traces to clients.
            return JSONResponse({"detail": "Operation failed. Check the local server log."}, 500)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; object-src 'none'; frame-src 'none'; base-uri 'self'"
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
        return {
            "status": "online",
            "version": "2.2.0",
            "local_only": True,
            "instance_id": app.state.instance_id,
        }

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
        def summary(m):
            return {**m, "held_out_windows": {h: True for h in m.get("held_out_windows", {})}}

        return {
            "datasets": [d for d in rows("dataset") if not d.get("synthetic")],
            "simulation_datasets": [d for d in rows("dataset") if d.get("synthetic")],
            "simulation_captures": [c for c in rows("capture") if c.get("synthetic")],
            "simulation_runs": [r for r in rows("run") if r.get("source") == "SIMULATION"],
            "simulation_models": [
                summary(m) for m in rows("model") if m.get("source") == "SIMULATION"
            ],
            "captures": [c for c in rows("capture") if not c.get("synthetic")],
            "models": [summary(m) for m in rows("model") if m.get("source") != "SIMULATION"],
            "runs": [r for r in rows("run") if r.get("source") != "SIMULATION"][:50],
            "jobs": rows("job")[:30],
            "lan": sharing["enabled"],
            "media": rows("media"),
            "references": rows("reference"),
            "version": "2.2.0",
        }

    cancelled = set()

    @app.post("/api/jobs/{id}/cancel")
    def cancel_job(id: str):
        get("job", id)
        cancelled.add(id)
        return {
            "message": "Cancellation requested; stops after the current numerical fit or chunk."
        }

    def job_start(kind, fn):
        with guard:
            if any(j["status"] in ("queued", "running") for j in rows("job")):
                raise HTTPException(409, "Another operation is running. Wait for it to finish.")
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
            if jid in cancelled:
                raise ValueError("Cancelled by user. Change settings and run again when ready.")
            job.update(status="running", message=message, progress=percent)
            put("job", job)

        def work():
            try:
                progress("Starting", 1)
                result = fn(jid, progress)
                if jid in cancelled:
                    raise ValueError("Cancelled by user.")
                job.update(status="completed", progress=100, message="Completed", result=result)
            except Exception as exc:
                import logging

                logging.exception("Orbit background operation failed")
                job.update(
                    status="cancelled" if jid in cancelled else "failed", message=str(exc)[:500]
                )
            finally:
                put("job", job)

        pool.submit(work)
        return job

    @app.get("/api/jobs/{id}")
    def job(id: str):
        return get("job", id)

    def import_recording(staged, filename, did, progress, profile="inspect", label="unlabelled"):
        dest = data / "captures" / did
        dest.mkdir()
        extracted = dest / "source"
        extracted.mkdir()
        try:
            if filename.lower().endswith(".zip"):
                core.safe_extract(staged, extracted)
            else:
                shutil.copyfile(staged, extracted / "recording.mat")
                if profile in ("ax20", "ax40"):
                    (extracted / "config.json").write_text(
                        json.dumps(
                            {
                                "modulation": "ax",
                                "bandwidth": 20 if profile == "ax20" else 40,
                                "people": {
                                    "present": (None if label == "unlabelled" else label == "true")
                                },
                                "metadata_source": "user-provided upload profile",
                            }
                        ),
                        encoding="utf-8",
                    )
            mats = sorted(p for p in extracted.rglob("*") if p.suffix.lower() == ".mat")
            if not mats:
                raise ValueError("No supported .mat recordings found in the archive.")
            if len(mats) > 100:
                raise ValueError("Import at most 100 recordings per archive.")
            captures = []
            errors = []
            seen = set()
            for i, path in enumerate(mats):
                progress(
                    f"Validating recording {i + 1}/{len(mats)}",
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
                        warnings.append("Presence label unavailable; excluded from training.")
                    if invalid.any():
                        warnings.append(
                            f"{int(invalid.sum())} invalid/all-zero packet columns. Both bandwidths use validity-aware windows under contract v2."
                        )
                    if not (~invalid).any():
                        raise ValueError("Capture has no valid packet columns.")
                    _, windows, audit = core.feature_windows(a, invalid, inferred)
                    sha = file_hash(path)
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
                    np.savez_compressed(dest / f"{cid}.npz", amplitude=a, invalid=invalid)
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
                            "metadata_source": m["config"].get(
                                "metadata_source", "recording configuration"
                            ),
                            "source": "SIMULATION" if m.get("synthetic") else "RECORDED DATA",
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
                    "No valid CSI captures. " + "; ".join(e["error"] for e in errors[:3])
                )
            if len({bool(c.get("synthetic")) for c in captures}) > 1:
                raise ValueError("Keep simulation and real recordings in separate uploads.")
            original = data / "originals" / f"{did}{Path(filename).suffix.lower()}"
            shutil.move(str(staged), original)
            dataset = {
                "id": did,
                "name": filename,
                "created": now(),
                "captures": len(captures),
                "synthetic": bool(captures[0].get("synthetic")),
                "errors": errors,
                "sha256": file_hash(original),
                "size": original.stat().st_size,
            }
            # Register atomically so observers never see partial imports.
            with closing(sqlite3.connect(db)) as con, con:
                for kind, row in [("dataset", dataset)] + [("capture", c) for c in captures]:
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
    async def upload(
        file: UploadFile = File(...),
        profile: str = Form(default="inspect"),
        label: str = Form(default="unlabelled"),
    ):
        filename = Path((file.filename or "upload").replace("\\", "/")).name
        if Path(filename).suffix.lower() not in (".mat", ".zip"):
            raise HTTPException(415, "Upload a .mat recording or .zip dataset.")
        if profile not in ("inspect", "ax20", "ax40") or label not in (
            "unlabelled",
            "true",
            "false",
        ):
            raise ValueError("Unsupported capture profile or label.")
        did = secrets.token_hex(12)
        staged = data / "staging" / did
        count = 0
        try:
            with staged.open("wb") as out:
                while chunk := await file.read(1024**2):
                    count += len(chunk)
                    if count > MAX_UPLOAD:
                        raise HTTPException(413, "Upload exceeds 2 GiB.")
                    out.write(chunk)
            if not count:
                raise HTTPException(422, "Empty upload.")
            return job_start(
                "import",
                lambda jid, p: import_recording(staged, filename, did, p, profile, label),
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
            raise HTTPException(409, "Wait for the current operation before deleting data.")
        saved = [("dataset", get("dataset", id))] + [
            ("capture", c) for c in rows("capture") if c["dataset_id"] == id
        ]
        put("trash", {"id": id, "created": now(), "name": saved[0][1]["name"], "records": saved})
        for kind, row in saved:
            delete(kind, row["id"])
        arrays.cache_clear()
        return {"ok": True, "undo_id": id}

    @lru_cache(maxsize=2)
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
            "trace": [None if invalid[start + i] else float(v) for i, v in enumerate(trace)],
            "packet_audit": cap.get("packet_audit")
            or core.read_capture(data / cap["path"], cap["bandwidth"], with_audit=True)[3],
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
        beta: float = Field(default=8.6, ge=0, le=20)
        order: int = Field(default=4, ge=1, le=8)
        cutoff_high: float = Field(default=0.2, gt=0, lt=0.5)
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
            x = np.median(segment, axis=0) if body.subcarrier < 0 else segment[body.subcarrier]
            source = "SIMULATION" if cap.get("synthetic") else "RECORDED DATA"
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
        synthetic: bool = False
        kinds: list[str] = Field(
            default_factory=lambda: ["lr", "rf", "mlp"], min_length=1, max_length=7
        )
        population: int = Field(default=8, ge=4, le=16)
        generations: int = Field(default=6, ge=1, le=15)
        mutation: float = Field(default=0.03, ge=0, le=0.3)

    @app.get("/api/train/options")
    def training_options(synthetic: bool = False):
        captures = [c for c in rows("capture") if bool(c.get("synthetic")) == synthetic]
        return [
            {
                "dataset_id": did,
                "bandwidth": bw,
                "split": split,
                "kind": kind,
                **models.training_check(
                    [c for c in captures if not did or c["dataset_id"] == did], bw, split, [kind]
                ),
            }
            for did in [
                "",
                *[d["id"] for d in rows("dataset") if bool(d.get("synthetic")) == synthetic],
            ]
            for bw in (20, 40)
            for split in ("date", "capture")
            for kind in ("lr", "rf", "mlp", "ga_rf", "ga_lr", "ga_mlp", "ga_lr_ann")
        ]

    @app.post("/api/train")
    def train(body: TrainBody):
        if (
            body.bandwidth not in (20, 40)
            or body.split not in ("date", "capture")
            or any(
                k not in ("lr", "rf", "mlp", "ga_rf", "ga_lr", "ga_mlp", "ga_lr_ann")
                for k in body.kinds
            )
        ):
            raise ValueError("Unsupported training configuration.")
        captures = [
            c
            for c in rows("capture")
            if (not body.dataset_id or c["dataset_id"] == body.dataset_id)
            and bool(c.get("synthetic")) == body.synthetic
        ]
        # Inferred bandwidth is useful for plots but never sufficient evidence for training.
        captures = [c for c in captures if c.get("bandwidth_verified")]

        check = models.training_check(captures, body.bandwidth, body.split, body.kinds)
        if not check["valid"]:
            raise ValueError(check["reason"])

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
                "source": "SIMULATION" if body.synthetic else "RECORDED DATA",
                "models": [r["id"] for r in result],
            }
            put("run", row)
            return {"model_ids": row["models"]}

        return job_start("training", work)

    class PredictBody(BaseModel):
        capture_id: str
        model_id: str
        mode: str = "held_out"

    @app.post("/api/predict")
    def predict(body: PredictBody):
        cap = get("capture", body.capture_id)
        get("model", body.model_id)
        if not cap.get("bandwidth_verified"):
            raise ValueError("Bandwidth must be verified by recording config before inference.")
        result = models.predict(cap, data, data / "models" / f"{body.model_id}.joblib", body.mode)
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
            with (ROOT / "results" / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
                out[name] = list(csv.DictReader(f))
        return out

    @app.get("/api/export/evidence/{name}")
    def export_evidence(name: str):
        allowed = {p.stem: p for p in (ROOT / "results").glob("*.csv")}
        if name not in allowed:
            raise HTTPException(404, "Result not found.")
        return FileResponse(allowed[name], filename=f"{name}.csv", media_type="text/csv")

    @app.get("/api/export/run/{id}")
    def export_run(id: str):
        row = get("run", id)
        buffer = io.StringIO()
        records = row.get("windows") or [
            row.get("metrics", {"kind": row["kind"], "source": row["source"]})
        ]
        records = [
            {
                **record,
                "validation_protocol": row.get(
                    "validation_protocol",
                    "DSP trace transformation; not classifier validation"
                    if row["kind"] == "DSP"
                    else "No classifier evaluation",
                ),
                "source": row["source"],
                "synthetic": row["source"] == "SIMULATION",
            }
            for record in records
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
        row["synthetic"] = row.get("source") == "SIMULATION"
        return Response(
            json.dumps(row, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="orbit-model-{id}.json"'},
        )

    def lan_info():
        addresses = set()
        try:
            for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = result[4][0]
                if not ip.startswith("127."):
                    addresses.add(ip)
        except OSError:
            pass
        return {
            "enabled": sharing["enabled"],
            "bound_for_lan": lan,
            "addresses": (
                [f"http://{ip}:{port}/#/upload" for ip in sorted(addresses)]
                if sharing["enabled"]
                else []
            ),
            "local_url": f"http://127.0.0.1:{port}",
            "max_upload_mib": MAX_UPLOAD // 1024**2,
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
        qrcode.make(addresses[0], image_factory=SvgPathImage, box_size=8, border=3).save(output)
        return Response(output.getvalue(), media_type="image/svg+xml")

    class LocalImportBody(BaseModel):
        paths: list[str] = Field(min_length=1, max_length=10)

    @app.post("/api/local/import")
    def local_import(body: LocalImportBody, request: Request):
        if not local_request(request):
            raise HTTPException(403, "Local file import is available on the laptop only.")
        paths = [Path(p).resolve() for p in body.paths]
        if any(
            not p.is_file()
            or p.suffix.lower() not in (".mat", ".zip")
            or p.stat().st_size > MAX_UPLOAD
            for p in paths
        ):
            raise ValueError("Choose existing .mat or .zip files up to 2 GiB each.")

        def work(jid, progress):
            results = []
            for i, path in enumerate(paths):
                progress(f"Preparing {path.name}", int(i / len(paths) * 100))
                digest = file_hash(path)
                existing = next(
                    (d for d in rows("dataset") + rows("reference") if d.get("sha256") == digest),
                    None,
                )
                if existing:
                    results.append({"id": existing["id"], "already_saved": True})
                    continue
                if path.suffix.lower() == ".zip":
                    with zipfile.ZipFile(path) as archive:
                        contains_csi = any(
                            n.lower().endswith(".mat")
                            and "__MACOSX" not in n
                            and not Path(n).name.startswith("._")
                            for n in archive.namelist()
                        )
                    if not contains_csi:
                        rid = secrets.token_hex(12)
                        target = data / "references" / (rid + ".zip")
                        shutil.copyfile(path, target)
                        row = {
                            "id": rid,
                            "name": path.name,
                            "created": now(),
                            "sha256": digest,
                            "size": path.stat().st_size,
                            "path": str(target.relative_to(data)),
                            "kind": "Project reference",
                        }
                        put("reference", row)
                        results.append({"reference_id": rid})
                        continue
                did = secrets.token_hex(12)
                staged = data / "staging" / did
                shutil.copyfile(path, staged)
                result = import_recording(
                    staged,
                    path.name,
                    did,
                    lambda message, pct: progress(
                        f"{path.name} · {message}",
                        int((i + pct / 100) / len(paths) * 100),
                    ),
                )
                results.append(result)
            return {"imports": results}

        return job_start("import", work)

    @app.get("/api/references/{id}/file")
    def reference_file(id: str):
        row = get("reference", id)
        return FileResponse(data / row["path"], filename=row["name"], media_type="application/zip")

    @app.post("/api/media")
    async def upload_media(
        file: UploadFile = File(...),
        title: str = Form(default="", max_length=160),
        notes: str = Form(default="", max_length=2000),
        dataset_id: str = Form(default=""),
        capture_id: str = Form(default=""),
    ):
        allowed = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".webm": "video/webm",
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
        }
        name = Path((file.filename or "recording").replace("\\", "/")).name
        ext = Path(name).suffix.lower()
        if ext not in allowed:
            raise HTTPException(
                415,
                "Choose a JPG, PNG, WebP, GIF, MP4, MOV, WebM, WAV or MP3 recording.",
            )
        if dataset_id:
            get("dataset", dataset_id)
        if capture_id:
            cap = get("capture", capture_id)
            if dataset_id and cap["dataset_id"] != dataset_id:
                raise ValueError("The recording and dataset do not match.")
            dataset_id = cap["dataset_id"]
        rid = secrets.token_hex(12)
        target = data / "media" / (rid + ext)
        count = 0
        try:
            with target.open("wb") as out:
                while chunk := await file.read(1024**2):
                    count += len(chunk)
                    if count > 1024**3:
                        raise HTTPException(413, "Media recording exceeds 1 GiB.")
                    out.write(chunk)
            with target.open("rb") as source:
                header = source.read(32)
            valid = (
                ext in (".jpg", ".jpeg")
                and header.startswith(b"\xff\xd8\xff")
                or ext == ".png"
                and header.startswith(b"\x89PNG\r\n\x1a\n")
                or ext == ".gif"
                and header[:6] in (b"GIF87a", b"GIF89a")
                or ext == ".webp"
                and header[:4] == b"RIFF"
                and header[8:12] == b"WEBP"
                or ext in (".mp4", ".mov")
                and header[4:8] in (b"ftyp", b"moov", b"wide")
                or ext == ".webm"
                and header.startswith(b"\x1aE\xdf\xa3")
                or ext == ".wav"
                and header[:4] == b"RIFF"
                and header[8:12] == b"WAVE"
                or ext == ".mp3"
                and (
                    header.startswith(b"ID3")
                    or header[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")
                )
            )
            if not valid:
                raise ValueError("The file content does not match its image/video/audio extension.")
            row = {
                "id": rid,
                "name": name,
                "title": title.strip() or name,
                "notes": notes,
                "dataset_id": dataset_id or None,
                "capture_id": capture_id or None,
                "created": now(),
                "size": count,
                "type": allowed[ext],
                "path": str(target.relative_to(data)),
                "sha256": file_hash(target),
            }
            put("media", row)
            return row
        except Exception:
            target.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

    @app.get("/api/media/{id}/file")
    def media_file(id: str):
        row = get("media", id)
        return FileResponse(
            data / row["path"],
            media_type=row["type"],
            filename=row["name"],
            content_disposition_type="inline",
        )

    class SharingBody(BaseModel):
        enabled: bool

    @app.post("/api/server/sharing")
    def sharing_switch(body: SharingBody, request: Request):
        if not local_request(request):
            raise HTTPException(403, "Change phone sharing from the laptop workspace.")
        if body.enabled and not lan:
            raise HTTPException(
                409, "Restart using Start-Orbit-Server.cmd to enable the LAN interface."
            )
        sharing["enabled"] = body.enabled
        put("settings", {"id": "network", "sharing": body.enabled})
        return lan_info()

    class CompareBody(BaseModel):
        capture_id: str
        mode: str = "held_out"

    @app.post("/api/predict/compare")
    def compare_predictions(body: CompareBody):
        cap = get("capture", body.capture_id)
        chosen = {}
        for m in rows("model"):
            if (
                m["contract"]["bandwidth"] == cap["bandwidth"]
                and m["contract"] == core.contract(cap["bandwidth"])
                and (body.mode != "held_out" or cap["sha256"] in m.get("held_out_windows", {}))
                and bool(m.get("synthetic")) == bool(cap.get("synthetic"))
                and m["name"] not in chosen
            ):
                chosen[m["name"]] = m
        if not chosen:
            raise ValueError("Train a compatible classifier in Learning Lab first.")
        results = [
            predict(PredictBody(capture_id=body.capture_id, model_id=m["id"], mode=body.mode))
            for m in chosen.values()
        ]
        return {"capture_id": body.capture_id, "results": results}

    download_root = Path(os.environ.get("ORBIT_DOWNLOADS_DIR", ROOT.parent)).resolve()
    downloads_allowed = {
        "Orbit-Windows.zip": ("Native Windows desktop application", "application/zip"),
        "Simulation-set-A.zip": (
            "Simulation set A · all generated classes and sessions",
            "application/zip",
        ),
        "Simulation-Empty.zip": ("Simulation · empty channel", "application/zip"),
        "Simulation-One-Still.zip": ("Simulation · one person still", "application/zip"),
        "Simulation-One-Moving.zip": ("Simulation · one person moving", "application/zip"),
        "Orbit-Demo-1-Empty.zip": ("Classroom Simulation · empty · three sessions", "application/zip"),
        "Orbit-Demo-2-Still.zip": ("Classroom Simulation · one still · three sessions", "application/zip"),
        "Orbit-Demo-3-Moving.zip": ("Classroom Simulation · one moving · three sessions", "application/zip"),
        "Simulation-Two-People.zip": ("Simulation · two people", "application/zip"),
        "Orbit-Phone-Companion.apk": (
            "Android phone app",
            "application/vnd.android.package-archive",
        ),
        "Phone-Upload-Demo.zip": (
            "Small real-CSI file for a phone upload demo",
            "application/zip",
        ),
        "Orbit-Laptop-Windows-Demo.zip": (
            "Windows laptop app with saved captures and models",
            "application/zip",
        ),
        "Orbit-App.zip": (
            "Application source and compiled interface",
            "application/zip",
        ),
        "Orbit-Presentation-Runbook.md": (
            "Step-by-step presentation script",
            "text/markdown",
        ),
    }

    @app.get("/api/downloads")
    def download_catalog():
        return [
            {
                "name": name,
                "title": title,
                "size": (download_root / name).stat().st_size,
                "url": "/api/downloads/" + name,
            }
            for name, (title, mime) in downloads_allowed.items()
            if (download_root / name).is_file()
        ]

    @app.get("/api/downloads/{name}")
    def download_file(name: str):
        if name not in downloads_allowed or not (download_root / name).is_file():
            raise HTTPException(404, "Download is not available.")
        return FileResponse(
            download_root / name, filename=name, media_type=downloads_allowed[name][1]
        )

    static = ROOT / "orbit" / "static"
    if static.exists():
        from .extensions import install
    install(app, {**locals(), "now": now})
    app.mount("/", StaticFiles(directory=static, html=True), name="frontend")
    app.add_middleware(UploadBodyLimit)
    return app
