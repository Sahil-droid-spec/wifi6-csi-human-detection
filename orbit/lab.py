"""Reproducible simulations and numerical teaching tools; never measurement evidence."""

import json
import zipfile
from pathlib import Path

import h5py
import numpy as np
from sklearn.linear_model import Perceptron, SGDRegressor
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

CLASSES = {
    "empty": (0, False),
    "one_still": (1, False),
    "one_moving": (1, True),
    "two_people": (2, True),
}


def generate(
    target: Path,
    *,
    subcarriers=256,
    packet_rate=100.0,
    duration=10.24,
    noise=0.03,
    seed=42,
    sessions=6,
    days=3,
    environment="LOS",
    loss=0.02,
    classes=None,
):
    classes = classes or list(CLASSES)
    if (
        subcarriers not in (256, 512)
        or not 20 <= packet_rate <= 500
        or not 3 <= duration <= 60
        or not 2 <= sessions <= 12
        or not 2 <= days <= sessions
        or not 0 <= noise <= 0.5
        or not 0 <= loss <= 0.2
        or environment not in ("LOS", "NLOS")
        or any(c not in CLASSES for c in classes)
    ):
        raise ValueError(
            "Choose 256/512 subcarriers, 20–500 packets/s, 3–60 seconds, 2–12 sessions and valid simulation settings."
        )
    n = int(packet_rate * duration)
    if n * subcarriers * sessions * len(classes) > 50_000_000:
        raise ValueError(
            "Reduce duration, sessions or subcarriers to fit the simulation memory cap."
        )
    rng = np.random.default_rng(seed)
    freq = np.linspace(-1, 1, subcarriers)
    t = np.arange(n) / packet_rate
    generated = []
    for session in range(sessions):
        day = session % days + 1
        static = sum(
            (rng.normal() + 1j * rng.normal()) * np.exp(-2j * np.pi * freq * rng.uniform(0, 5))
            for _ in range(6)
        ) / np.sqrt(6)
        static *= 1 if environment == "LOS" else 0.65
        for cls in classes:
            people, moving = CLASSES[cls]
            channel = np.broadcast_to(static[:, None], (subcarriers, n)).copy()
            drift = 1 + 0.025 * np.sin(2 * np.pi * 0.025 * t + rng.uniform(0, 6))
            for person in range(people):
                rate = rng.uniform(0.6, 1.5) if moving else rng.uniform(0.15, 0.3)
                excursion = 0.3 if moving else 0.008
                distance = rng.uniform(1, 3) + excursion * np.sin(
                    2 * np.pi * rate * t + rng.uniform(0, 6)
                )
                reflection = 0.2 * np.exp(
                    -1j * (freq[:, None] * rng.uniform(1, 5) + 2 * np.pi * distance[None, :] / 0.06)
                )
                channel += reflection
            channel *= drift
            gain = np.ones(n)
            step = int(rng.integers(n // 3, 2 * n // 3))
            gain[step:] = rng.uniform(0.8, 1.2)
            channel = channel * gain + noise * (
                rng.normal(size=channel.shape) + 1j * rng.normal(size=channel.shape)
            )
            missing = rng.random(n) < loss
            if loss and n > 512:
                begin = int(rng.integers(0, n - 32))
                missing[begin : begin + int(12 + loss * 100)] = True
            channel[:, missing] = 0
            folder = target / f"Session {session + 1}" / f"Day {day}" / cls
            folder.mkdir(parents=True, exist_ok=True)
            cfg = {
                "synthetic": True,
                "simulation_name": "Simulation set A",
                "session": f"Session {session + 1}",
                "date": f"Day {day}",
                "class": cls,
                "modulation": "ax",
                "bandwidth": 20 if subcarriers == 256 else 40,
                "packet_rate": packet_rate,
                "duration": duration,
                "environment": environment,
                "seed": seed,
                "people": {"present": people > 0, "num": people, "moving": moving},
                "generator": "orbit-reflections-v1",
                "meaning": "Simulated channel; not measured human motion or RF packet loss",
            }
            (folder / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf8")
            with h5py.File(folder / "recording.mat", "w") as f:
                f.attrs["synthetic"] = True
                f.attrs["generator"] = "orbit-reflections-v1"
                f.create_dataset("capture", data=channel.astype(np.complex64), compression="gzip")
            generated.append(folder / "recording.mat")
    return generated


def archive(folder: Path, destination: Path) -> Path:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(folder).as_posix())
    return destination


def convert_array(source: Path, destination: Path, subcarriers: int) -> bool:
    """Safe, bounded numeric import. Real arrays are explicitly amplitude-only."""
    if source.stat().st_size > 256 * 1024**2:
        raise ValueError("Split numeric files larger than 256 MiB.")
    if source.suffix.lower() == ".csv":
        a = np.loadtxt(source, delimiter=",", dtype=complex, ndmin=2)
    elif source.suffix.lower() == ".npy":
        a = np.load(source, allow_pickle=False, mmap_mode="r")
    else:
        with zipfile.ZipFile(source) as z:
            if (
                len(z.infolist()) > 32
                or sum(i.file_size for i in z.infolist()) > 256 * 1024**2
                or any(i.file_size / max(i.compress_size, 1) > 1000 for i in z.infolist())
            ):
                raise ValueError("NPZ exceeds safe expansion limits.")
        with np.load(source, allow_pickle=False) as z:
            key = (
                "capture"
                if "capture" in z
                else "csi"
                if "csi" in z
                else "amplitude"
                if "amplitude" in z
                else None
            )
            if key is None:
                raise ValueError("NPZ needs a capture, csi or amplitude numeric array.")
            a = z[key]
    if a.ndim != 2 or a.size * 8 > 256 * 1024**2 or a.dtype.hasobject:
        raise ValueError("Use a 2-D numeric array smaller than 256 MiB.")
    if a.shape[0] != subcarriers and a.shape[1] == subcarriers:
        a = a.T
    if a.shape[0] != subcarriers:
        raise ValueError("Array shape does not match the selected bandwidth/subcarriers.")
    amplitude_only = not np.iscomplexobj(a) or not np.any(np.asarray(a).imag)
    with h5py.File(destination, "w") as f:
        f.create_dataset("capture", data=np.asarray(a, dtype=np.complex64))
    return amplitude_only


def defuzzify(universe, membership, method: str = "centroid") -> float | None:
    u = np.asarray(universe)
    m = np.asarray(membership)
    area = np.trapezoid(m, u)
    if not area:
        return None
    if method == "centroid":
        return float(np.trapezoid(u * m, u) / area)
    peaks = u[np.isclose(m, m.max())]
    if method == "mean_of_maxima":
        return float(peaks.mean())
    if method == "smallest_of_maxima":
        return float(peaks.min())
    if method == "largest_of_maxima":
        return float(peaks.max())
    if method == "bisector":
        partial = np.r_[0, np.cumsum((m[1:] + m[:-1]) * np.diff(u) / 2)]
        return float(np.interp(area / 2, partial, u))
    raise ValueError("Choose centroid, bisector or a maxima method.")


def teaching(kind: str = "perceptron", seed: int = 42, epochs: int = 40, grid: int = 4) -> dict:
    """Explicit educational fixture, separate from saved CSI model evidence."""
    if (
        kind not in ("perceptron", "adaline", "mlp", "som")
        or not 5 <= epochs <= 200
        or not 2 <= grid <= 8
    ):
        raise ValueError("Choose a supported learning tool and bounded iterations.")
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(160, 2))
    y = (x[:, 0] * x[:, 1] > 0).astype(int)
    train = np.arange(120)
    test = np.arange(120, 160)
    scale = StandardScaler().fit(x[train])
    z = scale.transform(x)
    loss = []
    if kind == "som":
        weights = rng.normal(size=(grid * grid, 2))
        coords = np.array([(i, j) for i in range(grid) for j in range(grid)])
        for e in range(epochs):
            for v in z[train]:
                win = np.argmin(np.linalg.norm(weights - v, axis=1))
                near = np.exp(
                    -np.sum((coords - coords[win]) ** 2, axis=1)
                    / (2 * max(0.5, grid * (1 - e / epochs)) ** 2)
                )
                weights += 0.15 * (1 - e / epochs) * near[:, None] * (v - weights)
            loss.append(
                float(
                    np.min(
                        np.linalg.norm(z[train, None, :] - weights[None, :, :], axis=2), axis=1
                    ).mean()
                )
            )
        return {
            "kind": kind,
            "weights": weights.tolist(),
            "loss": loss,
            "source": "EDUCATIONAL SIMULATION",
            "protocol": "Unsupervised quantization error on the first 120 fixture points; no classification accuracy",
            "points": z.tolist(),
            "grid": grid,
        }
    model = (
        Perceptron(random_state=seed)
        if kind == "perceptron"
        else SGDRegressor(
            loss="squared_error", eta0=0.01, learning_rate="constant", random_state=seed
        )
        if kind == "adaline"
        else MLPClassifier(
            hidden_layer_sizes=(8,), solver="sgd", learning_rate_init=0.08, random_state=seed
        )
    )
    for _ in range(epochs):
        if kind == "adaline":
            model.partial_fit(z[train], y[train])
            p = model.predict(z[train])
            loss.append(float(np.mean((p - y[train]) ** 2)))
        else:
            model.partial_fit(z[train], y[train], classes=[0, 1])
            p = model.predict(z[train])
            loss.append(float(model.loss_) if kind == "mlp" else float(np.mean(p != y[train])))
    pred = (
        (model.predict(z[test]) >= 0.5).astype(int) if kind == "adaline" else model.predict(z[test])
    )
    accuracy = float(np.mean(pred == y[test]))
    return {
        "kind": kind,
        "loss": loss,
        "accuracy": accuracy,
        "source": "EDUCATIONAL SIMULATION",
        "protocol": "Seeded XOR fixture; first 120 train, last 40 held out; scaler fitted on training only; not CSI validation",
        "points": z.tolist(),
        "labels": y.tolist(),
        "predictions": pred.tolist(),
    }


def quality_gate(valid_fraction: float, variation: float) -> dict:
    score = float(np.clip((valid_fraction - 0.5) / 0.5, 0, 1) * np.clip(variation / 0.01, 0, 1))
    return {
        "score": score,
        "accept": valid_fraction >= 0.9 and score >= 0.5,
        "why": [
            "At least 90% usable packets required",
            "Near-flat traces receive lower fuzzy quality membership",
        ],
        "protocol": "Heuristic fuzzy quality gate; not a presence classifier or calibrated probability",
    }
