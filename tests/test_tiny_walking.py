"""Generated WAV acceptance only; no physical acoustic delivery claim."""

import base64
import hashlib
import io

import numpy as np
from fastapi.testclient import TestClient
from scipy.io import wavfile

from orbit.api import create_app
from tools.make_acoustic_walking import walking_payload


def test_tiny_walking_encrypted_pcm_to_library_and_sensing(tmp_path):
    payload = walking_payload()
    assert len(payload) <= 8192
    name, key = "Simulation-Walking-Tiny.npz", "orbit-demo-passphrase"
    with TestClient(create_app(tmp_path, "TINY", lan=True)) as client:
        assert client.post("/api/auth", json={"code": "TINY"}).is_success
        tx = client.post(
            "/api/link/transmit",
            json={
                "file_base64": base64.b64encode(payload).decode(),
                "name": name,
                "encrypted": True,
                "passphrase": key,
                "synthetic": True,
                "bit_rate": 400,
                "fec": False,
            },
        )
        assert tx.is_success, tx.text
        assert tx.json()["duration_seconds"] < 60
        received_wav = client.get(tx.json()["audio_url"]).content
        rate, pcm = wavfile.read(io.BytesIO(received_wav))
        assert rate == 16000 and pcm.dtype == np.int16
        rx = client.post(
            "/api/link/receive",
            content=received_wav,
            headers={"X-Orbit-Passphrase": base64.b64encode(key.encode()).decode()},
        )
        assert rx.is_success and rx.json()["success"], rx.text
        received = rx.json()["received"]
        assert received["sha256"] == hashlib.sha256(payload).hexdigest()
        assert received["synthetic"] is True
        assert client.get(received["download_url"]).content == payload
        saved = client.post(
            "/api/workspace/import-reference",
            json={"kind": "link_received", "id": received["id"]},
        )
        assert saved.is_success, saved.text
        opened = client.post(f'/api/sensing/recordings/{saved.json()["id"]}/open')
        assert opened.is_success, opened.text
        session = opened.json()
        assert session["synthetic"] is True and session["packets"] == 32
        assert session["subcarriers"] == 1 and session["config"]["scenario"] == "walking"
        assert np.asarray(session["positions"]).shape == (1, 32, 3)
        assert np.ptp(np.asarray(session["positions"])[0, :, 0]) > 0.5
        analysis = client.post(
            f'/api/sensing/sessions/{session["id"]}/analyze',
            json={"operation": "fir", "taps": 7, "length": 32, "stft_size": 32},
        )
        assert analysis.is_success, analysis.text
        assert len(analysis.json()["filtered"]) == 32
        print(
            f'Generated PCM test: {len(payload)} payload bytes, '
            f'{tx.json()["duration_seconds"]:.2f} s, '
            f'{tx.json()["packet_count"]} frames; exact encrypted recovery, '
            'Simulation Library import, supplied walking path and FIR analysis passed. '
            'Physical speaker-to-microphone test NOT EXECUTED.'
        )
