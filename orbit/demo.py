"""Presentation helpers: explicit source boundaries and archived research."""

import json
import secrets
from functools import lru_cache
from urllib.parse import quote

import numpy as np
from fastapi import HTTPException, Query, Request
from fastapi.responses import FileResponse

from . import core


def install(app, ctx):
    data, get, put = ctx["data"], ctx["get"], ctx["put"]

    @lru_cache(maxsize=4)
    def replay_trace(id: str):
        cap, amplitude, invalid = ctx["arrays"](id)
        return cap, np.median(amplitude, axis=0), invalid

    @app.get("/api/captures/{id}/replay")
    def replay_frames(id: str, first: int = Query(0, ge=0), count: int = Query(16, ge=1, le=32)):
        cap, trace, invalid = replay_trace(id)
        contract = core.contract(cap["bandwidth"])
        window, hop = contract["window"], contract["hop"]
        total = max(0, (len(trace) - window) // hop + 1)
        if first >= total and total:
            raise ValueError("Choose a window inside this recording.")
        finite = trace[(~invalid) & np.isfinite(trace)]
        domain = [float(finite.min()), float(finite.max())] if len(finite) else [0.0, 1.0]
        frames = []
        for index in range(first, min(first + count, total)):
            start = index * hop
            end = start + window
            valid = ~invalid[start:end]
            frames.append(
                {
                    "index": index,
                    "capture_id": id,
                    "packet": list(range(start, end)),
                    "trace": [
                        float(v) if valid[i] and np.isfinite(v) else None
                        for i, v in enumerate(trace[start:end])
                    ],
                    "valid_fraction": float(valid.mean()),
                    "invalid_indices": np.flatnonzero(~valid).tolist(),
                }
            )
        return {
            "capture_id": id,
            "window": window,
            "hop": hop,
            "count": total,
            "domain": domain,
            "frames": frames,
            "synthetic": bool(cap.get("synthetic")),
            "source": "SIMULATION" if cap.get("synthetic") else "RECORDED DATA",
        }

    @app.get("/api/research")
    def research():
        path = data / "research" / "index.json"
        return (
            json.loads(path.read_text(encoding="utf-8"))
            if path.exists()
            else {
                "files": [],
                "cells": [],
                "note": "Import your supplied research archive on the laptop.",
            }
        )

    @app.get("/api/research/figure/{name}")
    def research_figure(name: str):
        import re

        path = data / "research" / "figures" / name
        if not re.fullmatch(r"[0-9a-f]{64}\.png", name) or not path.is_file():
            raise HTTPException(404, "Archived figure unavailable")
        return FileResponse(path, media_type="image/png")

    @app.get("/api/captures/{id}/sc-demo")
    def sc_demo(id: str, index: int = Query(0, ge=0)):
        cap, amplitude, invalid = ctx["arrays"](id)
        contract = core.contract(cap["bandwidth"])
        start = index * contract["hop"]
        end = start + contract["window"]
        if end > amplitude.shape[1]:
            raise ValueError("Choose a complete window in this recording.")
        trace = np.median(amplitude[:, start:end], axis=0)
        valid = (~invalid[start:end]) & np.isfinite(trace)
        samples = trace[valid]
        scale = max(float(np.mean(np.abs(samples))) if len(samples) else 0.0, 1e-12)
        cv = float(np.std(samples) / scale) if len(samples) else 0.0
        adjacent = valid[:-1] & valid[1:]
        change = float(np.mean(np.abs(np.diff(trace)[adjacent])) / scale) if adjacent.any() else 0.0
        variation = float(np.clip(cv / 0.2, 0, 1))
        motion = float(np.clip(change / 0.1, 0, 1))
        fuzzy = core.fuzzy(variation, motion)
        return {
            "capture_id": id,
            "synthetic": bool(cap.get("synthetic")),
            "source": "SIMULATION" if cap.get("synthetic") else "RECORDED DATA",
            "start": start,
            "end": end,
            "valid_fraction": float(valid.mean()),
            "coefficient_of_variation": cv,
            "normalized_adjacent_change": change,
            "variation": variation,
            "motion": motion,
            "fuzzy": fuzzy,
            "method": "Mamdani min-AND, min implication, max aggregation, centroid over 201 points; fixed illustrative normalizers CV/0.2 and adjacent-change/0.1; not tuned on labels",
            "validation_protocol": "Descriptive single-recording window; no classifier accuracy or calibrated probability",
        }

    @app.get("/api/research/file/{name}")
    def research_file(name: str):
        allowed = {
            "WIFI6RECONSTRUCTION.ipynb",
            "wifi6reconstruction.py",
            "WIFI6RECONSTRUCTION.ipynb - Colab.pdf",
        }
        if name not in allowed or not (data / "research" / name).is_file():
            raise HTTPException(404, "Research file unavailable")
        return FileResponse(data / "research" / name, filename=name)

    @app.post("/api/media/{id}/link")
    async def link_media(id: str, request: Request):
        media = get("media", id)
        body = await request.json()
        cap = get("capture", str(body.get("capture_id", "")))
        media.update(
            capture_id=cap["id"], dataset_id=cap["dataset_id"], synthetic=bool(cap.get("synthetic"))
        )
        put("media", media)
        return media

    @app.post("/api/pair/app-link")
    def app_link(request: Request):
        # A paired browser may create a short-lived handoff to the same laptop's APK.
        token = secrets.token_urlsafe(32)
        with ctx["pair_lock"]:
            ctx["pair_tokens"][token] = __import__("time").monotonic() + 120
        host = str(request.base_url).rstrip("/")
        return {
            "url": "orbit://connect?url=" + quote(host + "/#/pair?token=" + token, safe=""),
            "expires_seconds": 120,
        }
