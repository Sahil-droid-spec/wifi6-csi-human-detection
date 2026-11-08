"""Reference-based comparisons and explicit, bounded separation experiments."""

import io

import numpy as np
from fastapi import File, UploadFile
from PIL import Image
from pydantic import BaseModel, Field
from sklearn.decomposition import FastICA

from .audio_studio import encode_wav, read_wav
from .vision import PulseInput, analyse_pulse


def mask_metrics(prediction, reference):
    p, r = np.asarray(prediction, bool), np.asarray(reference, bool)
    if p.shape != r.shape or p.ndim != 2:
        raise ValueError("Use two masks with exactly matching image dimensions.")
    tp = int(np.count_nonzero(p & r))
    tn = int(np.count_nonzero(~p & ~r))
    fp = int(np.count_nonzero(p & ~r))
    fn = int(np.count_nonzero(~p & r))
    ratio = lambda a, b: a / b if b else None
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "dice": ratio(2 * tp, 2 * tp + fp + fn),
        "iou": ratio(tp, tp + fp + fn),
        "sensitivity": ratio(tp, tp + fn),
        "specificity": ratio(tn, tn + fp),
        "accuracy": ratio(tp + tn, p.size),
        "pixels": p.size,
        "protocol": "One matched image, all mask pixels. User-provided reference; reference expertise/unseen status not independently verified. Pixel metrics are not diagnosis or dataset-level validation.",
    }


class Separate(BaseModel):
    input_id: str = Field(pattern="^[a-f0-9]{24}$")
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    consent: bool = False


class PulseCompare(PulseInput):
    reference_bpm: float = Field(gt=25, lt=240, allow_inf_nan=False)
    reference_source: str = Field(min_length=3, max_length=160)
    consent: bool = False
    synthetic: bool = False


def install(app, ctx):
    @app.post("/api/research/mask-compare/{ident}")
    async def compare_mask(ident: str, reference: UploadFile = File(...)):
        row, path = ctx["load_asset"](ident)
        if row.get("retina_role") != "mask":
            raise ValueError("Choose an Orbit retinal vessel-candidate mask.")
        raw = await reference.read(8 * 1024**2 + 1)
        await reference.close()
        if len(raw) > 8 * 1024**2:
            raise ValueError("Choose a reference mask up to 8 MiB.")
        with Image.open(path) as p, Image.open(io.BytesIO(raw)) as r:
            if r.width * r.height > 16_000_000:
                raise ValueError("Use a reference mask below 16 megapixels.")
            truth = np.asarray(r.convert("L"))
            prediction = np.asarray(p.convert("L"))
            if not np.isin(truth, [0, 255]).all():
                raise ValueError(
                    "Use a binary 0/255 reference mask without resizing or antialiasing."
                )
            return {
                **mask_metrics(prediction > 0, truth > 0),
                "input_id": ident,
                "synthetic": bool(row.get("synthetic")),
            }

    @app.post("/api/research/pulse-reference")
    def pulse_reference(body: PulseCompare):
        if not body.consent:
            raise ValueError("Confirm consent before comparing physiological samples.")
        result = analyse_pulse(body.samples)
        return {
            **result,
            "synthetic": body.synthetic,
            "source": "SIMULATION"
            if body.synthetic
            else "USER-SUPPLIED RECORDING · provenance unverified",
            "reference_bpm": body.reference_bpm,
            "reference_source": body.reference_source,
            "absolute_error_bpm": abs(result["bpm"] - body.reference_bpm)
            if result["bpm"] is not None
            else None,
            "comparison_protocol": "Single overlapping window, user-entered reference. Synchronization and device validation are user responsibilities; not clinical validation.",
        }

    @app.post("/api/research/separate")
    def separate(body: Separate):
        if not body.consent:
            raise ValueError("Confirm permission to process the audio locally.")
        row, path = ctx["load_asset"](body.input_id)
        if row["size"] > 12 * 1024**2:
            raise ValueError("Choose a stereo PCM WAV below 12 MiB.")
        rate, x = read_wav(path.read_bytes())
        if x.shape[1] != 2 or len(x) < rate // 2:
            raise ValueError(
                "ICA needs two independently mixed microphone channels, not a mono mixture. Choose stereo WAV lasting at least 0.5 seconds."
            )
        if np.linalg.matrix_rank(np.cov(x.T)) < 2:
            raise ValueError(
                "These channels are duplicates or linearly dependent; ICA cannot identify two sources."
            )
        model = FastICA(
            n_components=2, random_state=body.seed, whiten="unit-variance", max_iter=300, tol=0.001
        )
        separated = model.fit_transform(x)
        if model.n_iter_ >= 300:
            raise ValueError(
                "ICA did not converge. Try independently mixed channels or another seed; no successful separation was saved."
            )
        out = separated / np.maximum(abs(separated).max(axis=0), 1e-12) * 0.8
        outputs = []
        for channel in range(2):
            raw, clipped = encode_wav(rate, out[:, channel, None])
            outputs.append(
                ctx["save_asset"](
                    raw,
                    f"ICA-component-{channel + 1}.wav",
                    "EXPERIMENTAL ICA OUTPUT",
                    parent_id=row["id"],
                    synthetic=bool(row.get("synthetic")),
                    notes="Component order/sign/scale are ambiguous; listen and validate with reference sources before claiming speaker isolation.",
                )
            )
        return {
            "outputs": outputs,
            "iterations": int(model.n_iter_),
            "seed": body.seed,
            "protocol": "FastICA, two-channel instantaneous linear mixture assumption, centered unit-variance whitening; no source-quality metric without references. Reverberation, mono audio and moving sources violate assumptions.",
        }
