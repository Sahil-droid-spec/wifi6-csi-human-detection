import numpy as np
import pytest

from orbit import presence_experiment as presence


def test_filter_resets_at_packet_gaps_and_context_matches():
    b = presence.coefficients(15, 0.08)
    raw = np.array([[2.0] * 32 + [90.0] * 7 + [5.0] * 32 + [6.0] * 20])
    bad = np.r_[np.zeros(32), np.ones(7), np.zeros(52)].astype(bool)
    out = presence.filter_packets(raw, bad, b)
    np.testing.assert_allclose(out[0, :32], 2.0)
    np.testing.assert_allclose(out[0, 32:39], 0.0)
    np.testing.assert_allclose(out[0, 39:71], 5.0)
    np.testing.assert_allclose(
        presence.filter_packets(raw[:, 60:], bad[60:], b)[:, 14:], out[:, 74:]
    )
    with pytest.raises(ValueError, match="odd"):
        presence.coefficients(4, 0.08)


def test_matched_folds_only_train_on_other_dates(tmp_path, monkeypatch):
    fixture = [
        {"id": str(i), "sha256": str(i), "date": str(i // 2), "present": i % 2, "path": str(i)}
        for i in range(6)
    ]
    captured_fits = []

    class RF:
        def fit(self, x, y):
            captured_fits.append(set(np.rint(x[:, 0]).astype(int)))
            assert set(y) == {0, 1}

        def predict(self, x):
            return np.rint(x[:, 0]).astype(int) % 2

    monkeypatch.setattr(presence.models, "estimator", lambda _: RF())
    monkeypatch.setattr(
        presence.core,
        "read_capture",
        lambda path, _: (
            np.full((2, 384), int(path.name), dtype=float),
            np.zeros(384, dtype=bool),
            None,
        ),
    )
    result = presence.evaluate(
        fixture, tmp_path, presence.Settings(synthetic=True), lambda *_: None
    )
    assert result["synthetic"] and result["metrics"]["baseline"]["support"] == 6
    assert result["metrics"]["baseline"] == result["metrics"]["hamming"]
    for i, fold in enumerate(result["folds"]):
        assert (
            captured_fits[2 * i] == captured_fits[2 * i + 1] == {int(k) for k in fold["train_ids"]}
        )
        assert not set(fold["test_ids"]) & set(fold["train_ids"])
    assert all(
        len(r["baseline"]) == len(r["hamming"]) == len(r["windows"]) for r in result["recordings"]
    )
