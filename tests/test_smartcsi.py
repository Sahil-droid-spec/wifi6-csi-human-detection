import math

import pytest
from fastapi.testclient import TestClient

from orbit.api import create_app
from orbit.smartcsi import decision, validate_csv

HEADER = "sha256,actual_presence,rf_probability,fuzzy_score,original_prediction,ga_prediction,validation_protocol\n"
CAPS = [
    {"sha256": "a" * 64, "name": "Recorded A", "present": True, "synthetic": False},
    {"sha256": "b" * 64, "name": "Recorded B", "present": False, "synthetic": False},
]


@pytest.mark.parametrize(
    "p,f,active,pred",
    [
        (0.9, None, False, 1),
        (0.1, None, False, 0),
        (0.35, 0.9, True, 1),
        (0.65, 0, True, 0),
        (0.5, 0.5, True, 1),
    ],
)
def test_branches(p, f, active, pred):
    r = decision(p, f)
    assert r["fusion_activated"] == active
    assert r["prediction"] == pred


@pytest.mark.parametrize("p,f", [(math.nan, 0.2), (1.1, 0.3), (0.5, None), (0.5, math.inf)])
def test_invalid(p, f):
    with pytest.raises(ValueError):
        decision(p, f)


def test_import_metrics_and_identities():
    text = (
        HEADER
        + "a" * 64
        + ",1,0.6,0.8,0,1,original date-held-out\n"
        + "b" * 64
        + ",0,0.4,0.1,1,0,original date-held-out\n"
    )
    r = validate_csv(text, CAPS)
    assert r["metrics"]["prediction"]["confusion_matrix"] == [[1, 0], [0, 1]]
    assert r["metrics"]["original"]["accuracy"] == 0
    assert r["fusion_count"] == 2
    for bad in [
        text + text.splitlines()[-1] + "\n",
        text.replace("a" * 64, "c" * 64),
        text.replace(",1,0.6", ",0,0.6"),
    ]:
        with pytest.raises(ValueError):
            validate_csv(bad, CAPS)
    with pytest.raises(ValueError):
        validate_csv(text, [dict(c, synthetic=True) for c in CAPS])


def test_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    with TestClient(create_app(tmp_path, "TEST")) as c:
        assert c.get("/api/smartcsi").status_code == 401
        c.post("/api/auth", json={"code": "TEST"})
        assert c.get("/api/smartcsi").json()["unavailable"]
        assert "rf_probability" in c.get("/api/smartcsi/template").text
        assert c.post("/api/smartcsi/import", content=b"wrong").status_code == 422
        import json
        import sqlite3

        with sqlite3.connect(tmp_path / "orbit.sqlite3") as db:
            for i, cap in enumerate(CAPS):
                db.execute(
                    "insert into records values(?,?,?)", ("capture", str(i), json.dumps(cap))
                )
        text = HEADER + "a" * 64 + ",1,0.6,0.8,0,1,date held out\n"
        response = c.post("/api/smartcsi/import", content=text.encode())
        assert response.status_code == 200
        assert response.json()["metrics"]["prediction"]["accuracy"] == 1
        assert c.get("/api/smartcsi").json()["count"] == 1
        assert c.post("/api/smartcsi/import", content=b"x" * (2097153)).status_code == 422
