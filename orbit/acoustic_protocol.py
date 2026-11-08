"""SECDED coding and deterministic stop-and-wait protocol laboratory."""

import numpy as np


def encode(data: bytes) -> bytes:
    nibbles = np.unpackbits(np.frombuffer(data, dtype=np.uint8)).reshape(-1, 4)
    words = np.zeros((len(nibbles), 8), dtype=np.uint8)
    words[:, [2, 4, 5, 6]] = nibbles
    words[:, 0] = words[:, 2] ^ words[:, 4] ^ words[:, 6]
    words[:, 1] = words[:, 2] ^ words[:, 5] ^ words[:, 6]
    words[:, 3] = words[:, 4] ^ words[:, 5] ^ words[:, 6]
    words[:, 7] = np.bitwise_xor.reduce(words[:, :7], axis=1)
    return np.packbits(words).tobytes()


def decode(data: bytes):
    if not data or len(data) % 2:
        raise ValueError("Use an even number of SECDED codewords.")
    words = np.unpackbits(np.frombuffer(data, dtype=np.uint8)).reshape(-1, 8).copy()
    syndrome = (
        (words[:, 0] ^ words[:, 2] ^ words[:, 4] ^ words[:, 6])
        + 2 * (words[:, 1] ^ words[:, 2] ^ words[:, 5] ^ words[:, 6])
        + 4 * (words[:, 3] ^ words[:, 4] ^ words[:, 5] ^ words[:, 6])
    )
    parity = np.bitwise_xor.reduce(words, axis=1)
    doubles = (syndrome != 0) & (parity == 0)
    if doubles.any():
        raise ValueError("SECDED detected an uncorrectable double-bit error. Retry this frame.")
    single = (syndrome != 0) & (parity == 1)
    indices = np.flatnonzero(single)
    words[indices, syndrome[indices] - 1] ^= 1
    corrected = int(np.count_nonzero(parity))
    return np.packbits(words[:, [2, 4, 5, 6]].reshape(-1)).tobytes(), corrected


def arq_simulate(
    payload: bytes, seed: int = 42, loss: float = 0.2, ack_loss: float = 0.1, retries: int = 3
):
    """State machine over a seeded erasure channel; not physical acoustic evidence."""
    if (
        not 1 <= len(payload) <= 8192
        or not 0 <= loss <= 1
        or not 0 <= ack_loss <= 1
        or not 0 <= retries <= 6
    ):
        raise ValueError("Use 1–8192 bytes, loss probabilities 0–1 and up to six retries.")
    rng = np.random.default_rng(seed)
    delivered = set()
    events = []
    ok = True
    packets = [payload[i : i + 48] for i in range(0, len(payload), 48)]
    for seq, part in enumerate(packets):
        acked = False
        for attempt in range(retries + 1):
            event = {"sequence": seq, "attempt": attempt + 1, "bytes": len(part)}
            if rng.random() < loss:
                event["state"] = "DATA_LOST_TIMEOUT"
            else:
                duplicate = seq in delivered
                delivered.add(seq)
                if rng.random() < ack_loss:
                    event["state"] = "ACK_LOST_TIMEOUT"
                else:
                    event.update(state="ACK_RECEIVED", duplicate_suppressed=duplicate)
                    acked = True
            events.append(event)
            if acked:
                break
        if not acked:
            ok = False
            break
    return {
        "source": "SIMULATION",
        "synthetic": True,
        "success": ok,
        "packets": len(packets),
        "unique_delivered": len(delivered),
        "transmissions": len(events),
        "events": events,
        "protocol": f"Seed {seed}; stop-and-wait erasure-channel simulation; max {retries + 1} attempts/packet, duplicate suppression, separate ACK loss. No physical speaker/microphone or Wi-Fi fallback.",
    }
