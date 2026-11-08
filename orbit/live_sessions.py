"""Bounded local WebRTC signaling. Media never passes through this API."""

import hashlib
import secrets
import threading
import time

from fastapi import HTTPException, Request
from pydantic import BaseModel, Field


class Join(BaseModel):
    consent: bool = False


class Signaling(BaseModel):
    kind: str = Field(max_length=10)
    payload: dict


def install(app, ctx):
    rooms = {}
    lock = threading.Lock()
    identity = lambda request: hashlib.sha256(
        request.cookies.get("orbit_session", "").encode()
    ).hexdigest()[:20]

    def prune():
        for key in list(rooms):
            if time.monotonic() - rooms[key]["created"] > 1800:
                rooms.pop(key)

    def room(code, request):
        prune()
        r = rooms.get(code)
        who = identity(request)
        if r is None:
            raise HTTPException(404, "Create a fresh call code on the laptop.")
        if who not in r["members"]:
            raise HTTPException(403, "Join this call explicitly first.")
        r["members"][who] = time.monotonic()
        return r, who

    @app.post("/api/live/rooms")
    def create(request: Request):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Create the call code on your laptop.")
        with lock:
            prune()
            if len(rooms) >= 16:
                raise HTTPException(429, "Close an old call or wait for its expiry.")
            code = secrets.token_hex(4).upper()
            rooms[code] = {"created": time.monotonic(), "members": {}, "signals": [], "sequence": 0}
            return {
                "code": code,
                "expires_in_s": 1800,
                "protocol": "Local signaling only; browser secure-context camera/microphone permission required on each device. No STUN/TURN internet service or media recording.",
            }

    @app.post("/api/live/rooms/{code}/join")
    def join(code: str, body: Join, request: Request):
        if not body.consent:
            raise ValueError("Confirm that you want to join this audio/video session.")
        with lock:
            prune()
            r = rooms.get(code)
            if r is None:
                raise HTTPException(404, "Use a fresh call code.")
            who = identity(request)
            if who not in r["members"] and len(r["members"]) >= 2:
                raise HTTPException(409, "This two-device call is full.")
            r["members"][who] = time.monotonic()
            return {"member": who, "members": len(r["members"]), "media_connected": False}

    @app.get("/api/live/rooms/{code}")
    def poll(code: str, request: Request, after: int = 0):
        with lock:
            r, who = room(code, request)
            if after < 0:
                raise ValueError("Use a nonnegative signaling cursor.")
            return {
                "signals": [s for s in r["signals"] if s["seq"] > after and s["sender"] != who],
                "cursor": r["sequence"],
                "active_members": sum(time.monotonic() - t < 30 for t in r["members"].values()),
                "protocol": "Session heartbeats do not prove microphone or media delivery.",
            }

    @app.post("/api/live/rooms/{code}/signal")
    def send(code: str, body: Signaling, request: Request):
        import json

        if (
            body.kind not in ("offer", "answer", "ice", "hangup")
            or len(json.dumps(body.payload)) > 40000
        ):
            raise ValueError("Send a bounded WebRTC offer, answer, ICE candidate or hangup.")
        with lock:
            r, who = room(code, request)
            r["sequence"] += 1
            r["signals"].append(
                {"seq": r["sequence"], "sender": who, "kind": body.kind, "payload": body.payload}
            )
            r["signals"] = r["signals"][-256:]
            return {"sequence": r["sequence"]}

    @app.delete("/api/live/rooms/{code}/member")
    def leave(code: str, request: Request):
        with lock:
            r, who = room(code, request)
            r["members"].pop(who, None)
            r["sequence"] += 1
            r["signals"].append(
                {"seq": r["sequence"], "sender": who, "kind": "hangup", "payload": {}}
            )
            if not r["members"]:
                rooms.pop(code, None)
        return {"ok": True}
