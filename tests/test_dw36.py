"""DW36 negative-lane invariants; no live submissions and no scoring on test fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_dw36 import fields, smoothed_gradient  # noqa: E402


def test_normalized_gradient_missing_support():
    a = np.zeros((72, 72), np.float32)
    a[:, 32:] = 10
    foot = np.ones_like(a, bool)
    a[0, 0] = np.nan
    g, support = smoothed_gradient(a, foot, 2)
    assert np.isfinite(g).all()
    assert not support[0, 0]
    assert support[36, 36]
    assert g[36, 32] > g[36, 5]


def test_fields_nonnegative_and_finite(tmp_path, monkeypatch):
    # Use a tiny synthetic cache to check numerical and support handling, never a scored dataset.
    import run_dw36

    monkeypatch.setattr(run_dw36, "BANDS", tmp_path)
    y, x = np.indices((72, 72))
    arrays = {
        "02_rtp.npy": np.where(x > 32, 10., 0.).astype(np.float32),
        "13_iso_grav_anom.npy": (x + y).astype(np.float32),
        "12_det_elev.npy": (y / 10).astype(np.float32),
    }
    arrays["02_rtp.npy"][0, 0] = np.nan
    for name, a in arrays.items():
        np.save(tmp_path / name, a)
    foot = np.ones((72, 72), bool)
    feature, support, scales = fields(foot)
    assert not support[0, 0]
    assert all(v > 0 for v in scales.values())
    assert all(np.isfinite(a).all() and (a >= 0).all() for a in feature.values())
    assert feature["dw36_field"][0, 0] == 0


def test_duplicate_stopped_before_tiff():
    card = json.loads((ROOT / "evidence/dw36_run_card_20261026.json").read_text())
    assert card["experiments_run"] == 1
    assert card["duplicate_stop_stage"] == "final"
    assert card["registry"]["pinned_count"] == card["registry"]["verified_count"]
    assert card["registry"]["final"]["max_3px_overlap"] > .70
    assert card["raster_sha256"] is None and card["validator_output"] is None
    assert not card["submit_ok"] and card["verdict"] == "negative"
    assert not list((ROOT / "docs/downloads").glob("gemsdoe36-dw36*.tif"))
