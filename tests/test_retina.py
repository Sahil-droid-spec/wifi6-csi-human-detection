import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from orbit.api import create_app
from orbit.retina import Settings, decode_image, process


def generated_image():
    image = Image.new("RGB", (256, 256), "black")
    draw = ImageDraw.Draw(image)
    draw.ellipse((12, 12, 244, 244), fill=(180, 100, 70))
    draw.line([(70, 80), (120, 120), (150, 220)], fill=(80, 30, 25), width=5)
    draw.line([(120, 120), (200, 70)], fill=(80, 30, 25), width=5)
    raw = io.BytesIO()
    image.save(raw, format="PNG")
    return raw.getvalue()


def test_classical_pipeline_on_generated_geometry(tmp_path):
    pytest.importorskip("cv2")
    raw = generated_image()
    report, files = process(raw, Settings(size=256, source_kind="simulation"), tmp_path)
    assert report["synthetic"] and report["validation"]["accuracy"] is None
    assert report["validation"]["dice"] is None
    assert report["source_dimensions"] == [256, 256]
    assert 0 < report["candidate_pixels"] < report["field_pixels"]
    assert report["processing_ms"] > 0
    mask = np.asarray(Image.open(io.BytesIO(files["mask"])))
    assert set(np.unique(mask)) == {0, 255}
    assert mask[0, 0] == 0
    assert files["overlay"] != files["preview"]
    with pytest.raises(ValueError, match="readable"):
        decode_image(b"bad bytes", 256)


def test_phone_preview_save_reopen_and_laptop_delete(tmp_path, monkeypatch):
    pytest.importorskip("cv2")
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    app = create_app(tmp_path, "RETINA", lan=True)
    raw = generated_image()
    query = "/api/retina/analyse?consent=true&size=256&source_kind=simulation"
    with TestClient(app) as laptop, TestClient(app, client=("192.168.1.11", 1000)) as phone:
        assert phone.post(query, content=raw).status_code == 401
        for client in (laptop, phone):
            assert client.post("/api/auth", json={"code": "RETINA"}).status_code == 200
        assert phone.post("/api/retina/analyse", content=raw).status_code == 422
        assert phone.post(query + "&radius=300", content=raw).status_code == 422
        assert phone.post(query + "&sensitivity=nan", content=raw).status_code == 422
        preview = phone.post(query, content=raw)
        assert preview.status_code == 200, preview.text
        assert not preview.json()["saved"] and not laptop.get("/api/retina").json()
        saved = phone.post(query + "&save=true", content=raw).json()
        assert len(saved["saved"]) == 4
        assert len(phone.post(query + "&save=true", content=raw).json()["saved"]) == 4
        assert len(laptop.get("/api/retina").json()) == 4
        original = next(row for row in saved["saved"] if row["retina_role"] == "original")
        assert phone.get("/api/media/" + original["id"] + "/file").content == raw
        mask = next(row for row in saved["saved"] if row["retina_role"] == "mask")
        assert phone.delete("/api/retina/media/" + mask["id"]).status_code == 403
        assert laptop.delete("/api/retina/media/" + original["id"]).status_code == 409
        assert laptop.delete("/api/retina/media/" + mask["id"]).status_code == 200
        repaired = phone.post(query + "&save=true", content=raw).json()["saved"]
        assert len(repaired) == 4 and any(row["id"] == original["id"] for row in repaired)
        for row in repaired:
            if row["retina_role"] != "original":
                assert laptop.delete("/api/retina/media/" + row["id"]).status_code == 200
        assert laptop.delete("/api/retina/media/" + original["id"]).status_code == 200
        assert laptop.get("/api/retina").json() == []
        monkeypatch.setattr("orbit.retina.matlab_executable", lambda: None)
        assert phone.post(query + "&engine=matlab", content=raw).status_code == 503
        script = phone.get("/api/retina/matlab-script")
        assert script.status_code == 200
        for function in ("imread", "rgb2gray", "adapthisteq", "medfilt2", "imbinarize", "imopen"):
            assert function in script.text
