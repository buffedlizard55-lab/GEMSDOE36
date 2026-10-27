"""Comprehensive unit and release-integrity tests for TCD-36 (2026-10-27)."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio
from scipy.ndimage import distance_transform_edt

from gems.submission import check_variants
from gemsdoe36.submission import validate_submission
from gemsdoe36.tcd_features import (
    GEOPHYS_FEATURES,
    HYDRO_FLUV_SEIS_FEATURES,
    MORPHO_FEATURES,
    TCD123_FEATURES,
    TCD_BLIND_FEATURES,
    TCD_STAGE1_FEATURES,
    TCD_STAGE2_FEATURES,
    build_stage2_context_matrix,
)

ROOT = Path(__file__).resolve().parents[1]


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_tcd36_feature_partitions_are_exact_and_disjoint() -> None:
    assert len(TCD_STAGE1_FEATURES) == 22
    assert len(TCD123_FEATURES) == 123
    assert len(set(TCD123_FEATURES)) == 123
    assert len(TCD_BLIND_FEATURES) == 102
    assert set(TCD_STAGE1_FEATURES).issubset(TCD_BLIND_FEATURES)
    assert len(TCD_STAGE2_FEATURES) == 18

    m, g, h = set(MORPHO_FEATURES), set(GEOPHYS_FEATURES), set(HYDRO_FLUV_SEIS_FEATURES)
    assert not (m & g) and not (m & h) and not (g & h)
    assert (m | g | h) == set(TCD123_FEATURES)


def test_stage2_context_matrix_never_bleeds_across_mask_boundary() -> None:
    rng = np.random.default_rng(42)
    h, w = 48, 48
    mask = np.zeros((h, w), dtype=bool)
    mask[:24, :] = True

    p_f = rng.uniform(0.0, 0.3, size=(h, w)).astype(np.float32)
    p_m = rng.uniform(0.0, 0.3, size=(h, w)).astype(np.float32)
    p_g = rng.uniform(0.0, 0.3, size=(h, w)).astype(np.float32)
    p_h = rng.uniform(0.0, 0.3, size=(h, w)).astype(np.float32)

    X1, idx1 = build_stage2_context_matrix(p_f, p_m, p_g, p_h, mask)

    # Corrupt everything outside `mask` with extreme values; inside-mask features must not change!
    p_f2 = p_f.copy()
    p_m2 = p_m.copy()
    p_g2 = p_g.copy()
    p_h2 = p_h.copy()
    p_f2[~mask] = 1.0
    p_m2[~mask] = 1.0
    p_g2[~mask] = 1.0
    p_h2[~mask] = 1.0
    X2, idx2 = build_stage2_context_matrix(p_f2, p_m2, p_g2, p_h2, mask)

    assert np.array_equal(idx1, idx2)
    assert np.allclose(X1, X2, atol=1e-6)
    assert np.isfinite(X1).all()


def test_tcd36_preregistration_canary_holdout_and_fail_closed_run_card() -> None:
    prereg_p = ROOT / "evidence" / "tcd36_preregistration_20261027.json"
    prereg = json.loads(prereg_p.read_text(encoding="utf-8"))
    md_p = ROOT / prereg["markdown_path"]
    assert _sha256(md_p) == prereg["markdown_sha256"]

    canary = json.loads((ROOT / "evidence" / "tcd36_leakage_canary_20261027.json").read_text(encoding="utf-8"))
    assert canary["passed"] is True
    assert canary["stage1_passed"] is True and canary["stage2_passed"] is True
    assert canary["max_symmetric_auc"] <= 0.90

    hold = json.loads((ROOT / "evidence" / "tcd36_holdout_experiments_20261027.json").read_text(encoding="utf-8"))
    assert hold["experiments_executed"] == 3
    assert hold["evaluator_version"] == "gems-segment-pooled-v1"
    assert hold["withheld_positives"] == 60988
    assert hold["best_candidate_arm"] == "EXP-2"
    assert hold["summaries"]["EXP-2"]["dti"] > 0.190
    assert hold["summaries"]["EXP-2"]["dti"] > hold["recorded_kpl36_exp3_benchmark"] + 0.020
    assert hold["paired"]["EXP-2_vs_B0"]["paired_delta_ci95"][0] > 0.047
    assert hold["paired"]["EXP-2_vs_EXP-1"]["paired_delta_ci95"][0] > 0.003
    assert hold["paired"]["EXP-2_vs_EXP-1"]["ci95_strictly_positive"] is True
    assert hold["paired"]["EXP-2_vs_EXP-1"]["fold_wins"] == 4

    rc_ev = ROOT / "evidence" / "tcd36_run_card_20261027.json"
    rc_dl = ROOT / "docs" / "downloads" / "tcd36-run-card.json"
    assert rc_ev.read_bytes() == rc_dl.read_bytes()
    rc = json.loads(rc_ev.read_text(encoding="utf-8"))

    # Fail-closed protocol invariants
    assert rc["verdict"] == "negative"
    assert rc["submission"]["slot_approved"] is False
    assert rc["submission"]["ok_to_download_and_submit"] is False
    assert rc["submission"]["ok_to_download_research_tif"] is True
    assert len(rc["submission"]["note"]) <= 140
    assert rc["elapsed_seconds"] <= 7200

    # Chronology & multi-regime uniqueness
    cross = json.loads((ROOT / "evidence" / "tcd36_crosscheck_20261027.json").read_text(encoding="utf-8"))
    assert cross["chronology_proof"]["surface_checked_strictly_before_dot_placement"] is True
    assert rc["registry_uniqueness"]["surface_before_placement"]["max_abs_rank_correlation"] <= 0.90
    assert rc["registry_uniqueness"]["focus9_and_mutual_uniqueness"]["focus9_max_competing_3px_dot_overlap"] <= 0.70
    assert rc["registry_uniqueness"]["focus9_and_mutual_uniqueness"]["max_mutual_3px_dot_overlap"] <= 0.70
    assert rc["registry_uniqueness"]["literal_unseparated_a_gt_0"]["max_3px_dot_overlap"] > 0.70
    assert rc["crowding_forensics"]["frac_ge3_neighbors_within_300m"] < 0.10

    # Artifact SHA-256 & ZIP checks
    tif_p = ROOT / rc["submission"]["file"]
    nan_p = ROOT / rc["submission"]["companion_nan_file"]
    zip_p = ROOT / rc["submission"]["zip"]
    assert _sha256(tif_p) == rc["submission"]["sha256"]
    assert _sha256(nan_p) == rc["submission"]["companion_nan_sha256"]
    assert _sha256(zip_p) == rc["submission"]["zip_sha256"]
    with zipfile.ZipFile(zip_p) as zf:
        assert zf.namelist() == [tif_p.name]
        assert hashlib.sha256(zf.read(tif_p.name)).hexdigest() == rc["submission"]["sha256"]


@pytest.mark.skipif(
    not (ROOT / "data/raw/sample_submission.tif").is_file(),
    reason="data/raw not restored",
)
def test_tcd36_geotiff_strict_0_1_and_collar_compliance() -> None:
    rc = json.loads((ROOT / "evidence" / "tcd36_run_card_20261027.json").read_text(encoding="utf-8"))
    tif_p = ROOT / rc["submission"]["file"]
    nan_p = ROOT / rc["submission"]["companion_nan_file"]
    tmpl_p = ROOT / "data/raw/sample_submission.tif"
    lbl_p = ROOT / "data/raw/labels.tif"

    rep_z = validate_submission(tif_p, tmpl_p, require_nonfinite_outside=False)
    rep_n = validate_submission(nan_p, tmpl_p, require_nonfinite_outside=True)
    assert rep_z.passed and rep_n.passed

    chk_z = check_variants(tif_p, tmpl_p)
    chk_n = check_variants(nan_p, tmpl_p)
    assert chk_z["format_valid"]
    assert chk_z["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]
    assert chk_n["official_format_compliant"]

    with rasterio.open(tif_p) as ds, rasterio.open(tmpl_p) as ts, rasterio.open(lbl_p) as ls:
        arr = ds.read(1)
        fp = np.isfinite(ts.read(1))
        cat = fp & (ls.read(1) > 0.5)
    assert np.isfinite(arr).all()
    assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
    assert int((arr > 0.5).sum()) == 37_654
    assert int((arr[~fp] != 0.0).sum()) == 0
    d_cat = distance_transform_edt(~cat)
    assert int(((arr > 0.5) & (d_cat <= 2.0)).sum()) == 0
