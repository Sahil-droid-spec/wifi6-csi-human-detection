"""Opt-in LAN TLS companion. Private keys are generated per installation, never shipped."""

import datetime
import ipaddress
import os
import socket
import threading
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse


def addresses():
    values = {"127.0.0.1"}
    for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
        host = result[4][0]
        ip = ipaddress.ip_address(host)
        if ip.is_private and not ip.is_link_local:
            values.add(host)
    return sorted(values)


def certificate(folder: Path):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    folder.mkdir(exist_ok=True)
    hosts = addresses()
    state = folder / "addresses.txt"
    now = datetime.datetime.now(datetime.timezone.utc)
    if (
        (folder / "server.key").is_file()
        and (folder / "server.crt").is_file()
        and state.is_file()
        and state.read_text() == "\n".join(hosts)
    ):
        existing = x509.load_pem_x509_certificate((folder / "server.crt").read_bytes())
        if existing.not_valid_after_utc > now + datetime.timedelta(days=7):
            return
    if (folder / "ca.key").is_file() and (folder / "ca.crt").is_file():
        ca_key = serialization.load_pem_private_key((folder / "ca.key").read_bytes(), password=None)
        ca = x509.load_pem_x509_certificate((folder / "ca.crt").read_bytes())
    else:
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Orbit local lab CA")])
        ca = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=5))
            .not_valid_after(now + datetime.timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=None,
                    decipher_only=None,
                ),
                critical=True,
            )
            .sign(ca_key, hashes.SHA256())
        )
        (folder / "ca.key").write_bytes(
            ca_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        (folder / "ca.crt").write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Orbit local lab")]))
        .issuer_name(ca.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=90))
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.IPAddress(ipaddress.ip_address(h)) for h in hosts]
                + [x509.DNSName("localhost"), x509.DNSName("orbit.local")]
            ),
            critical=False,
        )
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .sign(ca_key, hashes.SHA256())
    )
    (folder / "server.key").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    (folder / "server.crt").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    state.write_text("\n".join(hosts))
    for name in ("ca.key", "server.key"):
        try:
            (folder / name).chmod(0o600)
        except OSError:
            pass


def install(app, ctx):
    folder = ctx["data"] / "tls"
    state = {
        "enabled": False,
        "error": None,
        "port": int(os.environ.get("ORBIT_HTTPS_PORT", str(ctx.get("port", 8765) + 1))),
    }

    def start(force=False):
        if (not force and os.environ.get("ORBIT_HTTPS") != "1") or getattr(
            app.state, "orbit_tls_started", False
        ):
            return
        app.state.orbit_tls_started = True
        try:
            import uvicorn

            certificate(folder)
            config = uvicorn.Config(
                app,
                host="0.0.0.0" if ctx["sharing"]["enabled"] else "127.0.0.1",
                port=state["port"],
                ssl_keyfile=str(folder / "server.key"),
                ssl_certfile=str(folder / "server.crt"),
                log_config=None,
                log_level="warning",
                lifespan="off",
            )
            server = uvicorn.Server(config)
            app.state.orbit_tls_server = server
            threading.Thread(target=server.run, name="orbit-local-tls", daemon=True).start()
            state["enabled"] = True
        except Exception:
            state["error"] = (
                "Secure listener could not start. Check port availability and the local certificate files."
            )

    def stop():
        server = getattr(app.state, "orbit_tls_server", None)
        if server:
            server.should_exit = True

    from contextlib import asynccontextmanager

    previous = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        async with previous(application):
            start()
            try:
                yield
            finally:
                stop()

    app.router.lifespan_context = lifespan

    @app.get("/api/security/tls")
    def status():
        server = getattr(app.state, "orbit_tls_server", None)
        fingerprint = None
        if (folder / "ca.crt").is_file():
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes

            fingerprint = (
                x509.load_pem_x509_certificate((folder / "ca.crt").read_bytes())
                .fingerprint(hashes.SHA256())
                .hex()
            )
        return {
            **state,
            "enabled": bool(server and server.started and not server.should_exit),
            "ca_sha256": fingerprint,
            "https_addresses": [
                "https://" + h + ":" + str(state["port"]) for h in addresses() if h != "127.0.0.1"
            ],
            "next_step": "Start-Orbit-Secure.cmd opts into a second HTTPS listener. On each device, manually trust ONLY this installation’s CA after comparing its SHA-256 fingerprint on the laptop. Never bypass browser certificate warnings. Do not share private .key files.",
        }

    @app.post("/api/security/start")
    def enable(request: Request, consent: bool = False):
        if not ctx["local_request"](request):
            raise HTTPException(403, "Enable the secure listener on the laptop.")
        if not consent:
            raise ValueError("Confirm that you want to start the private LAN HTTPS listener.")
        start(force=True)
        return status()

    @app.get("/api/security/ca.crt")
    def public_certificate():
        if not (folder / "ca.crt").is_file():
            raise HTTPException(
                404, "Start the secure server once to generate a local certificate."
            )
        return FileResponse(
            folder / "ca.crt",
            media_type="application/x-x509-ca-cert",
            filename="Orbit-local-CA.crt",
        )
