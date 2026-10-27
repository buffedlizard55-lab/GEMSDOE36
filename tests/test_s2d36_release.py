"""End-to-end verification tests for S2D-36 preregistration, holdout, GeoTIFF, and fail-closed Pages."""

from __future__ import annotations

import hashlib
import inspect
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gemsdoe36.s2d_features import (
    S2D_EXP3_AUX_FEATURES,
    S2D_FEATURES,
    S2D_STAGE2_FEATURES,
    apply_halo_sharpening,
    build_s2d_dual_aux_features,
    build_s2d_stage1_features,
    build_s2d_stage2_corridor_features,
)

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_s2d_feature_lists_and_zero_label_leakage() -> None:
    assert len(S2D_FEATURES) == 21
    assert len(set(S2D_FEATURES)) == 21
    assert len(S2D_STAGE2_FEATURES) == 14
    assert len(S2D_EXP3_AUX_FEATURES) == 4

    src = inspect.getsource(build_s2d_stage1_features)
    assert "labels.tif" not in src
    assert "existing_faults.tif" not in src


def test_s2d_stage2_and_halo_builders_are_finite_and_bounded() -> None:
    rng = np.random.default_rng(36)
    fp = np.ones((48, 48), dtype=bool)
    fp[:3, :] = False
    p1 = np.where(fp, rng.uniform(0.0, 0.25, size=fp.shape), 0.0).astype(np.float32)
    p1[24, 8:40] = 0.85  # synthetic E-W fault crest
    sub = np.where(fp, 0.4, 0.0).astype(np.float32)
    flat_idx = np.flatnonzero(fp.ravel())

    X_corr = build_s2d_stage2_corridor_features(p1, fp, sub, flat_idx)
    assert X_corr.shape == (int(fp.sum()), len(S2D_STAGE2_FEATURES))
    assert np.isfinite(X_corr).all()

    pdual = np.clip(p1 + 0.05, 0.0, 1.0).astype(np.float32)
    X_aux = build_s2d_dual_aux_features(pdual, p1, fp, flat_idx)
    assert X_aux.shape == (int(fp.sum()), len(S2D_EXP3_AUX_FEATURES))
    assert np.isfinite(X_aux).all()

    sharp = apply_halo_sharpening(p1, fp, gamma_halo=0.15)
    assert sharp.shape == fp.shape
    assert np.isfinite(sharp).all()
    assert float(sharp.min()) >= 0.0 and float(sharp.max()) <= 1.0
    assert float(sharp[~fp].max()) == 0.0


def test_s2d_preregistration_canary_and_holdout_evidence() -> None:
    prereg_path = ROOT / "evidence/s2d36_preregistration_20261027.json"
    card = _load("evidence/s2d36_run_card_20261027.json")
    canary = _load("evidence/s2d36_leakage_canary_20261027.json")
    hold = _load("evidence/s2d36_holdout_experiments_20261027.json")
    peers = _load("evidence/s2d36_oct27_peer_audit_20261027.json")

    assert card["preregistration"]["sha256"] == _sha256(prereg_path)
    assert card["experiments_executed"] == 3  # Rule 6 budget <= 3 experiments
    assert canary["passed"] is True
    assert canary["max_symmetric_auc"] <= 0.90
    assert canary["max_symmetric_auc_new_s2d"] <= 0.90

    assert hold["evaluator_version"] == "gems-segment-pooled-v1"
    assert hold["withheld_positives"] == 60988
    dti_b0 = hold["summaries"]["B0"]["dti"]
    dti_ckpl = hold["summaries"]["C-KPL"]["dti"]
    dti_exp1 = hold["summaries"]["EXP-1"]["dti"]
    dti_exp2 = hold["summaries"]["EXP-2"]["dti"]
    assert dti_exp2 == pytest.approx(0.2007657135656901, abs=1e-6)
    assert dti_exp2 > dti_exp1 > dti_ckpl > dti_b0
    assert dti_exp2 > 0.17010000946379217  # beats recorded KPL-36 EXP-3
    assert hold["paired"]["EXP-2_vs_B0"]["ci95_strictly_positive"] is True
    assert hold["paired"]["EXP-2_vs_C-KPL"]["ci95_strictly_positive"] is True
    assert hold["paired"]["EXP-2_vs_C-KPL"]["fold_wins"] == 4

    assert peers["all_oct25_27_peers_pass_70pct_overlap_and_90pct_spearman"] is True
    assert peers["max_oct25_27_peer_3px_overlap"] <= 0.70


def test_s2d_geotiff_portal_range_and_fail_closed_release_invariants() -> None:
    card = _load("evidence/s2d36_run_card_20261027.json")
    current = _load("docs/current-run.json")
    manifest = _load("docs/downloads/submissions_manifest.json")

    # Fail-closed authorization because literal reg-052 & wide blankets > 70%
    assert card["verdict"] == "negative"
    assert card["ok_to_download_and_submit"] is False
    assert card["slot_approved"] is False
    assert card["gates"]["G1_canary"] is True
    assert card["gates"]["G2_holdout_beats_CKPL_and_B0_with_CI"] is True
    assert card["gates"]["G3a_pre_placement_surface_spearman_all_198"] is True
    assert card["gates"]["G3c_literal_all_198_registry_including_reg052"] is False
    assert card["gates"]["G4_portal_format_and_0_1_range"] is True
    assert card["organizer_score"] is None
    assert card["scenario_projection_not_a_score"]["receipt"] is None

    sub = card["submission"]
    assert len(sub["note"]) <= 140
    tif_path = ROOT / sub["file"]
    zip_path = ROOT / sub["zip"]
    assert tif_path.is_file() and _sha256(tif_path) == sub["sha256"]
    assert zip_path.is_file() and _sha256(zip_path) == sub["zip_sha256"]

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert hashlib.sha256(zf.read(tif_path.name)).hexdigest() == sub["sha256"]

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert ds.dtypes == ("float32",)
        assert str(ds.crs) == "EPSG:32611"
        assert (ds.height, ds.width) == (3730, 3292)
        arr = ds.read(1)
    assert np.isfinite(arr).all()  # zero NaNs anywhere -> no portal [0, 1] range error
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
    assert int((arr > 0).sum()) == 37654

    # Manifest & current-run bindings
    assert current["lane_id"] == "S2D-36"
    assert current["verdict"] == "negative"
    assert current["slot_approved"] is False
    assert current["ok_to_download_and_submit"] is False
    assert current["tif_sha256"] == sub["sha256"]
    assert manifest["slot_approved"] is False
    assert manifest["current_candidate"] is None
    assert manifest["research_candidate"]["lane"] == "S2D-36"
    assert manifest["research_candidate"]["submit_ok"] is False
