import hashlib

import numpy as np
from fastapi.testclient import TestClient

from orbit.api import create_app
from orbit.audio_studio import encode_wav, read_wav


def test_transferred_wav_library_filter_restore_and_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    fs = 8000
    t = np.arange(fs) / fs
    samples = (0.3 * np.sin(2 * np.pi * 300 * t) + 0.25 * np.sin(2 * np.pi * 2000 * t))[:, None]
    wav, _ = encode_wav(fs, samples)
    sha = hashlib.sha256(wav).hexdigest()
    app = create_app(tmp_path, "WAV", lan=True)
    with TestClient(app) as laptop, TestClient(app, client=("192.168.1.10", 8000)) as phone:
        assert phone.get("/api/audio").status_code == 401
        for c in (laptop, phone):
            assert c.post("/api/auth", json={"code": "WAV"}).status_code == 200
        row = phone.post(
            "/api/exchange/files", json={"name": "test.wav", "size": len(wav), "sha256": sha}
        ).json()
        route = "/api/exchange/files/" + row["id"]
        assert phone.put(route, content=wav[:200]).status_code == 200
        assert phone.put(route + "?offset=200", content=wav[200:]).status_code == 200
        assert laptop.post("/api/audio/import", json={"exchange_id": row["id"]}).status_code == 422
        assert phone.post(route + "/complete").json()["verified_sha256"] == sha
        original = laptop.post("/api/audio/import", json={"exchange_id": row["id"]}).json()
        assert original["sha256"] == sha
        assert (
            laptop.post("/api/audio/import", json={"exchange_id": row["id"]}).json()["id"]
            == original["id"]
        )
        source = "/api/audio/" + original["id"]
        assert phone.post(source + "/trash").status_code == 403
        assert phone.post("/api/matlab/audio/" + original["id"]).status_code == 403
        data = laptop.get(source + "/analysis").json()
        assert data["frames"] == fs and data["rate"] == fs and data["stft_db"]
        assert (
            laptop.post(source + "/filter", json={"kind": "lowpass", "cutoff_hz": 4000}).status_code
            == 422
        )
        variant = laptop.post(source + "/filter", json={"kind": "lowpass", "cutoff_hz": 800}).json()
        assert variant["parent_id"] == original["id"] and variant["sha256"] != sha
        path = "/api/audio/" + variant["id"]
        file = "/api/media/" + variant["id"] + "/file"
        filtered = read_wav(laptop.get(file).content)[1][:, 0]
        spectrum = abs(np.fft.rfft(filtered))
        assert spectrum[300] > 20 * spectrum[2000]
        assert laptop.get("/api/media/" + original["id"] + "/file").content == wav
        assert (
            laptop.patch(path, json={"title": "Filtered example"}).json()["title"]
            == "Filtered example"
        )
        assert laptop.post(source + "/trash").status_code == 200
        assert laptop.delete(source).status_code == 409
        assert laptop.post(source + "/restore").status_code == 200
        assert laptop.post(path + "/trash").status_code == 200
        assert laptop.get(file).status_code == 404
        assert laptop.post(path + "/restore").status_code == 200
        assert laptop.get(file).status_code == 200
        assert laptop.post(path + "/trash").status_code == 200
        assert laptop.delete(path).status_code == 200
        assert not (tmp_path / variant["path"]).exists()
        assert phone.get(route + "/download").content == wav
