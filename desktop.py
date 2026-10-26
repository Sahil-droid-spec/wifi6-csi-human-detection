"""Native Orbit window with the same local server used by paired phones."""

import argparse
import json
import os
import secrets
import socket
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Orbit desktop and local phone server")
    parser.add_argument(
        "--server", action="store_true", help="Run phone/LAN server without desktop window"
    )
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--data-dir")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    for candidate in range(args.port, args.port + 20):
        try:
            with socket.socket() as probe:
                probe.bind(("127.0.0.1" if args.local_only else "0.0.0.0", candidate))
            args.port = candidate
            break
        except OSError:
            continue
    else:
        raise SystemExit("No free Orbit port. Close an older instance and retry.")
    home = (
        Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent
    )
    if getattr(sys, "frozen", False) and (home / "app-source" / "orbit").is_dir():
        sys.path.insert(0, str(home / "app-source"))
    from orbit.api import create_app

    os.environ.setdefault("ORBIT_DOWNLOADS_DIR", str(home))
    data = Path(args.data_dir).resolve() if args.data_dir else home / "orbit-data"
    if args.self_test:
        data = Path(tempfile.mkdtemp(prefix="orbit-desktop-check-"))
    app = create_app(data, lan=not args.local_only, port=args.port)
    app.state.desktop_bootstrap = secrets.token_urlsafe(32)
    config = uvicorn.Config(
        app,
        log_config=None,
        host="127.0.0.1" if args.local_only else "0.0.0.0",
        port=args.port,
        access_log=False,
    )
    server = uvicorn.Server(config)
    if args.server:
        server.run()
        return
    thread = threading.Thread(target=server.run, name="orbit-local-server", daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{args.port}"
    for _ in range(150):
        try:
            with urllib.request.urlopen(url + "/api/health", timeout=1) as r:
                if json.load(r).get("instance_id") == app.state.instance_id:
                    break
        except Exception:
            time.sleep(0.1)
    else:
        raise SystemExit(
            "Cannot start Orbit. Close another app using this port, or launch Orbit.exe --port 8766."
        )
    if args.self_test:
        import numpy as np

        from orbit.core import radix2

        assert np.allclose(radix2(np.arange(8)), np.fft.fft(np.arange(8)))
        import http.cookiejar

        session = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        request = urllib.request.Request(
            url + "/api/desktop/claim",
            data=json.dumps({"token": app.state.desktop_bootstrap}).encode(),
            headers={"Content-Type": "application/json"},
        )
        assert json.load(session.open(request))["ok"]
        assert "captures" in json.load(session.open(url + "/api/status"))
        from orbit.models import estimator

        fixture = np.array(
            [
                [0.0, 0.0],
                [0.0, 1.0],
                [1.0, 0.0],
                [1.0, 1.0],
                [0.1, 0.1],
                [0.1, 0.9],
                [0.9, 0.1],
                [0.9, 0.9],
            ]
        )
        labels = np.array([0, 0, 1, 1, 0, 0, 1, 1])
        for name in ("lr", "rf", "mlp"):
            m = estimator(name)
            m.fit(fixture, labels)
            assert len(m.predict(fixture)) == len(labels)
        print(
            "ORBIT DESKTOP SELF-TEST PASSED: local HTTP health, NumPy/SciPy/sklearn/HDF5 imports, own FFT"
        )
        server.should_exit = True
        thread.join(timeout=10)
        return
    try:
        import webview

        # A native window opens the bundled local interface; phones use the same server.
        webview.create_window(
            "Orbit — Wi-Fi Sensing Lab",
            url + "/#/desktop?token=" + app.state.desktop_bootstrap,
            width=1320,
            height=860,
            min_size=(390, 650),
        )
        webview.start(
            gui="edgechromium",
            private_mode=False,
            storage_path=str(data / ("webview-profile-" + str(args.port))),
        )
    finally:
        server.should_exit = True
        thread.join(timeout=10)


if __name__ == "__main__":
    main()
