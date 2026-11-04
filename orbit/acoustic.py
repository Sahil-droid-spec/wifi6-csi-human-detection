"""Audible BFSK frames: 100 bit/s, preamble/sync, UTF-8 length and CRC32."""

import io
import json
import math
import secrets
import struct
import zlib
from math import gcd

import numpy as np
import scipy
from fastapi import Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from scipy import signal
from scipy.io import wavfile

RATE = 16000
SPS = 160
PREFIX = b"\x55" * 4 + b"\xd3\x91"
MAX_PAYLOAD = 160


def encode(text: str):
    payload = text.encode("utf-8")
    if not payload or len(payload) > MAX_PAYLOAD:
        raise ValueError("Enter 1–160 UTF-8 bytes; use short text for this 100 bit/s modem.")
    body = struct.pack(">H", len(payload)) + payload
    frame = PREFIX + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    bits = np.unpackbits(np.frombuffer(frame, dtype=np.uint8))
    t = np.arange(SPS) / RATE
    wave = np.concatenate([0.65 * np.sin(2 * np.pi * (2200 if b else 1200) * t) for b in bits])
    audio = np.r_[np.zeros(1600), wave, np.zeros(1600)]
    return audio, bits


def decode(audio):
    x = np.asarray(audio, dtype=float)
    if x.ndim != 1 or not 1600 <= len(x) <= RATE * 30 or not np.isfinite(x).all():
        raise ValueError("Use a finite mono recording lasting 0.1–30 seconds.")
    if np.max(np.abs(x)) < 1e-8:
        raise ValueError("No audio detected. Check recording level and input file.")
    x = x - np.mean(x)
    t = np.arange(SPS) / RATE
    kernels = np.array([np.exp(-2j * np.pi * f * t) for f in (1200, 2200)]).T
    sync = "".join(map(str, np.unpackbits(np.frombuffer(PREFIX, dtype=np.uint8))))
    last = []
    # Search timing phases; noncoherent energy supports unknown carrier phase.
    for offset in range(0, SPS, 8):
        n = (len(x) - offset) // SPS
        symbols = x[offset : offset + n * SPS].reshape(n, SPS)
        energy = abs(symbols @ kernels) ** 2
        bits = (energy[:, 1] > energy[:, 0]).astype(np.uint8)
        last = bits.tolist()
        stream = "".join(map(str, bits))
        start = stream.find(sync)
        while start >= 0:
            pos = start + len(sync)
            if pos + 16 <= len(bits):
                size = int.from_bytes(np.packbits(bits[pos : pos + 16]).tobytes(), "big")
                end = pos + 16 + size * 8 + 32
                if 0 < size <= MAX_PAYLOAD and end <= len(bits):
                    body = np.packbits(bits[pos : end - 32]).tobytes()
                    expected = int.from_bytes(np.packbits(bits[end - 32 : end]).tobytes(), "big")
                    if zlib.crc32(body) & 0xFFFFFFFF == expected:
                        return {
                            "crc_valid": True,
                            "decoded_text": body[2:].decode("utf-8", errors="replace"),
                            "payload_bytes": size,
                            "recovered_bits": bits[start:end].tolist(),
                            "start_sample": offset + start * SPS,
                            "timing_phase_samples": offset,
                            "symbol_energy": energy[start:end:8].tolist(),
                            "protocol": "CRC32-checked BFSK frame; no encryption or calibrated confidence. Physical link is verified only for actual supplied microphone recordings.",
                        }
            start = stream.find(sync, start + 1)
    return {
        "crc_valid": False,
        "decoded_text": None,
        "recovered_bits": last[:2048],
        "reason": "No complete CRC-valid frame. Use the full recording, match tones/rate, reduce noise and retry. No decoded message is asserted.",
    }


def plots(audio):
    f, t, s = signal.spectrogram(audio, fs=RATE, nperseg=256, noverlap=128)
    db = 10 * np.log10(s + 1e-15)
    step = max(1, len(t) // 100)
    spectrum = 10 * np.log10(
        abs(np.fft.rfft(audio * np.hanning(len(audio)))) ** 2 / len(audio) + 1e-15
    )
    stride = max(1, len(spectrum) // 512)
    return {
        "waveform": audio[:: max(1, len(audio) // 600)].tolist(),
        "time_seconds": (np.arange(len(audio))[:: max(1, len(audio) // 600)] / RATE).tolist(),
        "spectrum_db_relative": spectrum[::stride].tolist(),
        "frequency_hz": np.fft.rfftfreq(len(audio), 1 / RATE)[::stride].tolist(),
        "spectrogram": db[:, ::step].T.tolist(),
        "spectrogram_frequency_hz": f.tolist(),
        "duration_seconds": len(audio) / RATE,
    }


class EncodeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=160)
    loopback: bool = False
    noise_std: float = Field(default=0.03, ge=0, le=0.5, allow_inf_nan=False)


def install(app, ctx):
    root = ctx["data"] / "acoustic"
    root.mkdir(exist_ok=True)

    def save(audio, result):
        ident = secrets.token_hex(12)
        wavfile.write(root / (ident + ".wav"), RATE, np.int16(np.clip(audio, -1, 1) * 32767))
        result.update(
            synthetic=True
            if result.get("source") in ("SIMULATED LOOPBACK", "GENERATED TRANSMIT AUDIO")
            else None,
            physical_link_verified=False,
            created=ctx["now"](),
            software_versions={"numpy": np.__version__, "scipy": scipy.__version__},
            algorithm="Noncoherent BFSK energy detector with timing search, framing and CRC32",
            sample_count=len(audio),
            wav_export_clipped_samples=int(np.sum(np.abs(audio) > 1)),
            wav_export_format="PCM16; clips to [-1,1] and quantizes analyzed float samples; re-decode exported WAV to evaluate that derived file",
            id=ident,
            audio_url="/api/acoustic/" + ident + "/wav",
            sample_rate=RATE,
            bit_rate=RATE / SPS,
            tones_hz=[1200, 2200],
            **plots(audio),
        )
        (root / (ident + ".json")).write_text(json.dumps(result))
        return result

    @app.post("/api/acoustic/encode")
    async def transmit(body: EncodeRequest):
        b = body.model_dump()
        text = b.get("text", "")
        if not isinstance(text, str) or len(text) > 160:
            raise ValueError("Enter short text, at most 160 UTF-8 bytes.")
        audio, bits = encode(text)
        if b.get("loopback", False):
            noise = float(b.get("noise_std", 0.03))
            if not math.isfinite(noise) or not 0 <= noise <= 0.5:
                raise ValueError("Choose noise standard deviation from 0 to 0.5.")
            received = audio + np.random.default_rng(42).normal(0, noise, len(audio))
            r = decode(received)
            recovered = r.get("recovered_bits", [])
            ber = (
                float(np.mean(np.array(recovered) != bits))
                if r["crc_valid"] and len(recovered) == len(bits)
                else None
            )
            return save(
                received,
                {
                    "source": "SIMULATED LOOPBACK",
                    "seed": 42,
                    "noise_std": noise,
                    "original_text": text,
                    "transmitted_bits": bits.tolist(),
                    "ber": ber,
                    "frame_success_rate": int(r["crc_valid"]),
                    "validation_protocol": "Single generated frame; known bit sequence; seed 42 additive noise, std "
                    + str(noise)
                    + ". BER only on aligned CRC-valid frame; failures retained. Not a physical channel test.",
                    **r,
                },
            )
        return save(
            audio,
            {
                "source": "GENERATED TRANSMIT AUDIO",
                "original_text": text,
                "transmitted_bits": bits.tolist(),
                "validation_protocol": "Generated sound only. Playing this WAV does not demonstrate receiver success.",
            },
        )

    @app.post("/api/acoustic/decode")
    async def receive(
        request: Request,
        source: str = Query("UPLOADED AUDIO", pattern="^(UPLOADED AUDIO|MICROPHONE RECORDING)$"),
    ):
        content = bytearray()
        async for part in request.stream():
            content.extend(part)
            if len(content) > 6 * 1024**2:
                raise ValueError("Use a PCM WAV smaller than 6 MiB.")
        rate, a = wavfile.read(io.BytesIO(content))
        if rate < 8000 or rate > 96000 or len(a) > rate * 30 or a.ndim > 2:
            raise ValueError("Use a mono/stereo WAV up to 30 seconds, 8–96 ksample/s.")
        if np.issubdtype(a.dtype, np.integer):
            a = (
                (a.astype(float) - 128) / 128
                if a.dtype == np.uint8
                else a.astype(float) / max(abs(np.iinfo(a.dtype).min), np.iinfo(a.dtype).max)
            )
        if a.ndim == 2:
            a = a.mean(axis=1)
        g = gcd(rate, RATE)
        a = signal.resample_poly(a, RATE // g, rate // g)
        if not np.isfinite(a).all() or np.max(np.abs(a), initial=0) > 4:
            raise ValueError("Use finite, normalized audio levels in the WAV file.")
        r = decode(a)
        return save(
            a,
            {
                "source": source,
                "validation_protocol": "Decode of user-supplied WAV; source label does not certify physical speaker-to-microphone transmission. Ground-truth bits absent, so BER is unavailable.",
                "ber": None,
                **r,
            },
        )

    @app.get("/api/acoustic/{ident}/{kind}")
    def exported(ident: str, kind: str):
        if (
            len(ident) != 24
            or any(c not in "0123456789abcdef" for c in ident)
            or kind not in ("wav", "json")
        ):
            raise ValueError("Choose a saved modem experiment.")
        p = root / (ident + "." + kind)
        if not p.is_file():
            raise ValueError("Generate or decode a modem frame first.")
        return FileResponse(
            p,
            filename="Orbit-acoustic-" + ident + "." + kind,
            media_type="audio/wav" if kind == "wav" else "application/json",
        )
