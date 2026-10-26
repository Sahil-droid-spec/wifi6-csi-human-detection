"""Presentation helpers: explicit source boundaries and archived research."""

import json
import secrets
from urllib.parse import quote

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse


def install(app, ctx):
    data, get, put = ctx["data"], ctx["get"], ctx["put"]

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
