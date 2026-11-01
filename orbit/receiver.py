"""Bounded offline IQ receiver. No hardware or RF power calibration claims."""

import io
import json
import math
import secrets

import numpy as np
from fastapi import Request
from fastapi.responses import FileResponse
from scipy import signal
from scipy.io import wavfile


def analyse(iq, rate, tune, modulation):
    iq = np.asarray(iq)
    if (
        iq.ndim != 1
        or not np.iscomplexobj(iq)
        or not 4096 <= len(iq) <= 262144
        or not np.isfinite(iq).all()
    ):
        raise ValueError("Use 4096–262144 finite complex samples in a one-dimensional NPY array.")
    if (
        not math.isfinite(rate)
        or not 16000 <= rate <= 256000
        or not math.isfinite(tune)
        or abs(tune) > rate * 0.4
        or modulation not in ("AM", "FM")
    ):
        raise ValueError("Choose AM/FM, sample rate 16–256 kHz and tuning within ±0.4 sample rate.")
    iq = iq - iq.mean()
    t = np.arange(len(iq)) / rate
    shifted = iq * np.exp(-2j * np.pi * t * tune)
    filtered = signal.sosfilt(
        signal.butter(6, min(10000, rate * 0.2), fs=rate, output="sos"), shifted
    )
    audio = (
        np.abs(filtered)
        if modulation == "AM"
        else np.r_[0, np.angle(filtered[1:] * np.conj(filtered[:-1]))] * rate / (2 * np.pi * 2000)
    )
    audio = signal.sosfilt(signal.butter(4, min(3000, rate * 0.15), fs=rate, output="sos"), audio)
    audio = signal.resample_poly(audio, 8000, int(rate))
    audio -= audio.mean()
    audio = audio / max(float(np.max(np.abs(audio))), 1e-12) * 0.9
    f, tt, s = signal.spectrogram(
        iq, fs=rate, nperseg=512, noverlap=256, return_onesided=False, mode="psd"
    )
    s = np.fft.fftshift(s, axes=0)
    f = np.fft.fftshift(f)
    p = s.mean(axis=1)
    db = 10 * np.log10(p + 1e-18)
    floor = float(np.median(db))
    peaks, _ = signal.find_peaks(db, height=floor + 12, distance=12, prominence=6)
    stations = [
        {
            "offset_hz": float(f[i]),
            "level_db_relative": float(db[i]),
            "contrast_db": float(db[i] - floor),
        }
        for i in peaks
    ]
    return {
        "frequency_hz": f.tolist(),
        "spectrum_db_relative": db.tolist(),
        "waterfall": (10 * np.log10(s[:, :: max(1, s.shape[1] // 80)] + 1e-18)).T.tolist(),
        "stations": stations,
        "audio": audio,
        "audio_rate": 8000,
        "iq_power_relative": float(np.mean(abs(iq) ** 2)),
        "waveform": iq.real[:: max(1, len(iq) // 500)].tolist(),
        "protocol": "Offline IQ analysis; relative PSD with arbitrary amplitude reference; peak contrast is not calibrated SNR. No modulation classifier or protocol decoder.",
        "tune_hz": tune,
        "modulation": modulation,
        "sample_rate": rate,
    }


def generate(rate=64000, seconds=1, seed=42):
    if rate != 64000 or not 0.25 <= seconds <= 2:
        raise ValueError("Simulation uses 64 ksample/s and 0.25–2 seconds.")
    t = np.arange(int(rate * seconds)) / rate
    rng = np.random.default_rng(seed)
    am = (1 + 0.5 * np.sin(2 * np.pi * 440 * t)) * np.exp(-2j * np.pi * 16000 * t)
    fm = np.exp(2j * np.pi * (16000 * t - 2000 / (2 * np.pi * 880) * np.cos(2 * np.pi * 880 * t)))
    return am + fm + 0.02 * (rng.normal(size=len(t)) + 1j * rng.normal(size=len(t)))


def install(app, ctx):
    root = ctx["data"] / "receiver"
    root.mkdir(exist_ok=True)

    def save(iq, rate, tune, modulation, source, center):
        if not math.isfinite(center) or center < 0:
            raise ValueError("Supply a finite non-negative center frequency in Hz.")
        r = analyse(iq, rate, tune, modulation)
        audio = r.pop("audio")
        ident = secrets.token_hex(12)
        wavfile.write(root / (ident + ".wav"), 8000, (audio * 32767).astype(np.int16))
        np.save(root / (ident + ".npy"), iq, allow_pickle=False)
        r.update(
            id=ident,
            source=source,
            center_hz=center,
            synthetic=source == "SIMULATED",
            audio_url="/api/receiver/" + ident + "/wav",
        )
        (root / (ident + ".json")).write_text(json.dumps(r))
        return r

    @app.post("/api/receiver/simulate")
    async def simulate(request: Request):
        b = await request.json()
        seconds = float(b.get("seconds", 1))
        seed = int(b.get("seed", 42))
        mod = b.get("modulation", "AM")
        tune = float(b.get("tune", -16000))
        r = save(generate(seconds=seconds, seed=seed), 64000, tune, mod, "SIMULATED", 100e6)
        r.update(seed=seed, seconds=seconds)
        (root / (r["id"] + ".json")).write_text(json.dumps(r))
        return r

    @app.post("/api/receiver/import")
    async def upload(
        request: Request, rate: int, center: float, tune: float = 0, modulation: str = "AM"
    ):
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > 5 * 1024 * 1024:
                raise ValueError("Use an IQ NPY smaller than 5 MiB.")
        return save(
            np.load(io.BytesIO(data), allow_pickle=False),
            rate,
            tune,
            modulation,
            "RECORDED IQ",
            center,
        )

    @app.get("/api/receiver/{ident}/{kind}")
    def export(ident: str, kind: str):
        if (
            len(ident) != 24
            or any(c not in "0123456789abcdef" for c in ident)
            or kind not in ("wav", "json", "npy")
        ):
            raise ValueError("Choose a saved receiver result.")
        path = root / (ident + "." + kind)
        if not path.is_file():
            raise ValueError("Run a receiver experiment first.")
        return FileResponse(
            path,
            media_type={
                "wav": "audio/wav",
                "json": "application/json",
                "npy": "application/octet-stream",
            }[kind],
            filename="Orbit-" + ident + "." + kind,
        )
