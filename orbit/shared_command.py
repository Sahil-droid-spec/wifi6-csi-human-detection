"""One authenticated, revisioned experiment; rendering cameras remain local.

All chart samples come from the selected stored buffer. Commands are idempotent,
processing commits by generation, and transfers use the existing exchange service.
"""

import asyncio
import copy
import hashlib
import io
import json
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Literal
from urllib.parse import urlsplit

from fastapi import HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .sensing_studio import Analysis, SessionInput, Simulation

TOUR_STEP_SECONDS = 4

class RoomObject(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]{1,32}$")
    kind: Literal["table", "chair", "sofa", "shelf", "partition", "desk"] = "table"
    x: float = Field(default=0, ge=-3, le=3, allow_inf_nan=False)
    z: float = Field(default=0, ge=-2, le=2, allow_inf_nan=False)
    rotation: float = Field(default=0, ge=-6.3, le=6.3, allow_inf_nan=False)
    scale: float = Field(default=1, ge=0.4, le=1.4, allow_inf_nan=False)


class Room(BaseModel):
    preset: Literal["lab", "classroom", "home", "office", "minimal", "radar"] = "lab"
    objects: list[RoomObject] = Field(default_factory=list, max_length=16)


class Command(BaseModel):
    event_id: str = Field(min_length=8, max_length=80)
    revision: int = Field(ge=0)
    action: Literal["claim", "scenario", "simulation", "play", "pause", "reset", "seek", "processing", "asset", "room", "save", "save_room", "load_room", "tour", "stop_tour"]
    payload: dict = Field(default_factory=dict)


def install(app, ctx):
    routes = {r.path: r.endpoint for r in app.routes if hasattr(r, "endpoint")}
    create = routes["/api/sensing/sessions"]
    analyze = routes["/api/sensing/sessions/{ident}/analyze"]
    open_asset = routes["/api/sensing/recordings/{ident}/open"]
    save_analysis = routes["/api/sensing/sessions/{ident}/save-analysis"]
    save_session = routes["/api/sensing/sessions/{ident}/save"]
    lock = threading.RLock()
    jobs = ThreadPoolExecutor(max_workers=2, thread_name_prefix="orbit-shared-dsp")
    config = Simulation(duration=12, packet_loss=0).model_dump()
    state = {
        "session_id": secrets.token_hex(12), "revision": 0,
        "controller": None, "controller_label": None, "playing": False,
        "cursor": 0.0, "anchor": time.monotonic(), "speed": 1.0,
        "config": config, "room": Room().model_dump(), "dataset": None,
        "processing": Analysis().model_dump(), "result": None,
        "job": {"generation": 0, "status": "idle"}, "events": [],
        "data_revision": 0,
        "tour_running": False, "tour_generation": 0,
    }
    seen: dict[tuple[str, str], dict] = {}

    def device(cookie):
        return hashlib.sha256((cookie or "").encode()).hexdigest()[:20]

    def cursor():
        elapsed = state["cursor"]
        if state["playing"]:
            elapsed += (time.monotonic() - state["anchor"]) * state["speed"]
        data = state["dataset"]
        duration = (data["time"][-1] + 1 / (data["rate"] or 100)) if data else 12
        return elapsed % max(duration, 0.1)

    def snapshot():
        with lock:
            return copy.deepcopy({**state, "cursor": cursor(), "server_monotonic": time.monotonic()})

    def schedule():
        state["result"] = None
        state["job"] = {"generation": state["job"]["generation"] + 1, "status": "running"}
        generation = state["job"]["generation"]
        ident = state["dataset"]["id"]
        params = Analysis(**state["processing"])

        def work():
            try:
                result = analyze(ident, params)
                with lock:
                    if generation == state["job"]["generation"]:
                        state["result"] = result
                        state["job"].update(status="complete", result_revision=generation)
                        state["revision"] += 1
            except Exception as exc:
                with lock:
                    if generation == state["job"]["generation"]:
                        state["job"].update(status="error", reason=str(exc)[:240])
                        state["revision"] += 1
        jobs.submit(work)

    @app.get("/api/shared/state")
    def shared_state(request: Request):
        return {**snapshot(), "device_id": device(request.cookies.get("orbit_session"))}

    @app.post("/api/shared/command")
    async def command(body: Command, request: Request):
        who = device(request.cookies.get("orbit_session"))
        with lock:
            key = (who, body.event_id)
            if key in seen:
                return {"ack": body.event_id, "duplicate": True, "state": {**snapshot(), "device_id": who}}
            if body.revision != state["revision"]:
                raise HTTPException(409, "The shared session changed. Refresh and retry your choice.")
            if body.action != "claim" and who != state["controller"]:
                raise HTTPException(403, "Use Take control before changing the shared experiment.")
            p, action = body.payload, body.action
            if action in ("claim", "scenario", "simulation", "asset", "pause", "reset", "stop_tour"):
                state["tour_generation"] += 1
                state["tour_running"] = False
            if action == "claim":
                state.update(controller=who, controller_label=str(p.get("label", "Paired controller"))[:48])
            elif action == "tour":
                state["tour_generation"] += 1
                generation = state["tour_generation"]
                state["tour_running"] = True

                def tour():
                    for scenario in ("still", "two_still", "two", "mixed"):
                        with lock:
                            if generation != state["tour_generation"] or state["controller"] != who:
                                return
                            cfg = Simulation(**{**state["config"], "scenario": scenario})
                            data = create(SessionInput(simulation=cfg))
                            ctx["sensing_pin"] = data["id"]
                            state.update(config=cfg.model_dump(), dataset=data, cursor=0., anchor=time.monotonic(), playing=True)
                            state["processing"].update(start=0, subcarrier=0)
                            state["data_revision"] += 1
                            schedule()
                            state["revision"] += 1
                            state["events"].append({"id": secrets.token_hex(12), "revision": state["revision"], "action": "tour:"+scenario, "device": who, "time": time.time(), "source": "SIMULATION"})
                            state["events"] = state["events"][-80:]
                        until = time.monotonic()+TOUR_STEP_SECONDS
                        while time.monotonic() < until:
                            time.sleep(.05)
                            with lock:
                                if generation != state["tour_generation"]:
                                    return
                    with lock:
                        if generation == state["tour_generation"]:
                            state["tour_running"] = False
                            state["revision"] += 1
                jobs.submit(tour)
            elif action == "stop_tour":
                pass
            elif action in ("scenario", "simulation"):
                if action == "scenario":
                    cfg = Simulation(**{**state["config"], "scenario": p.get("scenario")})
                else:
                    cfg = Simulation(**{**state["config"], **p})
                data = create(SessionInput(simulation=cfg))
                ctx["sensing_pin"] = data["id"]
                state.update(config=cfg.model_dump(), dataset=data, cursor=0.0, anchor=time.monotonic())
                state["data_revision"] += 1
                state["processing"].update(start=0, subcarrier=0)
                schedule()
            elif action == "asset":
                ident = p.get("asset_id", "")
                row, path = ctx["load_asset"](ident)
                if path.suffix.lower() in (".npz", ".json"):
                    data = await open_asset(ident)
                elif path.suffix.lower() in (".csv", ".wav", ".npy"):
                    import numpy as np
                    from scipy.io import wavfile
                    if path.stat().st_size > 32 * 1024**2:
                        raise ValueError("Use a signal file below 32 MiB for shared processing.")
                    if path.suffix.lower() == ".wav":
                        rate, values = wavfile.read(path)
                        values = np.asarray(values, dtype=float)
                        values = values.mean(axis=1) if values.ndim == 2 else values
                    else:
                        rate = None
                        values = np.load(path, allow_pickle=False) if path.suffix.lower() == ".npy" else np.loadtxt(path, delimiter=",")
                        if values.ndim == 2 and 1 in values.shape:
                            values = values.ravel()
                    if values.ndim != 1 or len(values) < 32:
                        raise ValueError("Choose a numeric single-column CSV/NPY or PCM WAV with at least 32 samples.")
                    values = values[:15000]
                    # Generic signal analysis, not CSI or a presence verdict.
                    raw = json.dumps({"schema": "orbit.sensing.v1", "synthetic": bool(row.get("synthetic")), "rate": rate if rate and rate <= 10000 else None, "trace": values.tolist(), "time": (np.arange(len(values)) / (rate or 100)).tolist()}).encode()
                    data = await routes["/api/sensing/import"](UploadFile(file=io.BytesIO(raw), filename="signal.json"))
                    data["source"] = "SIMULATION SIGNAL FILE" if row.get("synthetic") else "RECORDED SIGNAL FILE · NOT CSI"
                else:
                    raise ValueError("Use NPZ CSI, numeric single-column CSV/NPY or PCM WAV here. Images remain in Image processing/Retinal Lab.")
                data["asset_id"] = ident
                ctx["sensing_session"](data["id"])["asset_id"] = ident
                ctx["sensing_pin"] = data["id"]
                state.update(dataset=data, cursor=0.0, anchor=time.monotonic(), playing=False)
                state["processing"].update(start=0, subcarrier=0)
                state["data_revision"] += 1
                schedule()
            elif action == "processing":
                params = Analysis(**{**state["processing"], **p})
                if not state["dataset"]:
                    raise ValueError("Choose a scenario or received dataset first.")
                if params.subcarrier >= state["dataset"]["subcarriers"]:
                    raise ValueError("Choose a subcarrier present in the selected file.")
                if params.start + 32 > state["dataset"]["packets"]:
                    raise ValueError("Choose a window with at least 32 remaining packets.")
                state["processing"] = params.model_dump()
                schedule()
            elif action in ("play", "pause", "reset", "seek"):
                state["cursor"] = cursor()
                if action in ("reset", "seek"):
                    value = float(p.get("time", 0))
                    if not 0 <= value <= 3600:
                        raise ValueError("Choose a finite replay time from 0 to 3600 seconds.")
                    state["cursor"] = value
                state.update(playing=action == "play" or (state["playing"] and action == "seek"), anchor=time.monotonic())
            elif action == "room":
                candidate = Room(**p)
                if len({o.id for o in candidate.objects}) != len(candidate.objects):
                    raise ValueError("Use unique furniture IDs.")
                for i, a in enumerate(candidate.objects):
                    for b in candidate.objects[i+1:]:
                        if (a.x-b.x)**2+(a.z-b.z)**2 < (0.65*max(a.scale,b.scale))**2:
                            raise ValueError("Move furniture apart before saving; these objects overlap.")
                state["room"] = candidate.model_dump()
            elif action == "save_room":
                ctx["put"]("shared_room", {"id": "default", **state["room"]})
            elif action == "load_room":
                state["room"] = Room(**ctx["get"]("shared_room", "default")).model_dump()
            elif action == "save":
                if not state["dataset"] or state["job"]["status"] != "complete":
                    raise ValueError("Wait for processing to finish before saving.")
                saved = save_analysis(state["dataset"]["id"], Analysis(**state["processing"]))
                state["saved_result"] = saved
                state["saved_input"] = save_session(state["dataset"]["id"], None)
            state["revision"] += 1
            state["events"].append({"id": body.event_id, "revision": state["revision"], "action": action, "device": who, "time": time.time(), "source": state["dataset"]["source"] if state["dataset"] else "NO DATA"})
            state["events"] = state["events"][-80:]
            seen[key] = {"ack": body.event_id}
            if len(seen) > 512:
                seen.pop(next(iter(seen)))
            return {"ack": body.event_id, "state": {**snapshot(), "device_id": who}}

    @app.websocket("/api/shared/ws")
    async def stream(ws: WebSocket):
        origin = ws.headers.get("origin")
        if (origin and urlsplit(origin).netloc != ws.headers.get("host")) or ws.cookies.get("orbit_session") not in ctx["sessions"]:
            await ws.close(code=1008)
            return
        if not ctx["sharing"]["enabled"] and ws.client.host not in ("127.0.0.1", "::1", "testclient"):
            await ws.close(code=1008)
            return
        await ws.accept()
        revision = -1
        try:
            while ws.cookies.get("orbit_session") in ctx["sessions"]:
                with lock:
                    changed = state["revision"] != revision
                    payload = snapshot() if changed else {"cursor": cursor(), "revision": state["revision"], "playing": state["playing"]}
                    revision = state["revision"]
                await ws.send_json({"type": "snapshot" if changed else "clock", "state": payload})
                await asyncio.sleep(0.25)
        except (WebSocketDisconnect, RuntimeError):
            pass

    previous_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        async with previous_lifespan(application):
            try:
                yield
            finally:
                with lock:
                    state["tour_generation"] += 1
                    state["tour_running"] = False
                jobs.shutdown(wait=False, cancel_futures=True)

    app.router.lifespan_context = lifespan
