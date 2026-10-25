"""Numerical contracts extracted from the recorded comparison notebook."""

from pathlib import Path, PurePosixPath
import json, re, stat, zipfile, time
import h5py
import numpy as np
from scipy import signal

MAX_ARRAY_BYTES = 256 * 1024**2
MAX_EXPANDED = 4 * 1024**3


def safe_extract(archive, target):
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        if len(entries) > 2000 or sum(x.file_size for x in entries) > MAX_EXPANDED:
            raise ValueError("Archive exceeds 2,000 entries or 4 GiB expanded size.")
        seen = set()
        for item in entries:
            p = PurePosixPath(item.filename.replace("\\", "/"))
            if (
                p.is_absolute()
                or ".." in p.parts
                or ":" in str(p)
                or stat.S_ISLNK(item.external_attr >> 16)
            ):
                raise ValueError("Unsafe archive path or symbolic link.")
            if str(p).lower() in seen:
                raise ValueError("Duplicate archive paths are unsupported.")
            seen.add(str(p).lower())
            if (
                item.file_size > MAX_ARRAY_BYTES
                or item.file_size / max(item.compress_size, 1) > 1000
            ):
                raise ValueError(
                    "Archive member exceeds size or compression-ratio limit."
                )
            if item.is_dir() or "__MACOSX" in p.parts or p.name.startswith("._"):
                continue
            if p.suffix.lower() not in (".mat", ".json"):
                continue
            dest = target.joinpath(*p.parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(item) as src, dest.open("wb") as out:
                count = 0
                while chunk := src.read(1024**2):
                    count += len(chunk)
                    if count > MAX_ARRAY_BYTES:
                        raise ValueError("Expanded member exceeds limit.")
                    out.write(chunk)


def read_capture(path, bandwidth=None):
    if not h5py.is_hdf5(path):
        raise ValueError("Expected MATLAB v7.3 / HDF5 with a complex capture dataset.")
    with h5py.File(path, "r") as f:
        if not isinstance(f.get("capture", getlink=True), h5py.HardLink):
            raise ValueError(
                "capture must be a local HDF5 dataset; links are not accepted."
            )
        d = f["capture"]
        if not isinstance(d, h5py.Dataset) or d.is_virtual or d.external:
            raise ValueError("External or virtual HDF5 data is unsupported.")
        if d.ndim != 2 or d.size * d.dtype.itemsize > MAX_ARRAY_BYTES:
            raise ValueError("Expected a 2-D capture smaller than 256 MiB decoded.")
        if h5py.check_dtype(ref=d.dtype) or d.dtype.hasobject:
            raise ValueError("Object/reference arrays are unsupported.")
        raw = d[()]
    if raw.dtype.fields and {"real", "imag"}.issubset(raw.dtype.fields):
        real, imag = raw["real"].astype(np.float32), raw["imag"].astype(np.float32)
    elif np.iscomplexobj(raw):
        real, imag = raw.real.astype(np.float32), raw.imag.astype(np.float32)
    else:
        raise ValueError(
            "capture must contain complex CSI or real/imag compound fields."
        )
    expected = {20: 256, 40: 512}.get(bandwidth)
    if expected:
        if real.shape[0] != expected and real.shape[1] == expected:
            real, imag = real.T, imag.T
        if real.shape[0] != expected:
            raise ValueError(
                f"{bandwidth} MHz requires {expected} subcarriers; got {real.shape}."
            )
    elif real.shape[0] in (256, 512):
        pass
    elif real.shape[1] in (256, 512):
        real, imag = real.T, imag.T
    else:
        raise ValueError(
            "Supported arrays have 256 or 512 subcarriers; orientation is otherwise ambiguous."
        )
    if real.shape[1] < 2:
        raise ValueError("Capture has fewer than two packets.")
    finite = np.isfinite(real).all(axis=0) & np.isfinite(imag).all(axis=0)
    zero = ((real == 0) & (imag == 0)).all(axis=0)
    invalid = ~finite | zero
    a = np.hypot(
        np.nan_to_num(real, nan=0, posinf=0, neginf=0),
        np.nan_to_num(imag, nan=0, posinf=0, neginf=0),
    )
    if not np.isfinite(a).all():
        raise ValueError("CSI magnitude overflows float32.")
    return a, invalid, int(zero.sum())


def metadata(path, root):
    cfg = {}
    for folder in (path.parent, *path.parent.parents):
        if not folder.is_relative_to(root):
            break
        c = folder / "config.json"
        if c.exists():
            if c.stat().st_size > 1024**2:
                raise ValueError("Configuration exceeds 1 MiB.")
            cfg = json.loads(c.read_text(encoding="utf-8"))
            if not isinstance(cfg, dict):
                raise ValueError("config.json must be an object.")
            break
    people = cfg.get("people", {})
    if not isinstance(people, dict):
        people = {}
    bw = str(cfg.get("bandwidth", "")).lower().replace("mhz", "").strip()
    bw = int(bw) if bw in ("20", "40") else None
    date = re.search(r"20\d{2}-\d{2}-\d{2}", str(path.relative_to(root)))
    return {
        "bandwidth": bw,
        "modulation": str(cfg.get("modulation", "unknown")).lower(),
        "present": (
            people.get("present") if isinstance(people.get("present"), bool) else None
        ),
        "people": people.get("num"),
        "moving": people.get("moving"),
        "date": date.group() if date else str(cfg.get("date", "unknown")),
        "config": cfg,
    }


def four_features(segment, valid=None):
    a = segment if valid is None else segment[:, valid]
    if not a.shape[1]:
        raise ValueError("No valid packets in window.")
    if segment.shape[1] < 2:
        diff = np.zeros(segment.shape[0])
    elif valid is None:
        diff = np.mean(np.abs(np.diff(segment, axis=1)), axis=1)
    else:
        pairs = valid[:-1] & valid[1:]
        diff = (
            np.mean(np.abs(np.diff(segment, axis=1)[:, pairs]), axis=1)
            if pairs.any()
            else np.zeros(segment.shape[0])
        )
    return np.concatenate(
        [
            a.mean(axis=1),
            a.std(axis=1),
            diff,
            np.percentile(a, 90, axis=1) - np.percentile(a, 10, axis=1),
        ]
    ).astype(np.float32)


def contract(bandwidth):
    return {
        "version": "orbit-amplitude-v1",
        "bandwidth": bandwidth,
        "window": 256 if bandwidth == 20 else 512,
        "hop": 128 if bandwidth == 20 else 512,
        "features": ["mean", "std", "mean_abs_adjacent_difference", "p90_minus_p10"],
        "preprocessing": (
            "nonfinite-to-zero" if bandwidth == 20 else "valid-packets-adjacent-pairs"
        ),
        "min_valid_fraction": 0 if bandwidth == 20 else 0.90,
        "subcarriers": 256 if bandwidth == 20 else 512,
    }


def feature_windows(a, invalid, bandwidth):
    c = contract(bandwidth)
    rows = []
    windows = []
    audit = []
    stops = (
        range(0, a.shape[1] - c["window"] + 1, c["hop"])
        if bandwidth == 20
        else range(0, a.shape[1], c["hop"])
    )
    for start in stops:
        end = min(start + c["window"], a.shape[1])
        valid = ~invalid[start:end]
        reason = ""
        if end - start < 256:
            reason = "shorter_than_minimum_window"
        elif bandwidth == 40 and valid.mean() < 0.90:
            reason = "valid_fraction_below_90_percent"
        audit.append(
            {
                "start": start,
                "end": end,
                "valid_fraction": float(valid.mean()),
                "accepted": not reason,
                "reason": reason,
            }
        )
        if not reason:
            rows.append(
                four_features(a[:, start:end], valid if bandwidth == 40 else None)
            )
            windows.append({"start": start, "end": end})
    return np.vstack(rows) if rows else np.empty((0, a.shape[0] * 4)), windows, audit


def demo_signal(n=2048):
    t = np.arange(n)
    rng = np.random.default_rng(42)
    return (
        1.2
        + 0.28 * np.sin(2 * np.pi * 0.018 * t)
        + 0.12 * np.sin(2 * np.pi * 0.14 * t)
        + 0.07 * rng.normal(size=n)
    )


def radix2(x):
    x = np.asarray(x, dtype=complex)
    if not len(x) or len(x) & (len(x) - 1):
        raise ValueError("Radix-2 FFT requires a power-of-two length.")
    if len(x) == 1:
        return x
    even, odd = radix2(x[::2]), radix2(x[1::2])
    t = np.exp(-2j * np.pi * np.arange(len(x) // 2) / len(x)) * odd
    return np.concatenate([even + t, even - t])


def dsp(
    x,
    operation="moving_average",
    taps=15,
    window="hann",
    cutoff=0.1,
    kind="lowpass",
    factor=2,
):
    x = np.asarray(x, dtype=float)
    if not 3 <= taps <= 127 or not 0 < cutoff < 0.5 or not 2 <= factor <= 8:
        raise ValueError("Invalid DSP parameters.")
    if window not in ("boxcar", "triang", "hann", "hamming", "blackman"):
        raise ValueError("Unsupported window.")
    b, den = np.ones(taps) / taps, np.array([1.0])
    extra = {}
    if operation == "shootout":
        fir = signal.firwin(taps, 0.1, window=window, fs=1)
        but_b, but_a = signal.butter(4, 0.1, fs=1)
        y = signal.lfilter(b, den, x)
        extra = {
            "fir_trace": signal.lfilter(fir, [1], x).tolist(),
            "butterworth_trace": signal.lfilter(but_b, but_a, x).tolist(),
        }
        note = "Same-input comparison: moving average, windowed FIR and fourth-order Butterworth. Fixed cutoff 0.1 cycles/packet. No downstream accuracy claim."
    elif operation == "fir":
        if taps % 2 == 0:
            raise ValueError("Use an odd FIR tap count.")
        b = signal.firwin(taps, cutoff, window=window, fs=1)
        y = signal.lfilter(b, den, x)
        note = f"Windowed FIR low-pass. Causal delay {(taps-1)/2:g} packets; startup transient included."
    elif operation == "butterworth":
        if kind not in ("lowpass", "highpass", "bandpass"):
            raise ValueError("Unsupported Butterworth type.")
        edge = [cutoff / 2, cutoff] if kind == "bandpass" else cutoff
        b, den = signal.butter(4, edge, btype=kind, fs=1)
        y = signal.lfilter(b, den, x)
        note = "Fourth-order causal Butterworth; cutoff is cycles/packet, not Hz."
    elif operation == "convolution":
        linear = np.convolve(x, b)
        circular = np.fft.ifft(np.fft.fft(x) * np.fft.fft(b, len(x))).real
        y = linear[: len(x)]
        extra = {
            "linear": linear.tolist(),
            "circular": circular.tolist(),
            "fft_max_error": float(np.max(np.abs(linear - signal.fftconvolve(x, b)))),
        }
        note = "Linear convolution retains the tail. Circular convolution wraps the tail onto the start."
    elif operation == "multirate":
        y = signal.resample_poly(x, 1, factor)
        extra = {"naive": x[::factor].tolist(), "output_packet_spacing": factor}
        note = f"Anti-aliased decimation by {factor}; naive samples show aliasing risk."
    elif operation == "interpolation":
        y = signal.resample_poly(x, factor, 1)
        extra = {"output_packet_spacing": 1 / factor}
        note = f"Polyphase interpolation by {factor} with reconstruction filtering."
    elif operation == "hilbert":
        y = np.abs(signal.hilbert(x - x.mean()))
        note = "Envelope of mean-centred amplitude. This is not recovered CSI phase."
    elif operation == "stft":
        y = x.copy()
        f, t, z = signal.stft(
            x - x.mean(), fs=1, window=window, nperseg=min(128, len(x))
        )
        extra = {
            "stft": {
                "frequency": f.tolist(),
                "packet": t.tolist(),
                "magnitude": np.abs(z).tolist(),
            }
        }
        note = "Short-time spectrum of mean-centred amplitude, in cycles/packet."
    elif operation == "fft":
        n = min(256, 2 ** int(np.log2(len(x))))
        v = (x[:n] - x[:n].mean()) * signal.get_window(window, n)
        t = time.perf_counter()
        direct = np.exp(-2j * np.pi * np.outer(np.arange(n), np.arange(n)) / n) @ v
        direct_ms = (time.perf_counter() - t) * 1000
        t = time.perf_counter()
        own = radix2(v)
        fft_ms = (time.perf_counter() - t) * 1000
        extra = {
            "direct_dft_ms": direct_ms,
            "educational_fft_ms": fft_ms,
            "fft_max_error": float(np.max(np.abs(own - np.fft.fft(v)))),
            "dft_max_error": float(np.max(np.abs(direct - np.fft.fft(v)))),
            "compared_samples": n,
        }
        y = x * signal.get_window(window, len(x))
        note = "Direct DFT and recursive radix-2 FFT compared with NumPy. Timings are local measurements."
    elif operation == "q15":
        b = signal.firwin(taps, cutoff, window=window, fs=1)
        quant = np.round(b * 32768) / 32768
        y = signal.lfilter(quant, den, x)
        extra = {
            "q15": quant.tolist(),
            "max_coefficient_error": float(np.max(np.abs(quant - b))),
        }
        note = "Q15 coefficient quantization demo; accumulation remains floating point."
    elif operation == "moving_average":
        y = signal.lfilter(b, den, x)
        note = f"{taps}-tap causal moving average; group delay {(taps-1)/2:g} packets. Filtering does not establish improved detection."
    else:
        raise ValueError("Unknown DSP operation.")
    n = min(len(x), len(y))
    taper = signal.get_window(window, n)
    spectrum = lambda v: (
        2 / n * np.abs(np.fft.rfft((v[:n] - v[:n].mean()) * taper))
    ).tolist()
    w, h = signal.freqz(b, den, worN=256, fs=1)
    return {
        "raw": x.tolist(),
        "processed": y.tolist(),
        "frequency": np.fft.rfftfreq(n).tolist(),
        "raw_spectrum": spectrum(x),
        "processed_spectrum": spectrum(y),
        "response_frequency": w.tolist(),
        "response_db": (20 * np.log10(np.maximum(np.abs(h), 1e-10))).tolist(),
        "coefficients": b.tolist(),
        "denominator": den.tolist(),
        "note": note,
        "extra": extra,
        "metrics": {
            "raw_std": float(x.std()),
            "processed_std": float(y.std()),
            "raw_rms": float(np.sqrt(np.mean(x * x))),
            "processed_rms": float(np.sqrt(np.mean(y * y))),
        },
    }


def fuzzy(variation=0.4, motion=0.6, rules=None):
    low = lambda v: max(0.0, 1 - 2 * v)
    high = lambda v: max(0.0, 2 * v - 1)
    mid = lambda v: max(0.0, 1 - abs(2 * v - 1))
    functions = {"low": low, "medium": mid, "high": high}
    rules = rules or [
        {"variation": "low", "motion": "low", "output": "low"},
        {"variation": "medium", "motion": "medium", "output": "medium"},
        {"variation": "high", "motion": "high", "output": "high"},
        {"variation": "high", "motion": "medium", "output": "high"},
        {"variation": "medium", "motion": "high", "output": "high"},
    ]
    if len(rules) > 20:
        raise ValueError("At most 20 rules.")
    u = np.linspace(0, 1, 201)
    curves = {k: np.array([fn(t) for t in u]) for k, fn in functions.items()}
    aggregate = np.zeros_like(u)
    fired = []
    for rule in rules:
        if any(rule.get(k) not in functions for k in ("variation", "motion", "output")):
            raise ValueError("Rule labels must be low, medium or high.")
        strength = min(
            functions[rule["variation"]](variation), functions[rule["motion"]](motion)
        )
        aggregate = np.maximum(aggregate, np.minimum(strength, curves[rule["output"]]))
        fired.append({**rule, "strength": strength})
    area = np.trapezoid(aggregate, u)
    value = float(np.trapezoid(u * aggregate, u) / area) if area > 0 else None
    return {
        "universe": u.tolist(),
        "memberships": {k: v.tolist() for k, v in curves.items()},
        "aggregate": aggregate.tolist(),
        "value": value,
        "rules": fired,
        "source": "EDUCATIONAL DEMO",
        "meaning": "Illustrative activity score; not human-presence probability.",
    }
