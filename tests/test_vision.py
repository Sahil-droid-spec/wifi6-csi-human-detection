import io

import numpy as np
import pytest
import qrcode
from fastapi.testclient import TestClient

from orbit.api import create_app
from orbit.vision import analyse_pulse, inspect_frame


def test_frame_qr():
    pytest.importorskip("cv2")
    raw = io.BytesIO()
    qrcode.make("Orbit frame fixture").save(raw, format="PNG")
    result = inspect_frame(raw.getvalue())
    assert result["qr"] == "Orbit frame fixture"
    assert result["faces"] == []
    assert result["eyes"] == []
    with pytest.raises(ValueError, match="readable"):
        inspect_frame(b"not a frame")


def test_simulated_pulse_and_quality():
    t = np.arange(480) / 20
    pulse = 2 * np.sin(2 * np.pi * 1.25 * t)
    samples = list(zip(t, np.full_like(t, 120), 100 + pulse, np.full_like(t, 90), np.zeros_like(t)))
    result = analyse_pulse(samples)
    assert result["bpm"] == pytest.approx(75, abs=1)
    assert len(result["filtered"]) > 400
    assert analyse_pulse(samples[:40])["bpm"] is None
    assert analyse_pulse([(x, r, g, b, .12) for x, r, g, b, _ in samples])["bpm"] is None
    assert analyse_pulse([(x, 3, 3, 3, m) for x, _, _, _, m in samples])["bpm"] is None
    assert analyse_pulse([(x, 100, 100, 100, m) for x, _, _, _, m in samples])["bpm"] is None
    with pytest.raises(ValueError, match="ordered"):
        analyse_pulse(samples[::-1])


def test_private_frame_and_matlab_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    app = create_app(tmp_path, "TEST", lan=True)
    with TestClient(app, client=("192.168.43.50", 1000)) as client:
        assert client.post("/api/auth", json={"code": "TEST"}).status_code == 200
        assert client.post("/api/vision/frame", content=b"x").status_code == 403
        assert client.post("/api/matlab/fir").status_code == 403
    with TestClient(app) as client:
        assert client.post("/api/auth", json={"code": "TEST"}).status_code == 200
        assert client.post("/api/vision/frame", content=b"x" * 350001).status_code == 413
