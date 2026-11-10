"""Create a deliberately tiny, amplitude-only simulation for sound transport.

Stored generated positions drive replay; no inference from CSI is performed.
"""

import argparse
import io
import json
from pathlib import Path

import numpy as np

from orbit.sensing_studio import Simulation, synthesize


def walking_payload() -> bytes:
    """32 packets, one synthetic subcarrier, quantized float16 amplitude/path."""
    source = synthesize(
        Simulation(duration=4, packet_rate=20, subcarriers=16, packet_loss=0, jitter=0)
    )
    metadata = {
        "schema": "orbit.sensing.v1",
        "synthetic": True,
        "rate": 20,
        "config": {"scenario": "walking"},
        "notes": "Tiny amplitude-only Simulation. Stored generated path, not inferred pose. "
        "First 32 packets of seed 42; one of 16 generated subcarriers; float16 quantization. "
        "Not suitable for research validation or activity-classifier accuracy.",
    }
    out = io.BytesIO()
    np.savez_compressed(
        out,
        amplitude=source["amplitude"][:1, :32].astype(np.float16),
        invalid=np.zeros(32, dtype=bool),
        timestamps=(np.arange(32) / 20).astype(np.float32),
        positions=np.asarray(source["positions"])[:, :32].astype(np.float16),
        metadata=np.array(json.dumps(metadata, separators=(",", ":"))),
    )
    payload = out.getvalue()
    if len(payload) > 8192:
        raise ValueError("Tiny walking file exceeds the acoustic payload cap.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = walking_payload()
    args.output.write_bytes(payload)
    print(f"Created {args.output}: {len(payload)} bytes; Simulation, 32 packets, 1 subcarrier")


if __name__ == "__main__":
    main()
