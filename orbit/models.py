"""Leakage-safe local training with capture/date grouping and internal artifacts."""

import hashlib
import json
import platform
from datetime import datetime, timezone

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .core import contract, feature_windows, read_capture


def metrics(y, p):
    return {
        "accuracy": float(accuracy_score(y, p)),
        "balanced_accuracy": float(balanced_accuracy_score(y, p)),
        "precision": float(precision_score(y, p, zero_division=0)),
        "recall": float(recall_score(y, p, zero_division=0)),
        "f1": float(f1_score(y, p, zero_division=0)),
        "macro_f1": float(f1_score(y, p, average="macro", zero_division=0)),
        "support": len(y),
        "confusion_matrix": confusion_matrix(y, p, labels=[0, 1]).tolist(),
    }


def estimator(kind):
    if kind == "lr":
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=3000, class_weight="balanced", random_state=42),
        )
    if kind == "mlp":
        return make_pipeline(
            StandardScaler(),
            MLPClassifier(
                hidden_layer_sizes=(64, 32),
                max_iter=300,
                random_state=42,
                early_stopping=False,
            ),
        )
    return RandomForestClassifier(
        n_estimators=150,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=1,
    )


def aggregate(y, p, groups):
    out = []
    for g in np.unique(groups):
        idx = groups == g
        # Majority vote; a tie is resolved as absence, matching NumPy's sorted argmax baseline.
        pred = int(np.bincount(p[idx].astype(int), minlength=2).argmax())
        out.append(
            {
                "capture_id": str(g),
                "truth": int(y[idx][0]),
                "prediction": pred,
                "windows": int(idx.sum()),
            }
        )
    return out


def genetic_select(x, y, g, population=8, generations=6, mutation=0.03):
    """Inner capture-grouped fitness; outer evaluation rows never enter this function."""
    labels = {c: int(y[g == c][0]) for c in np.unique(g)}
    counts = [sum(v == k for v in labels.values()) for k in (0, 1)]
    if min(counts) < 2:
        raise ValueError(
            "GA needs at least two independent training captures per class in every outer fold."
        )
    capture_ids = np.array(list(labels))
    capture_y = np.array(list(labels.values()))
    splits = [
        (
            np.flatnonzero(np.isin(g, capture_ids[tr])),
            np.flatnonzero(np.isin(g, capture_ids[va])),
        )
        for tr, va in StratifiedKFold(
            n_splits=min(3, min(counts)), shuffle=True, random_state=42
        ).split(capture_ids, capture_y)
    ]
    if any(len(np.unique(y[a])) < 2 or len(np.unique(y[b])) < 2 for a, b in splits):
        raise ValueError("GA inner capture splits do not contain both classes; add more captures.")
    rng = np.random.default_rng(42)
    width = x.shape[1]
    pop = rng.random((population, width)) < 0.08
    cache = {}
    history = []

    def fitness(mask):
        if not mask.any():
            return -1.0
        key = mask.tobytes()
        if key not in cache:
            scores = []
            for tr, va in splits:
                m = RandomForestClassifier(
                    n_estimators=35, min_samples_leaf=2, random_state=42, n_jobs=1
                )
                m.fit(x[tr][:, mask], y[tr])
                pred = m.predict(x[va][:, mask])
                rows = aggregate(y[va], pred, g[va])
                scores.append(
                    balanced_accuracy_score(
                        [r["truth"] for r in rows], [r["prediction"] for r in rows]
                    )
                )
            cache[key] = float(np.mean(scores)) - 0.002 * mask.mean()
        return cache[key]

    for _ in range(generations):
        scores = np.array([fitness(m) for m in pop])
        order = np.argsort(scores)[::-1]
        pop = pop[order]
        history.append(float(scores[order[0]]))
        next_pop = [pop[0].copy(), pop[1].copy()]
        while len(next_pop) < population:
            a, b = pop[rng.integers(0, max(2, population // 2), 2)]
            child = np.where(rng.random(width) < 0.5, a, b)
            child ^= rng.random(width) < mutation
            if not child.any():
                child[rng.integers(width)] = True
            next_pop.append(child)
        pop = np.array(next_pop)
    best = max(pop, key=fitness)
    return np.flatnonzero(best), history


def training_check(captures, bandwidth=20, split="date", kinds=None):
    kinds = kinds or ["lr", "rf", "mlp"]
    unique = {}
    for c in captures:
        if (
            c.get("bandwidth_verified", True)
            and c.get("bandwidth") == bandwidth
            and c.get("modulation") == "ax"
            and c.get("present") is not None
            and c.get("windows", 0) > 0
        ):
            unique.setdefault(c["sha256"], c)
    rows = list(unique.values())
    reason = ""
    if not rows:
        reason = "Import labelled AX recordings with accepted windows for this bandwidth, or choose another dataset."
    elif split == "date" and any(c.get("date", "unknown") == "unknown" for c in rows):
        reason = (
            "Add recording dates in config.json, or choose capture-held-out exploratory evaluation."
        )
    else:
        group = lambda c: c.get("date") if split == "date" else c["id"]
        groups = set(group(c) for c in rows)
        if len(groups) < 2 or len(set(c["present"] for c in rows)) < 2:
            reason = "Add both presence classes and at least two independent recording groups."
        else:
            for held in groups:
                training = [c for c in rows if group(c) != held]
                counts = [sum(int(c["present"]) == k for c in training) for k in (0, 1)]
                if min(counts) == 0:
                    reason = "Date/class confounding leaves a training fold with one class. Choose capture-held-out exploratory evaluation or collect both classes on each date."
                    break
                if "ga_rf" in kinds and min(counts) < 2:
                    reason = "GA needs two independent training recordings per class in every outer fold. Add recordings or choose LR, RF or ANN."
                    break
    return {
        "valid": not reason,
        "reason": reason,
        "captures": len(rows),
        "protocol": "leave-one-recording-date-out" if split == "date" else "leave-one-capture-out",
    }


def train(
    captures,
    root,
    outdir,
    job_id,
    bandwidth=20,
    split="date",
    kinds=None,
    population=8,
    generations=6,
    mutation=0.03,
    progress=lambda *a: None,
):
    kinds = kinds or ["lr", "rf", "mlp"]
    xx = []
    yy = []
    gg = []
    dd = []
    used = []
    window_map = {}
    hashes = set()
    for cap in captures:
        if (
            cap.get("bandwidth") != bandwidth
            or cap.get("present") is None
            or cap.get("modulation") != "ax"
        ):
            continue
        if cap["sha256"] in hashes:
            continue
        a, invalid, _ = read_capture(root / cap["path"], bandwidth)
        x, accepted_windows, _ = feature_windows(a, invalid, bandwidth)
        window_map[cap["id"]] = accepted_windows
        if not len(x):
            continue
        hashes.add(cap["sha256"])
        xx.append(x)
        yy.extend([int(cap["present"])] * len(x))
        gg.extend([cap["id"]] * len(x))
        dd.extend([cap["date"]] * len(x))
        used.append(cap)
    if not xx:
        raise ValueError(
            "No labelled AX captures with accepted windows. Import a ZIP with per-recording config.json."
        )
    if len({bool(c.get("synthetic")) for c in used}) > 1:
        raise ValueError("Train simulation and real recordings in separate libraries.")
    x = np.vstack(xx)
    y = np.array(yy)
    g = np.array(gg)
    dates = np.array(dd)
    if len(x) > 100000:
        raise ValueError("Training capped at 100,000 windows; import a smaller subset.")
    groups = dates if split == "date" else g
    if split == "date" and "unknown" in groups:
        raise ValueError("Date-held-out training needs known recording dates for every capture.")
    if len(np.unique(groups)) < 2 or len(np.unique(y)) < 2:
        raise ValueError("Need both presence classes and at least two independent groups.")
    splits = list(LeaveOneGroupOut().split(x, y, groups))
    for tr, te in splits:
        if len(np.unique(y[tr])) < 2:
            raise ValueError(
                "An outer training fold has only one class. Date/class confounding prevents this evaluation."
            )
    versions = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
    }
    caveats = [
        "Exploratory local evaluation; probabilities are uncalibrated.",
        "Overlapping windows are correlated; capture-level metrics are primary.",
    ]
    if split == "capture":
        caveats.append(
            "Capture-held-out evaluation can retain same-date recordings in training; date confounding remains possible."
        )
    if len(np.unique(dates)) <= 2:
        caveats.append(
            "Only two or fewer recording dates; generalization estimates have high uncertainty."
        )
    results = []
    for ki, kind in enumerate(kinds):
        if kind not in ("lr", "rf", "mlp", "ga_rf"):
            raise ValueError("Unsupported model.")
        pred = np.full(len(y), -1)
        probability = np.full(len(y), np.nan)
        random_pred = np.full(len(y), -1)
        folds = []
        for i, (tr, te) in enumerate(splits):
            progress(
                f"{kind}: held-out fold {i + 1}/{len(splits)}",
                int(10 + 80 * (ki + i / len(splits)) / len(kinds)),
            )
            assert not set(g[tr]) & set(g[te]), "Capture leakage"
            if split == "date":
                assert not set(dates[tr]) & set(dates[te]), "Date leakage"
            cols = np.arange(x.shape[1])
            convergence = []
            if kind == "ga_rf":
                cols, convergence = genetic_select(
                    x[tr], y[tr], g[tr], population, generations, mutation
                )
            m = estimator(kind)
            m.fit(x[tr][:, cols], y[tr])
            pred[te] = m.predict(x[te][:, cols])
            probability[te] = m.predict_proba(x[te][:, cols])[:, list(m.classes_).index(1)]
            if kind == "ga_rf":
                random_cols = np.random.default_rng(42 + i).choice(
                    x.shape[1], len(cols), replace=False
                )
                rm = estimator("rf")
                rm.fit(x[tr][:, random_cols], y[tr])
                random_pred[te] = rm.predict(x[te][:, random_cols])
            folds.append(
                {
                    "held_out": np.unique(groups[te]).tolist(),
                    "train_dates": np.unique(dates[tr]).tolist(),
                    "test_dates": np.unique(dates[te]).tolist(),
                    "selector_capture_ids": np.unique(g[tr]).tolist() if kind == "ga_rf" else [],
                    "train_capture_ids": np.unique(g[tr]).tolist(),
                    "test_capture_ids": np.unique(g[te]).tolist(),
                    "selected_features": cols.tolist() if kind == "ga_rf" else None,
                    "convergence": convergence,
                }
            )
        rows = aggregate(y, pred, g)
        mtr = metrics([r["truth"] for r in rows], [r["prediction"] for r in rows])
        cols = np.arange(x.shape[1])
        convergence = []
        if kind == "ga_rf":
            cols, convergence = genetic_select(x, y, g, population, generations, mutation)
        final = estimator(kind)
        final.fit(x[:, cols], y)
        mid = f"{job_id}-{kind}"
        manifest = {
            "id": mid,
            "name": {
                "lr": "Logistic Regression",
                "rf": "Random Forest",
                "mlp": "ANN / MLP",
                "ga_rf": "GA + Random Forest",
            }[kind],
            "created": datetime.now(timezone.utc).isoformat(),
            "contract": contract(bandwidth),
            "source": "SIMULATION" if used[0].get("synthetic") else "RECORDED DATA",
            "synthetic": bool(used[0].get("synthetic")),
            "metrics": mtr,
            "window_metrics": metrics(y, pred),
            "capture_predictions": rows,
            "held_out_windows": {
                c["sha256"]: [
                    {**w, "prediction": int(p), "probability": float(q)}
                    for w, p, q in zip(
                        window_map[c["id"]], pred[g == c["id"]], probability[g == c["id"]]
                    )
                ]
                for c in used
            },
            "parameters": {
                "kind": kind,
                "seed": 42,
                "population": population,
                "generations": generations,
                "mutation": mutation,
                "ga_fitness": "capture balanced accuracy - 0.002 * selected_fraction",
                "inner_validation": "capture-stratified; outer held-out rows excluded",
            },
            "folds": folds,
            "split": (
                "leave-one-recording-date-out" if split == "date" else "leave-one-capture-out"
            ),
            "captures": [
                {
                    "id": c["id"],
                    "sha256": c["sha256"],
                    "dataset_id": c["dataset_id"],
                    "date": c["date"],
                    "present": c["present"],
                }
                for c in used
            ],
            "training_fingerprint": hashlib.sha256("".join(sorted(hashes)).encode()).hexdigest(),
            "versions": versions,
            "label_mapping": {"0": "No person", "1": "Person present"},
            "caveats": caveats,
            "selected_features": cols.tolist() if kind == "ga_rf" else None,
            "convergence": convergence,
            "architecture": [int(len(cols)), 64, 32, 1] if kind == "mlp" else None,
            "loss_curve": (getattr(final[-1], "loss_curve_", []) if kind == "mlp" else []),
        }
        if kind == "ga_rf":
            random_rows = aggregate(y, random_pred, g)
            manifest["random_feature_baseline"] = {
                "metrics": metrics(
                    [r["truth"] for r in random_rows],
                    [r["prediction"] for r in random_rows],
                ),
                "capture_predictions": random_rows,
                "method": "Same outer folds; same feature count as GA in each fold; seeded random subset.",
            }
        joblib.dump(
            {"estimator": final, "columns": cols, "manifest": manifest},
            outdir / f"{mid}.joblib",
        )
        (outdir / f"{mid}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        results.append(manifest)
    return results


def predict(capture, root, model_file, mode="held_out"):
    bundle = joblib.load(
        model_file
    )  # Only internal artifacts generated by train(); no upload endpoint accepts pickle.
    manifest = bundle["manifest"]
    c = manifest["contract"]
    if (
        bool(manifest.get("synthetic")) != bool(capture.get("synthetic"))
        or c != contract(capture["bandwidth"])
        or capture["subcarriers"] != c["subcarriers"]
        or capture["modulation"] != "ax"
    ):
        raise ValueError(
            "Model/recording mismatch: choose the matching bandwidth and AX modulation. Retrain legacy models under quality contract v2 before replay."
        )
    a, invalid, _ = read_capture(root / capture["path"], capture["bandwidth"])
    x, windows, _ = feature_windows(a, invalid, capture["bandwidth"])
    if not len(x):
        raise ValueError("No accepted feature windows.")
    in_training = any(row["sha256"] == capture["sha256"] for row in manifest["captures"])
    if mode not in ("held_out", "seen"):
        raise ValueError(
            "Choose held-out replay or the explicitly labelled Seen in training option."
        )
    if mode == "held_out":
        saved = manifest.get("held_out_windows", {}).get(capture["sha256"])
        if not saved:
            raise ValueError(
                "No saved held-out predictions for this recording. Retrain including it with independent groups, or explicitly choose Seen in training / final model inference."
            )
        lookup = {c["id"]: c for c in manifest["captures"]}
        identity = next(c["id"] for c in manifest["captures"] if c["sha256"] == capture["sha256"])
        fold = next((f for f in manifest["folds"] if identity in f["test_capture_ids"]), None)
        if (
            not fold
            or any(lookup[c]["sha256"] == capture["sha256"] for c in fold["train_capture_ids"])
            or (
                manifest["split"] == "leave-one-recording-date-out"
                and capture["date"] in fold.get("train_dates", [])
            )
        ):
            raise ValueError("Held-out provenance check failed. Retrain the model before replay.")
        if [(w["start"], w["end"]) for w in saved] != [(w["start"], w["end"]) for w in windows]:
            raise ValueError("Window contract changed. Retrain before held-out replay.")
        pred = np.array([w["prediction"] for w in saved])
        probs = np.array([w["probability"] for w in saved])
        in_training = False
        protocol = manifest["split"] + "; saved outer-fold predictions; capture majority vote"
    else:
        m = bundle["estimator"]
        columns = bundle["columns"]
        pred = m.predict(x[:, columns])
        probs = m.predict_proba(x[:, columns])[:, list(m.classes_).index(1)]
        protocol = (
            "final model inference; seen in training"
            if in_training
            else "final model inference; unseen capture; not a validation score"
        )
    return {
        "capture_id": capture["id"],
        "model_id": manifest["id"],
        "model_name": manifest["name"],
        "mode": mode,
        "validation_protocol": protocol,
        "source": "SIMULATION" if capture.get("synthetic") else "MODEL OUTPUT",
        "synthetic": bool(capture.get("synthetic")),
        "windows": [
            {**w, "prediction": int(p), "probability": float(q)}
            for w, p, q in zip(windows, pred, probs)
        ],
        "prediction": int(np.bincount(pred.astype(int), minlength=2).argmax()),
        "mean_probability": float(probs.mean()),
        "in_training": in_training,
        "caveat": "Uncalibrated probabilities. "
        + (
            "This capture was used to fit this model; inference is not held-out evidence."
            if in_training
            else protocol + ". Offline recorded-data replay, not verified live detection."
        ),
    }
