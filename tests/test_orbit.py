import io, json, time, zipfile, stat
from pathlib import Path
import h5py
import numpy as np
import pytest
from fastapi.testclient import TestClient
from scipy.signal import lfilter, firwin
from orbit import core, models
from orbit.api import create_app


def mat_bytes(shape=(256, 512), present=False, seed=4, compound=False):
    rng = np.random.default_rng(seed)
    x = (
        1
        + int(present) * 0.6
        + rng.normal(0, 0.1, shape)
        + 1j * rng.normal(0, 0.1, shape)
    ).astype(np.complex64)
    if compound:
        raw = np.empty(shape, dtype=[("real", "<f4"), ("imag", "<f4")])
        raw["real"] = x.real
        raw["imag"] = x.imag
        x = raw
    b = io.BytesIO()
    with h5py.File(b, "w") as f:
        f.create_dataset("capture", data=x)
    return b.getvalue()


def dataset_bytes(n=2, bw=20):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for day in range(2):
            for cls in range(2):
                folder = f"{bw}MHz/{cls}people/2024-07-{12+day:02d}"
                z.writestr(
                    folder + "/config.json",
                    json.dumps(
                        {
                            "bandwidth": bw,
                            "modulation": "ax",
                            "people": {"present": bool(cls)},
                        }
                    ),
                )
                for i in range(n):
                    z.writestr(
                        folder + f"/capture{i}.mat",
                        mat_bytes(
                            (256 if bw == 20 else 512, 768),
                            cls,
                            seed=day * 100 + cls * 10 + i,
                        ),
                    )
    return b.getvalue()


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path, access_code="TESTCODE")) as c:
        assert c.post("/api/auth", json={"code": "TESTCODE"}).status_code == 200
        yield c


def wait(c, id):
    for _ in range(1000):
        j = c.get("/api/jobs/" + id).json()
        if j["status"] not in ("queued", "running"):
            return j
        time.sleep(0.02)
    pytest.fail("Job did not finish.")


def import_data(c, bw=20):
    r = c.post(
        "/api/upload",
        files={"file": ("fixture.zip", dataset_bytes(bw=bw), "application/zip")},
    )
    assert r.status_code == 200, r.text
    j = wait(c, r.json()["id"])
    assert j["status"] == "completed", j
    return c.get("/api/status").json()


def test_complex_compound_orientation_and_invalid(tmp_path):
    p = tmp_path / "fixture.mat"
    p.write_bytes(mat_bytes((700, 256), compound=True))
    a, invalid, zero = core.read_capture(p, 20)
    assert a.shape == (256, 700)
    assert not invalid.any()
    assert zero == 0
    with h5py.File(p, "r+") as f:
        d = f["capture"][()]
        d["real"][0, :] = np.nan
        d["real"][1, :] = 0
        d["imag"][1, :] = 0
        del f["capture"]
        f["capture"] = d
    a, invalid, zero = core.read_capture(p, 20)
    assert invalid[:2].all()
    assert zero == 1
    assert np.isfinite(a).all()


def test_hdf_external_links_rejected(tmp_path):
    p = tmp_path / "bad.mat"
    with h5py.File(p, "w") as f:
        f["capture"] = h5py.ExternalLink("secret.h5", "capture")
    with pytest.raises(ValueError, match="local HDF5"):
        core.read_capture(p)


@pytest.mark.parametrize(
    "name", ["../escape.mat", "/absolute.mat", "C:/escape.mat", "..\\escape.mat"]
)
def test_zip_paths(tmp_path, name):
    p = tmp_path / "bad.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr(name, b"x")
    with pytest.raises(ValueError, match="Unsafe"):
        core.safe_extract(p, tmp_path / "dest")


def test_zip_symlink_and_duplicate(tmp_path):
    for duplicate in (False, True):
        p = tmp_path / "bad.zip"
        with zipfile.ZipFile(p, "w") as z:
            if duplicate:
                z.writestr("a.mat", b"a")
                z.writestr("A.mat", b"b")
            else:
                info = zipfile.ZipInfo("link.mat")
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(info, "elsewhere")
        with pytest.raises(ValueError):
            core.safe_extract(p, tmp_path / "dest")


def test_four_feature_contract_and_valid_adjacency():
    a = np.array([[1, 2, 10, 4], [3, 4, 5, 6]], dtype=np.float32)
    expected = np.concatenate(
        [
            a.mean(1),
            a.std(1),
            np.abs(np.diff(a, axis=1)).mean(1),
            np.percentile(a, 90, axis=1) - np.percentile(a, 10, axis=1),
        ]
    )
    np.testing.assert_allclose(core.four_features(a), expected, rtol=1e-6)
    v = np.array([True, False, True, True])
    f = core.four_features(a, v)
    np.testing.assert_allclose(
        f[4:6], [6, 1]
    )  # Adjacent valid pairs only; no bridging across missing packets.


def test_bandwidth_contracts_and_window_rejection():
    a = np.ones((512, 800))
    bad = np.zeros(800, dtype=bool)
    bad[0:70] = True
    x, w, audit = core.feature_windows(a, bad, 40)
    assert len(x) == 1 and w[0]["start"] == 512 and not audit[0]["accepted"]
    assert x.shape[1] == 2048
    x, w, audit = core.feature_windows(a[:256], bad, 20)
    assert len(x) == 4 and not audit[0]["accepted"]
    assert x.shape[1] == 1024


@pytest.mark.parametrize(
    "operation",
    [
        "moving_average",
        "fir",
        "butterworth",
        "fft",
        "convolution",
        "multirate",
        "interpolation",
        "hilbert",
        "stft",
        "q15",
        "shootout",
    ],
)
def test_dsp_numerics(operation):
    x = core.demo_signal(256)
    r = core.dsp(x, operation=operation)
    assert np.isfinite(r["processed"]).all()
    if operation == "moving_average":
        np.testing.assert_allclose(r["processed"], lfilter(np.ones(15) / 15, [1], x))
    if operation == "fir":
        np.testing.assert_allclose(
            r["processed"], lfilter(firwin(15, 0.1, window="hann", fs=1), [1], x)
        )
    if operation == "fft":
        assert (
            r["extra"]["fft_max_error"] < 1e-10 and r["extra"]["dft_max_error"] < 1e-10
        )
    if operation == "convolution":
        assert r["extra"]["fft_max_error"] < 1e-10
        assert len(r["extra"]["linear"]) == 270
    if operation == "multirate":
        assert len(r["processed"]) == 128
    if operation == "interpolation":
        assert len(r["processed"]) == 512


def test_radix_rejects_non_power():
    with pytest.raises(ValueError):
        core.radix2([1, 2, 3])
    for n in (2, 8, 64, 256):
        np.testing.assert_allclose(
            core.radix2(np.arange(n)), np.fft.fft(np.arange(n)), atol=1e-10
        )


def test_fuzzy_actual_defuzzification():
    lo = core.fuzzy(0, 0)
    hi = core.fuzzy(1, 1)
    assert 0 < lo["value"] < 0.2 and 0.8 < hi["value"] < 1
    assert core.fuzzy(0, 1)["value"] is None
    assert core.fuzzy(0.5, 0.5)["value"] == pytest.approx(0.5)
    custom = [{"variation": "low", "motion": "low", "output": "high"}]
    assert core.fuzzy(0, 0, custom)["value"] > 0.8


def test_auth_csrf_rate_and_host(tmp_path):
    with TestClient(create_app(tmp_path, "CODE")) as c:
        assert c.get("/api/status").status_code == 401
        assert (
            c.post(
                "/api/auth",
                json={"code": "CODE"},
                headers={"origin": "http://evil.test"},
            ).status_code
            == 403
        )
        assert c.get("/api/health", headers={"host": "evil.test"}).status_code == 400
        for i in range(10):
            assert c.post("/api/auth", json={"code": "bad"}).status_code == 401
        assert c.post("/api/auth", json={"code": "CODE"}).status_code == 429


def test_import_inspect_dsp_export_and_delete(client):
    s = import_data(client)
    assert len(s["captures"]) == 8
    cap = s["captures"][0]
    r = client.get("/api/captures/" + cap["id"])
    assert r.status_code == 200
    v = r.json()
    assert len(v["trace"]) == 768 and len(v["feature_vector"]) == 1024
    assert client.get("/api/captures/" + cap["id"] + "?start=99999").status_code == 422
    features = client.get("/api/captures/" + cap["id"] + "/features").json()
    assert len(features["windows"]) == 5
    result = client.post("/api/dsp", json={"capture_id": cap["id"]}).json()
    assert result["source"] == "RECORDED DATA"
    demo = client.post("/api/dsp", json={}).json()
    assert demo["source"] == "EDUCATIONAL DEMO"
    run = client.post("/api/runs", json={"capture_id": cap["id"]}).json()
    assert client.get("/api/export/run/" + run["id"]).status_code == 200
    assert (
        client.get(
            "/api/export/evidence/presence_model_comparison_by_bandwidth"
        ).status_code
        == 200
    )
    assert client.get("/api/qr").status_code == 409
    assert client.delete("/api/datasets/" + cap["dataset_id"]).status_code == 200
    assert client.get("/api/status").json()["captures"] == []


def test_import_rejects_invalid_and_cleans_staging(client):
    r = client.post("/api/upload", files={"file": ("bad.mat", b"not hdf5")})
    j = wait(client, r.json()["id"])
    assert j["status"] == "failed" and "No valid" in j["message"]
    assert not list((client.app.state.data / "staging").iterdir())
    assert (
        client.post("/api/upload", files={"file": ("bad.py", b"print(1)")}).status_code
        == 415
    )


def test_training_grouping_manifest_predict_and_mismatch(client):
    s = import_data(client)
    r = client.post("/api/train", json={"kinds": ["lr", "rf", "mlp"], "split": "date"})
    j = wait(client, r.json()["id"])
    assert j["status"] == "completed", j
    s = client.get("/api/status").json()
    assert len(s["models"]) == 3
    m = s["models"][0]
    for fold in m["folds"]:
        assert not set(fold["train_capture_ids"]) & set(fold["test_capture_ids"])
    assert len(m["capture_predictions"]) == 8 and m["contract"]["window"] == 256
    result = client.post(
        "/api/predict", json={"capture_id": s["captures"][0]["id"], "model_id": m["id"]}
    )
    assert result.status_code == 200, result.text
    assert not result.json()["in_training"] and result.json()["mode"] == "held_out" and len(result.json()["windows"]) == 5
    seen = client.post("/api/predict", json={"capture_id": s["captures"][0]["id"], "model_id": m["id"], "mode": "seen"}).json()
    assert seen["in_training"] and "seen in training" in seen["validation_protocol"]
    assert client.get("/api/export/model/" + m["id"]).status_code == 200
    s40 = import_data(client, 40)
    cap40 = next(c for c in s40["captures"] if c["bandwidth"] == 40)
    r = client.post(
        "/api/predict", json={"capture_id": cap40["id"], "model_id": m["id"]}
    )
    assert r.status_code == 422 and "mismatch" in r.text


def test_ga_feature_selection_uses_inner_groups():
    rng = np.random.default_rng(42)
    g = np.repeat(np.arange(8), 4)
    y = np.repeat(np.arange(8) % 2, 4)
    x = rng.normal(size=(32, 12))
    x[:, 0] += y * 3
    columns, history = models.genetic_select(x, y, g, 4, 2, 0.1)
    assert len(columns) > 0 and len(history) == 2


def test_restart_persistence(tmp_path):
    with TestClient(create_app(tmp_path, "ONE")) as c:
        c.post("/api/auth", json={"code": "ONE"})
        import_data(c)
    with TestClient(create_app(tmp_path, "TWO")) as c:
        assert c.get("/api/status").status_code == 401
        c.post("/api/auth", json={"code": "TWO"})
        assert len(c.get("/api/status").json()["captures"]) == 8


def test_upload_limits_before_multipart(client, monkeypatch):
    import orbit.api as service

    monkeypatch.setattr(service, "MAX_UPLOAD", 1024)
    assert (
        client.post(
            "/api/upload",
            headers={
                "content-length": "5000000",
                "content-type": "multipart/form-data; boundary=a",
            },
            content=b"",
        ).status_code
        == 413
    )
    assert (
        client.post(
            "/api/upload",
            headers={"content-type": "multipart/form-data; boundary=a"},
            content=iter([b"x" * 700000, b"x" * 700000]),
        ).status_code
        == 413
    )


def test_nested_ga_integration_and_random_baseline(client):
    import_data(client)
    r = client.post(
        "/api/train",
        json={
            "kinds": ["rf", "ga_rf"],
            "population": 4,
            "generations": 1,
            "split": "date",
        },
    )
    j = wait(client, r.json()["id"])
    assert j["status"] == "completed", j
    ga = next(
        m
        for m in client.get("/api/status").json()["models"]
        if m["name"] == "GA + Random Forest"
    )
    assert ga["selected_features"] and len(ga["folds"]) == 2
    assert ga["random_feature_baseline"]["metrics"]["support"] == 8
    for fold in ga["folds"]:
        assert not set(fold["train_capture_ids"]) & set(fold["test_capture_ids"])
        assert fold["selected_features"] and fold["convergence"]


def test_database_handles_are_closed(tmp_path, monkeypatch):
    import sqlite3
    import orbit.api as service

    original = sqlite3.connect
    handles = []

    def observed_connect(*args, **kwargs):
        # Allow the test to inspect worker-created connections after the request.
        kwargs["check_same_thread"] = False
        con = original(*args, **kwargs)
        handles.append(con)
        return con

    monkeypatch.setattr(service.sqlite3, "connect", observed_connect)
    app = create_app(tmp_path, "CLOSED")
    with TestClient(app) as c:
        c.post("/api/auth", json={"code": "CLOSED"})
        c.get("/api/status")
    assert handles
    # Retain each handle to prevent garbage collection from concealing a leak.
    for connection in handles:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")


def test_media_library_and_pairing(client):
    import base64

    state = import_data(client)
    cap = state["captures"][0]
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jXioAAAAASUVORK5CYII="
    )
    r = client.post(
        "/api/media",
        files={"file": ("experiment.png", png, "image/png")},
        data={
            "title": "Classroom experiment",
            "notes": "One person at desk",
            "capture_id": cap["id"],
        },
    )
    assert r.status_code == 200, r.text
    media = r.json()
    assert media["dataset_id"] == cap["dataset_id"]
    assert client.get("/api/media/" + media["id"] + "/file").content == png
    ranged = client.get(
        "/api/media/" + media["id"] + "/file", headers={"Range": "bytes=0-7"}
    )
    assert ranged.status_code == 206 and ranged.content == png[:8]
    assert len(client.get("/api/status").json()["media"]) == 1
    assert (
        client.post(
            "/api/media", files={"file": ("not-photo.png", b"hello", "image/png")}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/media", files={"file": ("code.html", b"<script/>")}
        ).status_code
        == 415
    )
    assert len(list((client.app.state.data / "media").iterdir())) == 1


def test_single_mat_user_profile(client):
    r = client.post(
        "/api/upload",
        files={
            "file": ("phone.mat", mat_bytes((256, 768)), "application/octet-stream")
        },
        data={"profile": "ax20", "label": "unlabelled"},
    )
    j = wait(client, r.json()["id"])
    assert j["status"] == "completed", j
    cap = client.get("/api/status").json()["captures"][0]
    assert (
        cap["bandwidth_verified"]
        and cap["modulation"] == "ax"
        and cap["present"] is None
    )
    assert cap["metadata_source"] == "user-provided upload profile"
    r = client.post(
        "/api/upload",
        files={
            "file": ("phone.mat", mat_bytes((256, 768)), "application/octet-stream")
        },
        data={"profile": "ax40"},
    )
    assert wait(client, r.json()["id"])["status"] == "failed"


def test_local_large_import_and_project_reference(client, tmp_path):
    dataset = tmp_path / "saved.zip"
    dataset.write_bytes(dataset_bytes())
    reference = tmp_path / "source.zip"
    with zipfile.ZipFile(reference, "w") as z:
        z.writestr("README.md", "Project reference, not instructions to execute.")
    r = client.post("/api/local/import", json={"paths": [str(dataset), str(reference)]})
    j = wait(client, r.json()["id"])
    assert j["status"] == "completed", j
    state = client.get("/api/status").json()
    assert len(state["datasets"]) == 1 and len(state["references"]) == 1
    ref = state["references"][0]
    assert (
        client.get("/api/references/" + ref["id"] + "/file").content
        == reference.read_bytes()
    )
    r = client.post("/api/local/import", json={"paths": [str(dataset)]})
    assert wait(client, r.json()["id"])["result"]["imports"][0]["already_saved"]
    assert len(client.get("/api/status").json()["datasets"]) == 1


def test_phone_sharing_control_and_local_import_security(tmp_path):
    app = create_app(tmp_path, "LAN", lan=True)
    with TestClient(app) as local, TestClient(
        app, client=("192.168.1.50", 50100)
    ) as remote:
        assert local.post("/api/auth", json={"code": "LAN"}).status_code == 200
        assert remote.post("/api/auth", json={"code": "LAN"}).status_code == 200
        assert (
            remote.post(
                "/api/local/import", json={"paths": ["C:/private.mat"]}
            ).status_code
            == 403
        )
        assert (
            remote.post("/api/server/sharing", json={"enabled": False}).status_code
            == 403
        )
        assert (
            local.post("/api/server/sharing", json={"enabled": False}).json()["enabled"]
            is False
        )
        assert remote.get("/api/status").status_code == 403
        assert local.get("/api/status").status_code == 200
        assert (
            local.post("/api/server/sharing", json={"enabled": True}).json()["enabled"]
            is True
        )
        assert remote.get("/api/status").status_code == 200


def test_compare_all_trained_models(client):
    state = import_data(client)
    cap = state["captures"][0]
    assert (
        client.post("/api/predict/compare", json={"capture_id": cap["id"]}).status_code
        == 422
    )
    r = client.post("/api/train", json={"kinds": ["lr", "rf"], "split": "date"})
    assert wait(client, r.json()["id"])["status"] == "completed"
    r = client.post("/api/predict/compare", json={"capture_id": cap["id"]})
    assert r.status_code == 200, r.text
    result = r.json()
    assert len(result["results"]) == 2
    assert {r["model_name"] for r in result["results"]} == {
        "Random Forest",
        "Logistic Regression",
    }
    assert all(
        r["source"] == "MODEL OUTPUT" and not r["in_training"] and r["mode"] == "held_out" for r in result["results"]
    )


def test_download_catalog_and_private_files(tmp_path, monkeypatch):
    root = tmp_path / "deliverables"
    root.mkdir()
    apk = root / "Orbit-Phone-Companion.apk"
    apk.write_bytes(b"PK" + b"example-apk")
    (root / "private-secret.txt").write_text("not downloadable")
    monkeypatch.setenv("ORBIT_DOWNLOADS_DIR", str(root))
    with TestClient(create_app(tmp_path / "data", "DOWNLOAD")) as c:
        assert c.get("/api/downloads").status_code == 401
        c.post("/api/auth", json={"code": "DOWNLOAD"})
        catalog = c.get("/api/downloads").json()
        assert len(catalog) == 1 and catalog[0]["name"] == apk.name
        response = c.get("/api/downloads/" + apk.name)
        assert response.status_code == 200 and response.content == apk.read_bytes()
        assert (
            response.headers["content-type"]
            == "application/vnd.android.package-archive"
        )
        assert c.get("/api/downloads/private-secret.txt").status_code == 404
        response = c.get("/api/downloads/" + apk.name, headers={"Range": "bytes=0-1"})
        assert response.status_code == 206 and response.content == b"PK"


def test_packet_audit_and_trace_gaps(client, tmp_path):
    p = tmp_path / "audit.mat"
    p.write_bytes(mat_bytes((256, 768)))
    with h5py.File(p, "r+") as f:
        raw = f["capture"][()]
        raw[:, 10:15] = 0
        raw[:, 30] = complex(float("nan"), 1)
        del f["capture"]
        f["capture"] = raw
    a, bad, zero, audit = core.read_capture(p, 20, with_audit=True)
    assert zero == 5 and audit["nonfinite_packets"] == 1
    assert audit["longest_burst"] == 5 and audit["invalid_packets"] == 6
    r = client.post("/api/upload", files={"file": ("audit.mat", p.read_bytes())}, data={"profile": "ax20"})
    assert wait(client, r.json()["id"])["status"] == "completed"
    cap = client.get("/api/status").json()["captures"][0]
    v = client.get("/api/captures/" + cap["id"]).json()
    assert v["trace"][10:15] == [None] * 5 and v["trace"][30] is None
    assert v["packet_audit"]["zero_packets"] == 5
    # Differences may not bridge across an unusable sample.
    features = core.four_features(np.array([[1., 2., 1000., 4., 5.]]), np.array([1,1,0,1,1], bool))
    assert features[2] == 1


@pytest.mark.parametrize("name", ["CON.mat", "aux/config.json", "a./x.mat", "a /x.mat", "NUL.txt", "COM1.mat"])
def test_zip_windows_aliases(tmp_path, name):
    p = tmp_path / "bad.zip"
    with zipfile.ZipFile(p, "w") as z: z.writestr(name, b"x")
    with pytest.raises(ValueError, match="Unsafe"): core.safe_extract(p, tmp_path / "dest")


def test_zip_bomb_and_size_caps(tmp_path, monkeypatch):
    p = tmp_path / "bomb.zip"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z: z.writestr("a.mat", b"0" * 2000000)
    with pytest.raises(ValueError, match="compression-ratio"): core.safe_extract(p, tmp_path / "out")
    monkeypatch.setattr(core, "MAX_EXPANDED", 10)
    with pytest.raises(ValueError, match="expanded size"): core.safe_extract(p, tmp_path / "out")


def test_eligibility_explains_invalid_choices(client):
    state = import_data(client, 40)
    # Classes/dates fixture is valid, but unavailable bandwidth is disabled.
    options = client.get("/api/train/options").json()
    bad = [o for o in options if o["bandwidth"] == 20]
    assert bad and all(not o["valid"] and "Import" in o["reason"] for o in bad)
    r = client.post("/api/train", json={"bandwidth": 20})
    assert r.status_code == 422 and "Import" in r.text
    caps = state["captures"]
    for c in caps: c["date"] = "Day A" if not c["present"] else "Day B"
    check = models.training_check(caps, 40, "date", ["rf"])
    assert not check["valid"] and "confounding" in check["reason"]


def test_held_out_replay_uses_saved_fold_without_final_estimator(client, monkeypatch):
    state = import_data(client)
    r = client.post("/api/train", json={"kinds": ["rf"]})
    assert wait(client, r.json()["id"])["status"] == "completed"
    state = client.get("/api/status").json(); model = state["models"][0]; cap = state["captures"][0]
    import joblib
    path = client.app.state.data / "models" / (model["id"] + ".joblib")
    bundle = joblib.load(path)
    bundle["estimator"] = None  # Held-out replay must not call the final fitted estimator.
    joblib.dump(bundle, path)
    result = client.post("/api/predict", json={"capture_id": cap["id"], "model_id": model["id"]})
    assert result.status_code == 200 and not result.json()["in_training"]
    assert result.json()["windows"] == model["held_out_windows"][cap["sha256"]]
    # Corrupt fold provenance: must refuse instead of silently using fitted outputs.
    fold = next(f for f in bundle["manifest"]["folds"] if cap["id"] in f["test_capture_ids"])
    fold["train_capture_ids"].append(cap["id"])
    joblib.dump(bundle, path)
    assert client.post("/api/predict", json={"capture_id": cap["id"], "model_id": model["id"]}).status_code == 422


def test_ga_selection_receives_only_outer_training_date(client, monkeypatch):
    state = import_data(client)
    observed = []
    original = models.genetic_select
    def spy(x, y, g, *args):
        observed.append(set(g.tolist()))
        return original(x, y, g, *args)
    monkeypatch.setattr(models, "genetic_select", spy)
    r = client.post("/api/train", json={"kinds": ["ga_rf"], "population": 4, "generations": 1})
    assert wait(client, r.json()["id"])["status"] == "completed"
    model = client.get("/api/status").json()["models"][0]
    for calls, fold in zip(observed[:-1], model["folds"]):
        assert calls == set(fold["train_capture_ids"])
        assert not calls & set(fold["test_capture_ids"])
        assert not set(fold["train_dates"]) & set(fold["test_dates"])
    assert observed[-1] == set(c["id"] for c in state["captures"])  # Separate deployment fit only, never used for held-out metrics.


def test_sha256_manifest_detects_corruption(tmp_path):
    import hashlib
    from tools.checksums import verify_manifest
    source = tmp_path / "data.txt"; source.write_bytes(b"actual file bytes")
    manifest = tmp_path / "SHA256SUMS.txt"
    manifest.write_text(hashlib.sha256(source.read_bytes()).hexdigest() + "  data.txt\n")
    assert verify_manifest(tmp_path, manifest) == 1
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Checksum mismatch"): verify_manifest(tmp_path, manifest)


def test_zip_symlink_destination_and_member_cap(tmp_path, monkeypatch):
    p = tmp_path / "member.zip"
    with zipfile.ZipFile(p, "w") as z: z.writestr("large.mat", b"x" * 200)
    monkeypatch.setattr(core, "MAX_ARRAY_BYTES", 100)
    with pytest.raises(ValueError, match="size or compression"): core.safe_extract(p, tmp_path / "out")
