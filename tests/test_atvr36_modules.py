"""Unit tests for ATVR-36 variational Anderson PDE, 300 m CELF submodular emitter, and integrity guards."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemsdoe36.anderson_dip import ExtensionField, azimuth_to_raster
from gemsdoe36.atvr_features import _assert_safe_source
from gemsdoe36.metric import distance_weighted_tversky
from gemsdoe36.submodular_emit import (
    build_euclidean_kernel_300m,
    emit_submodular_cover,
)
from gemsdoe36.variational_anderson import variational_anderson_refine


def test_euclidean_kernel_matches_metric_exactly():
    dy, dx, kw = build_euclidean_kernel_300m(100.0, 300.0)
    assert len(kw) == 25  # all integer (dy, dx) with hypot(dy, dx) < 3.0

    # Single dot at center of 11x11 grid: sum of credits against every individual truth cell
    # must equal kw sum
    pred = np.zeros((11, 11), dtype=np.float32)
    pred[5, 5] = 1.0
    for off_y, off_x, expected_w in zip(dy.tolist(), dx.tolist(), kw.tolist(), strict=True):
        truth = np.zeros((11, 11), dtype=np.float32)
        truth[5 + off_y, 5 + off_x] = 1.0
        comp = distance_weighted_tversky(pred, truth, return_components=True)
        assert comp.true_positive == pytest.approx(expected_w, abs=1e-6)


def test_submodular_cover_beats_naive_topk_along_ridge():
    # A 40-px N-S fault ridge at col 15 with monotonically slightly decreasing prob
    prob = np.zeros((48, 32), dtype=np.float32)
    elig = np.ones((48, 32), dtype=bool)
    truth = np.zeros((48, 32), dtype=np.float32)
    for r in range(4, 44):
        prob[r, 15] = 0.90 - 0.001 * r
        truth[r, 15] = 1.0

    budget = 10
    # Naive top-k puts all 10 dots packed into rows 4..13, leaving rows 16..43 uncovered!
    naive_mask = np.zeros_like(elig)
    naive_mask[4 : 4 + budget, 15] = True

    sub = emit_submodular_cover(prob, elig, budget=budget, min_spacing_px=2.0)
    assert int(sub.mask.sum()) == budget
    assert (sub.mask & ~elig).sum() == 0

    dti_naive = float(distance_weighted_tversky(naive_mask.astype(np.float32), truth))
    dti_sub = float(distance_weighted_tversky(sub.mask.astype(np.float32), truth))
    assert dti_sub > dti_naive + 0.15


def test_variational_anderson_damps_forbidden_ew_and_stays_in_0_1():
    h, w = 48, 48
    foot = np.ones((h, w), dtype=bool)
    foot[0, :] = False

    # Uniform ESE extension (112 deg azimuth -> normal faults strike NNE ~22 deg, normal ~112 deg)
    ang = np.full((h, w), float(azimuth_to_raster(112.0)), dtype=np.float32)
    conf = np.full((h, w), 0.95, dtype=np.float32)
    ext = ExtensionField(
        angle_raster=ang,
        confidence=conf,
    )

    # Ridge A: N-S fault ridge at col 14 (normal ~ E-W, aligned with ESE extension)
    # Ridge B: E-W stripe at row 34 (normal ~ N-S, perpendicular to ESE extension -> forbidden!)
    p0 = np.zeros((h, w), dtype=np.float32)
    p0[8:40, 14] = 0.70
    p0[34, 8:40] = 0.70
    # Inject NaN outside footprint to confirm sanitization
    p0[0, 5] = np.nan

    p_ref, diag = variational_anderson_refine(p0, ext, foot, steps=4, step_size=0.22)
    assert np.isfinite(p_ref).all()
    assert float(p_ref.min()) >= 0.0
    assert float(p_ref.max()) <= 1.0
    assert float(p_ref[~foot].max()) == 0.0
    # Permitted N-S ridge retains higher mean probability than forbidden E-W stripe
    ns_mean = float(p_ref[12:30, 14].mean())
    ew_mean = float(p_ref[34, 20:38].mean())
    assert ns_mean > ew_mean
    assert diag["stress_energy_after"] <= diag["stress_energy_before"] + 1e-4


def test_atvr_banned_source_guard():
    for bad in (
        Path("/tmp/derived_sgmc_faults_100m_u8.tif"),
        Path("/tmp/gdr_qfaults_traces.csv"),
        Path("/tmp/scored/prior.tif"),
        Path("/tmp/focus_registry/gems32.tif"),
        Path("/tmp/docs/downloads/legacy.tif"),
    ):
        with pytest.raises(RuntimeError, match="banned input path"):
            _assert_safe_source(bad)


def test_whole_segment_holdout_plan_never_splits_segments():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from evaluate_holdout import build_whole_segment_holdout_plan

    foot = np.ones((80, 80), dtype=bool)
    known = np.zeros((80, 80), dtype=bool)
    known[10:20, 10] = True
    # Segment 2 crosses quadrant boundary row 40 vertically
    known[32:48, 12] = True
    # Segment 2 in top-right
    known[10:22, 60] = True
    # Segment 3 in bottom-left
    known[55:68, 18] = True
    # Segment 4 in bottom-right
    known[58:72, 62] = True

    plan = build_whole_segment_holdout_plan(known, foot, buffer_px=6)
    assert plan.n_segments == 5
    # Every segment must lie 100% inside a single hidden_by_fold[k]
    for sid in range(1, plan.n_segments + 1):
        seg_px = plan.segment_ids == sid
        owners = [k for k in range(4) if (plan.hidden_by_fold[k] & seg_px).any()]
        assert len(owners) == 1
        k_own = owners[0]
        assert np.array_equal(plan.hidden_by_fold[k_own] & seg_px, seg_px)
        assert not (plan.visible_by_fold[k_own] & seg_px).any()
        assert np.array_equal(plan.eval_mask_by_fold[k_own] & seg_px, seg_px)


def test_site_gate_and_promoted_geotiff_cryptographic_consistency():
    import rasterio

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "scripts"))
    import check_site

    assert check_site.main() == 0
    tif_path = repo_root / "docs" / "downloads" / "gemsdoe36-atvr36-20261026.tif"
    assert tif_path.is_file()
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        assert src.crs.to_epsg() == 32611
        assert src.shape == (3730, 3292)
        assert src.nodata is None
        assert np.isfinite(arr).all()
        assert float(arr.min()) == 0.0
        assert float(arr.max()) == 1.0
        assert int((arr > 0.5).sum()) == 37654


def test_submission_writer_registry_audit_handles_placeholder_and_lattice(tmp_path: Path):
    import rasterio
    from rasterio.transform import Affine

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "scripts"))
    from atvr36_submission_gate import run_registry_audit

    h, w = 24, 24
    foot = np.ones((h, w), dtype=bool)
    profile = {
        "driver": "GTiff",
        "height": h,
        "width": w,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": Affine(100.0, 0.0, 300000.0, 0.0, -100.0, 4400000.0),
    }

    def _save(name: str, arr: np.ndarray) -> Path:
        p = tmp_path / name
        with rasterio.open(p, "w", **profile) as dst:
            dst.write(arr.astype(np.float32), 1)
        return p

    placeholder = _save("gemsdoe9-PLACEHOLDER.tif", np.zeros((h, w), dtype=np.float32))
    lat_arr = np.zeros((h, w), dtype=np.float32)
    lat_arr[::5, ::5] = 1.0
    lattice = _save("13gems_probe_lattice-s5.tif", lat_arr)
    geol_arr = np.zeros((h, w), dtype=np.float32)
    geol_arr[2, 2] = 1.0
    geol = _save("GEMSDOE32-b2.tif", geol_arr)

    surf = np.linspace(0.0, 0.8, h * w, dtype=np.float32).reshape(h, w)
    dots = np.zeros((h, w), dtype=bool)
    dots[20, 20] = True

    res = run_registry_audit(
        surf,
        dots,
        foot,
        [("ph", placeholder), ("lat", lattice), ("geol", geol)],
    )
    assert res["duplicate_gate_passed"] is True
    assert res["constant_placeholders_skipped"] == ["ph"]
    assert len(res["synthetic_lattice_disclosure"]) == 1
    assert res["n_geological_rasters_enforced"] == 1



