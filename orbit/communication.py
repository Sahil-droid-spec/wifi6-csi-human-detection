"""Authenticated, bounded local file exchange with persistent resumable offsets."""

import hashlib
import secrets
import threading
import time
from pathlib import Path

from fastapi import HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

CAP = 256 * 1024**2
TIMELINE_POINTS = 257


class Begin(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    size: int = Field(ge=0, le=CAP)
    sha256: str = Field(pattern="^[0-9a-f]{64}$")


class Message(BaseModel):
    text: str = Field(default="", max_length=4000)
    file_id: str | None = None


def install(app, ctx):
    root = ctx["data"] / "exchange"
    root.mkdir(exist_ok=True)
    rows, get, put = ctx["rows"], ctx["get"], ctx["put"]
    lock = threading.Lock()

    def device(request):
        return hashlib.sha256(request.cookies.get("orbit_session", "").encode()).hexdigest()[:16]

    def path(row):
        return root / row["id"]

    def summary(row):
        return {key: value for key, value in row.items() if key != "events"}

    def digest(p):
        h = hashlib.sha256()
        with p.open("rb") as f:
            for block in iter(lambda: f.read(1024**2), b""):
                h.update(block)
        return h.hexdigest()

    @app.get("/api/exchange")
    def status(request: Request):
        files = [summary(row) for row in rows("exchange")]
        messages = sorted(rows("message"), key=lambda r: r["created"])[-200:]
        return {
            "device_id": device(request),
            "files": files,
            "messages": messages,
            "protocol": "Authenticated ordinary LAN HTTP; application byte counters and acknowledgements, not Wi-Fi PHY statistics.",
            "limit_bytes": CAP,
        }

    @app.post("/api/exchange/files")
    def begin(b: Begin, request: Request):
        name = Path(b.name.replace("\\", "/")).name
        if (
            name != b.name
            or any(ord(c) < 32 or c in '<>:"|?*' for c in name)
            or name.endswith((".", " "))
        ):
            raise ValueError("Use a plain filename without path or control characters.")
        with lock:
            for r in rows("exchange"):
                if (
                    r["sha256"] == b.sha256
                    and r["size"] == b.size
                    and r["status"] in ("uploading", "complete")
                ):
                    r["duplicate"] = r["status"] == "complete"
                    return {**summary(r), "offset": path(r).stat().st_size}
            active = [r for r in rows("exchange") if r["status"] == "uploading"]
            if (
                len(active) >= 8
                or sum(r["size"] for r in rows("exchange") if r["status"] != "cancelled") + b.size
                > 4 * 1024**3
            ):
                raise HTTPException(
                    409,
                    "Finish/cancel pending transfers or use another workspace; exchange storage cap is 4 GiB.",
                )
            r = {
                "id": secrets.token_hex(12),
                **b.model_dump(),
                "name": name,
                "offset": 0,
                "status": "uploading",
                "created": ctx["now"](),
                "sender": device(request),
                "receipts": [],
                "chunks": 0,
                "duplicate": False,
                "events": [[time.time_ns(), 0]],
            }
            path(r).touch()
            put("exchange", r)
            return summary(r)

    @app.get("/api/exchange/files/{ident}")
    def offset(ident: str):
        r = get("exchange", ident)
        return {**summary(r), "offset": path(r).stat().st_size if path(r).exists() else 0}

    @app.get("/api/exchange/files/{ident}/timeline")
    def timeline(ident: str):
        r = get("exchange", ident)
        events = r.get("events", [])
        elapsed = (events[-1][0] - events[0][0]) / 1e9 if events else 0
        points = [
            {"elapsed_s": (stamp - events[0][0]) / 1e9, "accepted_bytes": size}
            for stamp, size in events
        ]
        interval = (events[-1][0] - events[-2][0]) / 1e9 if len(events) > 1 else 0
        return {
            "points": points,
            "elapsed_s": elapsed if len(events) > 1 else None,
            "observed_bytes": events[-1][1] - events[0][1] if events else 0,
            "total_bytes": r["size"],
            "average_bytes_per_s": (events[-1][1] - events[0][1]) / elapsed if elapsed else None,
            "last_interval_bytes_per_s": (events[-1][1] - events[-2][1]) / interval if interval else None,
            "status": r["status"],
            "verified": r["status"] == "complete",
            "offset_conflicts": r.get("offset_conflicts", 0),
            "protocol": "Laptop server timestamps after accepting payload chunks. Intervals include pauses and retries. Cumulative offsets exclude duplicate or rejected chunks.",
        }

    @app.put("/api/exchange/files/{ident}")
    async def chunk(ident: str, request: Request, offset: int = Query(0, ge=0)):
        payload = bytearray()
        async for block in request.stream():
            payload.extend(block)
            if len(payload) > 2 * 1024**2:
                raise HTTPException(413, "Use chunks no larger than 2 MiB.")
        if not payload:
            raise HTTPException(422, "Send a non-empty chunk, or verify the completed file.")
        with lock:
            r = get("exchange", ident)
            if r["status"] != "uploading":
                raise HTTPException(409, "Resume an active upload.")
            actual = path(r).stat().st_size
            if offset != actual:
                r["offset_conflicts"] = r.get("offset_conflicts", 0) + 1
                put("exchange", r)
                raise HTTPException(409, "Resync with the server offset and retry.")
            if actual + len(payload) > r["size"]:
                raise HTTPException(413, "Chunk exceeds the declared file size.")
            with path(r).open("ab") as f:
                f.write(payload)
            r.update(offset=actual + len(payload), chunks=r["chunks"] + 1)
            stamp = time.time_ns()
            events = r.setdefault("events", [[stamp, actual]])
            if len(events) >= TIMELINE_POINTS:
                events = events[::2]
            r["events"] = [*events, [max(stamp, events[-1][0]), r["offset"]]]
            put("exchange", r)
            return summary(r)

    @app.post("/api/exchange/files/{ident}/complete")
    def complete(ident: str):
        with lock:
            r = get("exchange", ident)
            if r["status"] == "complete":
                return summary(r)
            if r["status"] != "uploading" or path(r).stat().st_size != r["size"]:
                raise HTTPException(409, "Finish uploading all bytes first.")
            if digest(path(r)) != r["sha256"]:
                raise HTTPException(
                    422, "Hash mismatch. Cancel this upload, then reselect the original file."
                )
            r.update(status="complete", verified_sha256=r["sha256"], completed=ctx["now"]())
            put("exchange", r)
            return summary(r)

    @app.delete("/api/exchange/files/{ident}")
    def cancel(ident: str):
        with lock:
            r = get("exchange", ident)
            if r["status"] != "uploading":
                raise HTTPException(409, "Only pending uploads can be cancelled.")
            path(r).unlink(missing_ok=True)
            r["status"] = "cancelled"
            put("exchange", r)
            return {"ok": True}

    @app.get("/api/exchange/files/{ident}/download")
    def download(ident: str):
        if any(r["id"]=="exchange:"+ident for r in rows("revoked_export")):
            raise HTTPException(404,"This Library-linked export was revoked. Restore it in the Library.")
        r = get("exchange", ident)
        if r["status"] != "complete":
            raise HTTPException(409, "Wait for hash verification before downloading.")
        return FileResponse(
            path(r),
            filename=r["name"],
            media_type="application/octet-stream",
            headers={"X-Content-SHA256": r["sha256"]},
        )

    class Receipt(BaseModel):
        sha256: str = Field(pattern="^[0-9a-f]{64}$")
        bytes: int = Field(ge=0, le=CAP)
        transferred_bytes: int = Field(ge=0, le=CAP)
        elapsed_ms: float = Field(gt=0, le=86400000, allow_inf_nan=False)
        retries: int = Field(ge=0, le=1000)
        direction: str = Field(pattern="^(upload|download)$")

    @app.post("/api/exchange/files/{ident}/receipt")
    def receipt(ident: str, b: Receipt, request: Request):
        with lock:
            r = get("exchange", ident)
            if (
                r["status"] != "complete"
                or b.sha256 != r["sha256"]
                or b.bytes != r["size"]
                or b.transferred_bytes > b.bytes
            ):
                raise HTTPException(422, "Verify all bytes and SHA-256 before acknowledging.")
            value = {
                **b.model_dump(),
                "device": device(request),
                "created": ctx["now"](),
                "application_mbps": b.transferred_bytes * 8 / (b.elapsed_ms * 1000),
                "protocol": "Client-reported accepted payload bytes and elapsed wall time including processing/retries; verified full-file content hash. Retransmitted wire bytes are not counted. Not PHY throughput.",
            }
            r["receipts"] = (r["receipts"] + [value])[-30:]
            put("exchange", r)
            return value

    @app.post("/api/exchange/messages")
    def message(b: Message, request: Request):
        if not b.text.strip() and not b.file_id:
            raise ValueError("Type a message or attach a verified file.")
        if b.file_id and get("exchange", b.file_id)["status"] != "complete":
            raise ValueError("Finish verifying the attachment first.")
        with lock:
            if len(rows("message")) >= 5000:
                raise HTTPException(
                    409, "Message history limit reached; export and use a new workspace."
                )
            r = {
                "id": secrets.token_hex(12),
                "text": b.text.strip(),
                "file_id": b.file_id,
                "sender": device(request),
                "created": ctx["now"](),
                "acknowledged_by": [],
            }
            put("message", r)
            return r

    @app.post("/api/exchange/messages/{ident}/ack")
    def acknowledge(ident: str, request: Request):
        with lock:
            r = get("message", ident)
            peer = device(request)
            if peer != r["sender"] and peer not in r["acknowledged_by"]:
                r["acknowledged_by"].append(peer)
                put("message", r)
            return r

    @app.get("/api/exchange/ping")
    def ping():
        return {
            "server_time": ctx["now"](),
            "measurement": "Measure HTTP request/response RTT in the client; not radio latency.",
        }
