"""Tests for the HVG-36 lane (preregistration, canary, holdout experiments, GeoTIFF, and run card)."""

from __future__ import annotations

import hashlib
import json

import numpy as np
import rasterio

from gemsdoe36.hvg_features import (
    BANNED_GDR_COLS,
    HVG_FOLD_SAFE_NAMES,
    HVG_STATIC_NAMES,
)
from gemsdoe36.paths import repo_root


def test_hvg36_banned_cols_and_feature_names() -> None:
    assert "dist_known_fault_px" in BANNED_GDR_COLS
    assert len(HVG_STATIC_NAMES) == 12
    assert len(HVG_FOLD_SAFE_NAMES) == 2
    assert len(set(HVG_STATIC_NAMES) | set(HVG_FOLD_SAFE_NAMES)) == 14


def test_hvg36_preregistration_and_canary_evidence() -> None:
    root = repo_root()
    prereg_path = root / "evidence" / "hvg36_preregistration_20261026.json"
    canary_path = root / "evidence" / "hvg36_leakage_canary_20261026.json"
    assert prereg_path.exists()
    assert canary_path.exists()

    prereg = json.loads(prereg_path.read_text())
    assert prereg["evaluator_version"] == "gems-segment-pooled-v1"
    assert len(prereg["ranked_hypotheses"]) == 4
    assert len(prereg["experiments"]) == 3
    assert prereg["budget"]["max_experiments"] == 3

    canary = json.loads(canary_path.read_text())
    assert canary["passed"] is True
    assert canary["threshold"] == 0.90
    assert canary["max_two_polarity_auc_across_all_14_features"] <= 0.90
    assert len(canary["features"]) == 14
    for fname, fmeta in canary["features"].items():
        assert fmeta["leakage_suspected"] is False, f"Feature {fname} flagged!"
        assert fmeta["max_two_polarity_auc"] <= 0.90


def test_hvg36_run_card_and_geotiff_integrity() -> None:
    root = repo_root()
    card_ev = root / "evidence" / "hvg36_run_card_20261026.json"
    card_dl = root / "docs" / "downloads" / "hvg36-run-card.json"
    exp_path = root / "evidence" / "hvg36_holdout_experiments_20261026.json"
    assert card_ev.exists()
    assert card_dl.exists()
    assert exp_path.exists()

    card = json.loads(card_ev.read_text())
    assert card == json.loads(card_dl.read_text())
    assert card["lane"] == "HVG-36"
    assert card["verdict"] == "negative"
    assert card["submission"]["ok_to_download_for_research"] is True
    assert card["submission"]["ok_to_submit_to_live_portal"] is False
    assert card["submission"]["note_length"] <= 140

    holdout = card["holdout"]
    assert holdout["label"] == "HOLDOUT-DTI"
    assert holdout["evaluator_version"] == "gems-segment-pooled-v1"
    assert holdout["withheld_positives"] == 60988
    assert abs(holdout["pooled_dti"] - 0.1357593607032416) < 1e-6
    assert holdout["pooled_dti"] > holdout["matched_baseline_B0"]["pooled_dti"]
    assert holdout["pooled_dti"] > holdout["recorded_h36_gps_B0_dti"]

    tif_path = root / card["artifact"]["tif_path"]
    zip_path = root / card["artifact"]["zip_path"]
    receipt_path = root / card["artifact"]["receipt_path"]
    assert tif_path.exists()
    assert zip_path.exists()
    assert receipt_path.exists()

    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == card["artifact"]["tif_sha256"]
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest() == card["artifact"]["zip_sha256"]

    with rasterio.open(tif_path) as src:
        assert src.count == 1
        assert src.dtypes == ("float32",)
        assert str(src.crs) == "EPSG:32611"
        assert (src.height, src.width) == (3730, 3292)
        assert src.nodata is None
        arr = src.read(1, masked=False)
        assert np.isfinite(arr).all()
        assert float(arr.min()) >= 0.0
        assert float(arr.max()) <= 1.0
        assert int((arr > 0.5).sum()) == 37654
