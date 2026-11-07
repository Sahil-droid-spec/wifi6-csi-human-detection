import io
import json
import zipfile

from fastapi.testclient import TestClient

from orbit.api import create_app


def test_journey_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    root = tmp_path / "research/journey"
    root.mkdir(parents=True)
    graphs = [
        dict(
            id=i,
            file=f"graph-{i:02d}.png",
            title="A < B",
            caption="Source & limit",
            source_pages=[292],
            kind="Archived",
            status="Negative",
        )
        for i in range(1, 20)
    ]
    (root / "manifest.json").write_text(
        json.dumps(dict(graphs=graphs, stages=[], missing="19 not 20"))
    )
    for g in graphs:
        (root / g["file"]).write_bytes(b"png")
        (root / f"graph-{g['id']:02d}.pdf").write_bytes(b"%PDF-test")
    (root / "report.pdf").write_bytes(b"%PDF-report")
    with TestClient(create_app(tmp_path, "TEST")) as c:
        assert c.get("/api/journey").status_code == 401
        c.post("/api/auth", json={"code": "TEST"})
        assert len(c.get("/api/journey").json()["graphs"]) == 19
        assert c.get("/api/journey/file/report.pdf").content == b"%PDF-report"
        assert c.get("/api/journey/file/secret.txt").status_code == 422
        r = c.get("/api/journey/selected?ids=1,19")
        assert r.status_code == 200
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            assert z.namelist() == ["Figure-01.pdf", "Figure-19.pdf", "provenance.json"]
        for ids in ["0", "20", "1,1", "-1"]:
            assert c.get("/api/journey/selected", params={"ids": ids}).status_code == 422
        text = c.get("/api/journey/print?ids=1").text
        assert "A &lt; B" in text and "window.print" not in text
        assert "page-break-after" in text
        assert "window.print" in c.get("/api/journey/print.js").text
