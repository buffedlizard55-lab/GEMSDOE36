"""Unit tests for GVSC-36 physical operators, Bayes calibration, and anti-leakage guards."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from gemsdoe36.gvsc_features import (
    BANNED_COLUMN_NAMES,
    EXP1_FEATURES,
    EXP2_FEATURES,
    EXP3_BLIND_FEATURES,
    GVSC_FEATURES,
    LIDAR_FEATURE_SET,
    SA_FEATURES,
    directional_worm_anisotropy,
    strike_guided_projection,
    upgradient_backproject,
)


def test_feature_partition_counts_and_lidar_blindness() -> None:
    assert len(SA_FEATURES) == 16
    assert len(GVSC_FEATURES) == 14
    assert len(EXP1_FEATURES) == 59 + 16
    assert len(EXP2_FEATURES) == 59 + 16 + 14
    assert len(set(EXP2_FEATURES)) == 89
    assert len(LIDAR_FEATURE_SET) == 15
    assert len(EXP3_BLIND_FEATURES) == 74
    for name in EXP3_BLIND_FEATURES:
        assert not name.startswith("lid_")
        assert "lid_" not in name


def test_upgradient_backproject_shifts_plume_upslope_toward_fault() -> None:
    """Mountain in West (low col, high z), fault at col=18, hot spring at col=30 (low z)."""
    h, w = 48, 60
    cols = np.arange(w, dtype=np.float32)[None, :]
    # Elevation drops eastward at 15 m / pixel -> upslope points West (u_up_c < 0)
    z_reg = np.broadcast_to(2200.0 - 15.0 * cols, (h, w)).astype(np.float32)
    gz_r, gz_c = np.gradient(z_reg)
    gnorm = np.hypot(gz_r, gz_c) + np.float32(2.0)
    u_up_r = (gz_r / gnorm).astype(np.float32)
    u_up_c = (gz_c / gnorm).astype(np.float32)

    plume = np.zeros((h, w), dtype=np.float32)
    plume[24, 30] = 10.0  # Outflow spring 1.2 km downslope (east) of fault at col=18

    bp = upgradient_backproject(plume, u_up_r, u_up_c)
    assert np.isfinite(bp).all()
    assert float(bp.min()) >= 0.0
    peak_col = int(np.argmax(bp[24]))
    # Peak back-projected conduit potential must shift upslope (westward, col < 30), never east!
    assert 14 <= peak_col <= 26, f"Expected upslope shift to [14, 26], got col={peak_col}"
    assert float(bp[24, 20]) > 5.0 * float(bp[24, 38])


def test_directional_worm_anisotropy_prefers_fault_line_over_circular_blob() -> None:
    h, w = 45, 45
    line_img = np.zeros((h, w), dtype=np.float32)
    line_img[10:35, 22] = 1.0  # N-S fault line (azimuth 0 deg)

    yy, xx = np.ogrid[:h, :w]
    blob_img = (((yy - 22) ** 2 + (xx - 22) ** 2) <= 7**2).astype(np.float32)

    aniso_line, strike_line = directional_worm_anisotropy(line_img, ortho_penalty=0.5)
    aniso_blob, _ = directional_worm_anisotropy(blob_img, ortho_penalty=0.5)

    assert float(aniso_line[22, 22]) > 0.80
    # Circular blob has isotropic line integrals along all azimuths -> suppressed by ortho_penalty
    assert float(aniso_line[22, 22]) > 1.5 * float(aniso_blob[22, 22])
    assert float(strike_line[22, 22]) == 0.0


def test_strike_guided_projection_elongates_along_strike() -> None:
    h, w = 45, 45
    imp = np.zeros((h, w), dtype=np.float32)
    imp[22, 22] = 5.0
    strike = np.zeros((h, w), dtype=np.float32)  # 0 deg = N-S
    proj = strike_guided_projection(imp, strike)
    # Along-strike N-S (row=16, col=22) must exceed cross-strike E-W (row=22, col=28)
    assert float(proj[16, 22]) > 2.5 * float(proj[22, 28])


def test_gvsc_source_has_strict_anti_leakage_guards() -> None:
    src = Path("src/gemsdoe36/gvsc_features.py").read_text(encoding="utf-8")
    # Ensure banned raster filenames are never opened (only mentioned in module docstring guard)
    code_body = src.split('"""', 2)[-1]
    for banned in ("labels.tif", "existing_faults.tif", "derived_sgmc", "qfaults_traces"):
        assert banned not in code_body, f"Banned token {banned} found in gvsc_features code body"
    assert "dist_known_fault_px" in BANNED_COLUMN_NAMES


def test_gvsc_negative_release_is_hash_pinned_and_never_submit_authorized() -> None:
    root = Path(__file__).resolve().parents[1]
    card = json.loads((root / "evidence/gvsc36_run_card_20261026.json").read_text())
    sub = card["submission"]
    tif = root / "docs/downloads" / sub["zeros_filename"]
    assert card["verdict"] == "negative"
    assert card["safe_to_download_for_research"] is True
    assert card["safe_to_submit_live_slot"] is False
    assert card["gates"]["G4c_competing_methods_3px_overlap_le_0p70"] is False
    assert card["gates"]["G4d_literal_all_registry_3px_overlap_le_0p70"] is False
    assert len(sub["note"]) <= 140
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == sub["raster_sha256"]
