import base64
import hashlib
import io
import json
import time
import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from orbit.acoustic_link import decode_packets, envelope, modulate
from orbit.acoustic_protocol import arq_simulate, decode, encode
from orbit.api import create_app
from orbit.audio_studio import encode_wav
from orbit.practicals import Practical, run
from orbit.research_tools import mask_metrics


def wait(client, job):
    for _ in range(200):
        row = client.get("/api/jobs/" + job["id"]).json()
        if row["status"] in ("completed", "failed", "cancelled"):
            return row
        time.sleep(0.02)
    raise AssertionError("Job did not finish")


@pytest.fixture
def clients(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_DISABLE_MDNS", "1")
    app = create_app(tmp_path, "PRO", lan=True)
    with TestClient(app) as a, TestClient(app, client=("192.168.1.6", 7000)) as b:
        for c in (a, b):
            assert c.post("/api/auth", json={"code": "PRO"}).status_code == 200
        yield a, b


def test_shared_asset_lifecycle_workflow_and_revocation(clients):
    a, b = clients
    wav, _ = encode_wav(8000, (0.3 * np.sin(2 * np.pi * 300 * np.arange(8000) / 8000))[:, None])
    row = b.post(
        "/api/workspace/import",
        files={"file": ("voice.wav", wav, "audio/wav")},
        data={"synthetic": "true"},
    ).json()
    ident = row["id"]
    assert row["sha256"] == hashlib.sha256(wav).hexdigest()
    assert a.get("/api/workspace").json()["assets"][0]["id"] == ident
    started = a.post(
        "/api/workspace/run",
        json={
            "input_id": ident,
            "template": "audio-filter",
            "filter": {"kind": "lowpass", "cutoff_hz": 800},
        },
    )
    assert started.status_code == 200, started.text
    finished = wait(a, started.json())
    assert finished["status"] == "completed", finished
    report = finished["result"]
    assert report["input_refs"][0]["sha256"] == row["sha256"]
    assert a.get("/api/media/" + ident + "/file").content == wav
    bundle = a.get("/api/workspace/assets/" + ident + "/export")
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
        assert (
            archive.read("voice.wav") == wav
            and json.loads(archive.read("config.json"))["synthetic"]
        )
    assert (
        a.get("/api/workspace/experiments/" + report["id"] + "/export").json()["output_id"]
        == report["output_id"]
    )
    assert b.post("/api/workspace/assets/" + ident + "/trash").status_code == 403
    assert a.post("/api/workspace/assets/" + ident + "/trash").status_code == 200
    assert a.get("/api/media/" + ident + "/file").status_code == 404
    assert a.delete("/api/workspace/assets/" + ident).status_code == 409
    assert a.post("/api/workspace/assets/" + ident + "/restore").status_code == 200
    assert (
        wait(a, a.post("/api/workspace/experiments/" + report["id"] + "/rerun").json())["status"]
        == "completed"
    )
    # A transferred copy becomes inaccessible when its Library import is trashed.
    exchange = b.post(
        "/api/exchange/files",
        json={"name": "note.txt", "size": 3, "sha256": hashlib.sha256(b"abc").hexdigest()},
    ).json()
    route = "/api/exchange/files/" + exchange["id"]
    b.put(route, content=b"abc")
    b.post(route + "/complete")
    imported = a.post(
        "/api/workspace/import-reference", json={"kind": "exchange", "id": exchange["id"]}
    ).json()
    assert a.post("/api/workspace/assets/" + imported["id"] + "/trash").status_code == 200
    assert b.get(route + "/download").status_code == 404
    a.post("/api/workspace/assets/" + imported["id"] + "/restore")
    assert b.get(route + "/download").content == b"abc"
    a.post("/api/workspace/assets/" + imported["id"] + "/trash")
    assert a.delete("/api/workspace/assets/" + imported["id"]).status_code == 200
    assert b.get(route + "/download").status_code == 404


def test_image_workflow_and_missing_input(clients):
    a, _ = clients
    raw = io.BytesIO()
    Image.new("RGB", (64, 64), (128, 80, 20)).save(raw, format="PNG")
    row = a.post(
        "/api/workspace/import", files={"file": ("image.png", raw.getvalue(), "image/png")}
    ).json()
    result = wait(
        a,
        a.post(
            "/api/workspace/run", json={"template": "image-edges", "input_id": row["id"]}
        ).json(),
    )
    assert result["status"] == "completed", result
    assert (
        a.get("/api/media/" + result["result"]["output_id"] + "/file").content[:8]
        == b"\x89PNG\r\n\x1a\n"
    )
    bad = wait(
        a,
        a.post(
            "/api/workspace/run", json={"template": "audio-filter", "input_id": row["id"]}
        ).json(),
    )
    assert bad["status"] == "failed"
    assert (
        a.post("/api/workspace/import", files={"file": ("empty.wav", b"", "audio/wav")}).status_code
        == 422
    )


@pytest.mark.parametrize(
    "kind", ["signals", "sampling", "quantisation", "fourier", "hilbert", "fir", "laplace"]
)
def test_practicals_have_real_finite_outputs(kind):
    result = run(Practical(kind=kind))
    assert result["synthetic"] and result["source"] == "SIMULATION" and result["elapsed_ms"] > 0
    assert np.isfinite(result["input"]).all() and "protocol" in result
    if kind == "fourier":
        assert result["reconstruction_max_error"] < 1e-12
    if kind == "laplace":
        assert result["stable"]


@pytest.mark.parametrize("mode", ["ASK", "BPSK", "DPSK", "QPSK", "16QAM", "OFDM"])
def test_modulation_counts_reference_bits_and_reports_failures(mode):
    good = run(Practical(kind="modulation", modulation=mode, ebn0_db=30))
    bad = run(Practical(kind="modulation", modulation=mode, ebn0_db=-10))
    assert good["bit_count"] == 4096 and good["bit_errors"] == 0
    assert bad["bit_errors"] > 0 and bad["ber"] == bad["bit_errors"] / bad["bit_count"]
    assert len(good["ber_curve"]) == 6


def test_quantisation_aliasing_and_fir_reference():
    low = run(Practical(kind="quantisation", bits=2))
    high = run(Practical(kind="quantisation", bits=12))
    assert high["mse"] < low["mse"]
    assert run(Practical(kind="sampling", frequency_hz=70))["aliased_frequency_hz"] == 30
    from scipy import signal

    result = run(Practical(kind="fir", window="hamming", filter_type="highpass"))
    np.testing.assert_allclose(
        result["taps"], signal.firwin(63, 30, fs=100, window="hamming", pass_zero=False)
    )


def test_secded_single_correction_double_rejection_and_arq():
    raw = b"ABCD"
    wire = encode(raw)
    assert decode(wire)[0] == raw
    for bit in range(8):
        changed = bytearray(wire)
        changed[1] ^= 1 << bit
        recovered, corrected = decode(changed)
        assert recovered == raw and corrected == 1
    changed = bytearray(wire)
    changed[0] ^= 3
    with pytest.raises(ValueError, match="double-bit"):
        decode(changed)
    assert arq_simulate(b"Hello", loss=0, ack_loss=0)["success"]
    failed = arq_simulate(b"Hello", loss=1, ack_loss=0, retries=2)
    assert not failed["success"] and failed["transmissions"] == 3
    raw = envelope(b"Hello", "text.txt", True, "public-test-passphrase")
    for rate in (100, 200, 400):
        audio, _ = modulate(raw, True, rate)
        assert decode_packets(audio)[0] == [raw]


def test_ack_authentication_retry_and_replay(clients):
    a, b = clients
    key = "public-test-passphrase"
    header = {"X-Orbit-Passphrase": base64.b64encode(key.encode()).decode()}
    tx = a.post(
        "/api/link/transmit",
        json={"text": "Hello", "passphrase": key, "fec": True, "bit_rate": 200},
    ).json()
    wav = a.get(tx["audio_url"]).content
    received = b.post("/api/link/receive", content=wav, headers=header).json()
    assert received["success"] and received["ack"]["audio_url"]
    assert not a.get("/api/link/transmissions/" + tx["id"]).json()["acknowledged"]
    ack = b.get(received["ack"]["audio_url"]).content
    assert b.post("/api/link/receive", content=ack, headers=header).status_code == 422
    decoded = a.post("/api/link/receive", content=ack, headers=header).json()
    assert decoded["acknowledgement_received"]["acknowledged"]
    assert a.post("/api/link/transmissions/" + tx["id"] + "/retry").json()["audio_url"] is None
    assert b.post("/api/link/receive", content=wav, headers=header).json()["duplicate"]


def test_reference_metrics_and_signaling_permissions(clients):
    result = mask_metrics([[1, 0], [1, 0]], [[1, 1], [0, 0]])
    assert (
        result["tp"] == result["fp"] == result["fn"] == result["tn"] == 1 and result["dice"] == 0.5
    )
    a, b = clients
    assert b.post("/api/live/rooms").status_code == 403
    code = a.post("/api/live/rooms").json()["code"]
    assert a.post("/api/live/rooms/" + code + "/join", json={"consent": False}).status_code == 422
    for c in (a, b):
        assert (
            c.post("/api/live/rooms/" + code + "/join", json={"consent": True}).status_code == 200
        )
    assert (
        a.post(
            "/api/live/rooms/" + code + "/signal",
            json={"kind": "offer", "payload": {"type": "offer", "sdp": "test-only"}},
        ).status_code
        == 200
    )
    assert b.get("/api/live/rooms/" + code).json()["signals"][0]["payload"]["sdp"] == "test-only"
    assert not a.get("/api/live/rooms/" + code).json()["signals"]
    assert (
        a.post(
            "/api/live/rooms/" + code + "/signal", json={"kind": "shell", "payload": {}}
        ).status_code
        == 422
    )
    assert b.delete("/api/live/rooms/" + code + "/member").status_code == 200


def test_hardware_and_speech_missing_consent(clients):
    a, b = clients
    assert b.get("/api/hardware/sdr").status_code == 403
    assert a.get("/api/workspace/diagnostics").json()["server"] == "CONNECTED"
    assert a.post("/api/speech/transcribe", json={"input_id": "a" * 24}).status_code == 422
    assert (
        a.post(
            "/api/hardware/csi/receive",
            json={"source_ip": "127.0.0.1", "source_description": "test"},
        ).status_code
        == 422
    )
    assert (
        a.post("/api/workspace/transport", json={"bytes": 20000, "sound_only": True}).json()[
            "recommendation"
        ]
        == "Keep acoustic-only selection"
    )
    assert a.post("/api/workspace/negotiate", json={"peer_rates": [600]}).status_code == 422


def test_print_report_escaping_and_array_header_bound(clients):
    a, _ = clients
    finished = wait(
        a,
        a.post(
            "/api/workspace/run",
            json={
                "template": "dsp-practical",
                "name": "<script>alert(1)</script>",
                "practical": {"kind": "fourier"},
            },
        ).json(),
    )
    assert finished["status"] == "completed"
    ident = finished["result"]["id"]
    printed = a.get("/api/workspace/experiments/" + ident + "/print")
    assert b"<script>" not in printed.content and b"&lt;script&gt;" in printed.content
    assert a.get("/api/workspace/experiments/" + ident + "/csv").content.startswith(
        b"source,synthetic,validation_protocol"
    )
    buffer = io.BytesIO()
    np.lib.format.write_array_header_1_0(
        buffer, {"descr": "<c8", "fortran_order": False, "shape": (10**9,)}
    )
    row = a.post(
        "/api/workspace/import",
        files={"file": ("oversized.npy", buffer.getvalue(), "application/octet-stream")},
    ).json()
    result = wait(
        a, a.post("/api/workspace/run", json={"template": "iq-fm", "input_id": row["id"]}).json()
    )
    assert result["status"] == "failed" and "262144" in result["message"]


def test_secure_server_certificate_and_consent(tmp_path, clients):
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import padding

    from orbit.secure_server import certificate

    folder = tmp_path / "certs"
    certificate(folder)
    root = x509.load_pem_x509_certificate((folder / "ca.crt").read_bytes())
    leaf = x509.load_pem_x509_certificate((folder / "server.crt").read_bytes())
    root.public_key().verify(
        leaf.signature,
        leaf.tbs_certificate_bytes,
        padding.PKCS1v15(),
        leaf.signature_hash_algorithm,
    )
    assert (
        str(leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value).find(
            "127.0.0.1"
        )
        >= 0
    )
    a, b = clients
    assert b.post("/api/security/start?consent=true").status_code == 403
    assert a.post("/api/security/start").status_code == 422


def test_pulse_reference_is_explicit_simulation(clients):
    a, _ = clients
    t = np.arange(500) / 20
    s = np.sin(2 * np.pi * 1.25 * t)
    rows = np.column_stack(
        [t, 120 + 0.5 * s, 115 + 2.5 * s, 105 + 0.2 * s, np.full(500, 0.001)]
    ).tolist()
    result = a.post(
        "/api/research/pulse-reference",
        json={
            "samples": rows,
            "reference_bpm": 75,
            "reference_source": "Generated reference",
            "consent": True,
            "synthetic": True,
        },
    ).json()
    assert result["source"] == "SIMULATION" and result["synthetic"]
    assert result["bpm"] is not None and result["absolute_error_bpm"] == abs(result["bpm"] - 75)
