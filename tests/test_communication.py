import hashlib

from fastapi.testclient import TestClient

from orbit.api import ExpiringSessions, create_app


def test_general_file_roundtrip_resume_and_chat(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    app = create_app(tmp_path, "PAIR")
    with TestClient(app) as laptop, TestClient(app) as phone:
        assert phone.get("/api/exchange").status_code == 401
        laptop.post("/api/auth", json={"code": "PAIR"})
        phone.post("/api/auth", json={"code": "PAIR"})
        payload = bytes(range(256)) * 40
        sha = hashlib.sha256(payload).hexdigest()
        b = {"name": "real-test-document.bin", "size": len(payload), "sha256": sha}
        row = laptop.post("/api/exchange/files", json=b).json()
        url = "/api/exchange/files/" + row["id"]
        assert laptop.put(url + "?offset=0", content=payload[:300]).status_code == 200
        assert phone.put(url + "?offset=0", content=b"bad-offset").status_code == 409
        resumed = phone.post("/api/exchange/files", json=b).json()
        assert resumed["offset"] == 300
        assert phone.put(url + "?offset=300", content=payload[300:]).status_code == 200
        assert phone.post(url + "/complete").json()["verified_sha256"] == sha
        graph = phone.get(url + "/timeline").json()
        assert [point["accepted_bytes"] for point in graph["points"]] == [0, 300, len(payload)]
        assert graph["offset_conflicts"] == 1 and graph["verified"]
        assert graph["elapsed_s"] > 0 and graph["observed_bytes"] == len(payload)
        assert graph["average_bytes_per_s"] == len(payload) / graph["elapsed_s"]
        assert "events" not in laptop.get("/api/exchange").json()["files"][0]
        received = phone.get(url + "/download")
        assert received.content == payload
        assert hashlib.sha256(received.content).hexdigest() == sha
        assert received.headers["x-content-sha256"] == sha
        assert "media-src 'self' blob:" in received.headers["content-security-policy"]
        assert (
            phone.post(
                url + "/receipt",
                json={
                    "sha256": sha,
                    "bytes": len(payload),
                    "transferred_bytes": len(payload),
                    "elapsed_ms": 100,
                    "retries": 1,
                    "direction": "download",
                },
            ).status_code
            == 200
        )
        dup = laptop.post("/api/exchange/files", json=b).json()
        assert dup["duplicate"] and dup["id"] == row["id"]
        message = laptop.post(
            "/api/exchange/messages", json={"text": "hello from laptop", "file_id": row["id"]}
        ).json()
        assert phone.post("/api/exchange/messages/" + message["id"] + "/ack", json={}).json()[
            "acknowledged_by"
        ]
        reply = phone.post(
            "/api/exchange/messages", json={"text": "received on second session"}
        ).json()
        assert reply["sender"] != message["sender"]
        assert (
            laptop.get("/api/exchange").json()["messages"][-1]["text"]
            == "received on second session"
        )
        laptop.post("/api/logout")
        assert laptop.get(url + "/download").status_code == 401


def test_invalid_file_hash_cancel_and_persisted_resume(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    app = create_app(tmp_path, "A")
    with TestClient(app) as c:
        c.post("/api/auth", json={"code": "A"})
        b = {"name": "note.txt", "size": 4, "sha256": hashlib.sha256(b"good").hexdigest()}
        for name in ["../x", "a\\x", "bad:name", "tail."]:
            assert c.post("/api/exchange/files", json={**b, "name": name}).status_code == 422
        r = c.post("/api/exchange/files", json=b).json()
        url = "/api/exchange/files/" + r["id"]
        c.put(url, content=b"ba")
    with TestClient(create_app(tmp_path, "B")) as c:
        c.post("/api/auth", json={"code": "B"})
        assert c.post("/api/exchange/files", json=b).json()["offset"] == 2
        assert c.get(url + "/timeline").json()["observed_bytes"] == 2
        c.put(url + "?offset=2", content=b"d!")
        assert c.post(url + "/complete").status_code == 422
        assert c.get(url + "/download").status_code == 409
        assert c.delete(url).status_code == 200
        assert not (tmp_path / "exchange" / r["id"]).exists()
        assert c.post("/api/exchange/files", json={**b, "size": 268435457}).status_code == 422
        assert c.post("/api/exchange/messages", json={"text": ""}).status_code == 422


def test_sessions_expire_server_side(monkeypatch):
    now = [10.0]
    monkeypatch.setattr("orbit.api.time.monotonic", lambda: now[0])
    sessions = ExpiringSessions()
    sessions.add("token")
    assert "token" in sessions
    now[0] += 43201
    assert "token" not in sessions
