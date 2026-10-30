"""Exploratory SmartCSI score fusion and identity-checked research imports."""

import csv
import hashlib
import io
import math

from fastapi import Request

PROTOCOL = "Exploratory offline capture-level analysis; rule explored on available results; independent validation still required. Not a new held-out benchmark."


def decision(probability: float, fuzzy_score: float | None = None) -> dict:
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("Provide an RF probability between zero and one.")
    active = abs(probability - 0.5) <= 0.15 + 1e-12
    if fuzzy_score is not None and (not math.isfinite(fuzzy_score) or not 0 <= fuzzy_score <= 1):
        raise ValueError("Provide a finite fuzzy score between zero and one.")
    if active and fuzzy_score is None:
        raise ValueError("Import the research fuzzy score for this uncertain capture.")
    score = (probability + fuzzy_score) / 2 if active else probability
    return {
        "rf_probability": probability,
        "fusion_activated": active,
        "fuzzy_score": fuzzy_score if active else None,
        "score": score,
        "prediction": int(score >= 0.5),
    }


def validate_csv(text: str, captures: list[dict]) -> dict:
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or len(rows) > 10000:
        raise ValueError("Import between 1 and 10000 capture predictions.")
    required = {
        "sha256",
        "actual_presence",
        "rf_probability",
        "fuzzy_score",
        "original_prediction",
        "ga_prediction",
        "validation_protocol",
    }
    if not required.issubset(rows[0]):
        raise ValueError(
            "Use the downloadable CSV schema; missing columns: "
            + ", ".join(sorted(required - rows[0].keys()))
        )
    lookup = {c["sha256"]: c for c in captures}
    seen = set()
    output = []
    for r in rows:
        sha = r["sha256"]
        cap = lookup.get(sha)
        if not cap or sha in seen or cap.get("synthetic") or cap.get("present") is None:
            raise ValueError(
                "Match every row to a unique labelled recorded capture SHA-256 in Library."
            )
        seen.add(sha)
        actual, original, ga = (
            int(r[k]) for k in ["actual_presence", "original_prediction", "ga_prediction"]
        )
        if any(v not in (0, 1) for v in [actual, original, ga]) or actual != int(cap["present"]):
            raise ValueError("Use binary labels matching the stored recording labels.")
        if not r["validation_protocol"].strip():
            raise ValueError("Supply the original validation protocol for every row.")
        result = decision(
            float(r["rf_probability"]),
            float(r["fuzzy_score"]) if r["fuzzy_score"].strip() else None,
        )
        if ga != int(result["rf_probability"] >= 0.5):
            raise ValueError(
                "GA prediction disagrees with its probability threshold; check the capture-level aggregation."
            )
        output.append(
            {
                "sha256": sha,
                "capture": cap["name"],
                "date": cap.get("date"),
                "actual": actual,
                "original": original,
                "ga": ga,
                "original_protocol": r["validation_protocol"],
                **result,
            }
        )
    metrics = {}
    for key in ["original", "ga", "prediction"]:
        cm = [[0, 0], [0, 0]]
        for r in output:
            cm[r["actual"]][r[key]] += 1
        metrics[key] = {
            "accuracy": (cm[0][0] + cm[1][1]) / len(output),
            "false_alarms": cm[0][1],
            "misses": cm[1][0],
            "confusion_matrix": cm,
            "protocol": PROTOCOL,
        }
    return {
        "rows": output,
        "metrics": metrics,
        "count": len(output),
        "fusion_count": sum(r["fusion_activated"] for r in output),
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "protocol": PROTOCOL,
        "synthetic": False,
    }


def install(app, ctx):
    from fastapi.responses import Response

    path = ctx["data"] / "research" / "smartcsi.json"
    import json

    @app.get("/api/smartcsi")
    def saved():
        return (
            json.loads(path.read_text())
            if path.exists()
            else {
                "unavailable": True,
                "reason": "Import capture predictions; SmartCSI research artifacts are not installed.",
            }
        )

    @app.get("/api/smartcsi/template")
    def template():
        return Response(
            "sha256,actual_presence,rf_probability,fuzzy_score,original_prediction,ga_prediction,validation_protocol\n",
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="SmartCSI-schema.csv"'},
        )

    @app.post("/api/smartcsi/import")
    async def upload(request: Request):
        content = bytearray()
        async for part in request.stream():
            content.extend(part)
            if len(content) > 2 * 1024 * 1024:
                raise ValueError("Use a prediction CSV smaller than 2 MiB.")
        result = validate_csv(content.decode("utf-8-sig"), ctx["rows"]("capture"))
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(result), encoding="utf-8")
        temp.replace(path)
        return result
