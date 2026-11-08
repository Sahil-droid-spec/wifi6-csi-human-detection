import base64
import hashlib
import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from scipy.io import wavfile
from scipy.signal import resample

from orbit.acoustic_link import RATE, decode_packets, envelope, modulate, open_envelope
from orbit.api import create_app
from orbit.audio_studio import Mix, encode_wav, mix_audio, read_wav

KEY = "test-only-shared-passphrase"


def wav(raw):
    x, _ = modulate(raw)
    out = io.BytesIO()
    wavfile.write(out, RATE, np.int16(x * 32767))
    return out.getvalue()


def test_encryption_authentication_and_payload_bounds():
    raw = envelope("Hello · नमस्ते".encode(), "message.txt", True, KEY)
    other = envelope("Hello · नमस्ते".encode(), "message.txt", True, KEY)
    assert raw != other and b"Hello" not in raw
    assert open_envelope(raw, KEY)[2] == "Hello · नमस्ते".encode()
    with pytest.raises(ValueError, match="Authentication failed"):
        open_envelope(raw, "wrong-key-is-long-enough")
    with pytest.raises(ValueError, match="Authentication failed"):
        open_envelope(raw[:-1] + bytes([raw[-1] ^ 1]), KEY)
    with pytest.raises(ValueError, match="8192"):
        envelope(b"x" * 8193, "big.bin", True, KEY)
    with pytest.raises(ValueError, match="12"):
        envelope(b"hi", "x.txt", True, "short")
    with pytest.raises(ValueError, match="plain filename"):
        envelope(b"x", "unsafe:name", False, "")


def test_decoder_requires_complete_crc_checked_samples():
    payload = bytes(range(256)) * 2
    raw = envelope(payload, "test.bin", True, KEY)
    x, total = modulate(raw)
    recovered, report = decode_packets(x)
    assert recovered == [raw] and report["crc_valid_packets"] == total
    assert open_envelope(recovered[0], KEY)[2] == payload
    assert not decode_packets(x[: len(x) // 2])[0]
    assert not decode_packets(np.zeros(16000))[0]
    # A microphone starts at an arbitrary sample position. Check all phases.
    for shift in (1, 7, 19, 37):
        assert decode_packets(np.r_[np.zeros(shift), x])[0] == [raw]


@pytest.mark.parametrize("ppm", [1000, -1000, 2000, -2000])
def test_bounded_clock_search_on_generated_drift_only(ppm):
    raw = envelope(b"Physical clock check", "message.txt", True, KEY)
    x, total = modulate(raw)
    # Explicit generated impairment, not a captured phone/speaker measurement.
    received = np.r_[np.zeros(873), resample(x, round(len(x) * (1 + ppm / 1e6)))]
    assert not decode_packets(received)[0]
    recovered, report = decode_packets(received, clock_search=True)
    assert recovered == [raw]
    assert report["crc_valid_packets"] == total
    assert report["clock_adjustment_ppm"] == ppm
    assert open_envelope(recovered[0], KEY)[2] == b"Physical clock check"


def test_clock_search_does_not_invent_silent_or_truncated_payload():
    assert not decode_packets(np.zeros(RATE), clock_search=True)[0]
    raw = envelope(b"short", "message.txt", True, KEY)
    x, _ = modulate(raw)
    assert not decode_packets(x[: len(x) // 3], clock_search=True)[0]


@pytest.mark.parametrize("lost_training_bits", [8, 24, 32])
def test_clipped_training_prefix_still_requires_payload_crc(lost_training_bits):
    raw = envelope(b"Clipped training prefix", "message.txt", True, KEY)
    x, total = modulate(raw)
    # Synthetic reproduction of the user's screen-clip boundary, not a room test.
    cropped = x[RATE + 320 + lost_training_bits * 40 :]
    result, report = decode_packets(cropped)
    assert result == [raw] and report["crc_valid_packets"] == total
    assert report["packet_groups"][0]["missing"] == []
    # Damage the first frame's payload: the shorter sync cannot waive its CRC.
    broken = cropped.copy()
    broken[2400:4800] = 0
    assert not decode_packets(broken)[0]


def test_missing_payload_reports_missing_packet_without_guessing():
    raw = envelope(b"No fabricated missing bytes", "message.txt", True, KEY)
    x, total = modulate(raw)
    result, report = decode_packets(x[RATE + 320 + 50 * 40 :])
    assert not result
    assert total == 2 and report["crc_valid_packets"] == 1
    assert report["packet_groups"][0]["received"] == [1]
    assert report["packet_groups"][0]["missing"] == [0]


def test_api_two_sessions_reconstruction_replay_and_library(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    with TestClient(create_app(tmp_path, "LINK", lan=True)) as laptop:
        assert laptop.get("/api/link").status_code == 401
        assert laptop.post("/api/auth", json={"code": "LINK"}).status_code == 200
        app = laptop.app
        with TestClient(app, client=("192.168.1.7", 9000)) as phone:
            phone.post("/api/auth", json={"code": "LINK"})
            tx = phone.post("/api/link/transmit", json={"text": "Hello laptop", "passphrase": KEY})
            assert tx.status_code == 200, tx.text
            sound = phone.get(tx.json()["audio_url"]).content
            headers = {"X-Orbit-Passphrase": base64.b64encode(KEY.encode()).decode()}
            assert laptop.post("/api/link/receive", content=sound).status_code == 422
            result = laptop.post("/api/link/receive", headers=headers, content=sound)
            assert result.status_code == 200, result.text
            result = result.json()
            assert result["success"] and not result["physical_verified"]
            row = result["received"]
            assert row["text"] == "Hello laptop"
            assert phone.get(row["download_url"]).content == b"Hello laptop"
            assert phone.get("/api/link").json()["received"][0]["id"] == row["id"]
            assert laptop.post("/api/link/receive", headers=headers, content=sound).json()[
                "duplicate"
            ]
            filtered = laptop.post(
                "/api/link/receive?preset=bandpass", headers=headers, content=sound
            ).json()
            assert (
                filtered["success"]
                and filtered["before"]["crc_valid_packets"]
                == filtered["after"]["crc_valid_packets"]
            )
            assert phone.delete(row["download_url"]).status_code == 403
            assert laptop.delete(row["download_url"]).status_code == 200
            audio, _ = encode_wav(
                8000, np.sin(2 * np.pi * 300 * np.arange(160) / 8000)[:, None] * 0.2
            )
            tx = phone.post(
                "/api/link/transmit",
                json={
                    "file_base64": base64.b64encode(audio).decode(),
                    "name": "voice.wav",
                    "passphrase": KEY,
                },
            ).json()
            sound = phone.get(tx["audio_url"]).content
            received = laptop.post("/api/link/receive", headers=headers, content=sound).json()[
                "received"
            ]
            assert received["sha256"] == hashlib.sha256(audio).hexdigest()
            saved = laptop.post(
                "/api/audio/import-link", json={"received_id": received["id"]}
            ).json()
            assert saved["sha256"] == received["sha256"]
            assert phone.get("/api/media/" + saved["id"] + "/file").content == audio
            assert read_wav(audio)[0] == 8000


def test_mixer_cancellation_resampling_and_clipping():
    fs = 8000
    a = np.sin(2 * np.pi * 400 * np.arange(fs) / fs)[:, None] * 0.2
    b = np.sin(2 * np.pi * 400 * np.arange(fs * 2) / (fs * 2))[:, None] * 0.2
    settings = Mix(first_id="a" * 24, second_id="b" * 24, gain_a=1, gain_b=1, operation="subtract")
    assert np.max(abs(mix_audio(fs, a, fs, a, settings))) == 0
    result = mix_audio(fs, a, fs * 2, b, settings)
    assert result.shape == a.shape and np.sqrt(np.mean(result[100:-100] ** 2)) < 0.001
    _, clipped = encode_wav(fs, a * 10)
    assert clipped > 0
