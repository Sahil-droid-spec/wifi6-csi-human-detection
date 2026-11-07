import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from scipy import signal
from scipy.io import wavfile

from orbit.acoustic import RATE, SPS, decode, encode
from orbit.api import create_app


@pytest.mark.parametrize(
    "text,delay,noise",
    [("Hello Orbit", 0, 0), ("Wi-Fi to sound", 57, 0.04), ("Hello नमस्ते", 133, 0.06)],
)
def test_loopback_frames(text, delay, noise):
    x, bits = encode(text)
    r = decode(
        np.r_[np.zeros(delay), x] + np.random.default_rng(10).normal(0, noise, len(x) + delay)
    )
    assert r["crc_valid"] and r["decoded_text"] == text
    np.testing.assert_array_equal(r["recovered_bits"], bits)


def test_crc_rejects_corruption_and_noise():
    x, bits = encode("Test payload")
    i = 80
    start = 1600 + i * SPS
    t = np.arange(SPS) / RATE
    x[start : start + SPS] = 0.65 * np.sin(2 * np.pi * (1200 if bits[i] else 2200) * t)
    r = decode(x)
    assert not r["crc_valid"] and r["decoded_text"] is None
    assert not decode(np.random.default_rng(4).normal(0, 0.1, 6000))["crc_valid"]
    with pytest.raises(ValueError):
        encode("a" * 161)
    with pytest.raises(ValueError):
        decode(np.zeros(3000))


def test_modem_api_wav_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    with TestClient(create_app(tmp_path, "A")) as c:
        assert c.post("/api/acoustic/encode", json={"text": "hi"}).status_code == 401
        c.post("/api/auth", json={"code": "A"})
        r = c.post("/api/acoustic/encode", json={"text": "demo", "loopback": True}).json()
        assert r["crc_valid"] and r["ber"] == 0 and r["source"] == "SIMULATED LOOPBACK"
        assert r["synthetic"] is True and r["physical_link_verified"] is False
        assert r["sample_count"] > 0 and r["created"] and r["software_versions"]["numpy"]
        raw = c.get(r["audio_url"]).content
        assert raw[:4] == b"RIFF"
        decoded = c.post("/api/acoustic/decode", content=raw).json()
        assert decoded["decoded_text"] == "demo" and decoded["ber"] is None
        x, _ = encode("resampled WAV")
        a = signal.resample_poly(x, 441, 160)
        stream = io.BytesIO()
        wavfile.write(stream, 44100, np.int16(np.c_[a, a] * 32000))
        r = c.post("/api/acoustic/decode", content=stream.getvalue()).json()
        assert r["crc_valid"] and r["decoded_text"] == "resampled WAV"
