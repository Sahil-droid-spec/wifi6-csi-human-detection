"""Leakage-safe DSP tuning and explicitly heuristic fuzzy fusion."""

import numpy as np
from scipy import signal
from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold

from . import core, models


def tune(captures, root, progress=lambda *args: None):
    captures = list(
        {
            c["sha256"]: c
            for c in captures
            if c.get("present") is not None and c.get("windows", 0) > 0
        }.values()
    )
    if len(captures) > 40:
        raise ValueError("Choose at most 40 labelled recordings for the laptop DSP search.")
    dates = np.array([c["date"] for c in captures])
    y = np.array([int(c["present"]) for c in captures])
    if len(set(dates)) < 2 or "unknown" in dates:
        raise ValueError("DSP tuning needs at least two known recording groups/dates.")
    cache = {}
    folds = []
    truth = []
    prediction = []
    rng = np.random.default_rng(42)

    def features(i, genes):
        key = (i, *genes)
        if key not in cache:
            cap = captures[i]
            a, bad, _ = core.read_capture(root / cap["path"], cap["bandwidth"])
            taps = [5, 9, 15, 25][genes[0]]
            cutoff = [0.04, 0.08, 0.12, 0.2][genes[1]]
            b = signal.firwin(taps, cutoff, fs=1, window="hann")
            filtered = signal.lfilter(b, [1], a, axis=1)
            x, _, _ = core.feature_windows(filtered, bad, cap["bandwidth"])
            cache[key] = x
        return cache[key]

    for fold, (tr, te) in enumerate(LeaveOneGroupOut().split(np.arange(len(y)), y, dates)):
        if len(set(y[tr])) < 2:
            raise ValueError(
                "Both classes must occur in each outer training set; collect balanced sessions."
            )
        counts = np.bincount(y[tr], minlength=2)
        if min(counts) < 2:
            raise ValueError("DSP GA needs two training recordings per class in every outer fold.")
        inner = list(
            StratifiedKFold(n_splits=min(3, int(min(counts))), shuffle=True, random_state=42).split(
                tr, y[tr]
            )
        )
        fitness_cache = {}

        def fit_predict(train_ids, test_ids, genes):
            x = np.vstack([features(i, genes) for i in train_ids])
            labels = np.concatenate([np.repeat(y[i], len(features(i, genes))) for i in train_ids])
            m = models.estimator("lr")
            m.fit(x, labels)
            return [
                int(np.bincount(m.predict(features(i, genes)).astype(int), minlength=2).argmax())
                for i in test_ids
            ]

        def fitness(genes):
            key = tuple(genes)
            if key not in fitness_cache:
                scores = []
                for a, b in inner:
                    p = fit_predict(tr[a], tr[b], genes)
                    scores.append(models.metrics(y[tr[b]], p)["balanced_accuracy"])
                fitness_cache[key] = float(np.mean(scores))
            return fitness_cache[key]

        pop = rng.integers(0, 4, size=(4, 2))
        history = []
        for generation in range(2):
            progress(
                f"DSP GA outer fold {fold + 1}: generation {generation + 1}",
                int(10 + 70 * (fold + generation / 2) / len(set(dates))),
            )
            pop = sorted(pop, key=fitness, reverse=True)
            history.append(fitness(pop[0]))
            children = [pop[0].copy()]
            while len(children) < 4:
                child = np.where(rng.random(2) < 0.5, pop[0], pop[1])
                mut = rng.random(2) < 0.3
                child[mut] = rng.integers(0, 4, size=mut.sum())
                children.append(child)
            pop = children
        genes = max(pop, key=fitness)
        p = fit_predict(tr, te, genes)
        truth.extend(y[te].tolist())
        prediction.extend(p)
        folds.append(
            {
                "held_out": list(set(dates[te])),
                "train_capture_ids": [captures[i]["id"] for i in tr],
                "test_capture_ids": [captures[i]["id"] for i in te],
                "train_dates": list(set(dates[tr])),
                "taps": [5, 9, 15, 25][genes[0]],
                "cutoff": [0.04, 0.08, 0.12, 0.2][genes[1]],
                "inner_fitness": history,
            }
        )
    return {
        "metrics": models.metrics(truth, prediction),
        "folds": folds,
        "source": "SIMULATION" if captures[0].get("synthetic") else "RECORDED DATA",
        "synthetic": bool(captures[0].get("synthetic")),
        "validation_protocol": "Nested leave-one-group/date-out; inner capture-stratified GA; LR scaling fitted only inside each training fold; capture majority vote",
        "caveat": "Small fixed search (4 candidates, 2 generations). No generalization or superiority claim; inner fitness is not test accuracy.",
    }
