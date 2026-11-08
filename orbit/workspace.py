"""Shared asset lifecycle, safe contextual operations, and reproducible workflows."""

import csv
import hashlib
import html
import importlib.util
import io
import json
import secrets
import shutil
import threading
import time
import zipfile
from pathlib import Path
from typing import Literal

import numpy as np
from fastapi import File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from PIL import Image
from pydantic import BaseModel, Field
from scipy import ndimage
from starlette.background import BackgroundTask

from .acoustic_protocol import arq_simulate
from .audio_studio import Filter, analyse, apply_filter, encode_wav, read_wav
from .matlab_lab import matlab_executable
from .practicals import Practical
from .practicals import run as practical

CAP = 256 * 1024**2
MIMES = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".webm": "video/webm",
    ".mp4": "video/mp4",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".json": "application/json",
    ".npy": "application/octet-stream",
    ".npz": "application/octet-stream",
    ".mat": "application/octet-stream",
    ".zip": "application/zip",
}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024**2), b""):
            h.update(block)
    return h.hexdigest()


def capabilities(row):
    mime = row.get("type", "")
    name = row.get("name", "").lower()
    actions = ["export", "rename", "trash"]
    if mime == "audio/wav":
        actions += ["audio", "speech", "matlab", "separate"]
    elif mime.startswith("image/"):
        actions += ["image", "retina"]
    elif mime.startswith("video/"):
        actions += ["video"]
    elif name.endswith((".mat", ".npz", ".csv")):
        actions += ["csi-import"]
    elif name.endswith(".npy"):
        actions += ["iq"]
    return actions


class Metadata(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    notes: str = Field(default="", max_length=4000)
    synthetic: bool | None = None


class ImportReference(BaseModel):
    kind: Literal["exchange", "link_received"]
    id: str = Field(pattern="^[a-f0-9]{24}$")


class Pipeline(BaseModel):
    template: Literal["audio-filter", "image-edges", "iq-fm", "dsp-practical"] = "audio-filter"
    input_id: str | None = Field(default=None, pattern="^[a-f0-9]{24}$")
    name: str = Field(default="Experiment", min_length=1, max_length=160)
    notes: str = Field(default="", max_length=4000)
    filter: Filter = Field(default_factory=Filter)
    practical: Practical = Field(default_factory=Practical)
    sample_rate_hz: int = Field(default=48000, ge=16000, le=256000)


def install(app, ctx):
    data = ctx["data"]
    rows, get, put, delete = (ctx[k] for k in ("rows", "get", "put", "delete"))
    lock = threading.RLock()

    def asset(ident, include_trash=False):
        row = get("media", ident)
        if row.get("trashed") and not include_trash:
            raise HTTPException(404, "Restore this file from Trash first.")
        path = (data / row["path"]).resolve()
        if not path.is_relative_to((data / "media").resolve()):
            raise ValueError("This asset path is not in the media Library.")
        return row, path

    def save(raw, name, source, *, parent_id=None, synthetic=False, notes="", **metadata):
        if not 0 < len(raw) <= CAP:
            raise ValueError("Save a nonempty file up to 256 MiB.")
        name = Path(name.replace("\\", "/")).name[:180]
        ext = Path(name).suffix.lower()
        if ext not in MIMES:
            raise ValueError("Choose a supported data, image, video or audio format.")
        if shutil.disk_usage(data).free < len(raw) + 32 * 1024**2:
            raise ValueError("Free disk space on the laptop, then save again.")
        ident = secrets.token_hex(12)
        path = data / "media" / (ident + ext)
        row = {
            "id": ident,
            "name": name,
            "title": name,
            "created": ctx["now"](),
            "path": str(path.relative_to(data)),
            "size": len(raw),
            "type": MIMES[ext],
            "source": source,
            "synthetic": synthetic,
            "parent_id": parent_id,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "notes": notes,
            **metadata,
        }
        try:
            with path.open("xb") as f:
                f.write(raw)
            put("media", row)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return row

    ctx.update(save_asset=save, load_asset=asset)

    def catalog():
        return [{**r, "capabilities": capabilities(r)} for r in rows("media")]

    @app.get("/api/workspace")
    def state():
        return {
            "assets": catalog(),
            "experiments": rows("experiment")[:200],
            "templates": ["audio-filter", "image-edges", "iq-fm", "dsp-practical"],
        }

    @app.post("/api/workspace/import")
    async def upload(
        file: UploadFile = File(...),
        synthetic: bool = Form(False),
        source: str = Form("IMPORTED FILE", max_length=100),
    ):
        # Spool on disk so video imports do not allocate the entire upload in RAM.
        ext = Path(file.filename or "").suffix.lower()
        if ext not in MIMES:
            raise ValueError("Choose a supported file extension.")
        ident = secrets.token_hex(12)
        target = data / "media" / (ident + ext)
        count = 0
        h = hashlib.sha256()
        try:
            with target.open("xb") as out:
                while block := await file.read(1024**2):
                    count += len(block)
                    if count > CAP:
                        raise HTTPException(413, "Choose a file up to 256 MiB.")
                    if shutil.disk_usage(data).free < len(block) + 32 * 1024**2:
                        raise ValueError("Free disk space and retry the import.")
                    out.write(block)
                    h.update(block)
            if not count:
                raise ValueError("Choose a nonempty file.")
            name = Path((file.filename or "input" + ext).replace("\\", "/")).name[:180]
            row = {
                "id": ident,
                "name": name,
                "title": name,
                "path": str(target.relative_to(data)),
                "type": MIMES[ext],
                "size": count,
                "sha256": h.hexdigest(),
                "source": source,
                "synthetic": synthetic,
                "created": ctx["now"](),
                "notes": "Unprocessed input; each studio validates content before processing.",
            }
            put("media", row)
            return row
        except Exception:
            target.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

    @app.post("/api/workspace/import-reference")
    def import_reference(body: ImportReference):
        with lock:
            existing = next((r for r in rows("media") if r.get(body.kind + "_id") == body.id), None)
            if existing:
                if existing.get("trashed"):
                    raise HTTPException(409, "Restore the imported file from Library Trash.")
                return existing
            source = get(body.kind, body.id)
            if body.kind == "exchange" and source.get("status") != "complete":
                raise ValueError("Wait for SHA-256 verification before importing.")
            target = (
                data
                / ("exchange" if body.kind == "exchange" else "acoustic_link")
                / (body.id + (".bin" if body.kind == "link_received" else ""))
            )
            if target.stat().st_size > CAP or digest(target) != source["sha256"]:
                raise ValueError("Stored bytes do not match. Receive the original again.")
            # Streaming copy preserves large received videos without a second RAM copy.
            ext = Path(source["name"]).suffix.lower()
            if ext not in MIMES:
                raise ValueError("Download this format or import it with a compatible studio.")
            ident = secrets.token_hex(12)
            dest = data / "media" / (ident + ext)
            try:
                shutil.copyfile(target, dest)
                row = {
                    "id": ident,
                    "name": source["name"],
                    "title": source["name"],
                    "path": str(dest.relative_to(data)),
                    "created": ctx["now"](),
                    "size": source["size"],
                    "sha256": source["sha256"],
                    "type": MIMES[ext],
                    "source": "RECEIVED FILE · original provenance unspecified",
                    "synthetic": bool(source.get("synthetic")),
                    body.kind + "_id": body.id,
                    "notes": "Transfer copy is independent. Library lifecycle revokes its download while this Library copy is trashed/deleted.",
                }
                put("media", row)
                return row
            except Exception:
                dest.unlink(missing_ok=True)
                raise

    def revoke(row):
        for kind in ("exchange", "link_received"):
            if row.get(kind + "_id"):
                put(
                    "revoked_export",
                    {
                        "id": kind + ":" + row[kind + "_id"],
                        "reason": "Library copy was removed. Restore it in the Library or deliberately send a new copy.",
                    },
                )

    def unrevoke(row):
        for kind in ("exchange", "link_received"):
            if row.get(kind + "_id"):
                delete("revoked_export", kind + ":" + row[kind + "_id"])

    ctx.update(revoke_asset=revoke, unrevoke_asset=unrevoke)

    @app.patch("/api/workspace/assets/{ident}")
    def rename(ident: str, body: Metadata):
        with lock:
            row, _ = asset(ident)
            if not body.title.strip():
                raise ValueError("Enter a file title.")
            row.update(title=body.title.strip(), notes=body.notes)
            if body.synthetic is False and row.get("synthetic"):
                raise ValueError(
                    "Generated provenance cannot be relabelled as a real recording. Import a genuine recorded source separately."
                )
            if body.synthetic is not None:
                row["synthetic"] = body.synthetic
            put("media", row)
            return row

    @app.get("/api/workspace/assets/{ident}/export")
    def export_asset(ident: str):
        row, path = asset(ident)
        if shutil.disk_usage(data).free < row["size"] + 32 * 1024**2:
            raise ValueError("Free disk space before exporting a provenance bundle.")
        output = data / "staging" / ("export-" + secrets.token_hex(12) + ".zip")
        try:
            with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
                filename = Path(row["name"]).name
                if filename.lower() == "config.json":
                    filename = "input-config.json"
                checksum = hashlib.sha256()
                size = 0
                with path.open("rb") as source, archive.open(filename, "w") as target:
                    for block in iter(lambda: source.read(1024**2), b""):
                        target.write(block)
                        checksum.update(block)
                        size += len(block)
                if size != row["size"] or checksum.hexdigest() != row["sha256"]:
                    raise ValueError(
                        "Input bytes changed. Reimport the original before exporting provenance."
                    )
                archive.writestr(
                    "config.json",
                    json.dumps(
                        {
                            **row,
                            "synthetic": bool(row.get("synthetic")),
                            "validation_protocol": row.get(
                                "notes", "Unprocessed input; no validation metric asserted."
                            ),
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            return FileResponse(
                output,
                media_type="application/zip",
                filename="Orbit-file-with-provenance.zip",
                background=BackgroundTask(output.unlink, missing_ok=True),
            )
        except Exception:
            output.unlink(missing_ok=True)
            raise

    def require_local(request):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Manage Trash and permanent deletion on the laptop.")

    @app.post("/api/workspace/assets/{ident}/trash")
    def trash(ident: str, request: Request):
        require_local(request)
        with lock:
            row, _ = asset(ident)
            row["trashed"] = True
            row["trashed_at"] = ctx["now"]()
            put("media", row)
            revoke(row)
        return {
            "ok": True,
            "next_step": "Use Restore to undo. Independent exports already saved outside Orbit are unaffected.",
        }

    @app.post("/api/workspace/assets/{ident}/restore")
    def restore(ident: str, request: Request):
        require_local(request)
        with lock:
            row, _ = asset(ident, True)
            row.pop("trashed", None)
            row.pop("trashed_at", None)
            put("media", row)
            for kind in ("exchange", "link_received"):
                if row.get(kind + "_id"):
                    delete("revoked_export", kind + ":" + row[kind + "_id"])
        return row

    @app.delete("/api/workspace/assets/{ident}")
    def remove(ident: str, request: Request):
        require_local(request)
        with lock:
            row, path = asset(ident, True)
            if not row.get("trashed"):
                raise HTTPException(409, "Move this item to Trash before permanent deletion.")
            if any(
                ident in (r.get("parent_id"), r.get("secondary_parent_id")) for r in rows("media")
            ):
                raise HTTPException(
                    409, "Permanently delete linked derived versions before their original."
                )
            if any(r["status"] in ("queued", "running") for r in rows("job")):
                raise HTTPException(
                    409, "Wait for running jobs before permanently deleting inputs."
                )
            revoke(row)
            path.unlink(missing_ok=True)
            delete("media", ident)
        return {
            "ok": True,
            "retention": "Experiment history retains checksums and reports; it cannot reproduce a permanently deleted input. Files exported outside Orbit must be removed separately.",
        }

    def execute(body, progress):
        progress("Verifying input checksum", 5)
        row, path = asset(body.input_id) if body.input_id else (None, None)
        if row and (path.stat().st_size > 32 * 1024**2 or digest(path) != row["sha256"]):
            raise ValueError("Use a verified input under 32 MiB for this processing template.")
        report = {
            "name": body.name,
            "description": body.notes,
            "template": body.template,
            "parameters": body.model_dump(),
            "created": ctx["now"](),
            "input_refs": [
                {
                    "kind": "media",
                    "id": row["id"],
                    "sha256": row["sha256"],
                    "source": row.get("source", "UPLOADED"),
                    "synthetic": bool(row.get("synthetic")),
                }
            ]
            if row
            else [],
            "software_version": "Orbit 4.4",
            "limitations": [],
            "notes": body.notes,
        }
        began = time.perf_counter()
        output = None
        progress("Processing selected input", 25)
        if body.template == "dsp-practical":
            report.update(result=practical(body.practical), synthetic=True)
        elif body.template == "audio-filter":
            if not row:
                raise ValueError("Select a saved PCM WAV input.")
            rate, x = read_wav(path.read_bytes())
            y = apply_filter(x, rate, body.filter)
            raw, clipped = encode_wav(rate, y)
            report.update(
                result={
                    "input": analyse(rate, x),
                    "output": analyse(rate, y),
                    "clipped_samples": clipped,
                },
                synthetic=bool(row.get("synthetic")),
                validation_protocol="Same-input causal zero-state filter; original preserved. Waveform, Hann Welch PSD and STFT computed from input and PCM16 output.",
            )
            output = (raw, "filtered.wav")
        elif body.template == "image-edges":
            if not row:
                raise ValueError("Select a saved image.")
            with Image.open(path) as image:
                if image.width * image.height > 16_000_000:
                    raise ValueError("Choose an image below 16 megapixels.")
                image.thumbnail((1024, 1024))
                x = np.asarray(image.convert("L")) / 255
            smooth = ndimage.gaussian_filter(x, 1, mode="reflect")
            edges = np.hypot(ndimage.sobel(smooth, axis=0), ndimage.sobel(smooth, axis=1))
            raw = io.BytesIO()
            Image.fromarray(np.uint8(np.clip(edges, 0, 1) * 255)).save(raw, format="PNG")
            report.update(
                result={
                    "width": x.shape[1],
                    "height": x.shape[0],
                    "mean_edge_magnitude": float(edges.mean()),
                },
                synthetic=bool(row.get("synthetic")),
                validation_protocol="Same uploaded image resized to fit 1024px, grayscale, Gaussian sigma=1 pixel, Sobel magnitude. No segmentation accuracy asserted.",
            )
            output = (raw.getvalue(), "edges.png")
        else:
            if not row:
                raise ValueError("Select a complex I/Q NPY recording.")
            from .receiver import analyse as iq_analyse

            with path.open("rb") as source:
                version = np.lib.format.read_magic(source)
                shape, _, dtype = (
                    np.lib.format.read_array_header_1_0(source)
                    if version == (1, 0)
                    else np.lib.format.read_array_header_2_0(source)
                )
                if (
                    len(shape) != 1
                    or not 4096 <= shape[0] <= 262144
                    or dtype.kind != "c"
                    or dtype.itemsize > 16
                ):
                    raise ValueError(
                        "Use a one-dimensional NPY with 4096–262144 complex samples; object and oversized arrays are not accepted."
                    )
            iq = np.load(path, allow_pickle=False)
            r = iq_analyse(iq, body.sample_rate_hz, 0, "FM")
            raw, clipped = encode_wav(8000, np.asarray(r.pop("audio"))[:, None])
            report.update(
                result=r,
                synthetic=bool(row.get("synthetic")),
                validation_protocol="Selected complex recording, fixed receiver FM demodulation, 8 kHz normalized WAV; RF power is uncalibrated.",
            )
            output = (raw, "fm-audio.wav")
        progress("Saving reproducibility record", 85)
        report.update(elapsed_ms=(time.perf_counter() - began) * 1000, id=secrets.token_hex(12))
        # Cancellation is checked before committing any derived asset.
        if output:
            saved = save(
                output[0],
                output[1],
                "DERIVED WORKFLOW",
                parent_id=row["id"],
                synthetic=bool(report.get("synthetic")),
                experiment_id=report["id"],
            )
            report["output_id"] = saved["id"]
        try:
            put("experiment", report)
        except Exception:
            if output:
                (data / saved["path"]).unlink(missing_ok=True)
                delete("media", saved["id"])
            raise
        return report

    @app.post("/api/workspace/run")
    def run_pipeline(body: Pipeline):
        return ctx["job_start"]("workflow", lambda jid, progress: execute(body, progress))

    @app.post("/api/workspace/experiments/{ident}/rerun")
    def rerun(ident: str):
        report = get("experiment", ident)
        body = Pipeline(**report["parameters"])
        return ctx["job_start"]("workflow", lambda jid, progress: execute(body, progress))

    @app.get("/api/workspace/experiments/{ident}/export")
    def export(ident: str):
        return Response(
            json.dumps(get("experiment", ident), ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="Orbit-experiment.json"'},
        )

    @app.get("/api/workspace/experiments/{ident}/csv")
    def csv_export(ident: str):
        report = get("experiment", ident)
        r = report["result"]
        left = r.get("input", [])
        right = r.get("output", [])
        if isinstance(left, dict):
            tx = [
                i * left["duration"] / max(1, len(left["waveform"]) - 1)
                for i in range(len(left["waveform"]))
            ]
            ty = [
                i * right["duration"] / max(1, len(right["waveform"]) - 1)
                for i in range(len(right["waveform"]))
            ]
            left = [v[1] for v in left["waveform"]]
            right = [v[1] for v in right["waveform"]]
        else:
            tx = r.get("times", list(range(len(left))))
            ty = r.get("dense_times", tx) if len(right) != len(left) else tx
        if not isinstance(left, list) or not isinstance(right, list):
            raise ValueError("Use JSON export for this result type.")
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(
            [
                "source",
                "synthetic",
                "validation_protocol",
                "input_x",
                "input_value",
                "output_x",
                "output_value",
            ]
        )
        for i in range(max(len(left), len(right))):
            w.writerow(
                [
                    "SIMULATION" if report.get("synthetic") else "SELECTED INPUT",
                    bool(report.get("synthetic")),
                    report.get("validation_protocol", r.get("protocol", "")),
                    tx[i] if i < len(tx) and i < len(left) else "",
                    left[i] if i < len(left) else "",
                    ty[i] if i < len(ty) and i < len(right) else "",
                    right[i] if i < len(right) else "",
                ]
            )
        return Response(
            out.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="Orbit-measured-series.csv"'},
        )

    @app.get("/api/workspace/experiments/{ident}/print")
    def printable(ident: str):
        r = get("experiment", ident)
        escape = html.escape
        body = (
            "<h1>"
            + escape(r["name"])
            + "</h1><p>Print this page with Ctrl+P; choose Save as PDF if your browser offers it.</p>"
        )
        for label, value in [
            ("Source", "SIMULATION" if r.get("synthetic") else "SELECTED INPUT"),
            ("Created", r["created"]),
            ("Software", r["software_version"]),
            ("Validation protocol", r.get("validation_protocol", r["result"].get("protocol", ""))),
            ("Notes", r.get("notes", "")),
        ]:
            body += "<h2>" + label + "</h2><p>" + escape(str(value)) + "</p>"
        measured = {
            k: v
            for k, v in r["result"].items()
            if isinstance(v, (str, int, float, bool)) or v is None
        }
        measured["computation_ms"] = r.get("elapsed_ms")
        body += (
            "<h2>Measured outputs</h2><pre>"
            + escape(json.dumps(measured, ensure_ascii=False, indent=2))
            + "</pre>"
        )
        body += (
            "<h2>Inputs and checksums</h2><pre>"
            + escape(json.dumps(r["input_refs"], indent=2))
            + "</pre><h2>Parameters</h2><pre>"
            + escape(json.dumps(r["parameters"], indent=2))
            + "</pre>"
        )
        return Response(
            '<!doctype html><meta charset="utf-8"><title>Orbit experiment report</title><style>body{font:16px system-ui;max-width:850px;margin:40px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere}h2{font-size:18px}@media print{body{margin:0}}</style>'
            + body,
            media_type="text/html",
        )

    @app.get("/api/workspace/diagnostics")
    def diagnostics(request: Request):
        free = shutil.disk_usage(data)
        model = Path(__file__).resolve().parent.parent / "speech-models/vosk-model-small-en-us-0.15"
        return {
            "server": "CONNECTED",
            "storage_free_bytes": free.free,
            "storage_total_bytes": free.total,
            "matlab": "AVAILABLE" if matlab_executable() else "NOT INSTALLED",
            "simulink": "HARDWARE UNVERIFIED · run the licensed MATLAB comparison to verify toolbox",
            "speech": "AVAILABLE"
            if model.is_dir() and importlib.util.find_spec("vosk")
            else "NOT INSTALLED",
            "sdr": "AVAILABLE · enumerate devices on laptop"
            if importlib.util.find_spec("SoapySDR")
            else "NOT INSTALLED · install compatible driver and SoapySDR",
            "csi": "HARDWARE UNVERIFIED · normal Wi-Fi adapters do not expose CSI through this app; use a compatible external capture source",
            "phone": "Check another session's explicit readiness acknowledgement; server reachability alone is not phone acceptance",
            "browser_permissions": "PERMISSION REQUIRED · test microphone, camera and screen capture explicitly on this device",
            "local_laptop": ctx["local_request"](request),
            "protocol": "Actual file-system/dependency checks; no camera or microphone is opened by diagnostics.",
        }

    @app.get("/api/workspace/search")
    def search(q: str = ""):
        words = q.lower().strip().split()[:8]
        entries = [
            {
                "id": r["id"],
                "title": r.get("title", r["name"]),
                "route": "/workbench?asset=" + r["id"],
                "kind": "file",
            }
            for r in catalog()
            if not r.get("trashed")
        ]
        entries += [
            {
                "id": r["id"],
                "title": r["name"],
                "route": "/workbench?experiment=" + r["id"],
                "kind": "experiment",
            }
            for r in rows("experiment")
        ]
        return [
            r for r in entries if all(w in (r["title"] + " " + r["kind"]).lower() for w in words)
        ][:30]

    @app.post("/api/workspace/transport")
    async def recommend(request: Request):
        body = await request.json()
        size = body.get("bytes")
        if not isinstance(size, int) or not 0 < size <= CAP:
            raise ValueError("Provide a payload size from 1 byte to 256 MiB.")
        encrypted = bool(body.get("encrypted"))
        sound_only = bool(body.get("sound_only"))
        estimate = (size + 200) * 8 / 400
        method = (
            "Wi-Fi"
            if size > 8192 or estimate > 30
            else "Encrypted acoustic"
            if encrypted
            else "Acoustic"
        )
        return {
            "recommendation": method if not sound_only else "Keep acoustic-only selection",
            "acoustic_supported": size <= 8192,
            "estimated_payload_seconds": estimate,
            "protocol": "Rule-based lower estimate at 400 bit/s plus nominal envelope; actual framed WAV duration is shown after generation, not measured delivery time.",
            "why": "Wi-Fi suits large files and voice notes; sound is a low-rate teaching channel. Physical device availability and room reliability must be checked.",
            "manual_override": True,
            "silent_fallback": False,
        }

    @app.post("/api/workspace/arq")
    async def arq(request: Request):
        b = await request.json()
        return arq_simulate(
            str(b.get("text", "Hello Orbit"))[:1024].encode(),
            int(b.get("seed", 42)),
            float(b.get("data_loss", 0.2)),
            float(b.get("ack_loss", 0.1)),
            int(b.get("retries", 3)),
        )

    @app.post("/api/workspace/negotiate")
    async def negotiate(request: Request):
        b = await request.json()
        rates = b.get("peer_rates", [100, 200, 400])
        if (
            not isinstance(rates, list)
            or len(rates) > 10
            or not all(isinstance(x, int) for x in rates)
        ):
            raise ValueError("Provide a short list of supported bit rates.")
        common = sorted(set(rates) & {100, 200, 400})
        if not common:
            raise ValueError(
                "No common modem rate. Both peers must support at least one shared profile."
            )
        return {
            "protocol": "Orbit AgentLink/1 · deterministic capability negotiation; not generative AI or a physical link test",
            "bit_rate": min(common) if b.get("robust") else max(common),
            "fec": bool(b.get("fec", True)),
            "cipher": "AES-256-GCM",
            "max_payload_bytes": 8192,
            "automatic_transport_fallback": False,
        }
