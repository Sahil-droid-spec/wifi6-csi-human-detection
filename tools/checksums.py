"""Generate/verify actual SHA-256 bytes, never Git object IDs."""

import argparse
import hashlib
import subprocess
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root, manifest):
    checked = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        digest, name = line.split("  ", 1)
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or len(digest) != 64 or sha256(path) != digest:
            raise ValueError("Checksum mismatch: " + name + ". Re-extract the original download.")
        checked += 1
    if not checked:
        raise ValueError("Empty checksum manifest")
    print(f"SHA-256 verified: {checked} files")
    return checked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = root / "SHA256SUMS.txt"
    if args.verify:
        return verify_manifest(root, manifest)
    paths = (
        subprocess.check_output(["git", "ls-files", "--cached", "-z"], cwd=root)
        .decode()
        .split("\0")
    )
    paths = sorted(p for p in paths if p and p != "SHA256SUMS.txt" and (root / p).is_file())
    manifest.write_text(
        "# SHA-256 of file bytes; excludes this manifest. Regenerate after changes.\n"
        + "".join(sha256(root / p) + "  " + p + "\n" for p in paths),
        encoding="utf-8",
        newline="\n",
    )
    print(f"SHA-256 generated: {len(paths)} files")


if __name__ == "__main__":
    main()
