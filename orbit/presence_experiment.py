"""Matched held-out comparison with identical windows and RF settings."""

import numpy as np
from fastapi import HTTPException, Query
from pydantic import BaseModel, Field
from scipy import signal
from sklearn.model_selection import LeaveOneGroupOut

from . import core, models


class Settings(BaseModel):
    dataset_id: str | None = None
    bandwidth: int = 20
    synthetic: bool = False
    taps: int = Field(default=15, ge=3, le=63)
    cutoff: float = Field(default=0.08, gt=0, lt=0.5)


def coefficients(taps, cutoff):
    if taps % 2 != 1:
        raise ValueError("Choose an odd number of Hamming FIR taps.")
    return signal.firwin(taps, cutoff, fs=1, window="hamming")


def filter_packets(a, invalid, b):
    output = np.zeros_like(a)
    edges = np.flatnonzero(np.diff(np.r_[False, ~invalid, False].astype(np.int8)))
    state = signal.lfilter_zi(b, [1])
    for start, end in edges.reshape(-1, 2):
        samples = a[:, start:end]
        output[:, start:end] = signal.lfilter(b, [1], samples, axis=1, zi=samples[:, :1] * state)[0]
    return output


def evaluate(captures, root, settings, progress):
    taps = coefficients(settings.taps, settings.cutoff)
    prepared, seen, skipped = [], {}, []
    total = 0
    for i, row in enumerate(captures):
        stamp = row["sha256"]
        if stamp in seen:
            if seen[stamp] != (row["date"], row["present"]):
                raise ValueError(
                    "Duplicate CSI bytes have conflicting dates or labels. Resolve the metadata first."
                )
            continue
        seen[stamp] = (row["date"], row["present"])
        progress(f"Preparing recording {i + 1}/{len(captures)}", int(5 + 35 * i / len(captures)))
        raw, invalid, _ = core.read_capture(root / row["path"], settings.bandwidth)
        left, windows, audit = core.feature_windows(raw, invalid, settings.bandwidth)
        if not len(left):
            skipped.append(
                {"id": row["id"], "reason": "No windows passed the shared quality gate."}
            )
            continue
        total += len(left)
        if total > 12000:
            raise ValueError("Choose a smaller dataset with at most 12,000 accepted windows.")
        right, _, _ = core.feature_windows(
            filter_packets(raw, invalid, taps), invalid, settings.bandwidth
        )
        prepared.append((row, left, right, windows, len(audit) - len(windows)))
    if not prepared:
        raise ValueError("No labelled AX recording passed the shared quality gate.")
    truth = np.asarray([int(r[0]["present"]) for r in prepared])
    dates = np.asarray([r[0]["date"] for r in prepared])
    if len(set(dates)) < 2 or "unknown" in dates or len(set(truth)) < 2:
        raise ValueError(
            "Use labelled AX recordings from at least two known dates with both presence classes."
        )
    folds, replay = [], {}
    scores = {"baseline": [], "hamming": []}
    expected = []
    for fold, (tr, te) in enumerate(LeaveOneGroupOut().split(truth, truth, dates)):
        if len(set(truth[tr])) < 2:
            raise ValueError(
                "A training fold has only one class. Collect empty and present recordings across dates."
            )
        progress(
            f"Fitting both paths with {dates[te[0]]} held out",
            int(42 + 52 * fold / len(set(dates))),
        )
        folds.append(
            {
                "held_out_date": str(dates[te[0]]),
                "train_ids": [prepared[i][0]["id"] for i in tr],
                "test_ids": [prepared[i][0]["id"] for i in te],
            }
        )
        expected.extend(truth[te].tolist())
        for col, name in ((1, "baseline"), (2, "hamming")):
            clf = models.estimator("rf")
            clf.fit(
                np.vstack([prepared[i][col] for i in tr]),
                np.concatenate([np.repeat(truth[i], len(prepared[i][col])) for i in tr]),
            )
            for i in te:
                row, _, _, windows, skipped_count = prepared[i]
                prediction = clf.predict(prepared[i][col]).astype(int)
                majority = int(np.bincount(prediction, minlength=2).argmax())
                scores[name].append(majority)
                trace = replay.setdefault(
                    row["id"],
                    {
                        "id": row["id"],
                        "name": row.get("name", row["id"]),
                        "sha256": row["sha256"],
                        "date": row["date"],
                        "truth": int(truth[i]),
                        "windows": windows,
                        "quality_skipped": skipped_count,
                    },
                )
                trace[name] = prediction.tolist()
    frequency, response = signal.freqz(taps, worN=128, fs=1)
    return {
        "settings": settings.model_dump(),
        "source": "SIMULATION" if settings.synthetic else "RECORDED DATA",
        "synthetic": settings.synthetic,
        "coefficients": taps.tolist(),
        "frequency": frequency.tolist(),
        "response_db": (20 * np.log10(np.maximum(abs(response), 1e-10))).tolist(),
        "filter_delay_packets": (len(taps) - 1) / 2,
        "folds": folds,
        "metrics": {name: models.metrics(expected, p) for name, p in scores.items()},
        "recordings": list(replay.values()),
        "skipped_recordings": skipped,
        "protocol": "Leave one date out; independent Random Forest fits with identical seeds, feature groups, and packet masks. FIR settings fixed before this run. Majority vote per capture, ties resolved as absent.",
    }


def install(app, ctx):
    @app.post("/api/presence")
    def run(settings: Settings):
        if settings.bandwidth not in (20, 40):
            raise ValueError("Choose 20 or 40 MHz.")
        coefficients(settings.taps, settings.cutoff)
        cohort = [
            r
            for r in ctx["rows"]("capture")
            if r["bandwidth"] == settings.bandwidth
            and r.get("modulation") == "ax"
            and r.get("present") is not None
            and bool(r.get("synthetic")) == settings.synthetic
            and (not settings.dataset_id or r["dataset_id"] == settings.dataset_id)
        ]
        if not 1 <= len(cohort) <= 40:
            raise ValueError("Choose a dataset with 1–40 labelled AX recordings.")
        return ctx["job_start"](
            "Matched CSI presence experiment",
            lambda _, p: evaluate(cohort, ctx["data"], settings, p),
        )

    @app.get("/api/presence/{job_id}/{capture_id}/window")
    def window(job_id: str, capture_id: str, index: int = Query(0, ge=0)):
        job = ctx["get"]("job", job_id)
        if job["kind"] != "Matched CSI presence experiment" or job["status"] != "completed":
            raise HTTPException(409, "Complete a matched experiment first.")
        result = job["result"]
        row = next((r for r in result["recordings"] if r["id"] == capture_id), None)
        if not row or index >= len(row["windows"]):
            raise HTTPException(404, "Choose a held-out window from this experiment.")
        cap, amplitude, invalid = ctx["arrays"](capture_id)
        if cap["sha256"] != row["sha256"]:
            raise HTTPException(409, "The original recording changed. Run a new experiment.")
        limits = row["windows"][index]
        start, end = limits["start"], limits["end"]
        # Only the last taps samples can affect a causal FIR value. Read enough
        # leading context to match the whole-recording result at this window.
        b = np.asarray(result["coefficients"])
        context = max(0, start - len(b) + 1)
        local = amplitude[:, context:end]
        left = np.median(local[:, start - context :], axis=0)
        right = np.median(
            filter_packets(local, invalid[context:end], b)[:, start - context :], axis=0
        )
        return {
            **limits,
            "raw": [None if bad else float(v) for v, bad in zip(left, invalid[start:end])],
            "filtered": [None if bad else float(v) for v, bad in zip(right, invalid[start:end])],
            "baseline": row["baseline"][index],
            "hamming": row["hamming"][index],
            "truth": row["truth"],
        }
