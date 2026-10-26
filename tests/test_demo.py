import json

import numpy as np
from fastapi.testclient import TestClient

from orbit import models
from orbit.api import create_app


def test_status_summarizes_predictions_and_apk_handoff(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    app = create_app(tmp_path, "DEMO", lan=True)
    import sqlite3

    model = {
        "id": "m",
        "source": "RECORDED DATA",
        "held_out_windows": {"hash": [{"prediction": 1}] * 500},
    }
    with sqlite3.connect(tmp_path / "orbit.sqlite3") as db:
        db.execute("insert into records values(?,?,?)", ("model", "m", json.dumps(model)))
    with TestClient(app) as browser:
        browser.post("/api/auth", json={"code": "DEMO"})
        assert browser.get("/api/status").json()["models"][0]["held_out_windows"] == {"hash": True}
        handoff = browser.post("/api/pair/app-link").json()
        from urllib.parse import parse_qs, urlparse

        url = parse_qs(urlparse(handoff["url"]).query)["url"][0]
        token = url.split("token=")[1]
        with TestClient(app) as phone:
            assert phone.post("/api/pair/claim", json={"token": token}).status_code == 200
            assert phone.get("/api/status").status_code == 200
            assert phone.post("/api/pair/claim", json={"token": token}).status_code == 401
        assert browser.get("/api/research/file/secret").status_code == 404


def test_ga_ladder_excludes_outer_group(tmp_path, monkeypatch):
    caps = []
    feature_map = {}
    for day in range(3):
        for label in range(2):
            for repeat in range(2):
                i = len(caps)
                cid = str(i)
                caps.append(
                    {
                        "id": cid,
                        "path": cid,
                        "bandwidth": 20,
                        "present": bool(label),
                        "modulation": "ax",
                        "date": "Day " + str(day),
                        "sha256": cid,
                        "dataset_id": "d",
                        "synthetic": True,
                    }
                )
                feature_map[cid] = np.array(
                    [[label + i * 0.001, 1.0, 2.0, 3.0], [label + i * 0.001, 1.1, 2.0, 3.0]]
                )
    monkeypatch.setattr(models, "read_capture", lambda p, bw: (str(p.name), None, None))
    monkeypatch.setattr(
        models,
        "feature_windows",
        lambda a, b, bw: (feature_map[a], [{"start": 0}, {"start": 128}], {}),
    )
    selector_groups = []

    def select(x, y, g, *args):
        selector_groups.append(set(g))
        return np.array([0, 1]), [0.5]

    monkeypatch.setattr(models, "genetic_select", select)
    out = models.train(
        caps, tmp_path, tmp_path, "ladder", 20, "date", ["ga_lr", "ga_mlp", "ga_lr_ann"], 4, 1
    )
    assert (
        len(selector_groups) == 4
    )  # three outer searches plus final deployment search, reused across classifiers
    for result in out:
        assert result["metrics"]["support"] == 12
        for fold in result["folds"]:
            assert not set(fold["train_dates"]) & set(fold["test_dates"])
            assert not set(fold["selector_capture_ids"]) & set(fold["test_capture_ids"])
        assert set(result["held_out_windows"]) == set(str(i) for i in range(12))


def insert_trace_fixture(client, bandwidth=20):
    import sqlite3

    root = client.app.state.data
    n = 1100 if bandwidth == 40 else 1024
    amplitude = np.ones((512 if bandwidth == 40 else 256, n), dtype=np.float32)
    amplitude[:, 260] = 0
    invalid = np.zeros(n, dtype=bool)
    invalid[260] = True
    cache = "captures/replay-fixture.npz"
    np.savez(root / cache, amplitude=amplitude, invalid=invalid)
    cap = {
        "id": "frame-fixture",
        "cache": cache,
        "bandwidth": bandwidth,
        "synthetic": False,
        "packets": n,
        "subcarriers": amplitude.shape[0],
    }
    with sqlite3.connect(root / "orbit.sqlite3") as db:
        db.execute("insert into records values(?,?,?)", ("capture", cap["id"], json.dumps(cap)))
    return cap


def test_replay_frames_use_exact_window_contract_and_gaps(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    with TestClient(create_app(tmp_path, "FRAMES")) as c:
        c.post("/api/auth", json={"code": "FRAMES"})
        cap = insert_trace_fixture(c)
        r = c.get("/api/captures/" + cap["id"] + "/replay?first=1&count=2")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["count"] == 7 and body["window"] == 256 and body["hop"] == 128
        assert [f["index"] for f in body["frames"]] == [1, 2]
        assert body["frames"][1]["packet"][0] == 256
        assert body["frames"][1]["trace"][4] is None
        assert body["frames"][1]["valid_fraction"] == 255 / 256
        assert body["domain"] == [1.0, 1.0]
        assert c.get("/api/captures/" + cap["id"] + "/replay?count=33").status_code == 422
        assert c.get("/api/captures/" + cap["id"] + "/replay?first=10").status_code == 422
        fuzzy = c.get("/api/captures/" + cap["id"] + "/sc-demo?index=2").json()
        assert fuzzy["coefficient_of_variation"] == 0 and fuzzy["normalized_adjacent_change"] == 0
        assert abs(fuzzy["fuzzy"]["value"] - 1 / 6) < 0.001
        assert "accuracy" not in fuzzy and "probability" not in fuzzy
        assert len(fuzzy["fuzzy"]["rules"]) == 5


def test_40mhz_replay_frames_use_512_packet_windows(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    with TestClient(create_app(tmp_path, "FRAMES")) as c:
        c.post("/api/auth", json={"code": "FRAMES"})
        cap = insert_trace_fixture(c, 40)
        body = c.get("/api/captures/" + cap["id"] + "/replay").json()
        assert body["count"] == 2 and body["hop"] == 512 and body["window"] == 512
        assert body["frames"][1]["packet"] == list(range(512, 1024))
        assert len(body["frames"][1]["trace"]) == 512
        assert c.get("/api/research/figure/not-a-hash.png").status_code == 404
