"""One-command local setup/launch. Python 3.10+; frontend is prebuilt."""

import argparse, hashlib, os, subprocess, sys, venv
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
    args = parser.parse_args()
    environment = root / ".venv"
    executable = environment / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    if not executable.exists():
        print("Creating a private Python environment…", flush=True)
        venv.create(environment, with_pip=True)
    requirements = root / "requirements-app.txt"
    fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker = environment / "orbit-requirements.sha256"
    if not marker.exists() or marker.read_text() != fingerprint:
        print("Installing Orbit dependencies from PyPI…", flush=True)
        subprocess.run(
            [str(executable), "-m", "pip", "install", "-r", str(requirements)],
            check=True,
            cwd=root,
        )
        marker.write_text(fingerprint)
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
