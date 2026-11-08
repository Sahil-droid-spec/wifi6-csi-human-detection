import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from scipy import signal

from orbit.control_room import ControlInput, install, process


@pytest.mark.parametrize("operation", ["fir", "butterworth", "moving_average"])
def test_control_processing_matches_scipy_on_same_clean_input(operation):
    x = np.sin(np.arange(256) * 0.12) + 0.2 * np.cos(np.arange(256) * 1.7)
    body = ControlInput(capture_id="a" * 24, operation=operation)
    r = process(x[None, :], np.zeros(256, dtype=bool), body)
    expected = signal.lfilter(r["coefficients"], r["denominator"], x)
    np.testing.assert_allclose(r["processed"], expected, atol=1e-12)
    assert r["spectral_window"] == {"start": 0, "end": 256, "samples": 256}
    assert r["metrics"]["processed_packets"] == 256


def test_packet_gaps_reset_filter_and_do_not_stitch_fft():
    x = np.linspace(1, 2, 240)
    invalid = np.zeros(240, bool)
    invalid[80:90] = True
    invalid[105:115] = True  # Fifteen-sample island remains withheld.
    x[80:90] = 0
    r = process(x[None, :], invalid, ControlInput(capture_id="a" * 24))
    assert r["raw"][80:90] == [None] * 10
    assert r["processed"][80:115] == [None] * 35
    np.testing.assert_allclose(
        r["processed"][115:], signal.lfilter(r["coefficients"], [1], x[115:]), atol=1e-12
    )
    assert r["spectral_window"] == {"start": 115, "end": 240, "samples": 125}
    assert len(r["raw_spectrum"]) == 125 // 2 + 1
    assert r["metrics"]["processed_packets"] == 205


def test_no_usable_segment_is_reported_as_a_failure():
    with pytest.raises(ValueError, match="32 usable packets"):
        process(np.zeros((1, 100)), np.ones(100, bool), ControlInput(capture_id="a" * 24))


def test_control_routes_preserve_simulation_and_save_provenance():
    app = FastAPI()
    rows = []
    x = np.arange(200, dtype=float)[None, :]
    install(
        app,
        {
            "arrays": lambda ident: ({"id": ident, "synthetic": True}, x, np.zeros(200, bool)),
            "now": lambda: "test-clock",
            "put": lambda kind, row: rows.append((kind, row)),
        },
    )
    with TestClient(app) as c:
        p = c.post("/api/control/process", json={"capture_id": "a" * 24}).json()
        assert p["source"] == "SIMULATION" and len(p["processed"]) == 200
        saved = c.post("/api/control/save", json={"capture_id": "a" * 24}).json()
        assert saved["source"] == "SIMULATION" and saved["spectral_window"] == p["spectral_window"]
        assert rows[0][0] == "run" and rows[0][1]["settings"]["capture_id"] == "a" * 24
