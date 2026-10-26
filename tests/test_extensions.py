import hashlib
import io
import json
import time
import zipfile
from pathlib import Path

import h5py
import numpy as np
import pytest
from fastapi.testclient import TestClient
from scipy import signal
from test_orbit import dataset_bytes, mat_bytes, wait

from orbit import core, lab
from orbit.api import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    with TestClient(create_app(tmp_path, "EXT", lan=True)) as c:
        c.post("/api/auth", json={"code": "EXT"})
        yield c


def transfer(c, payload, name="recording.mat", settings=None):
    r = c.post(
        "/api/transfers",
        json={
            "name": name,
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "settings": settings or {"bandwidth": 20, "label": "present"},
        },
    )
    assert r.status_code == 200, r.text
    row = r.json()
    mid = len(payload) // 2
    assert (
        c.put("/api/transfers/" + row["id"] + "?offset=0", content=payload[:mid]).status_code == 200
    )
    resumed = c.post(
        "/api/transfers",
        json={
            "name": name,
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "settings": settings or {"bandwidth": 20, "label": "present"},
        },
    ).json()
    assert resumed["id"] == row["id"] and resumed["offset"] == mid
    assert c.put("/api/transfers/" + row["id"] + "?offset=0", content=b"x").status_code == 409
    assert (
        c.put(
            "/api/transfers/" + row["id"] + "?offset=" + str(mid), content=payload[mid:]
        ).status_code
        == 200
    )
    r = c.post("/api/transfers/" + row["id"] + "/complete")
    assert r.status_code == 200, r.text
    job = wait(c, r.json()["id"])
    assert job["status"] == "completed", job
    return job


def test_resumable_hash_duplicate_and_inbox(client):
    payload = mat_bytes((256, 768))
    job = transfer(client, payload)
    r = client.post(
        "/api/transfers",
        json={
            "name": "same.mat",
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
    ).json()
    assert r["duplicate"] and r["dataset_id"] == job["result"]["dataset_id"]
    inbox = client.get("/api/inbox").json()
    assert len(inbox["items"]) == 1
    assert (
        client.post("/api/inbox/" + inbox["items"][0]["id"] + "/ack").json()["status"] == "Reviewed"
    )
    bad = client.post(
        "/api/transfers", json={"name": "bad.mat", "size": 3, "sha256": "0" * 64}
    ).json()
    client.put("/api/transfers/" + bad["id"], content=b"bad")
    assert client.post("/api/transfers/" + bad["id"] + "/complete").status_code == 422
    assert client.delete("/api/transfers/" + bad["id"]).status_code == 200


@pytest.mark.parametrize("extension", ["npy", "npz", "csv"])
def test_numeric_import_wizard(client, extension):
    array = np.random.default_rng(4).normal(1, 0.1, (256, 512))
    stream = io.BytesIO()
    if extension == "npy":
        np.save(stream, array)
    elif extension == "npz":
        np.savez_compressed(stream, amplitude=array)
    else:
        stream.write((",".join("1" for _ in range(512)) + "\n").encode() * 256)
    transfer(client, stream.getvalue(), "data." + extension)
    cap = client.get("/api/status").json()["captures"][0]
    assert cap["bandwidth"] == 20 and cap["present"] is True and not cap["synthetic"]


def test_pairing_is_one_use_and_sharing_respected(client):
    token = client.post("/api/pair/token").json()
    assert client.get(token["qr"]).status_code == 200
    with TestClient(client.app, client=("192.168.1.20", 1000)) as phone:
        assert phone.get("/api/status").status_code == 401
        assert phone.post("/api/pair/claim", json={"token": token["token"]}).status_code == 200
        assert phone.get("/api/status").status_code == 200
        assert phone.post("/api/pair/claim", json={"token": token["token"]}).status_code == 401
        assert phone.post("/api/pair/token").status_code == 403
        assert phone.post("/api/watch", json={"path": "C:/", "enabled": False}).status_code == 403
        assert client.post("/api/server/sharing", json={"enabled": False}).status_code == 200
        assert phone.get("/api/status").status_code == 403


def test_simulation_separation_reproducibility_and_exports(client, tmp_path):
    one = tmp_path / "one"
    two = tmp_path / "two"
    paths = lab.generate(one, sessions=2, days=2, duration=3, seed=7)
    again = lab.generate(two, sessions=2, days=2, duration=3, seed=7)
    with h5py.File(paths[0]) as a, h5py.File(again[0]) as b:
        np.testing.assert_array_equal(a["capture"][()], b["capture"][()])
    cfg = json.loads((paths[0].parent / "config.json").read_text())
    assert cfg["synthetic"] and cfg["date"].startswith("Day ")
    r = client.post("/api/simulation", json={"sessions": 2, "days": 2, "duration": 3, "seed": 7})
    job = wait(client, r.json()["id"])
    assert job["status"] == "completed", job
    state = client.get("/api/status").json()
    assert not state["captures"] and not state["datasets"]
    assert len(state["simulation_captures"]) == 8
    cap = state["simulation_captures"][0]
    assert cap["source"] == "SIMULATION"
    exported = client.get("/api/captures/" + cap["id"] + "/download")
    with zipfile.ZipFile(io.BytesIO(exported.content)) as z:
        assert json.loads(z.read("config.json"))["synthetic"] is True
    archive = client.get("/api/simulation/" + job["result"]["dataset_id"] + "/download")
    assert archive.status_code == 200
    # Provenance embedded in MAT survives missing sidecar config.
    m = core.metadata(paths[0], one)
    assert m["synthetic"]
    assert not client.get("/api/train/options").json()[0]["valid"]
    assert any(o["valid"] for o in client.get("/api/train/options?synthetic=true").json())


def test_trash_restore_and_manual_marker(client):
    transfer(client, mat_bytes((256, 768)))
    cap = client.get("/api/status").json()["captures"][0]
    assert (
        client.post(
            "/api/markers", json={"capture_id": cap["id"], "label": "Moving", "packet": 100}
        ).status_code
        == 200
    )
    assert "Moving" in client.get("/api/markers/export").text
    assert (
        client.post(
            "/api/markers", json={"capture_id": cap["id"], "label": "Bad", "packet": 999999}
        ).status_code
        == 422
    )
    client.delete("/api/datasets/" + cap["dataset_id"])
    assert not client.get("/api/status").json()["captures"]
    client.post("/api/trash/" + cap["dataset_id"] + "/restore")
    assert len(client.get("/api/status").json()["captures"]) == 1


@pytest.mark.parametrize("kind", ["perceptron", "adaline", "mlp", "som"])
def test_learning_ladder_and_som(kind):
    r = lab.teaching(kind, seed=3, epochs=10)
    assert len(r["loss"]) == 10 and np.isfinite(r["loss"]).all()
    assert "protocol" in r and r["source"] == "EDUCATIONAL SIMULATION"
    if kind == "som":
        assert np.asarray(r["weights"]).shape == (16, 2)
    else:
        assert 0 <= r["accuracy"] <= 1 and len(r["predictions"]) == 40


@pytest.mark.parametrize(
    "method", ["centroid", "bisector", "mean_of_maxima", "smallest_of_maxima", "largest_of_maxima"]
)
def test_defuzzification_methods(method):
    u = np.linspace(0, 1, 201)
    m = 1 - np.abs(2 * u - 1)
    assert lab.defuzzify(u, m, method) == pytest.approx(0.5, abs=0.005)
    assert lab.defuzzify(u, np.zeros_like(u), method) is None


@pytest.mark.parametrize("kind", ["lowpass", "highpass", "bandpass"])
def test_butterworth_matches_scipy(kind):
    x = core.demo_signal(512)
    r = core.dsp(x, operation="butterworth", kind=kind, order=3, cutoff=0.06, cutoff_high=0.2)
    b, a = signal.butter(3, [0.06, 0.2] if kind == "bandpass" else 0.06, btype=kind, fs=1)
    np.testing.assert_allclose(r["processed"], signal.lfilter(b, a, x))
    assert len(r["extra"]["poles"]) == len(a) - 1
    assert r["extra"]["estimated_multiplications"] > 0 and r["extra"]["measured_elapsed_ms"] >= 0


def test_kaiser_fir_and_rate_estimation(client):
    x = core.demo_signal(256)
    r = core.dsp(x, operation="fir", window="kaiser", beta=7, taps=21)
    np.testing.assert_allclose(
        r["processed"], signal.lfilter(signal.firwin(21, 0.1, fs=1, window=("kaiser", 7)), [1], x)
    )
    assert client.post("/api/rate", json={"timestamps": [0, 0.01, 0.02, 0.03]}).json()[
        "packet_rate"
    ] == pytest.approx(100)
    assert client.post("/api/rate", json={}).json()["packet_rate"] is None
    assert client.post("/api/rate", json={"timestamps": [1, 1, 1]}).status_code == 422


def test_offline_guide_and_plan(client):
    r = client.post("/api/guide", json={"question": "phone pair qr"}).json()
    assert "local server" in r["answer"] and "rule-based" in r["source"]
    assert (
        client.post("/api/plan", json={"session": "Session 1", "consent": True}).status_code == 200
    )
    assert client.get("/api/plan").json()[0]["sheet"]["consent"] is True
    assert client.get("/api/doctor").json()["hostname"] == "orbit.local"


def test_quality_gate_abstains():
    assert not lab.quality_gate(0.8, 0.2)["accept"]
    assert lab.quality_gate(0.99, 0.2)["accept"]


def test_watch_folder_imports_stable_file(client, tmp_path):
    folder = tmp_path.parent / (tmp_path.name + "-incoming")
    folder.mkdir()
    (folder / "recording.mat").write_bytes(mat_bytes((256, 512)))
    r = client.post(
        "/api/watch",
        json={
            "path": str(folder),
            "enabled": True,
            "settings": {"label": "present", "bandwidth": 20},
        },
    )
    assert r.status_code == 200
    deadline = time.monotonic() + 14
    while time.monotonic() < deadline:
        if client.get("/api/status").json()["captures"]:
            break
        time.sleep(0.2)
    assert len(client.get("/api/status").json()["captures"]) == 1
    assert client.get("/api/inbox").json()["items"][0]["origin"] == "watch folder"
    assert (
        client.post("/api/watch", json={"path": str(folder), "enabled": False}).status_code == 200
    )


def test_nested_dsp_ga_and_fuzzy_fusion(client):
    response = client.post(
        "/api/upload", files={"file": ("fixture.zip", dataset_bytes(), "application/zip")}
    )
    assert wait(client, response.json()["id"])["status"] == "completed"
    r = client.post("/api/pipeline/tune", json={"bandwidth": 20})
    j = wait(client, r.json()["id"])
    assert j["status"] == "completed", j
    result = j["result"]
    assert result["metrics"]["support"] == 8
    for fold in result["folds"]:
        assert not set(fold["train_capture_ids"]) & set(fold["test_capture_ids"])
        assert not set(fold["train_dates"]) & set(fold["held_out"])
    r = client.post("/api/train", json={"kinds": ["lr", "rf"], "split": "date"})
    assert wait(client, r.json()["id"])["status"] == "completed"
    cap = client.get("/api/status").json()["captures"][0]
    r = client.post("/api/pipeline/fuse", json={"capture_id": cap["id"], "mode": "held_out"})
    assert r.status_code == 200, r.text
    assert len(r.json()["models"]) == 2 and "Heuristic" in r.json()["validation_protocol"]
    assert 0 <= r.json()["fuzzy_score"] <= 1


def test_training_cancel(client, monkeypatch):
    import threading

    from orbit import models

    response = client.post(
        "/api/upload", files={"file": ("fixture.zip", dataset_bytes(), "application/zip")}
    )
    wait(client, response.json()["id"])
    entered = threading.Event()

    def slow(*args):
        progress = args[-1]
        entered.set()
        for i in range(100):
            time.sleep(0.01)
            progress("test fit boundary", i)
        return []

    monkeypatch.setattr(models, "train", slow)
    r = client.post("/api/train", json={"kinds": ["rf"]})
    assert entered.wait(2)
    assert client.post("/api/jobs/" + r.json()["id"] + "/cancel").status_code == 200
    assert wait(client, r.json()["id"])["status"] == "cancelled"


def test_simulation_cannot_be_inferred_by_recorded_model(client):
    response = client.post(
        "/api/upload", files={"file": ("fixture.zip", dataset_bytes(), "application/zip")}
    )
    wait(client, response.json()["id"])
    r = client.post("/api/train", json={"kinds": ["rf"]})
    assert wait(client, r.json()["id"])["status"] == "completed"
    model = client.get("/api/status").json()["models"][0]
    r = client.post("/api/simulation", json={"sessions": 2, "days": 2, "duration": 3})
    assert wait(client, r.json()["id"])["status"] == "completed"
    cap = client.get("/api/status").json()["simulation_captures"][0]
    assert (
        client.post(
            "/api/predict", json={"capture_id": cap["id"], "model_id": model["id"], "mode": "seen"}
        ).status_code
        == 422
    )


def test_som_error_matches_numpy_reference():
    r = lab.teaching("som", seed=3, epochs=8)
    points = np.array(r["points"])[:120]
    weights = np.array(r["weights"])
    expected = np.linalg.norm(points[:, None, :] - weights[None, :, :], axis=2).min(axis=1).mean()
    assert r["loss"][-1] == pytest.approx(expected)


def test_aliasing_spectra_reference():
    x = core.demo_signal(256)
    r = core.dsp(x, operation="multirate", factor=2)
    naive = x[::2]
    taper = signal.get_window("hann", len(naive))
    np.testing.assert_allclose(
        r["extra"]["aliasing"]["naive"], np.abs(np.fft.rfft((naive - naive.mean()) * taper))
    )


def test_native_bootstrap_is_local_and_one_use(client):
    client.app.state.desktop_bootstrap = "native-once"
    with TestClient(client.app, client=("192.168.1.20", 1000)) as phone:
        assert phone.post("/api/desktop/claim", json={"token": "native-once"}).status_code == 403
    assert client.post("/api/desktop/claim", json={"token": "wrong"}).status_code == 401
    assert client.post("/api/desktop/claim", json={"token": "native-once"}).status_code == 200
    assert client.post("/api/desktop/claim", json={"token": "native-once"}).status_code == 401


def test_all_theme_text_tokens_meet_aa_contrast():
    import ast

    text = (Path(__file__).resolve().parents[1] / "frontend/src/themes.ts").read_text()
    palettes = ast.literal_eval(text.split("export const themes = ", 1)[1].split("];", 1)[0] + "]")

    def lum(value):
        rgb = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        channels = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
        return sum(v * w for v, w in zip(channels, [0.2126, 0.7152, 0.0722]))

    assert len(palettes) == 18
    for theme in palettes:
        for foreground in theme[4:6]:
            for background in theme[2:4]:
                a, b = sorted([lum(foreground), lum(background)])
                assert (b + 0.05) / (a + 0.05) >= 4.5, (theme[1], foreground, background)
