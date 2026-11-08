"""Opt-in local Vosk transcription. No model download or cloud speech requests."""

import importlib.util
import json
import math
import os
import threading
import time
from pathlib import Path

import numpy as np
from fastapi import HTTPException
from pydantic import BaseModel, Field
from scipy import signal

from .audio_studio import read_wav

_lock = threading.Lock()
_model = None


def model_path():
    return Path(
        os.environ.get(
            "ORBIT_SPEECH_MODEL",
            str(
                Path(__file__).resolve().parent.parent / "speech-models/vosk-model-small-en-us-0.15"
            ),
        )
    )


def transcribe(raw: bytes):
    global _model
    if not importlib.util.find_spec("vosk") or not (model_path() / "am/final.mdl").is_file():
        raise HTTPException(
            503, "Install the bundled offline speech runtime and English model, then retry."
        )
    if not _lock.acquire(blocking=False):
        raise HTTPException(409, "Wait for the current transcription to finish.")
    try:
        from vosk import KaldiRecognizer, Model, SetLogLevel

        started = time.perf_counter()
        rate, x = read_wav(raw)
        mono = x.mean(axis=1)
        divisor = math.gcd(rate, 16000)
        mono = signal.resample_poly(mono, 16000 // divisor, rate // divisor)
        pcm = np.int16(np.clip(mono, -1, 0.999969) * 32768).tobytes()
        SetLogLevel(-1)
        if _model is None:
            _model = Model(str(model_path()))
        recognizer = KaldiRecognizer(_model, 16000)
        recognizer.SetWords(True)
        texts = []
        words = []
        for offset in range(0, len(pcm), 8000):
            if recognizer.AcceptWaveform(pcm[offset : offset + 8000]):
                result = json.loads(recognizer.Result())
                texts.append(result.get("text", ""))
                words.extend(result.get("result", []))
        result = json.loads(recognizer.FinalResult())
        texts.append(result.get("text", ""))
        words.extend(result.get("result", []))
        return {
            "text": " ".join(t for t in texts if t).strip(),
            "words": words,
            "duration_s": len(mono) / 16000,
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "model": "vosk-model-small-en-us-0.15",
            "protocol": "Offline Vosk English decoding of the selected PCM WAV, mono resampled to 16 kHz. Transcript is model output, may be wrong, and requires review. No WER/accuracy without a reference transcript.",
        }
    finally:
        _lock.release()


class SpeechInput(BaseModel):
    input_id: str = Field(pattern="^[a-f0-9]{24}$")
    consent: bool = False


def install(app, ctx):
    @app.get("/api/speech")
    def status():
        return {
            "available": bool(
                importlib.util.find_spec("vosk") and (model_path() / "am/final.mdl").is_file()
            ),
            "model": "vosk-model-small-en-us-0.15",
            "offline": True,
        }

    @app.post("/api/speech/transcribe")
    def run(body: SpeechInput):
        if not body.consent:
            raise ValueError("Confirm permission for local speech processing.")
        row, path = ctx["load_asset"](body.input_id)
        if row["size"] > 12 * 1024**2:
            raise ValueError("Choose a PCM WAV up to 60 seconds and 12 MiB.")
        result = transcribe(path.read_bytes())
        if result["text"]:
            saved = ctx["save_asset"](
                result["text"].encode(),
                "transcript.txt",
                "OFFLINE SPEECH MODEL OUTPUT",
                parent_id=row["id"],
                synthetic=bool(row.get("synthetic")),
                notes=result["protocol"],
            )
            result["output_id"] = saved["id"]
        else:
            result["reason"] = (
                "No words recognized. Try clear English speech with less noise; no transcript was invented."
            )
        return result
