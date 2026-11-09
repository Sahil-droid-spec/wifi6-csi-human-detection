import hashlib
import io
import json
import zipfile

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import ValidationError
from scipy import signal

from orbit.sensing_studio import Analysis, Simulation, analyze, install, motion_audit, synthesize


def test_seed_reproducibility_and_distinct_sessions():
    a = synthesize(Simulation(duration=4))
    b = synthesize(Simulation(duration=4))
    np.testing.assert_array_equal(a["channel"], b["channel"])
    np.testing.assert_array_equal(a["timestamps"], b["timestamps"])
    c = synthesize(Simulation(duration=4, seed=43))
    assert not np.allclose(a["amplitude"], c["amplitude"], equal_nan=True)


@pytest.mark.parametrize(
    "change",
    [
        {"multipath": 7},
        {"gain": 2},
        {"noise": 0.2},
        {"drift": 0.1},
        {"motion_intensity": 0.1},
        {"virtual_speed": 2},
    ],
)
def test_each_channel_control_changes_channel(change):
    a = synthesize(Simulation(duration=4, packet_loss=0))
    b = synthesize(Simulation(duration=4, packet_loss=0, **change))
    assert not np.allclose(a["channel"], b["channel"])


def test_scenarios_positions_jitter_loss_and_motion_gap_policy():
    empty = synthesize(Simulation(scenario="empty", duration=4, jitter=0, packet_loss=0))
    assert empty["positions"] == [] and not empty["invalid"].any()
    np.testing.assert_allclose(np.diff(empty["timestamps"]), 0.01, atol=1e-14)
    two = synthesize(Simulation(scenario="two", duration=4, packet_loss=0.2))
    assert len(two["positions"]) == 2
    assert np.std(np.diff(two["timestamps"])) > 0
    assert two["invalid"].any() and np.isnan(two["channel"][:, two["invalid"]]).all()
    audit = motion_audit(two)
    for i in np.flatnonzero(two["invalid"]):
        assert np.isnan(audit["score"][i : min(i + 16, len(audit["score"]))]).all()


@pytest.mark.parametrize(
    "operation,kind",
    [
        ("fir", "lowpass"),
        ("fir", "highpass"),
        ("fir", "bandpass"),
        ("butterworth", "lowpass"),
        ("butterworth", "highpass"),
        ("butterworth", "bandstop"),
        ("notch", "lowpass"),
    ],
)
def test_filters_and_fft_match_scipy_numpy(operation, kind):
    s = synthesize(Simulation(duration=4, packet_loss=0))
    r = analyze(s, Analysis(operation=operation, kind=kind))
    np.testing.assert_allclose(
        r["filtered"],
        signal.lfilter(r["coefficients"]["b"], r["coefficients"]["a"], r["raw"]),
        atol=1e-12,
    )
    x = np.asarray(r["filtered"])
    expected = np.abs(np.fft.rfft((x - x.mean()) * signal.windows.hann(len(x), sym=False))) / len(x)
    np.testing.assert_allclose(np.asarray(r["spectrum"])[:, 2], expected, atol=1e-12)
    assert r["phase"] is not None and r["frequency_unit"] == "Hz"


def test_recorded_gap_reset_phase_and_units_are_honest():
    x = np.linspace(1, 2, 256)[None, :]
    invalid = np.zeros(256, bool)
    invalid[80:90] = True
    s = {"amplitude": x, "invalid": invalid, "rate": None}
    r = analyze(s, Analysis())
    assert r["filtered"][80:90] == [None] * 10
    assert r["phase"] is None and r["frequency_unit"] == "cycles / packet"
    assert r["spectral_window"] == {"start": 90, "end": 256, "samples": 166}
    np.testing.assert_allclose(
        r["filtered"][90:],
        signal.lfilter(r["coefficients"]["b"], r["coefficients"]["a"], x[0, 90:]),
        atol=1e-12,
    )


def test_bounds_fail_before_allocation_and_invalid_cutoffs_fail():
    with pytest.raises(ValidationError):
        Simulation(packet_rate=500, duration=30, subcarriers=256)
    with pytest.raises(ValidationError):
        Simulation(noise=float("nan"))
    with pytest.raises(ValueError, match="upper cutoff"):
        analyze(
            synthesize(Simulation(duration=4)), Analysis(kind="bandpass", cutoff=0.3, upper=0.2)
        )


def test_routes_exports_flags_hash_library_and_bounded_cache():
    app, saved = FastAPI(), []

    def save(raw, name, source, **kw):
        row = {"name": name, "sha256": hashlib.sha256(raw).hexdigest(), **kw}
        saved.append((raw, row))
        return row

    install(
        app,
        {
            "save_asset": save,
            "arrays": lambda ident: (
                {"id": ident, "name": "Actual recording", "synthetic": False},
                np.ones((16, 400)),
                np.zeros(400, bool),
            ),
        },
    )
    with TestClient(app) as c:
        r = c.post("/api/sensing/sessions", json={"simulation": {"duration": 4}})
        assert r.status_code == 200, r.text
        row = r.json()
        assert row["synthetic"] is True and row["threshold"] is not None
        ident = row["id"]
        r = c.get(f"/api/sensing/sessions/{ident}/export/npz")
        assert hashlib.sha256(r.content).hexdigest() == r.headers["X-Content-SHA256"]
        with np.load(io.BytesIO(r.content), allow_pickle=False) as z:
            assert json.loads(str(z["metadata"]))["synthetic"] is True
            assert z["csi_real"].shape == (52, 400)
        assert c.post(f"/api/sensing/sessions/{ident}/save").status_code == 200
        assert saved[0][1]["synthetic"] is True
        assert c.get(f"/api/sensing/sessions/{ident}/export/json").json()["source"] == "SIMULATION"
        csv = c.get(f"/api/sensing/sessions/{ident}/export/csv").text
        assert "synthetic,source" in csv and "True,SIMULATION" in csv
        recorded = c.post(
            "/api/sensing/sessions", json={"source": "recorded", "capture_id": "a" * 24}
        ).json()
        assert recorded["threshold"] is None and recorded["positions"] == []
        assert recorded["synthetic"] is False and recorded["rate"] is None
        for _ in range(4):
            c.post("/api/sensing/sessions", json={"simulation": {"duration": 4}})
        assert c.post(f"/api/sensing/sessions/{ident}/analyze", json={}).status_code == 404


def test_session_import_roundtrip_and_hostile_archives():
    app = FastAPI()

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, 422)

    install(app, {})
    with TestClient(app) as c:
        row = c.post("/api/sensing/sessions", json={"simulation": {"duration": 4}}).json()
        for fmt in ("npz", "json"):
            raw = c.get(f"/api/sensing/sessions/{row['id']}/export/{fmt}").content
            response = c.post("/api/sensing/import", files={"file": ("session." + fmt, raw)})
            assert response.status_code == 200, response.text
            imported = response.json()
            assert imported["synthetic"] and imported["source"] == "SIMULATION IMPORT"
            assert imported["trace"] == row["trace"] and imported["time"] == row["time"]
            assert imported["threshold"] is None and imported["capture_id"] is None
            if fmt == "npz":
                r = c.post(f"/api/sensing/sessions/{imported['id']}/analyze", json={}).json()
                assert r["phase"] is not None
        bad = io.BytesIO()
        with zipfile.ZipFile(bad, "w") as z:
            z.writestr("../../escape.npy", b"not an array")
        r = c.post("/api/sensing/import", files={"file": ("bad.npz", bad.getvalue())})
        assert r.status_code == 422 and "supported arrays" in r.text
        bad = io.BytesIO()
        with zipfile.ZipFile(bad, "w") as z:
            header = io.BytesIO()
            np.lib.format.write_array_header_1_0(
                header, {"shape": (2**40,), "fortran_order": False, "descr": "<f8"}
            )
            z.writestr("amplitude.npy", header.getvalue())
        r = c.post("/api/sensing/import", files={"file": ("huge.npz", bad.getvalue())})
        assert r.status_code == 422 and "oversized" in r.text
        r = c.post("/api/sensing/import", files={"file": ("bad.json", b'{"trace": []}')})
        assert r.status_code == 422


def test_segment_save_library_replay_analysis_and_motion_metrics(tmp_path):
    app, assets = FastAPI(), {}

    def save(raw, name, source, **metadata):
        ident = f"{len(assets) + 1:024x}"
        path = tmp_path / (ident + name[-4:])
        path.write_bytes(raw)
        row = {
            "id": ident,
            "name": name,
            "source": source,
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            **metadata,
        }
        assets[ident] = (row, path)
        return row

    install(
        app,
        {
            "save_asset": save,
            "rows": lambda kind: [r for r, _ in assets.values()],
            "load_asset": lambda ident: assets[ident],
        },
    )
    with TestClient(app) as c:
        s = c.post(
            "/api/sensing/sessions", json={"simulation": {"duration": 4, "packet_loss": 0}}
        ).json()
        ident = s["id"]
        raw = np.asarray(s["trace"])
        assert s["variance"][15] == pytest.approx(np.var(raw[:16]))
        assert s["relative_level_db"][15] == pytest.approx(
            20 * np.log10(np.sqrt(np.mean(raw[:16] ** 2)))
        )
        assert s["interval_ms"][0] is None and s["interval_ms"][1] > 0
        result = c.post(f"/api/sensing/sessions/{ident}/save", json={"start": 32, "end": 128})
        assert result.status_code == 200, result.text
        row = result.json()["asset"]
        assert row["packet_range"] == {"start": 32, "end": 128}
        listed = c.get("/api/sensing/recordings").json()["recordings"]
        assert len(listed) == 1 and listed[0]["synthetic"]
        opened = c.post(f"/api/sensing/recordings/{row['id']}/open").json()
        assert opened["packets"] == 96 and opened["trace"] == s["trace"][32:128]
        assert opened["source"] == "SIMULATION IMPORT"
        analysis = c.post(
            f"/api/sensing/sessions/{ident}/analyze", json={"operation": "fir"}
        ).json()
        finite = np.isfinite(np.array(analysis["group_delay_samples"], dtype=float))
        expected = (31 - 1) / 2
        np.testing.assert_allclose(
            np.asarray(analysis["group_delay_samples"], dtype=float)[finite], expected, atol=1e-6
        )
        # Hann has zero endpoint coefficients; unreduced z-plane includes delay poles.
        assert len(analysis["zeros"]) == 29
        np.testing.assert_array_equal(analysis["poles"], np.zeros((30, 2)))
        saved = c.post(f"/api/sensing/sessions/{ident}/save-analysis", json={"operation": "fir"})
        assert saved.status_code == 200, saved.text
        evidence = json.loads(assets[saved.json()["asset"]["id"]][1].read_bytes())
        assert evidence["synthetic"] and evidence["settings"]["operation"] == "fir"
        assert evidence["result"]["filtered"] == analysis["filtered"]
