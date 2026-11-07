"""Consented fundus-image processing for educational inspection."""

import base64
import hashlib
import io
import json
import os
import secrets
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path
from threading import Lock
from typing import Literal

import numpy as np
from fastapi import HTTPException, Query, Request
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .matlab_lab import _active as matlab_active
from .matlab_lab import matlab_executable

MAX_BYTES = 8 * 1024**2
MAX_PIXELS = 16_000_000
analysis_lock = Lock()
save_lock = Lock()

MATLAB_SCRIPT = """% Orbit educational fundus processing. Requires Image Processing Toolbox.
I = imread('input.png');
if size(I,3)==3
    G = rgb2gray(I);
    C = I(:,:,2);
else
    G = I; C = I;
end
F = G > 15;
F = bwareafilt(F,1);
F = imerode(F,strel('disk',4,0));
E = medfilt2(adapthisteq(C),[3 3],'symmetric');
R = imbothat(E,strel('disk',ORBIT_RADIUS,0));
B = imbinarize(R,'adaptive','Sensitivity',ORBIT_SENSITIVITY) & F & (R > 0);
B = imopen(B,strel('disk',1,0));
B = bwareaopen(B,ORBIT_AREA);
imwrite(E,'enhanced.png');
imwrite(R,'response.png');
imwrite(B,'mask.png');
imwrite(F,'field.png');
fid=fopen('version.txt','w');fprintf(fid,'%s',version);fclose(fid);
"""


class Settings(BaseModel):
    source_kind: Literal["uploaded", "simulation"] = "uploaded"
    radius: int = Field(default=9, ge=3, le=20)
    minimum_area: int = Field(default=12, ge=0, le=400)
    sensitivity: float = Field(default=0.45, ge=0.1, le=0.8, allow_inf_nan=False)
    size: int = Field(default=768, ge=256, le=1024)
    engine: Literal["python", "matlab"] = "python"


def decode_image(raw: bytes, size: int) -> tuple[np.ndarray, tuple[int, int]]:
    if len(raw) > MAX_BYTES:
        raise ValueError("Choose a JPEG or PNG up to 8 MiB.")
    try:
        with Image.open(io.BytesIO(raw), formats=["JPEG", "PNG"]) as image:
            width, height = image.size
            if width * height > MAX_PIXELS or min(width, height) < 64:
                raise ValueError(
                    "Use an image at least 64 pixels per side and up to 16 megapixels."
                )
            image.load()
            rgb = image.convert("RGB")
            rgb.thumbnail((size, size), Image.Resampling.LANCZOS)
            return np.asarray(rgb), (width, height)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Choose a readable fundus JPEG or PNG.") from exc


def png(array: np.ndarray) -> bytes:
    output = io.BytesIO()
    Image.fromarray(array).save(output, format="PNG")
    return output.getvalue()


def python_pipeline(rgb: np.ndarray, settings: Settings) -> tuple[dict, str]:
    import cv2

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (gray > 15).astype(np.uint8), connectivity=8
    )
    if count <= 1:
        raise ValueError("The photo is too dark. Choose a clear fundus image.")
    component = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    field = cv2.erode((labels == component).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(
        bool
    )
    if field.mean() < 0.05:
        raise ValueError(
            "The illuminated image region is too small. Choose a clearer fundus image."
        )
    enhanced = cv2.medianBlur(
        cv2.createCLAHE(clipLimit=2, tileGridSize=(8, 8)).apply(rgb[:, :, 1]), 3
    )
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * settings.radius + 1, 2 * settings.radius + 1)
    )
    response = cv2.morphologyEx(enhanced, cv2.MORPH_BLACKHAT, kernel)
    # Sensitivity adjusts a local threshold on the bright vessel response.
    threshold = cv2.adaptiveThreshold(
        response,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        -8 * (1 - settings.sensitivity),
    )
    mask = ((threshold > 0) & (response > 0) & field).astype(np.uint8)
    mask = cv2.morphologyEx(
        mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    )
    _, components, areas, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    keep = areas[:, cv2.CC_STAT_AREA] >= settings.minimum_area
    keep[0] = False
    mask = keep[components] & field
    return {
        "enhanced": enhanced,
        "response": response,
        "mask": mask,
        "field": field,
    }, cv2.__version__


def matlab_pipeline(rgb: np.ndarray, settings: Settings, workspace: Path) -> tuple[dict, str]:
    executable = matlab_executable()
    if not executable:
        raise HTTPException(
            503, "Install licensed MATLAB with Image Processing Toolbox, or choose Python."
        )
    if not matlab_active.acquire(blocking=False):
        raise HTTPException(409, "Wait for the current MATLAB experiment to finish.")
    try:
        prefs = workspace / "matlab-prefs"
        prefs.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="orbit-retina-", dir=workspace) as directory:
            folder = Path(directory)
            (folder / "input.png").write_bytes(png(rgb))
            script = matlab_script(settings)
            (folder / "orbit_retina.m").write_text(script, encoding="utf-8")
            proc = subprocess.run(
                [
                    executable,
                    *(["-wait"] if os.name == "nt" else []),
                    "-batch",
                    "run('orbit_retina.m')",
                ],
                cwd=folder,
                env={**os.environ, "MATLAB_PREFDIR": str(prefs)},
                capture_output=True,
                timeout=150,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode:
                raise HTTPException(
                    503,
                    "Open MATLAB and check its Image Processing Toolbox license, or choose Python.",
                )
            result = {}
            for name in ("enhanced", "response", "mask", "field"):
                with Image.open(folder / (name + ".png")) as file:
                    result[name] = np.asarray(file.convert("L"))
            result["mask"] = result["mask"] > 0
            result["field"] = result["field"] > 0
            return result, (folder / "version.txt").read_text()
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(504, "MATLAB timed out. Check its license or choose Python.") from exc
    finally:
        matlab_active.release()


def matlab_script(settings: Settings) -> str:
    return (
        MATLAB_SCRIPT.replace("ORBIT_RADIUS", str(settings.radius))
        .replace("ORBIT_SENSITIVITY", str(settings.sensitivity))
        .replace("ORBIT_AREA", str(settings.minimum_area))
    )


def process(raw: bytes, settings: Settings, workspace: Path) -> tuple[dict, dict]:
    started = time.perf_counter()
    rgb, dimensions = decode_image(raw, settings.size)
    result, version = (
        matlab_pipeline(rgb, settings, workspace)
        if settings.engine == "matlab"
        else python_pipeline(rgb, settings)
    )
    overlay = rgb.copy()
    overlay[result["mask"]] = np.rint(
        0.45 * overlay[result["mask"]] + 0.55 * np.array([0, 220, 160])
    ).astype(np.uint8)
    files = {
        "preview": png(rgb),
        "enhanced": png(result["enhanced"]),
        "response": png(result["response"]),
        "mask": png(result["mask"].astype(np.uint8) * 255),
        "overlay": png(overlay),
    }
    report = {
        "source": "SIMULATION · generated image"
        if settings.source_kind == "simulation"
        else "UPLOADED FUNDUS · user declaration",
        "synthetic": settings.source_kind == "simulation",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_dimensions": list(dimensions),
        "processed_dimensions": [rgb.shape[1], rgb.shape[0]],
        "settings": settings.model_dump(),
        "engine_version": version,
        "candidate_pixels": int(result["mask"].sum()),
        "field_pixels": int(result["field"].sum()),
        "processing_ms": (time.perf_counter() - started) * 1000,
        "protocol": "Classical vessel-candidate segmentation. Reference annotations and clinical validation pending.",
        "validation": {"reference_mask": False, "accuracy": None, "dice": None},
        "engine_note": "OpenCV and MATLAB use their own CLAHE and adaptive-threshold implementations.",
    }
    return report, files


def install(app, ctx):
    @app.get("/api/retina")
    def library():
        return [r for r in ctx["rows"]("media") if r.get("retina_role")]

    @app.post("/api/retina/import")
    async def import_input(request: Request, consent: bool = False, synthetic: bool = False):
        if not consent:
            raise HTTPException(422, "Confirm permission to send this photo to the laptop.")
        raw = bytearray()
        async for part in request.stream():
            if len(raw) + len(part) > MAX_BYTES:
                raise HTTPException(413, "Choose a JPEG or PNG up to 8 MiB.")
            raw.extend(part)
        await run_in_threadpool(decode_image, bytes(raw), 256)
        digest = hashlib.sha256(raw).hexdigest()
        with save_lock:
            existing = next(
                (
                    r
                    for r in ctx["rows"]("media")
                    if r.get("retina_role") == "original"
                    and r["sha256"] == digest
                    and bool(r.get("synthetic")) == synthetic
                ),
                None,
            )
            if existing:
                return existing
            ident = secrets.token_hex(12)
            ext = ".jpg" if raw[:2] == b"\xff\xd8" else ".png"
            target = ctx["data"] / "media" / (ident + ext)
            row = {
                "id": ident,
                "name": "Orbit-fundus-input" + ext,
                "title": "Fundus · received input",
                "type": "image/jpeg" if ext == ".jpg" else "image/png",
                "path": str(target.relative_to(ctx["data"])),
                "size": len(raw),
                "sha256": digest,
                "created": ctx["now"](),
                "retina_role": "original",
                "parent_id": None,
                "synthetic": synthetic,
                "source": "SIMULATION" if synthetic else "UPLOADED FUNDUS",
                "notes": "Original image sent to the laptop for processing.",
            }
            try:
                target.write_bytes(raw)
                ctx["put"]("media", row)
            except Exception:
                target.unlink(missing_ok=True)
                raise
            return row

    @app.get("/api/retina/matlab-script")
    def export_script():
        return Response(
            matlab_script(Settings()),
            media_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="orbit_retina.m"'},
        )

    def save_results(raw, report, files):
        key = hashlib.sha256(
            (report["source_sha256"] + json.dumps(report["settings"], sort_keys=True)).encode()
        ).hexdigest()
        with save_lock:
            media = ctx["rows"]("media")
            old = [r for r in media if r.get("retina_group") == key]
            if not any(r["retina_role"] == "original" for r in old):
                original = next(
                    (
                        r
                        for r in media
                        if r.get("retina_role") == "original"
                        and r["sha256"] == report["source_sha256"]
                        and bool(r.get("synthetic")) == report["synthetic"]
                    ),
                    None,
                )
                if original:
                    old.append(original)
            roles = {row["retina_role"] for row in old}
            if roles == {"original", "enhanced", "mask", "overlay"}:
                return old
            now = ctx["now"]()
            original_id = next(
                (row["id"] for row in old if row["retina_role"] == "original"),
                secrets.token_hex(12),
            )
            original_ext = ".jpg" if raw[:2] == b"\xff\xd8" else ".png"
            assets = {
                "original": raw,
                "enhanced": files["enhanced"],
                "mask": files["mask"],
                "overlay": files["overlay"],
            }
            rows, written = [], []
            try:
                for name, content in assets.items():
                    if name in roles:
                        continue
                    ident = original_id if name == "original" else secrets.token_hex(12)
                    ext = original_ext if name == "original" else ".png"
                    target = ctx["data"] / "media" / (ident + ext)
                    with target.open("xb") as file:
                        file.write(content)
                    written.append(target)
                    rows.append(
                        {
                            "id": ident,
                            "name": "Orbit-fundus-" + name + ext,
                            "title": "Fundus · " + name,
                            "created": now,
                            "size": len(content),
                            "type": "image/jpeg" if ext == ".jpg" else "image/png",
                            "path": str(target.relative_to(ctx["data"])),
                            "sha256": hashlib.sha256(content).hexdigest(),
                            "source": report["source"],
                            "notes": report["protocol"],
                            "retina_role": name,
                            "synthetic": report["synthetic"],
                            "retina_group": key,
                            "parent_id": None if name == "original" else original_id,
                            "retina_report": report,
                        }
                    )
                with sqlite3.connect(ctx["db"]) as db:
                    db.executemany(
                        "INSERT INTO records VALUES (?,?,?)",
                        [("media", row["id"], json.dumps(row)) for row in rows],
                    )
            except Exception:
                for path in written:
                    path.unlink(missing_ok=True)
                raise
            return old + rows

    @app.post("/api/retina/analyse")
    async def analyse(
        request: Request,
        consent: bool = False,
        save: bool = False,
        radius: int = Query(9, ge=3, le=20),
        minimum_area: int = Query(12, ge=0, le=400),
        sensitivity: float = Query(0.45, ge=0.1, le=0.8, allow_inf_nan=False),
        size: int = Query(768, ge=256, le=1024),
        engine: Literal["python", "matlab"] = "python",
        source_kind: Literal["uploaded", "simulation"] = "uploaded",
    ):
        if not consent:
            raise HTTPException(422, "Confirm permission to process this fundus photo.")
        settings = Settings(
            radius=radius,
            minimum_area=minimum_area,
            sensitivity=sensitivity,
            size=size,
            engine=engine,
            source_kind=source_kind,
        )
        payload = bytearray()
        async for block in request.stream():
            if len(payload) + len(block) > MAX_BYTES:
                raise HTTPException(413, "Choose a JPEG or PNG up to 8 MiB.")
            payload.extend(block)
        if not analysis_lock.acquire(blocking=False):
            raise HTTPException(409, "Wait for the current retinal image to finish.")
        try:
            report, files = await run_in_threadpool(process, bytes(payload), settings, ctx["data"])
            saved = (
                await run_in_threadpool(save_results, bytes(payload), report, files) if save else []
            )
            return {
                **report,
                "saved": saved,
                "images": {
                    name: "data:image/png;base64," + base64.b64encode(raw).decode()
                    for name, raw in files.items()
                },
            }
        finally:
            analysis_lock.release()

    @app.delete("/api/retina/media/{ident}")
    def delete_image(ident: str, request: Request):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Delete saved fundus images from the laptop.")
        with save_lock:
            row = ctx["get"]("media", ident)
            if not row.get("retina_role"):
                raise HTTPException(404, "Choose an image saved by the retinal lab.")
            if any(r.get("parent_id") == ident for r in ctx["rows"]("media")):
                raise HTTPException(
                    409, "Delete the linked masks and overlays before the original."
                )
            (ctx["data"] / row["path"]).unlink(missing_ok=True)
            ctx["delete"]("media", ident)
        return {"ok": True}
