"""On-laptop, ephemeral frame inspection and educational pulse signal processing."""

import io
from functools import lru_cache
from threading import Lock

import numpy as np
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field
from scipy import signal
from starlette.concurrency import run_in_threadpool

FRAME_LIMIT = 350_000
_opencv_lock = Lock()


@lru_cache(maxsize=1)
def detectors():
    import cv2

    face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    eye = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
    if face.empty() or eye.empty():
        raise RuntimeError("Missing OpenCV cascade files")
    return cv2, face, eye, cv2.QRCodeDetector()


def inspect_frame(raw: bytes) -> dict:
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(raw), formats=["JPEG", "PNG"]) as image:
            if max(image.size) > 800 or min(image.size) < 24:
                raise ValueError("Use a frame between 24 and 800 pixels per side.")
            rgb = np.asarray(image.convert("RGB"))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Choose a readable JPEG or PNG.") from exc
    with _opencv_lock:
        cv2, face, eye, qr = detectors()
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        boxes = [list(map(int, b)) for b in face.detectMultiScale(gray, 1.15, 5, minSize=(32, 32))]
        eyes = []
        for x, y, w, h in boxes[:6]:
            for a, b, c, d in eye.detectMultiScale(
                gray[y : y + h // 2, x : x + w], 1.13, 5, minSize=(10, 10)
            ):
                eyes.append([int(x + a), int(y + b), int(c), int(d)])
        try:
            decoded = qr.detectAndDecode(gray)[0]
        except (UnicodeDecodeError, cv2.error):
            decoded = ""
    return {"faces": boxes, "eyes": eyes, "qr": decoded[:2048], "width": rgb.shape[1], "height": rgb.shape[0]}


class PulseInput(BaseModel):
    samples: list[tuple[float, float, float, float, float]] = Field(min_length=2, max_length=1200)


def analyse_pulse(samples: list[tuple[float, float, float, float, float]]) -> dict:
    data = np.asarray(samples, dtype=float)
    times, rgb, motion = data[:, 0], data[:, 1:4], data[:, 4]
    if not np.isfinite(data).all() or (np.diff(times) <= 0).any() or (
        (rgb < 0) | (rgb > 255)
    ).any() or ((motion < 0) | (motion > 1)).any():
        raise ValueError("Supply ordered timestamps and finite camera channel samples.")
    span = times[-1] - times[0]
    rate = 1 / np.median(np.diff(times))
    result = {
        "bpm": None,
        "protocol": "Single-window RGB rPPG, experimental. No clinical validation.",
        "duration_s": float(span),
        "sample_rate_hz": float(rate),
    }
    if span < 18 or span > 45 or not 12 <= rate <= 45 or np.max(np.diff(times)) > 0.35:
        return {**result, "reason": "Capture at least 18 seconds of continuous face video."}
    if float(np.median(rgb)) < 35 or float(np.percentile(rgb, 90)) > 245:
        return {**result, "reason": "Improve lighting and avoid glare on the face."}
    if float(np.percentile(motion, 90)) > 0.045:
        return {**result, "reason": "Keep your head and camera still."}
    grid = np.arange(0, span, 1 / rate)
    raw = np.column_stack([np.interp(grid, times - times[0], v) for v in rgb.T])
    normal = raw / raw.mean(axis=0).clip(1)
    # A normalized colour difference reduces common brightness changes.
    trace = signal.detrend(normal[:, 1] - (normal[:, 0] + normal[:, 2]) / 2)
    filt = signal.sosfiltfilt(signal.butter(3, [0.7, 3.3], fs=rate, btype="bandpass", output="sos"), trace)
    freq, power = signal.periodogram(filt, fs=rate, window="hann")
    eligible = (freq >= 0.7) & (freq <= 3.3)
    peak = int(np.argmax(power[eligible]))
    peak_hz = freq[eligible][peak]
    concentration = power[eligible & (np.abs(freq - peak_hz) <= 0.12)].sum() / max(power[eligible].sum(), 1e-15)
    stride = max(1, len(grid) // 600)
    result.update(
        times=grid[::stride].tolist(), rgb=raw[::stride].tolist(), filtered=filt[::stride].tolist(),
        frequency_hz=freq[eligible].tolist(), power=power[eligible].tolist(),
    )
    if np.std(filt) < 0.00045 or concentration < 0.48:
        return {**result, "reason": "No sufficiently distinct pulse-band peak. Try steady lighting and repeat."}
    return {**result, "bpm": float(60 * peak_hz), "reason": "Signal passed the experimental quality checks."}


def install(app, ctx):
    def require_laptop(request):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Open Camera Studio on the laptop for private frame analysis.")

    @app.post("/api/vision/frame")
    async def frame(request: Request):
        require_laptop(request)
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > FRAME_LIMIT:
                raise HTTPException(413, "Choose a smaller JPEG or PNG frame.")
            raw.extend(chunk)
        try:
            return await run_in_threadpool(inspect_frame, bytes(raw))
        except (ImportError, RuntimeError) as exc:
            raise HTTPException(503, "Install Orbit’s OpenCV runtime to enable frame analysis.") from exc

    @app.post("/api/vision/pulse")
    def pulse(body: PulseInput, request: Request):
        require_laptop(request)
        return analyse_pulse(body.samples)
