"""WAV analysis and non-destructive versions in Orbit's existing media library."""

import hashlib
import io
import secrets
from pathlib import Path
from threading import Lock
from typing import Literal

import numpy as np
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field
from scipy import signal
from scipy.io import wavfile

MAX_WAV = 12 * 1024**2
MAX_SECONDS = 60


class Filter(BaseModel):
    kind: Literal["lowpass", "highpass", "bandpass", "notch", "hamming"] = "lowpass"
    cutoff_hz: float = Field(default=1200, gt=0, allow_inf_nan=False)
    upper_hz: float = Field(default=2500, gt=0, allow_inf_nan=False)


class Import(BaseModel):
    exchange_id: str = Field(pattern="^[a-f0-9]{24}$")


class Rename(BaseModel):
    title: str = Field(min_length=1, max_length=160)


def read_wav(raw: bytes) -> tuple[int, np.ndarray]:
    if len(raw) < 44 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError("Choose a readable 16-bit PCM WAV.")
    if int.from_bytes(raw[4:8], "little") + 8 > len(raw):
        raise ValueError("The WAV is truncated. Export the original again.")
    try:
        rate, samples = wavfile.read(io.BytesIO(raw))
    except (ValueError, OSError, EOFError) as exc:
        raise ValueError("Choose a readable 16-bit PCM WAV.") from exc
    if samples.ndim == 1:
        samples = samples[:, None]
    if samples.dtype != np.int16 or samples.shape[1] not in (1, 2) or not 8000 <= rate <= 48000:
        raise ValueError("Use 16-bit PCM WAV, mono or stereo, at 8–48 kHz.")
    if not 32 <= len(samples) <= rate * MAX_SECONDS:
        raise ValueError("Choose a WAV with at least 32 samples and up to 60 seconds.")
    return rate, samples.astype(float) / 32768


def encode_wav(rate: int, x: np.ndarray) -> tuple[bytes, int]:
    levels = np.rint(x * 32768)
    clipped = int(np.count_nonzero((levels < -32768) | (levels > 32767)))
    raw = io.BytesIO()
    wavfile.write(raw, rate, levels.clip(-32768, 32767).astype("<i2"))
    return raw.getvalue(), clipped


def apply_filter(x: np.ndarray, rate: int, settings: Filter) -> np.ndarray:
    edge = settings.cutoff_hz
    if edge >= rate / 2 or (
        settings.kind == "bandpass" and not edge < settings.upper_hz < rate / 2
    ):
        raise ValueError("Keep the cutoff edges ordered and below half the sample rate.")
    if settings.kind == "hamming":
        taps = signal.firwin(63, edge, fs=rate, window="hamming")
        return signal.lfilter(taps, [1], x, axis=0)
    if settings.kind == "notch":
        b, a = signal.iirnotch(edge, 30, fs=rate)
        return signal.lfilter(b, a, x, axis=0)
    edges = [edge, settings.upper_hz] if settings.kind == "bandpass" else edge
    return signal.sosfilt(
        signal.butter(4, edges, btype=settings.kind, fs=rate, output="sos"), x, axis=0
    )


def analyse(rate: int, x: np.ndarray) -> dict:
    channel = x[:, 0]
    # Min/max pairs retain brief peaks when rendering a long waveform.
    blocks = np.array_split(channel, min(400, len(channel)))
    n = min(len(channel), 1024)
    freq, power = signal.welch(channel, fs=rate, nperseg=n, window="hann")
    frequencies, times, z = signal.stft(channel, fs=rate, nperseg=min(512, n), boundary=None)
    stride = max(1, (len(times) + 95) // 96)
    spectrum = 10 * np.log10(np.maximum(power, 1e-16))
    return {
        "rate": rate,
        "channels": x.shape[1],
        "frames": len(channel),
        "duration": len(channel) / rate,
        "waveform": [[float(block.min()), float(block.max())] for block in blocks],
        "spectrum_hz": freq.tolist(),
        "spectrum_db": spectrum.tolist(),
        "stft_seconds": times[::stride].tolist(),
        "stft_hz": frequencies[::2].tolist(),
        "stft_db": (20 * np.log10(np.maximum(abs(z[::2, ::stride]), 1e-8))).round(2).tolist(),
        "protocol": "Channel 1 display. Min/max time buckets, Hann Welch PSD (dBFS²/Hz), Hann STFT (dBFS).",
    }


def install(app, ctx):
    data = ctx["data"]
    rows, put, get, delete = (ctx[k] for k in ("rows", "put", "get", "delete"))
    lock = Lock()

    def item(ident, *, trash=False):
        row = get("media", ident)
        if row["type"] != "audio/wav" or bool(row.get("trashed")) != trash:
            raise HTTPException(404, "Choose a WAV from the correct Library view.")
        return row

    def load(row):
        target = data / row["path"]
        if target.stat().st_size > MAX_WAV:
            raise HTTPException(413, "Choose a WAV smaller than 12 MiB.")
        raw = target.read_bytes()
        return read_wav(raw)

    def save(raw, name, notes, **meta):
        ident = secrets.token_hex(12)
        target = data / "media" / (ident + ".wav")
        row = {
            "id": ident,
            "name": name,
            "title": name,
            "type": "audio/wav",
            "created": ctx["now"](),
            "size": len(raw),
            "path": str(target.relative_to(data)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "notes": notes,
            "dataset_id": None,
            "capture_id": None,
            "audio_studio": True,
            **meta,
        }
        try:
            with target.open("xb") as file:
                file.write(raw)
            put("media", row)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return row

    @app.get("/api/audio")
    def library():
        return [row for row in rows("media") if row["type"] == "audio/wav"]

    @app.post("/api/audio/import")
    def from_exchange(body: Import):
        row = get("exchange", body.exchange_id)
        if row["status"] != "complete" or Path(row["name"]).suffix.lower() != ".wav":
            raise ValueError("Choose a verified WAV from Transfer & chat.")
        if row["size"] > MAX_WAV:
            raise HTTPException(413, "Choose a WAV smaller than 12 MiB.")
        with lock:
            for existing in rows("media"):
                if existing.get("exchange_id") == row["id"]:
                    if existing.get("trashed"):
                        raise HTTPException(409, "Restore this WAV from Audio Studio Trash first.")
                    return existing
            target = data / "exchange" / row["id"]
            with target.open("rb") as file:
                raw = file.read(MAX_WAV + 1)
            if len(raw) != row["size"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
                raise HTTPException(
                    409, "The saved bytes changed. Send and verify the original again."
                )
            rate, samples = read_wav(raw)
            return save(
                raw,
                row["name"],
                "Saved from verified file exchange.",
                exchange_id=row["id"],
                source="TRANSFERRED WAV · content provenance unspecified",
                sample_rate=rate,
                channels=samples.shape[1],
            )

    @app.get("/api/audio/{ident}/analysis")
    def analysis(ident: str):
        with lock:
            row = item(ident)
            rate, x = load(row)
        return {**analyse(rate, x), "source": row.get("source", "UPLOADED WAV")}

    @app.post("/api/audio/{ident}/filter")
    def run(ident: str, body: Filter):
        with lock:
            row = item(ident)
            rate, x = load(row)
            raw, clipped = encode_wav(rate, apply_filter(x, rate, body))
            label = f"{Path(row['name']).stem[:125]}-{body.kind}.wav"
            return save(
                raw,
                label,
                "Causal filter with zero initial state; stored as PCM16.",
                parent_id=ident,
                filter=body.model_dump(),
                sample_rate=rate,
                channels=x.shape[1],
                clipped_samples=clipped,
                source="DERIVED WAV",
            )

    @app.patch("/api/audio/{ident}")
    def rename(ident: str, body: Rename):
        with lock:
            row = item(ident)
            if not body.title.strip():
                raise ValueError("Enter a title.")
            row["title"] = body.title.strip()
            put("media", row)
        return row

    @app.post("/api/audio/{ident}/trash")
    def trash(ident: str, request: Request):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Move saved audio to Trash on the laptop.")
        with lock:
            row = item(ident)
            row["trashed"] = True
            put("media", row)
        return {"ok": True}

    @app.post("/api/audio/{ident}/restore")
    def restore(ident: str, request: Request):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Restore saved audio on the laptop.")
        with lock:
            row = item(ident, trash=True)
            row.pop("trashed")
            put("media", row)
        return {"ok": True}

    @app.delete("/api/audio/{ident}")
    def remove(ident: str, request: Request):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Permanently delete saved audio on the laptop.")
        with lock:
            row = item(ident, trash=True)
            if any(other.get("parent_id") == ident for other in rows("media")):
                raise HTTPException(
                    409, "Delete linked audio versions before permanently deleting the original."
                )
            (data / row["path"]).unlink(missing_ok=True)
            delete("media", ident)
        return {"ok": True}
