"""Binary BFSK frames and optional AES-GCM, decoded only from received samples."""

import base64
import hashlib
import io
import json
import math
import secrets
import struct
import threading
import time
import zlib
from pathlib import Path
from typing import Literal

import numpy as np
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from scipy import signal
from scipy.io import wavfile
from starlette.concurrency import run_in_threadpool

from . import acoustic_protocol as fec_codec
from .acoustic import PREFIX, RATE, plots

SPS = 40
BIT_RATE = RATE // SPS
TONES = (1200, 2400)
CHUNK = 128
MAX_CONTENT = 8192
MAX_ENVELOPE = MAX_CONTENT + 1024
MAX_SECONDS = 300
MAGIC = b"OAL2"
operation_lock = threading.Lock()


def derive(passphrase: str, salt: bytes) -> bytes:
    if not 12 <= len(passphrase) <= 128:
        raise ValueError("Use a shared passphrase of 12–128 characters for encrypted audio.")
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000).derive(
        passphrase.encode("utf-8")
    )


def envelope(
    payload: bytes,
    name: str,
    encrypted: bool,
    passphrase: str,
    fundus=False,
    role="data",
    synthetic=False,
) -> bytes:
    if not 0 < len(payload) <= MAX_CONTENT:
        raise ValueError(
            "Acoustic payloads support 1–8192 bytes. Use Wi-Fi for larger originals or explicitly create a small teaching copy."
        )
    name = Path(name.replace("\\", "/")).name
    if len(name) > 120 or not name or any(ord(c) < 32 for c in name):
        raise ValueError("Use a short plain filename.")
    metadata = json.dumps(
        {
            "name": name,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "fundus": fundus,
            "role": role,
            "synthetic": bool(synthetic),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    if len(metadata) > 512 or any(c in name for c in '<>:"|?*') or name.endswith((".", " ")):
        raise ValueError("Use a shorter plain filename without special characters.")
    body = struct.pack(">H", len(metadata)) + metadata + payload
    message_id, salt, nonce = (
        secrets.token_bytes(16),
        secrets.token_bytes(16),
        secrets.token_bytes(12),
    )
    header = MAGIC + bytes([int(encrypted)]) + message_id + salt + nonce
    return header + (
        AESGCM(derive(passphrase, salt)).encrypt(nonce, body, header) if encrypted else body
    )


def open_envelope(raw: bytes, passphrase: str):
    if not 51 <= len(raw) <= MAX_ENVELOPE or raw[:4] != MAGIC or raw[4] not in (0, 1):
        raise ValueError("The recovered envelope is invalid.")
    header, body = raw[:49], raw[49:]
    if raw[4]:
        try:
            body = AESGCM(derive(passphrase, raw[21:37])).decrypt(raw[37:49], body, header)
        except InvalidTag as exc:
            raise ValueError(
                "Authentication failed. Check the passphrase or retry the recording."
            ) from exc
    if len(body) < 3:
        raise ValueError("The recovered payload is incomplete.")
    size = int.from_bytes(body[:2], "big")
    if not 1 <= size <= 512 or len(body) <= size + 2:
        raise ValueError("The recovered metadata is invalid.")
    try:
        metadata = json.loads(body[2 : 2 + size])
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("The recovered metadata is unreadable.") from exc
    if not isinstance(metadata, dict):
        raise ValueError("The recovered metadata must describe a file.")
    content = body[2 + size :]
    name = metadata.get("name", "")
    if (
        not isinstance(name, str)
        or not name
        or Path(name.replace("\\", "/")).name != name
        or any(c in name for c in '<>:"|?*')
        or name.endswith((".", " "))
    ):
        raise ValueError("The recovered filename is invalid.")
    if len(content) > MAX_CONTENT or hashlib.sha256(content).hexdigest() != metadata.get("sha256"):
        raise ValueError("The recovered content hash did not match.")
    return raw[5:21].hex(), metadata, content, bool(raw[4])


def frame_audio(payload: bytes, sps: int = SPS) -> np.ndarray:
    body = struct.pack(">H", len(payload)) + payload
    wire = PREFIX + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    bits = np.unpackbits(np.frombuffer(wire, dtype=np.uint8))
    t = np.arange(sps) / RATE
    tones = np.array([0.6 * np.sin(2 * np.pi * f * t) for f in TONES])
    return tones[bits].reshape(-1)


def modulate(raw: bytes, fec: bool = False, bit_rate: int = BIT_RATE):
    if bit_rate not in (100, 200, 400):
        raise ValueError("Choose 100, 200 or 400 bit/s.")
    chunk = 48 if fec else CHUNK
    ident = raw[5:21]
    total = math.ceil(len(raw) / chunk)
    frames = []
    for i in range(total):
        packet = (
            b"L2"
            + ident
            + struct.pack(">HHI", i, total, len(raw))
            + raw[i * chunk : (i + 1) * chunk]
        )
        if fec:
            protected = packet + struct.pack(">I", zlib.crc32(packet) & 0xFFFFFFFF)
            packet = b"F3" + fec_codec.encode(protected)
        frames.append(np.r_[np.zeros(320), frame_audio(packet, RATE // bit_rate)])
    audio = np.concatenate([np.zeros(1600), *frames, np.zeros(1600)])
    if len(audio) > RATE * MAX_SECONDS:
        raise ValueError(
            "This framing exceeds 300 seconds. Use a smaller payload, faster rate, or Wi-Fi explicitly."
        )
    return audio, total


def _decode_at_rate(audio: np.ndarray, sps: int):
    t = np.arange(sps) / RATE
    kernels = np.array([np.exp(-2j * np.pi * f * t) for f in TONES]).T
    sync = "".join(map(str, np.unpackbits(np.frombuffer(PREFIX, dtype=np.uint8))))
    frames, rejected, corrected = {}, 0, 0
    for offset in range(0, sps, max(1, sps // 10)):
        count = (len(audio) - offset) // sps
        if count <= 0:
            continue
        symbols = audio[offset : offset + count * sps].reshape(count, sps)
        energy = abs(symbols @ kernels) ** 2
        bits = (energy[:, 1] > energy[:, 0]).astype(np.uint8)
        stream = "".join(map(str, bits))
        start = stream.find(sync)
        while start >= 0:
            pos = start + len(sync)
            if pos + 16 <= len(bits):
                size = int.from_bytes(np.packbits(bits[pos : pos + 16]).tobytes(), "big")
                end = pos + 16 + size * 8 + 32
                if 26 < size <= 160 and end <= len(bits):
                    body = np.packbits(bits[pos : end - 32]).tobytes()
                    crc = int.from_bytes(np.packbits(bits[end - 32 : end]).tobytes(), "big")
                    packet = body[2:]
                    valid = zlib.crc32(body) & 0xFFFFFFFF == crc
                    if packet[:2] == b"F3":
                        try:
                            protected, count_corrected = fec_codec.decode(packet[2:])
                            packet = protected[:-4]
                            valid = zlib.crc32(packet) & 0xFFFFFFFF == int.from_bytes(
                                protected[-4:], "big"
                            )
                            if valid:
                                corrected += count_corrected
                        except ValueError:
                            valid = False
                    if valid and packet[:2] == b"L2":
                        ident = packet[2:18].hex()
                        seq, total, length = struct.unpack(">HHI", packet[18:26])
                        if 0 <= seq < total <= 200 and 0 < length <= MAX_ENVELOPE:
                            key = (ident, seq)
                            part = {"total": total, "length": length, "bytes": packet[26:]}
                            if key in frames and frames[key] != part:
                                raise ValueError(
                                    "Conflicting acoustic packets. Record the transmission again."
                                )
                            frames[key] = part
                    else:
                        rejected += 1
            start = stream.find(sync, start + 1)
    groups = {}
    for (ident, seq), part in frames.items():
        groups.setdefault(ident, {})[seq] = part
    complete = []
    for ident, parts in groups.items():
        first = next(iter(parts.values()))
        total, length = first["total"], first["length"]
        if (
            all(p["total"] == total and p["length"] == length for p in parts.values())
            and len(parts) == total
        ):
            content = b"".join(parts[i]["bytes"] for i in range(total))
            if len(content) == length and content[5:21].hex() == ident:
                complete.append(content)
    return complete, {
        "crc_valid_packets": len(frames),
        "crc_rejected_candidates": rejected,
        "complete_messages": len(complete),
        "corrected_bit_candidates": corrected,
        "bit_rate": RATE // sps,
    }


def decode_packets(audio: np.ndarray, clock_search: bool = False):
    best = None
    for sps in (40, 80, 160):
        complete, report = _decode_at_rate(audio, sps)
        if complete:
            return complete, {**report, "clock_adjustment_ppm": 0}
        if best is None or report["crc_valid_packets"] > best[1]["crc_valid_packets"]:
            best = (complete, report)
    # Speaker/ADC clocks need not agree with WAV metadata. Keep the nominal
    # path unchanged; bounded fallback never bypasses CRC, AEAD or SHA checks.
    if clock_search and len(audio) <= RATE * 60 and np.max(np.abs(audio)) > 1e-7:
        for ppm in (1000, -1000, 2000, -2000, 500, -500, 250, -250):
            divisor = math.gcd(1000000, 1000000 + ppm)
            adjusted = signal.resample_poly(audio, 1000000 // divisor, (1000000 + ppm) // divisor)
            for sps in (40, 80, 160):
                complete, report = _decode_at_rate(adjusted, sps)
                report["clock_adjustment_ppm"] = ppm
                if complete:
                    return complete, report
                if report["crc_valid_packets"] > best[1]["crc_valid_packets"]:
                    best = (complete, report)
    best[1].setdefault("clock_adjustment_ppm", 0)
    best[1]["clock_search"] = (
        "Eight fixed clock corrections, at most 60 seconds of input."
        if clock_search and len(audio) <= RATE * 60
        else "Not requested or recording exceeds the 60-second fallback bound."
    )
    return best


def samples(raw: bytes):
    try:
        rate, x = wavfile.read(io.BytesIO(raw))
    except (ValueError, OSError) as exc:
        raise ValueError("Upload a readable PCM WAV of the received sound.") from exc
    if (
        not 8000 <= rate <= 96000
        or x.ndim not in (1, 2)
        or not rate // 10 <= len(x) <= rate * MAX_SECONDS
    ):
        raise ValueError("Use a recording up to 300 seconds at 8–96 kHz.")
    if np.issubdtype(x.dtype, np.integer):
        x = (
            (x.astype(float) - 128) / 128
            if x.dtype == np.uint8
            else x.astype(float) / max(abs(np.iinfo(x.dtype).min), np.iinfo(x.dtype).max)
        )
    if x.ndim == 2:
        x = x.mean(axis=1)
    if not np.isfinite(x).all() or abs(x).max() > 4:
        raise ValueError("Use finite normalized audio samples.")
    divisor = math.gcd(rate, RATE)
    return signal.resample_poly(x, RATE // divisor, rate // divisor)


class Transmit(BaseModel):
    text: str = Field(default="", max_length=1024)
    file_base64: str = Field(default="", max_length=12000)
    name: str = Field(default="message.txt", max_length=120)
    encrypted: bool = True
    passphrase: str = Field(default="", max_length=128)
    fundus: bool = False
    fec: bool = False
    synthetic: bool = False
    bit_rate: Literal[100, 200, 400] = 400


def install(app, ctx):
    root = ctx["data"] / "acoustic_link"
    root.mkdir(exist_ok=True)
    save_lock = threading.Lock()

    def snapshot(x):
        result = plots(x)
        result["rms_dbfs"] = float(20 * np.log10(max(float(np.sqrt(np.mean(x * x))), 1e-12)))
        result["peak_dbfs"] = float(20 * np.log10(max(float(abs(x).max()), 1e-12)))
        return result

    @app.get("/api/link")
    def status():
        return {
            "received": ctx["rows"]("link_received"),
            "transmissions": ctx["rows"]("link_tx")[:100],
            "max_payload_bytes": MAX_CONTENT,
            "bit_rate": BIT_RATE,
            "sample_rate": RATE,
            "tones_hz": TONES,
        }

    @app.post("/api/link/transmit")
    def transmit(body: Transmit, request: Request):
        started = time.perf_counter()
        if body.file_base64 and body.text:
            raise ValueError("Choose either text or a file for this transmission.")
        try:
            payload = (
                base64.b64decode(body.file_base64, validate=True)
                if body.file_base64
                else body.text.encode("utf-8")
            )
        except ValueError as exc:
            raise ValueError("Choose the file again.") from exc
        raw = envelope(
            payload,
            body.name if body.file_base64 else "message.txt",
            body.encrypted,
            body.passphrase,
            body.fundus,
            synthetic=body.synthetic,
        )
        audio, total = modulate(raw, body.fec, body.bit_rate)
        ident = secrets.token_hex(12)
        wavfile.write(root / (ident + ".wav"), RATE, np.int16(audio * 32767))
        ctx["put"](
            "link_tx",
            {
                "id": ident,
                "message_id": raw[5:21].hex(),
                "sender": hashlib.sha256(
                    request.cookies.get("orbit_session", "").encode()
                ).hexdigest()[:20],
                "sha256": hashlib.sha256(payload).hexdigest(),
                "encrypted": body.encrypted,
                "attempts": 1,
                "acknowledged": False,
                "created": ctx["now"](),
                "payload_bytes": len(payload),
                "bit_rate": body.bit_rate,
                "fec": body.fec,
                "packet_count": total,
                "duration_seconds": len(audio) / RATE,
                "generation_ms": (time.perf_counter() - started) * 1000,
                "protocol": "Same-payload hash comparison; generated envelope/framing/WAV-creation wall time and WAV duration, not measured physical delivery latency.",
            },
        )
        return {
            "id": ident,
            "audio_url": "/api/link/audio/" + ident,
            "packet_count": total,
            "payload_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "encrypted": body.encrypted,
            "source": "GENERATED TRANSMIT AUDIO",
            "bit_rate": body.bit_rate,
            "fec": body.fec,
            "algorithm": "BFSK, sequence framing and CRC32; AES-256-GCM when selected",
            "physical_verified": False,
            **snapshot(audio),
        }

    @app.get("/api/link/audio/{ident}")
    def audio(ident: str):
        if len(ident) != 24 or any(c not in "0123456789abcdef" for c in ident):
            raise HTTPException(404, "Choose a generated transmission.")
        path = root / (ident + ".wav")
        if not path.is_file():
            raise HTTPException(404, "Generate the transmission again.")
        return FileResponse(path, media_type="audio/wav", filename="Orbit-AcousticLink.wav")

    @app.get("/api/link/transmissions/{ident}")
    def transmission(ident: str):
        return ctx["get"]("link_tx", ident)

    @app.post("/api/link/transmissions/{ident}/retry")
    def retry(ident: str):
        with save_lock:
            row = ctx["get"]("link_tx", ident)
            if row["acknowledged"]:
                return {**row, "audio_url": None}
            if row["attempts"] >= 3:
                raise HTTPException(
                    409, "Three attempts used. Check the receiver and start a fresh transmission."
                )
            row["attempts"] += 1
            ctx["put"]("link_tx", row)
        return {**row, "audio_url": "/api/link/audio/" + ident}

    def acknowledgement(row, phrase):
        ack = json.dumps(
            {"type": "ACK", "for": row["message_id"], "sha256": row["sha256"]},
            separators=(",", ":"),
        ).encode()
        wave, _ = modulate(
            envelope(ack, "ack.json", row["encrypted"], phrase, role="ack"), False, 400
        )
        ident = secrets.token_hex(12)
        wavfile.write(root / (ident + ".wav"), RATE, np.int16(wave * 32767))
        return {
            "audio_url": "/api/link/audio/" + ident,
            "duration_s": len(wave) / RATE,
            "protocol": "Generated return ACK. Sender must decode this audio before its matching transmission is acknowledged; generation/playback alone is not delivery.",
        }

    def recover(raw, passphrase, preset, source, receiver_session, clock_search):
        began = time.perf_counter()
        x = samples(raw)
        before, baseline = decode_packets(x, clock_search=clock_search)
        if preset == "bandpass":
            processed = signal.sosfilt(
                signal.butter(4, [800, 2800], btype="bandpass", fs=RATE, output="sos"), x
            )
        elif preset == "lowpass":
            processed = signal.sosfilt(
                signal.butter(4, 1700, btype="lowpass", fs=RATE, output="sos"), x
            )
        elif preset == "notch":
            b, a = signal.iirnotch(50, 30, fs=RATE)
            processed = signal.lfilter(b, a, x)
        else:
            processed = x
        envelopes, after = (
            (before, baseline)
            if preset == "raw"
            else decode_packets(processed, clock_search=clock_search)
        )
        report = {
            "source": source,
            "filter": preset,
            "before": baseline,
            "after": after,
            "physical_verified": False,
            "protocol": "Decode only the supplied received WAV. Ground-truth bits absent; BER unavailable. Audio dBFS describes digital level.",
            **snapshot(processed),
        }
        if len(envelopes) != 1:
            return {
                **report,
                "success": False,
                "reason": (
                    "No valid packets found. Check that the selected microphone heard the full modem beeps, not speech; save this recording for diagnosis."
                    if after["crc_valid_packets"] == 0
                    else "Some packets passed CRC, but the whole message is incomplete. Record every frame, including the end; try a shorter message and 100/200 bit/s with SECDED."
                ),
                "elapsed_ms": (time.perf_counter() - began) * 1000,
            }
        ident, metadata, content, encrypted = open_envelope(envelopes[0], passphrase)
        if metadata.get("role") == "ack":
            try:
                ack = json.loads(content)
            except ValueError:
                raise ValueError("The ACK content is invalid.")
            if not isinstance(ack, dict):
                raise ValueError("The ACK must describe a matching transmission.")
            with save_lock:
                tx = next(
                    (r for r in ctx["rows"]("link_tx") if r["message_id"] == ack.get("for")), None
                )
                if (
                    not tx
                    or ack.get("type") != "ACK"
                    or ack.get("sha256") != tx["sha256"]
                    or encrypted != tx["encrypted"]
                ):
                    raise ValueError("This ACK does not authenticate a matching transmission.")
                if tx.get("sender") != receiver_session:
                    raise ValueError(
                        "Decode the return ACK on the original sending session, or start a fresh transmission after re-pairing."
                    )
                tx["acknowledged"] = True
                ctx["put"]("link_tx", tx)
            return {
                **report,
                "success": True,
                "acknowledgement_received": tx,
                "elapsed_ms": (time.perf_counter() - began) * 1000,
            }
        with save_lock:
            seen = next((r for r in ctx["rows"]("link_received") if r["message_id"] == ident), None)
            if seen:
                return {
                    **report,
                    "success": True,
                    "duplicate": True,
                    "received": seen,
                    "ack": acknowledgement(seen, passphrase),
                    "elapsed_ms": (time.perf_counter() - began) * 1000,
                }
            record_id = secrets.token_hex(12)
            target = root / (record_id + ".bin")
            name = metadata["name"]
            mime = {
                ".txt": "text/plain",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".wav": "audio/wav",
                ".m4a": "audio/mp4",
                ".webm": "audio/webm",
            }.get(Path(name).suffix.lower(), "application/octet-stream")
            row = {
                "id": record_id,
                "message_id": ident,
                "created": ctx["now"](),
                "name": name,
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "synthetic": bool(metadata.get("synthetic")),
                "encrypted": encrypted,
                "type": mime,
                "source": source,
                "download_url": "/api/link/received/" + record_id,
            }
            if mime == "text/plain":
                try:
                    row["text"] = content.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ValueError("The reconstructed text is not valid UTF-8.") from exc
            # A recovered file is retained unchanged. Import into a specialist lab
            # only after that lab's input validation and explicit user consent.
            target.write_bytes(content)
            try:
                ctx["put"]("link_received", row)
            except Exception:
                target.unlink(missing_ok=True)
                raise
        return {
            **report,
            "success": True,
            "duplicate": False,
            "received": row,
            "ack": acknowledgement(row, passphrase),
            "elapsed_ms": (time.perf_counter() - began) * 1000,
        }

    @app.post("/api/link/receive")
    async def receive(
        request: Request,
        preset: Literal["raw", "bandpass", "lowpass", "notch"] = "raw",
        source: Literal["UPLOADED MODEM WAV", "MICROPHONE RECORDING"] = "UPLOADED MODEM WAV",
        clock_search: bool = False,
    ):
        key = request.headers.get("x-orbit-passphrase", "")
        if len(key) > 700:
            raise ValueError("Use a passphrase up to 128 characters.")
        try:
            phrase = base64.b64decode(key, validate=True).decode("utf-8") if key else ""
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError("Enter the receiver passphrase again.") from exc
        raw = bytearray()
        async for part in request.stream():
            if len(raw) + len(part) > 32 * 1024**2:
                raise HTTPException(413, "Choose a received WAV smaller than 32 MiB.")
            raw.extend(part)
        if not operation_lock.acquire(blocking=False):
            raise HTTPException(409, "Wait for the current acoustic decode to finish.")
        try:
            return await run_in_threadpool(
                recover,
                bytes(raw),
                phrase,
                preset,
                source,
                hashlib.sha256(request.cookies.get("orbit_session", "").encode()).hexdigest()[:20],
                clock_search,
            )
        finally:
            operation_lock.release()

    @app.get("/api/link/received/{ident}")
    def received_file(ident: str):
        if any(r["id"] == "link_received:" + ident for r in ctx["rows"]("revoked_export")):
            raise HTTPException(
                404, "This Library-linked export was revoked. Restore it in the Library."
            )
        row = ctx["get"]("link_received", ident)
        return FileResponse(
            root / (row["id"] + ".bin"),
            media_type=row["type"],
            filename=row["name"],
            headers={"X-Content-SHA256": row["sha256"]},
        )

    @app.delete("/api/link/received/{ident}")
    def remove_received(ident: str, request: Request):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Delete reconstructed files from the laptop.")
        with save_lock:
            row = ctx["get"]("link_received", ident)
            (root / (row["id"] + ".bin")).unlink(missing_ok=True)
            ctx["delete"]("link_received", ident)
        return {"ok": True}
