import hashlib
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from orbit.api import create_app
from orbit.sensing_studio import Simulation, synthesize
from tools.make_acoustic_walking import walking_payload


@pytest.mark.parametrize("scenario,states", [
    ("empty", []), ("still", [False]), ("walking", [True]),
    ("two_still", [False, False]), ("two", [True, True]), ("mixed", [False, True]),
])
def test_exact_independent_scenario_motion(scenario, states):
    data = synthesize(Simulation(duration=4, scenario=scenario))
    assert len(data["people"]) == len(data["positions"]) == len(states)
    for path, moving in zip(data["positions"], states):
        assert bool(np.ptp(path[:, 0]) > .5) == moving
        if not moving:
            assert np.ptp(path[:, 1]) == 0
    if len(states) == 2:
        distance = np.linalg.norm(data["positions"][0][:, :2]-data["positions"][1][:, :2], axis=1)
        assert distance.min() > .65


def test_shared_auth_ownership_revisions_reconnect_and_saved_input(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    app = create_app(tmp_path, "SHARED", lan=True)
    from orbit import sensing_studio
    original_analysis = sensing_studio.analyze

    def delayed(session, body):
        if body.taps == 7:
            time.sleep(.3)
        return original_analysis(session, body)

    monkeypatch.setattr(sensing_studio, "analyze", delayed)
    laptop, stranger = TestClient(app), TestClient(app)
    with TestClient(app) as phone:
        assert stranger.get("/api/shared/state").status_code == 401
        for c in (phone, laptop):
            assert c.post("/api/auth", json={"code": "SHARED"}).is_success

        def command(c, action, payload=None, event=None):
            state = c.get("/api/shared/state").json()
            return c.post("/api/shared/command", json={"event_id": event or f"test-{time.time_ns()}", "revision": state["revision"], "action": action, "payload": payload or {}})

        assert command(phone, "claim", {"label": "Phone controller"}).is_success
        assert command(laptop, "scenario", {"scenario": "walking"}).status_code == 403
        applied = command(phone, "scenario", {"scenario": "two_still"}, "repeat-safe-event")
        assert applied.is_success, applied.text
        assert command(phone, "scenario", {"scenario": "two_still"}, "repeat-safe-event").json()["duplicate"]
        stale = phone.post("/api/shared/command", json={"event_id": "stale-event", "revision": 0, "action": "pause"})
        assert stale.status_code == 409
        with laptop.websocket_connect("/api/shared/ws") as ws:
            first = ws.receive_json()
            assert first["type"] == "snapshot"
            assert len(first["state"]["dataset"]["people"]) == 2
            assert first["state"]["controller_label"] == "Phone controller"
        data = walking_payload()
        uploaded = phone.post("/api/workspace/import", files={"file": ("Simulation-Walking-Tiny.npz", data)}, data={"synthetic": "true"})
        assert uploaded.is_success, uploaded.text
        original = uploaded.json()
        assert command(phone, "asset", {"asset_id": original["id"]}).is_success
        assert command(phone, "processing", {"operation": "fir", "taps": 7, "length": 32}).is_success
        assert command(phone, "processing", {"operation": "fir", "taps": 9, "length": 32}).is_success
        for _ in range(100):
            latest = laptop.get("/api/shared/state").json()
            if latest["job"]["status"] == "complete":
                break
            time.sleep(.02)
        assert latest["processing"]["taps"] == 9
        assert len(latest["result"]["coefficients"]["b"]) == 9
        time.sleep(.35)
        assert laptop.get("/api/shared/state").json()["processing"]["taps"] == 9
        assert latest["dataset"]["synthetic"] is True
        assert hashlib.sha256(laptop.get(f'/api/media/{original["id"]}/file').content).hexdigest() == original["sha256"]
        assert command(phone, "save").is_success
        assert command(phone, "room", {"objects": [{"id": "a", "x": 0, "z": 0}, {"id": "b", "x": 0, "z": 0}]}).status_code == 422
        assert command(phone, "room", {"preset": "home", "objects": [{"id": "a", "kind": "sofa", "x": -2, "z": -1.5}]}).is_success
        assert command(phone, "save_room").is_success
        assert command(laptop, "claim", {"label": "Laptop controller"}).is_success
        assert command(phone, "play").status_code == 403


def test_transfer_progress_survives_shared_scenario_change(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    app = create_app(tmp_path, "CHUNKS", lan=True)
    with TestClient(app) as sender:
        receiver = TestClient(app)
        for c in (sender, receiver):
            c.post("/api/auth", json={"code": "CHUNKS"})
        def command(action, payload):
            rev = sender.get("/api/shared/state").json()["revision"]
            r = sender.post("/api/shared/command", json={"event_id": str(time.time_ns()), "revision": rev, "action": action, "payload": payload})
            assert r.is_success, r.text
        command("claim", {"label": "Phone controller"})
        raw = np.random.default_rng(42).bytes(512*1024)
        digest = hashlib.sha256(raw).hexdigest()
        begun = sender.post("/api/exchange/files", json={"name": "Simulation-transfer-bytes.bin", "size": len(raw), "sha256": digest}).json()
        ident = begun["id"]
        assert sender.put(f"/api/exchange/files/{ident}?offset=0", content=raw[:256*1024]).is_success
        before = receiver.get(f"/api/exchange/files/{ident}/timeline").json()
        assert before["observed_bytes"] == 256*1024
        command("scenario", {"scenario": "two"})
        assert sender.put(f"/api/exchange/files/{ident}?offset={256*1024}", content=raw[256*1024:]).is_success
        assert sender.post(f"/api/exchange/files/{ident}/complete").is_success
        after = receiver.get(f"/api/exchange/files/{ident}/timeline").json()
        assert after["verified"] and after["observed_bytes"] == len(raw)
        assert len(after["points"]) >= 3
        assert hashlib.sha256(receiver.get(f"/api/exchange/files/{ident}/download").content).hexdigest() == digest
        assert len(receiver.get("/api/shared/state").json()["dataset"]["people"]) == 2


def test_custom_unique_ids_and_four_person_limit():
    with pytest.raises(ValueError):
        Simulation(scenario="custom", avatars=[{"id": "same"}, {"id": "same"}])
    with pytest.raises(ValueError):
        Simulation(scenario="custom", avatars=[{"id": f"person-{i}"} for i in range(5)])
    data = synthesize(Simulation(scenario="custom", avatars=[{"id": "a", "activity": "standing"}, {"id": "b", "activity": "walking"}, {"id": "c", "activity": "standing", "visible": False}]))
    assert [p["id"] for p in data["people"]] == ["a", "b"]


def test_shared_tour_is_server_owned_and_visits_exact_scenarios(tmp_path, monkeypatch):
    from orbit import shared_command
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    monkeypatch.setattr(shared_command, "TOUR_STEP_SECONDS", .06)
    with TestClient(create_app(tmp_path, "TOUR", lan=True)) as client:
        client.post("/api/auth", json={"code": "TOUR"})
        def send(action):
            for _ in range(4):
                revision = client.get("/api/shared/state").json()["revision"]
                r = client.post("/api/shared/command", json={"event_id": str(time.time_ns()), "revision": revision, "action": action})
                if r.status_code != 409:
                    assert r.is_success, r.text
                    return
            raise AssertionError("Unexpected continuous revision conflict")
        send("claim")
        send("tour")
        for _ in range(100):
            state = client.get("/api/shared/state").json()
            if not state["tour_running"]:
                break
            time.sleep(.02)
        events = [e["action"] for e in state["events"] if e["action"].startswith("tour:")]
        assert events == ["tour:still", "tour:two_still", "tour:two", "tour:mixed"]
        assert [p["activity"] for p in state["dataset"]["people"]] == ["standing", "walking"]
