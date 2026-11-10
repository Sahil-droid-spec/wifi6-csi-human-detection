"""Seeded complex-channel experiments; illustrative geometry is never inferred pose.

Simulation buffers are bounded, never mixed into recorded model evidence, and
only persist on an explicit save. Analysis resets filters at missing packets.
"""

import csv
import hashlib
import io
import json
import math
import secrets
import threading
import time
import warnings
import zipfile
from collections import OrderedDict
from typing import Literal

import numpy as np
from fastapi import File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator
from scipy import signal


class AvatarState(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,24}$")
    activity: Literal["standing", "walking", "running", "turning", "entering", "leaving", "hand", "custom"] = "walking"
    speed: float = Field(default=1, ge=0, le=3, allow_inf_nan=False)
    visible: bool = True


class Simulation(BaseModel):
    scenario: Literal["empty", "still", "walking", "moving", "two", "crossing", "two_still", "mixed", "entering", "leaving", "two_entering", "two_leaving", "fast", "hand", "custom"] = "walking"
    avatars: list[AvatarState] | None = Field(default=None, max_length=4)
    packet_rate: int = Field(default=100, ge=20, le=500)
    subcarriers: int = Field(default=52, ge=16, le=256)
    duration: float = Field(default=12, ge=4, le=30, allow_inf_nan=False)
    noise: float = Field(default=0.012, ge=0, le=0.3, allow_inf_nan=False)
    motion_intensity: float = Field(default=0.7, ge=0, le=2, allow_inf_nan=False)
    virtual_speed: float = Field(default=1, ge=0, le=3, allow_inf_nan=False)
    multipath: int = Field(default=5, ge=1, le=12)
    gain: float = Field(default=1, ge=0.1, le=3, allow_inf_nan=False)
    packet_loss: float = Field(default=0.01, ge=0, le=0.3, allow_inf_nan=False)
    jitter: float = Field(default=0.01, ge=0, le=0.3, allow_inf_nan=False)
    drift: float = Field(default=0.015, ge=0, le=0.2, allow_inf_nan=False)
    threshold_multiplier: float = Field(default=3, ge=1, le=8, allow_inf_nan=False)
    seed: int = Field(default=42, ge=0, le=2**32 - 1)

    @model_validator(mode="after")
    def bounded(self):
        if self.avatars and len({p.id for p in self.avatars}) != len(self.avatars):
            raise ValueError("Use a unique ID for each person.")
        if self.packet_rate * self.duration * self.subcarriers > 1_000_000:
            raise ValueError(
                "Reduce rate, duration or subcarriers to at most one million complex samples."
            )
        return self


class SessionInput(BaseModel):
    source: Literal["simulation", "recorded"] = "simulation"
    capture_id: str | None = Field(default=None, pattern="^[a-f0-9]{24}$")
    simulation: Simulation = Field(default_factory=Simulation)


class Analysis(BaseModel):
    start: int = Field(default=0, ge=0)
    length: int = Field(default=256, ge=32, le=2048)
    operation: Literal["raw", "fir", "butterworth", "notch"] = "butterworth"
    kind: Literal["lowpass", "highpass", "bandpass", "bandstop"] = "lowpass"
    cutoff: float = Field(default=0.08, gt=0, lt=0.5, allow_inf_nan=False)
    upper: float = Field(default=0.2, gt=0, lt=0.5, allow_inf_nan=False)
    order: int = Field(default=4, ge=1, le=8)
    taps: int = Field(default=31, ge=3, le=127)
    window: Literal["hann", "hamming", "blackman", "kaiser"] = "hann"
    stft_size: Literal[32, 64, 128, 256] = 64
    overlap: float = Field(default=0.5, ge=0, le=0.9, allow_inf_nan=False)
    subcarrier: int = Field(default=0, ge=0, le=255)


def scenario_people(config: Simulation) -> list[AvatarState]:
    """Explicit scenario truth, never an inferred count or activity."""
    if config.scenario == "custom":
        return config.avatars or []
    states = {
        "empty": [], "still": ["standing"], "walking": ["walking"],
        "moving": ["hand"], "two": ["walking", "walking"],
        "crossing": ["walking", "walking"], "two_still": ["standing", "standing"],
        "mixed": ["standing", "walking"], "entering": ["entering"],
        "leaving": ["leaving"], "two_entering": ["entering", "entering"],
        "two_leaving": ["leaving", "leaving"], "fast": ["running"], "hand": ["hand"],
    }[config.scenario]
    return [AvatarState(id=f"person-{i+1}", activity=a) for i, a in enumerate(states)]


def synthesize(config: Simulation) -> dict:
    """Multipath baseband model, not a validated 802.11ax PHY or RF measurement."""
    rng = np.random.default_rng(config.seed)
    n = round(config.packet_rate * config.duration)
    dt = np.maximum(0.1, 1 + rng.normal(0, config.jitter, n)) / config.packet_rate
    timestamps = np.cumsum(dt)
    timestamps -= timestamps[0]
    carrier = np.linspace(-0.5, 0.5, config.subcarriers)
    channel = np.zeros((config.subcarriers, n), dtype=np.complex128)
    for _ in range(config.multipath):
        delay, phase = rng.uniform(0, 8), rng.uniform(-np.pi, np.pi)
        channel += rng.uniform(0.15, 0.7) * np.exp(
            1j * (phase - 2 * np.pi * carrier[:, None] * delay)
        )
    people = [p for p in scenario_people(config) if p.visible]
    count = len(people)
    positions = []
    for person in range(count):
        avatar = people[person]
        phase = person * np.pi
        moving = avatar.activity not in ("standing", "hand", "turning")
        speed = config.virtual_speed * avatar.speed * (1.8 if avatar.activity == "running" else 1)
        x = np.sin(timestamps * speed * (0.55 + person * 0.035) + phase) * (1.7 if moving else 0)
        # Disjoint lanes keep independent activities from occupying the same point.
        lane = (person - (count - 1) / 2) * 1.1
        z = lane + np.cos(timestamps * speed * 0.35 + phase) * ((0.7 if count == 1 else 0.18) if moving else 0)
        if avatar.activity in ("entering", "leaving"):
            travel = np.clip(timestamps / max(config.duration * 0.7, 1), 0, 1)
            x = (-3.3 + travel * 3.3) if avatar.activity == "entering" else travel * 3.3
        if config.scenario == "crossing":
            travel = 1.7 * (np.sin(timestamps * config.virtual_speed * 0.55) if person == 0 else np.cos(timestamps * config.virtual_speed * 0.55))
            x = travel if person == 0 else np.zeros(n)
            z = travel if person == 1 else np.zeros(n)
        elif config.scenario == "moving":
            x = 0.2 * np.sin(timestamps * config.virtual_speed * 2)
            z = lane + 0.15 * np.cos(timestamps * config.virtual_speed * 1.7)
        path = np.sqrt((x + 2.8) ** 2 + z**2 + 1) + np.sqrt((x - 2.8) ** 2 + z**2 + 1)
        if avatar.activity == "hand" and config.scenario != "moving":
            path += 0.02 * np.sin(timestamps * speed * 3)
        breathing = 0.002 * np.sin(2 * np.pi * 0.25 * timestamps + phase)
        reflection = 0.22 * np.exp(1j * (-2 * np.pi * (path + breathing) / 0.06))
        channel += (
            config.motion_intensity
            * reflection[None, :]
            * np.exp(-1j * carrier[:, None] * (path[None, :] + person))
        )
        yaw = np.arctan2(np.gradient(x), np.gradient(z))
        if avatar.activity == "turning":
            yaw = timestamps * speed
        positions.append(np.c_[x, z, yaw])
    # Slow drift and an AGC-like step affect all channels; they are not motion truth.
    gain = config.gain * (1 + config.drift * np.sin(timestamps * 0.7))
    gain[n // 2 :] *= 1.06
    channel *= gain
    channel += config.noise * (rng.normal(size=channel.shape) + 1j * rng.normal(size=channel.shape))
    invalid = rng.random(n) < config.packet_loss
    channel[:, invalid] = complex(np.nan, np.nan)
    return {
        "channel": channel,
        "amplitude": np.abs(channel),
        "invalid": invalid,
        "timestamps": timestamps,
        "positions": positions,
        "people": [p.model_dump() for p in people],
        "synthetic": True,
        "config": config.model_dump(),
        "rate": config.packet_rate,
        "capture_id": None,
        "name": "Simulation set A",
        "source": "SIMULATION",
    }


def motion_audit(session: dict) -> dict:
    """Motion proxy, no classifier, localization, accuracy or confidence claim."""
    amplitude, invalid = session["amplitude"], session["invalid"]
    safe = np.where(np.isfinite(amplitude), amplitude, 0)
    trace = np.median(safe, axis=0)
    valid = ~invalid & np.isfinite(trace)
    score = np.full(len(trace), np.nan)
    variance = np.full(len(trace), np.nan)
    level = np.full(len(trace), np.nan)
    for i in range(15, len(trace)):
        if valid[i - 15 : i + 1].all():
            part = trace[i - 15 : i + 1]
            variance[i] = np.var(part)
            level[i] = 20 * np.log10(max(np.sqrt(np.mean(part**2)), 1e-12))
            score[i] = 100 * np.std(part) / max(np.mean(np.abs(part)), 1e-9)
    return {
        "trace": trace,
        "valid": valid,
        "score": score,
        "variance": variance,
        "relative_level_db": level,
    }


def finite_list(values: np.ndarray) -> list[float | None]:
    return [float(v) if np.isfinite(v) else None for v in values]


def analyze(session: dict, body: Analysis) -> dict:
    began = time.perf_counter()
    amplitude, invalid = session["amplitude"], session["invalid"]
    if body.start >= amplitude.shape[1]:
        raise ValueError("Move the timeline inside the selected recording.")
    if body.subcarrier >= amplitude.shape[0]:
        raise ValueError("Select an available subcarrier.")
    end = min(amplitude.shape[1], body.start + body.length)
    raw = np.median(
        np.where(np.isfinite(amplitude[:, body.start : end]), amplitude[:, body.start : end], 0),
        axis=0,
    )
    valid = ~invalid[body.start : end] & np.isfinite(raw)
    if body.kind in ("bandpass", "bandstop") and body.upper <= body.cutoff:
        raise ValueError("Set the upper cutoff above the lower cutoff.")
    cutoff = [body.cutoff, body.upper] if body.kind in ("bandpass", "bandstop") else body.cutoff
    if body.operation == "raw":
        b, a = np.array([1.0]), np.array([1.0])
    elif body.operation == "fir":
        if body.taps % 2 == 0:
            raise ValueError("Use an odd number of FIR taps.")
        window = ("kaiser", 8.0) if body.window == "kaiser" else body.window
        b, a = (
            signal.firwin(body.taps, cutoff, window=window, pass_zero=body.kind, fs=1),
            np.array([1.0]),
        )
    elif body.operation == "notch":
        b, a = signal.iirnotch(body.cutoff, 15, fs=1)
    else:
        b, a = signal.butter(body.order, cutoff, btype=body.kind, fs=1)
    filtered = np.full(len(raw), np.nan)
    edges = np.flatnonzero(np.diff(np.r_[False, valid, False])).reshape(-1, 2)
    runs = [(int(x), int(y)) for x, y in edges if y - x >= 16]
    for x, y in runs:
        filtered[x:y] = signal.lfilter(b, a, raw[x:y])
    rate = session.get("rate") or 1.0
    w, response = signal.freqz(b, a, worN=256, fs=rate)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        _, delay = signal.group_delay((b, a), w=256, fs=rate)
    delay[np.abs(response) < 1e-7] = np.nan
    phase_response = np.unwrap(np.angle(response))
    spectrum, stft, interval = [], None, None
    spectrum_phase, psd = [], []
    if runs:
        x, y = max(runs, key=lambda p: p[1] - p[0])
        length = y - x
        taper = signal.get_window(("kaiser", 8) if body.window == "kaiser" else body.window, length)
        frequency = np.fft.rfftfreq(length, 1 / rate)
        spectra = [
            np.abs(np.fft.rfft((v[x:y] - np.mean(v[x:y])) * taper)) / length
            for v in (raw, filtered)
        ]
        spectrum = np.column_stack([frequency, *spectra]).tolist()
        transforms = [np.fft.rfft((v[x:y]-np.mean(v[x:y]))*taper) for v in (raw, filtered)]
        spectrum_phase = np.column_stack([frequency, np.angle(transforms[0]), np.angle(transforms[1])]).tolist()
        pf, power = signal.welch(filtered[x:y], fs=rate, nperseg=min(256, length))
        psd = np.c_[pf, power].tolist()
        nperseg = min(body.stft_size, length)
        f, t, z = signal.stft(
            filtered[x:y],
            fs=rate,
            window=("kaiser", 8) if body.window == "kaiser" else body.window,
            nperseg=nperseg,
            noverlap=min(nperseg - 1, int(nperseg * body.overlap)),
            boundary=None,
            padded=False,
        )
        stft = {
            "frequency": f.tolist(),
            "time": (t + (body.start + x) / rate).tolist(),
            "db": (20 * np.log10(np.maximum(np.abs(z), 1e-12))).tolist(),
        }
        interval = {"start": body.start + x, "end": body.start + y, "samples": length}
    indices = np.linspace(body.start, end - 1, min(128, end - body.start)).astype(int)
    channels = np.linspace(0, amplitude.shape[0] - 1, min(32, amplitude.shape[0])).astype(int)
    heat = [
        [int(p), int(k), float(amplitude[k, p])]
        for k in channels
        for p in indices
        if not invalid[p] and np.isfinite(amplitude[k, p])
    ]
    phase = None
    if "channel" in session:
        phase = finite_list(np.angle(session["channel"][body.subcarrier, body.start : end]))
    raw[~valid] = np.nan
    return {
        "start": body.start,
        "end": end,
        "raw": finite_list(raw),
        "filtered": finite_list(filtered),
        "phase": phase,
        "phase_note": "Wrapped complex-channel phase in radians; no inferred position."
        if phase
        else "Phase unavailable: this input stores amplitude only.",
        "spectrum": spectrum,
        "spectrum_phase": spectrum_phase,
        "psd": psd,
        "stft": stft,
        "heatmap": heat,
        "response": np.c_[w, 20 * np.log10(np.maximum(np.abs(response), 1e-12))].tolist(),
        "coefficients": {"b": b.tolist(), "a": a.tolist()},
        "response_phase": finite_list(phase_response),
        "group_delay_samples": finite_list(delay),
        "poles": [
            [float(z.real), float(z.imag)]
            for z in np.roots(np.pad(a, (0, max(len(a), len(b)) - len(a))))
        ],
        "zeros": [
            [float(z.real), float(z.imag)]
            for z in np.roots(np.pad(b, (0, max(len(a), len(b)) - len(b))))
        ],
        "spectral_window": interval,
        "frequency_unit": "Hz" if session.get("rate") else "cycles / packet",
        "computation_ms": (time.perf_counter() - began) * 1000,
        "protocol": "Selected input window. Causal filter reset at every gap; runs under 16 samples withheld. FFT and STFT use longest contiguous usable run, include startup transient, no interpolation. Elapsed time excludes network and rendering.",
    }


def install(app, ctx: dict) -> None:
    sessions: OrderedDict[str, dict] = OrderedDict()
    lock = threading.RLock()

    def get_session(ident: str) -> dict:
        with lock:
            if ident not in sessions:
                raise HTTPException(
                    404, "Reload this session; the bounded in-memory preview has expired."
                )
            sessions.move_to_end(ident)
            return sessions[ident]

    ctx["sensing_session"] = get_session

    def register(session: dict, threshold: float | None = None) -> dict:
        session["audit"] = motion_audit(session)
        session["threshold"] = threshold
        ident = secrets.token_hex(12)
        with lock:
            sessions[ident] = session
            while len(sessions) > 4:
                removable = next(k for k in sessions if k != ctx.get("sensing_pin"))
                sessions.pop(removable)
        audit = session["audit"]
        valid_score = np.isfinite(audit["score"])
        events = []
        if threshold is not None:
            active = valid_score & (audit["score"] > threshold)
            edges = np.flatnonzero(np.diff(np.r_[False, active, False])).reshape(-1, 2)
            events = [
                {"start": int(a), "end": int(b), "kind": "motion proxy above threshold"}
                for a, b in edges
            ][:200]
        return {
            "id": ident,
            "capture_id": session["capture_id"],
            "source": session["source"],
            "synthetic": session["synthetic"],
            "name": session["name"],
            "packets": len(audit["trace"]),
            "subcarriers": session["amplitude"].shape[0],
            "rate": session["rate"],
            "time": session["timestamps"].tolist(),
            "trace": finite_list(np.where(audit["valid"], audit["trace"], np.nan)),
            "score": finite_list(audit["score"]),
            "variance": finite_list(audit["variance"]),
            "relative_level_db": finite_list(audit["relative_level_db"]),
            "interval_ms": finite_list(np.r_[np.nan, np.diff(session["timestamps"]) * 1000])
            if session.get("rate")
            else None,
            "positions": [p.tolist() for p in session["positions"]],
            "people": session.get("people", []),
            "threshold": threshold,
            "events": events,
            "config": session["config"],
            "packet_audit": {
                "received": int(audit["valid"].sum()),
                "missing_or_invalid": int((~audit["valid"]).sum()),
                "total": len(audit["trace"]),
            },
            "protocol": "Motion proxy: 100 × rolling population standard deviation / mean absolute median-subcarrier amplitude over 16 contiguous valid packets. Simulation threshold: mean + multiplier × SD from a separate empty scenario with the same seed/configuration. This is not classifier confidence or validation accuracy. Recorded data have no automatic empty-room calibration or inferred pose.",
        }

    @app.post("/api/sensing/sessions")
    def create(body: SessionInput):
        if body.source == "simulation":
            session = synthesize(body.simulation)
            baseline = synthesize(body.simulation.model_copy(update={"scenario": "empty"}))
            values = motion_audit(baseline)["score"]
            values = values[np.isfinite(values)]
            threshold = (
                float(np.mean(values) + body.simulation.threshold_multiplier * np.std(values))
                if len(values)
                else None
            )
        else:
            if not body.capture_id:
                raise ValueError("Choose a saved CSI recording first.")
            cap, amplitude, invalid = ctx["arrays"](body.capture_id)
            # Bounded preview, no silent downsampling or fabricated physical clock.
            amplitude, invalid = amplitude[:, :10000].copy(), invalid[:10000].copy()
            session = {
                "amplitude": amplitude,
                "invalid": invalid,
                "synthetic": bool(cap.get("synthetic")),
                "source": "SIMULATION RECORDING" if cap.get("synthetic") else "RECORDED DATA",
                "name": cap["name"],
                "capture_id": cap["id"],
                "rate": None,
                "config": {},
                "positions": [],
                "timestamps": np.arange(amplitude.shape[1], dtype=float),
            }
            threshold = None
        return register(session, threshold)

    @app.post("/api/sensing/import")
    async def import_session(file: UploadFile = File(...)):
        raw = await file.read(32 * 1024**2 + 1)
        if not raw or len(raw) > 32 * 1024**2:
            raise ValueError("Choose a nonempty Orbit JSON/NPZ export below 32 MiB.")
        try:
            if file.filename and file.filename.lower().endswith(".json"):
                if len(raw) > 2 * 1024**2:
                    raise ValueError(
                        "Use NPZ for larger sessions; JSON imports are capped at 2 MiB."
                    )
                metadata = json.loads(raw)
                trace = np.asarray(metadata["trace"], dtype=float)
                if trace.ndim != 1 or not 32 <= len(trace) <= 15000:
                    raise ValueError("Choose an Orbit trace export with 32–15000 packets.")
                amplitude = trace[None, :]
                invalid = ~np.isfinite(trace)
                timestamps = np.asarray(metadata["time"], dtype=float)
                channel = None
                imported_positions = []
            elif file.filename and file.filename.lower().endswith(".npz"):
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    items = z.infolist()
                    if len(items) > 8 or sum(i.file_size for i in items) > 64 * 1024**2:
                        raise ValueError("Choose a bounded Orbit NPZ export below 64 MiB expanded.")
                    allowed = {
                        "amplitude.npy",
                        "invalid.npy",
                        "timestamps.npy",
                        "metadata.npy",
                        "csi_real.npy",
                        "csi_imag.npy",
                        "positions.npy",
                    }
                    if len({i.filename for i in items}) != len(items):
                        raise ValueError("The NPZ contains duplicate array entries.")
                    for item in items:
                        if item.filename not in allowed or item.file_size > 48 * 1024**2:
                            raise ValueError(
                                "Choose an unmodified Orbit NPZ with supported arrays only."
                            )
                        with z.open(item) as f:
                            version = np.lib.format.read_magic(f)
                            if version == (1, 0):
                                shape, _, dtype = np.lib.format.read_array_header_1_0(
                                    f, max_header_size=10000
                                )
                            elif version == (2, 0):
                                shape, _, dtype = np.lib.format.read_array_header_2_0(
                                    f, max_header_size=10000
                                )
                            else:
                                raise ValueError(
                                    "Choose an Orbit export using supported NPY array headers."
                                )
                            count = math.prod(shape) if shape else 1
                            if (
                                dtype.hasobject
                                or any(d < 0 or d > 5_120_000 for d in shape)
                                or not 0 < count <= 5_120_000
                                or count * dtype.itemsize > 48 * 1024**2
                            ):
                                raise ValueError(
                                    "The NPZ has an unsupported or oversized array header."
                                )
                            if item.filename == "metadata.npy" and count * dtype.itemsize > 32768:
                                raise ValueError("The NPZ metadata are too large.")
                with np.load(io.BytesIO(raw), allow_pickle=False) as z:
                    metadata = json.loads(str(z["metadata"]))
                    amplitude, invalid, timestamps = z["amplitude"], z["invalid"], z["timestamps"]
                    imported_positions = list(z["positions"]) if "positions" in z else []
                    channel = (
                        z["csi_real"] + 1j * z["csi_imag"]
                        if "csi_real" in z and "csi_imag" in z
                        else None
                    )
            else:
                raise ValueError("Choose an Orbit .json or .npz session export.")
            if (
                not isinstance(metadata, dict)
                or metadata.get("schema") != "orbit.sensing.v1"
                or not isinstance(metadata.get("synthetic"), bool)
            ):
                raise ValueError("Use an Orbit export with explicit source metadata.")
            if (
                amplitude.ndim != 2
                or not 1 <= amplitude.shape[0] <= 512
                or not 32 <= amplitude.shape[1] <= 15000
                or amplitude.dtype.kind not in "fiu"
            ):
                raise ValueError("Choose a numeric channel array with 32–15000 packets.")
            n = amplitude.shape[1]
            if (
                invalid.shape != (n,)
                or timestamps.shape != (n,)
                or not np.isfinite(timestamps).all()
                or not (np.diff(timestamps) > 0).all()
            ):
                raise ValueError(
                    "Session time and validity arrays must match its packet count and increase strictly."
                )
            invalid = (
                invalid.astype(bool)
                | ~np.isfinite(amplitude).all(axis=0)
                | (amplitude == 0).all(axis=0)
            )
            if channel is not None and channel.shape != amplitude.shape:
                raise ValueError("Real and imaginary CSI must match the amplitude array.")
            rate = metadata.get("rate")
            if rate is not None and (
                not isinstance(rate, (int, float))
                or not np.isfinite(rate)
                or not 1 <= rate <= 10000
            ):
                raise ValueError("Use a valid recorded or synthetic packet rate.")
            session = {
                "amplitude": amplitude,
                "invalid": invalid,
                "timestamps": timestamps,
                "rate": rate,
                "synthetic": metadata["synthetic"],
                "source": "SIMULATION IMPORT" if metadata["synthetic"] else "RECORDED IMPORT",
                "name": "Imported session",
                "capture_id": None,
                "config": {},
                "positions": [],
                "import_config": metadata.get("config", {}),
            }
            if channel is not None:
                session["channel"] = channel
            threshold = None
            if session["synthetic"]:
                if len(imported_positions) > 4 or any(
                    p.shape != (n, 3)
                    or p.dtype.kind not in "fiu"
                    or not np.isfinite(p).all()
                    or (np.abs(p) > 1000).any()
                    for p in imported_positions
                ):
                    raise ValueError(
                        "Use generated ground-truth positions matching the synthetic packet count."
                    )
                session["positions"] = imported_positions
                config = metadata.get("config", {})
                if not isinstance(config, dict):
                    raise ValueError("Use an Orbit export with dictionary configuration metadata.")
                if imported_positions or config.get("scenario") == "empty":
                    session["config"] = config
                    session["people"] = [p.model_dump() for p in scenario_people(Simulation(**config)) if p.visible][:len(imported_positions)]
                threshold = metadata.get("calibrated_threshold")
                if threshold is not None and (
                    not isinstance(threshold, (int, float))
                    or not np.isfinite(threshold)
                    or not 0 <= threshold <= 1e6
                ):
                    raise ValueError("The saved synthetic calibration threshold is invalid.")
            return register(session, threshold)
        except (
            KeyError,
            TypeError,
            OSError,
            zipfile.BadZipFile,
            json.JSONDecodeError,
            RecursionError,
        ) as exc:
            raise ValueError(
                "Choose an intact Orbit session export; this file could not be read safely."
            ) from exc

    @app.post("/api/sensing/sessions/{ident}/analyze")
    def analysis(ident: str, body: Analysis):
        return analyze(get_session(ident), body)

    def export(ident, format, start=0, end=None):
        original = get_session(ident)
        n = original["amplitude"].shape[1]
        end = n if end is None else end
        if not 0 <= start < end <= n or end - start < 32:
            raise ValueError(
                "Select a recording range with at least 32 packets inside this session."
            )
        session = {
            **original,
            "amplitude": original["amplitude"][:, start:end],
            "invalid": original["invalid"][start:end],
            "timestamps": original["timestamps"][start:end],
        }
        if "channel" in original:
            session["channel"] = original["channel"][:, start:end]
        session["audit"] = motion_audit(session)
        metadata = {
            "schema": "orbit.sensing.v1",
            "packet_range": {"start": start, "end": end, "end_exclusive": True},
            "calibrated_threshold": original.get("threshold") if original["synthetic"] else None,
            "calibration_protocol": "Saved paired same-seed empty-simulation mean+kSD; not independently validated"
            if original.get("threshold") is not None
            else None,
            "synthetic": session["synthetic"],
            "source": session["source"],
            "capture_id": session["capture_id"],
            "config": session.get("import_config", session["config"]),
            "rate": session["rate"],
            "notes": "Procedural avatar is illustration, not recovered location. Amplitude-only recorded inputs have no invented phase. No trained inference or accuracy in this experiment.",
        }
        if format == "npz":
            buf = io.BytesIO()
            content = {
                "amplitude": session["amplitude"],
                "invalid": session["invalid"],
                "timestamps": session["timestamps"],
                "metadata": np.array(json.dumps(metadata)),
            }
            if original["synthetic"] and original.get("positions"):
                content["positions"] = np.asarray([p[start:end] for p in original["positions"]])
            if "channel" in session:
                content.update(csi_real=session["channel"].real, csi_imag=session["channel"].imag)
            np.savez_compressed(buf, **content)
            return buf.getvalue(), "application/octet-stream"
        audit = session["audit"]
        if format == "json":
            return json.dumps(
                {
                    **metadata,
                    "trace": finite_list(np.where(audit["valid"], audit["trace"], np.nan)),
                    "score": finite_list(audit["score"]),
                    "time": session["timestamps"].tolist(),
                },
                allow_nan=False,
            ).encode(), "application/json"
        if format == "csv":
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(
                [
                    "packet",
                    "time_or_packet",
                    "synthetic",
                    "source",
                    "valid",
                    "median_amplitude",
                    "motion_proxy",
                ]
            )
            for i, t in enumerate(session["timestamps"]):
                writer.writerow(
                    [
                        i + start,
                        t,
                        session["synthetic"],
                        session["source"],
                        bool(audit["valid"][i]),
                        float(audit["trace"][i]) if audit["valid"][i] else "",
                        float(audit["score"][i]) if np.isfinite(audit["score"][i]) else "",
                    ]
                )
            return buf.getvalue().encode(), "text/csv"
        raise HTTPException(400, "Choose JSON, CSV or NPZ.")

    @app.get("/api/sensing/sessions/{ident}/export/{format}")
    def download(ident: str, format: str, start: int = 0, end: int | None = None):
        raw, mime = export(ident, format, start, end)
        return Response(
            raw,
            media_type=mime,
            headers={
                "Content-Disposition": f'attachment; filename="Orbit-sensing-{ident}.{format}"',
                "X-Content-SHA256": hashlib.sha256(raw).hexdigest(),
            },
        )

    @app.post("/api/sensing/sessions/{ident}/save")
    def save(ident: str, body: dict | None = None):
        body = body or {}
        start, end = body.get("start", 0), body.get("end")
        if not isinstance(start, int) or (end is not None and not isinstance(end, int)):
            raise ValueError("Use whole packet numbers for the selected range.")
        session = get_session(ident)
        raw, _ = export(ident, "npz", start, end)
        row = ctx["save_asset"](
            raw,
            "Orbit-sensing-" + ident + ".npz",
            "sensing-studio",
            synthetic=session["synthetic"],
            parent_id=session.get("asset_id"),
            capture_id=session["capture_id"],
            packet_range={"start": start, "end": end or session["amplitude"].shape[1]},
            notes="Complex-channel experiment. Synthetic flag embedded in NPZ metadata. Original capture unchanged.",
        )
        return {"asset": row, "sha256": row["sha256"]}

    @app.get("/api/sensing/recordings")
    def recordings():
        return {
            "recordings": [
                r
                for r in ctx["rows"]("media")
                if r.get("source") == "sensing-studio" and not r.get("trashed")
            ]
        }

    @app.post("/api/sensing/recordings/{ident}/open")
    async def open_recording(ident: str):
        row, path = ctx["load_asset"](ident)
        if path.suffix.lower() not in (".json", ".npz") or path.stat().st_size > 32 * 1024**2:
            raise ValueError("Open an Orbit JSON/NPZ session below 32 MiB from the Library.")
        result = await import_session(
            UploadFile(file=io.BytesIO(path.read_bytes()), filename=row["name"])
        )
        get_session(result["id"])["asset_id"] = ident
        if row.get("synthetic") and not result["synthetic"]:
            session = get_session(result["id"])
            session.update(synthetic=True, source="SIMULATION IMPORT")
            return register(session)
        if result["synthetic"] and not row.get("synthetic"):
            latest, _ = ctx["load_asset"](ident)
            ctx["put"]("media", {**latest, "synthetic": True})
        return result

    @app.post("/api/sensing/sessions/{ident}/save-analysis")
    def save_analysis(ident: str, body: Analysis):
        session = get_session(ident)
        result = analyze(session, body)
        payload = {
            "schema": "orbit.sensing.analysis.v1",
            "synthetic": session["synthetic"],
            "source": session["source"],
            "capture_id": session["capture_id"],
            "settings": body.model_dump(),
            "result": result,
        }
        raw = json.dumps(payload, allow_nan=False).encode()
        row = ctx["save_asset"](
            raw,
            "Orbit-filter-comparison-" + ident + ".json",
            "sensing-analysis",
            synthetic=session["synthetic"],
            parent_id=session.get("asset_id"),
            capture_id=session["capture_id"],
            notes=result["protocol"],
        )
        return {"asset": row, "sha256": row["sha256"]}
