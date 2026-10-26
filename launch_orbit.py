"""One-command local setup/launch. Python 3.10+; frontend is prebuilt."""

import argparse, hashlib, os, subprocess, sys, venv, json
from pathlib import Path


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Orbit requires Python 3.10 or newer.")
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Set up and start Orbit")
    parser.add_argument(
        "--lan", action="store_true", help="Enable trusted-LAN phone access"
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--offline", action="store_true", help="Install only verified wheels from the bundled Windows x64 / CPython 3.10 wheelhouse")
    parser.add_argument("--check-install", action="store_true", help="Verify dependencies and exit without starting the server")
    args = parser.parse_args()
    if args.offline and (os.name != "nt" or sys.version_info[:2] != (3, 10) or sys.maxsize <= 2**32):
        raise SystemExit("Offline bundle requires Windows x64 and CPython 3.10. Use a matching interpreter or launch online.")
    environment = root / ".venv"
    executable = environment / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    if not executable.exists():
        print("Creating a private Python environment…", flush=True)
        venv.create(environment, with_pip=True)
    requirements = root / ("requirements-offline-win-py310.txt" if args.offline else "requirements-app.txt")
    wheelhouse = root / "wheelhouse/windows-x64-py310"
    if args.offline:
        from tools.checksums import verify_manifest
        verify_manifest(root, wheelhouse / "SHA256SUMS.txt")
    fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest() + ("-offline" if args.offline else "")
    marker = environment / "orbit-requirements.sha256"
    if not marker.exists() or marker.read_text() != fingerprint:
        print("Installing Orbit dependencies from " + ("verified offline wheels…" if args.offline else "PyPI…"), flush=True)
        subprocess.run(
            [str(executable), "-m", "pip", "install", *(["--no-index", "--find-links", str(wheelhouse)] if args.offline else []), "-r", str(requirements)],
            check=True,
            cwd=root,
        )
        marker.write_text(fingerprint)
    subprocess.run([str(executable), "-m", "pip", "check"], check=True, cwd=root)
    if args.check_install:
        subprocess.run([str(executable), "-c", "from orbit.api import create_app; import numpy, scipy, sklearn, h5py; print('Orbit dependency imports passed')"], check=True, cwd=root)
        return 0
    command = [str(executable), "-m", "orbit", "--port", str(args.port)]
    if args.lan:
        command += ["--lan"]
    print(
        "Open http://127.0.0.1:"
        + str(args.port)
        + " in your browser. Use the access code printed below.",
        flush=True,
    )
    try:
        return subprocess.call(command, cwd=root)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
