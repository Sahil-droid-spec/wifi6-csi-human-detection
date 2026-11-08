"""Same-input visual DSP with explicit gaps and no stitching across packet loss."""

import secrets
import time
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

from . import core


class ControlInput(BaseModel):
    capture_id: str = Field(pattern="^[a-f0-9]{24}$")
    start: int = Field(default=0, ge=0)
    length: int = Field(default=1024, ge=32, le=4096)
    operation: Literal["fir", "butterworth", "moving_average"] = "fir"
    taps: int = Field(default=15, ge=3, le=127)
    window: Literal["hann", "hamming", "blackman", "kaiser"] = "hamming"
    cutoff: float = Field(default=0.08, gt=0, lt=0.5, allow_inf_nan=False)
    order: int = Field(default=4, ge=1, le=8)
    kind: Literal["lowpass"] = "lowpass"


def process(amplitude, invalid, body: ControlInput):
    if body.start >= amplitude.shape[1]:
        raise ValueError("Choose a window inside this recording.")
    began = time.perf_counter()
    end = min(amplitude.shape[1], body.start + body.length)
    trace = np.median(amplitude[:, body.start : end], axis=0)
    valid = ~invalid[body.start : end] & np.isfinite(trace)
    edges = np.flatnonzero(np.diff(np.r_[False, valid, False]))
    runs = [(int(a), int(b)) for a, b in edges.reshape(-1, 2) if b - a >= 32]
    if not runs:
        raise ValueError(
            "No contiguous run of 32 usable packets in this window. Move the window slider; raw gaps remain visible."
        )
    settings = {
        k: v for k, v in body.model_dump().items() if k not in ("capture_id", "start", "length")
    }
    filtered = np.full(len(trace), np.nan)
    longest = max(runs, key=lambda pair: pair[1] - pair[0])
    spectral = None
    count = 0
    for a, b in runs:
        result = core.dsp(trace[a:b], **settings)
        filtered[a:b] = result["processed"]
        count += result["extra"]["estimated_multiplications"]
        if (a, b) == longest:
            spectral = result
    result = {
        k: spectral[k]
        for k in (
            "frequency",
            "raw_spectrum",
            "processed_spectrum",
            "response_frequency",
            "response_db",
            "coefficients",
            "denominator",
        )
    }
    result.update(
        raw=[float(v) if valid[i] else None for i, v in enumerate(trace)],
        processed=[float(v) if np.isfinite(v) else None for v in filtered],
        note="Causal filtering resets at each packet gap. Runs below 32 samples are withheld. Startup transients are included. Spectrum uses only the longest contiguous usable run; no gaps are zero-filled or stitched.",
        spectral_window={
            "start": body.start + longest[0],
            "end": body.start + longest[1],
            "samples": longest[1] - longest[0],
        },
        metrics={
            "usable_fraction": float(valid.mean()),
            "processed_packets": int(np.isfinite(filtered).sum()),
            "contiguous_runs": len(runs),
        },
        extra={
            "estimated_multiplications": count,
            "measured_elapsed_ms": (time.perf_counter() - began) * 1000,
            "computation_protocol": "Core DSP direct-form multiplication estimate, summed over filtered runs; measured window processing time excludes disk read and network transfer.",
        },
    )
    return result


def install(app, ctx):
    def run(body):
        cap, amplitude, invalid = ctx["arrays"](body.capture_id)
        result = process(amplitude, invalid, body)
        result.update(
            source="SIMULATION" if cap.get("synthetic") else "RECORDED DATA",
            capture_id=cap["id"],
            start=body.start,
        )
        return result

    @app.post("/api/control/process")
    def preview(body: ControlInput):
        return run(body)

    @app.post("/api/control/save")
    def save(body: ControlInput):
        result = run(body)
        row = {
            "id": secrets.token_hex(12),
            "created": ctx["now"](),
            "kind": "DSP",
            "source": result["source"],
            "settings": body.model_dump(),
            "metrics": result["metrics"],
            "note": result["note"],
            "spectral_window": result["spectral_window"],
            "protocol": "Gap-aware Command center processing. No classifier retraining or held-out accuracy claim.",
        }
        ctx["put"]("run", row)
        return row
