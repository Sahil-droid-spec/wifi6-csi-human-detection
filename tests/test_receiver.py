import numpy as np
import pytest
from scipy.signal import periodogram

from orbit.receiver import analyse, generate


def test_tones_and_scan():
    iq = generate()
    for tune, mod, tone in [(-16000, "AM", 440), (16000, "FM", 880)]:
        r = analyse(iq, 64000, tune, mod)
        f, p = periodogram(r["audio"][1000:], fs=8000)
        assert abs(f[p.argmax()] - tone) < 5
        assert max(abs(r["audio"])) <= 0.90001
        assert any(abs(s["offset_hz"] - tune) < 1500 for s in r["stations"])
        assert np.isfinite(r["waterfall"]).all()
    np.testing.assert_array_equal(generate(seed=2), generate(seed=2))


def test_rejections():
    for iq, rate, tune, mod in [
        (np.ones(5000), 64000, 0, "AM"),
        (np.ones(5000, dtype=complex) * np.nan, 64000, 0, "AM"),
        (generate(), 64000, 40000, "AM"),
        (generate(), 64000, 0, "BPSK"),
    ]:
        with pytest.raises(ValueError):
            analyse(iq, rate, tune, mod)


def test_noise_and_api(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from orbit.api import create_app

    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    with TestClient(create_app(tmp_path, "CHECK")) as c:
        assert c.post("/api/receiver/simulate", json={}).status_code == 401
        c.post("/api/auth", json={"code": "CHECK"})
        r = c.post("/api/receiver/simulate", json={}).json()
        assert r["source"] == "SIMULATED"
        wav = c.get(r["audio_url"])
        assert wav.content[:4] == b"RIFF"
        assert c.get("/api/receiver/" + r["id"] + "/json").json()["id"] == r["id"]
        import io

        stream = io.BytesIO()
        np.save(stream, generate())
        r = c.post(
            "/api/receiver/import?rate=64000&center=100000000&tune=-16000&modulation=AM",
            content=stream.getvalue(),
        )
        assert r.status_code == 200 and r.json()["source"] == "RECORDED IQ"
