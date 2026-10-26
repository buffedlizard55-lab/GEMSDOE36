"""KPL-36 unit tests: feature geometry (no data files required)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe36.kpl_features import (  # noqa: E402
    KPL_FEATURES,
    KPL_LIDAR_FEATURES,
    line_anisotropy,
    structure_tensor,
)


def test_feature_inventory() -> None:
    assert len(KPL_FEATURES) == 12
    assert len(set(KPL_FEATURES)) == 12
    # LiDAR-blind expert must exclude every LiDAR-derived KPL column.
    assert all(n in KPL_FEATURES for n in KPL_LIDAR_FEATURES)
    assert "kpl_xorient_agree" not in KPL_LIDAR_FEATURES  # slope+mag tensors only
    assert "kpl_xcoh_product" in KPL_LIDAR_FEATURES  # consumes LiDAR coherence


def test_structure_tensor_prefers_straight_line_over_blob() -> None:
    rng = np.random.default_rng(0)
    fp = np.ones((120, 120), bool)
    line = np.zeros((120, 120), np.float32)
    line[58:62, :] = 1.0  # long straight horizontal band -> strong oriented gradients
    line += (0.02 * rng.standard_normal(line.shape)).astype(np.float32)
    blob = np.zeros((120, 120), np.float32)
    yy, xx = np.mgrid[:120, :120]
    blob += np.exp(-(((yy - 60) ** 2 + (xx - 60) ** 2) / (2 * 8.0**2))).astype(np.float32)
    blob += (0.02 * rng.standard_normal(blob.shape)).astype(np.float32)
    coh_line, _, _ = structure_tensor(line, fp, sigma_int=5.0)
    coh_blob, _, _ = structure_tensor(blob, fp, sigma_int=5.0)
    assert float(np.nanmean(coh_line[50:70, 20:100])) > float(np.nanmean(coh_blob[40:80, 40:80]))
    assert np.isfinite(coh_line).all() and (coh_line >= 0).all() and (coh_line <= 1.0001).all()


def test_line_anisotropy_detects_long_line_not_noise() -> None:
    rng = np.random.default_rng(1)
    noise = rng.random((100, 100)).astype(np.float32)
    lined = noise.copy()
    lined[49:51, :] = 1.0
    a_noise = line_anisotropy(noise, 15)
    a_line = line_anisotropy(lined, 15)
    assert float(np.mean(a_line[48:52, 30:70])) > float(np.mean(a_noise[48:52, 30:70])) + 0.05
    assert a_line.shape == (100, 100) and np.isfinite(a_line).all()
