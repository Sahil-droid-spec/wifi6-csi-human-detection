"""Build the pinned Windows x64 CPython 3.10 offline wheelhouse."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path


def main():
    if os.name != "nt" or sys.version_info[:2] != (3, 10) or sys.maxsize <= 2**32:
        raise SystemExit("Use Windows x64 CPython 3.10 to prepare this wheelhouse.")
    root = Path(__file__).resolve().parents[1]
    folder = root / "wheelhouse/windows-x64-py310"
    folder.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--only-binary=:all:",
            "--dest",
            str(folder),
            "-r",
            str(root / "requirements-offline-win-py310.txt"),
        ],
        check=True,
    )
    wheels = sorted(folder.glob("*.whl"))
    (folder / "SHA256SUMS.txt").write_text(
        "".join(
            hashlib.sha256(p.read_bytes()).hexdigest()
            + "  "
            + p.relative_to(root).as_posix()
            + "\n"
            for p in wheels
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(f"Offline wheelhouse ready: {len(wheels)} wheels")


if __name__ == "__main__":
    main()
