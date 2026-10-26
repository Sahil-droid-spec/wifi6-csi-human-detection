import argparse
import socket

import uvicorn

from .api import create_app


def main():
    parser = argparse.ArgumentParser(description="Orbit local Wi-Fi sensing lab")
    parser.add_argument(
        "--lan", action="store_true", help="Enable trusted private-LAN phone access"
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir")
    args = parser.parse_args()
    for candidate in range(args.port, args.port + 20):
        try:
            with socket.socket() as probe:
                probe.bind(("0.0.0.0" if args.lan else "127.0.0.1", candidate))
            args.port = candidate
            break
        except OSError:
            continue
    else:
        raise SystemExit("No free port. Close an older Orbit instance and retry.")
    uvicorn.run(
        create_app(args.data_dir, lan=args.lan, port=args.port),
        host="0.0.0.0" if args.lan else "127.0.0.1",
        port=args.port,
    )


if __name__ == "__main__":
    main()
