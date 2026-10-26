"""Unit tests for H36-CTRB physical operators, CSV leak-guard, and submodular DTI emitter."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from gems.metric import KERNEL_OFFSETS, dti_score_fast
from gemsdoe36.ctrb import (
    ALL_FEATURE_NAMES,
    KERNEL_DX,
    KERNEL_DY,
    KERNEL_W,
    LOCAL_FEATURE_NAMES,
    STRUCTURAL_FEATURE_NAMES,
    _build_anisotropic_gdr_geotherm,
    anderson_azimuth_weight,
    extract_geophysical_trunk_topology,
    fill_nearest_valid,
    hessian_curvilinear_response,
    oriented_worm_persistence,
    structure_double_angle,
    submodular_dti_emit,
)


def test_feature_stack_partition_counts() -> None:
    assert len(LOCAL_FEATURE_NAMES) == 17
    assert len(STRUCTURAL_FEATURE_NAMES) == 8
    assert len(ALL_FEATURE_NAMES) == 25
    assert len(set(ALL_FEATURE_NAMES)) == 25
    # Verify raw elevation and raw slope confounds are absent
    assert "det_elev" not in ALL_FEATURE_NAMES
    assert "det_elev_slope" not in ALL_FEATURE_NAMES


def test_triangular_kernel_matches_official_metric_offsets() -> None:
    assert KERNEL_DY.size == len(KERNEL_OFFSETS) == 25
    assert KERNEL_DX.size == 25
    assert KERNEL_W.size == 25
    center_idx = np.flatnonzero((KERNEL_DY == 0) & (KERNEL_DX == 0))
    assert center_idx.size == 1
    assert np.isclose(KERNEL_W[center_idx[0]], 1.0)
    assert np.all((KERNEL_W > 0.0) & (KERNEL_W <= 1.0))


def test_anderson_azimuth_weight_extensional_mechanics() -> None:
    w_nne = anderson_azimuth_weight(20.0)
    w_nw = anderson_azimuth_weight(148.0)
    w_ew = anderson_azimuth_weight(100.0)
    assert w_nne > 0.98
    assert w_nw > 0.80
    assert w_ew < 0.25
    assert w_nne > w_nw > w_ew


def test_oriented_worm_beats_isolated_speckles() -> None:
    fp = np.ones((64, 64), dtype=bool)
    surf_line = np.zeros((64, 64), dtype=np.float32)
    # 19-px N-S lineament
    surf_line[22:41, 32] = 1.0

    surf_dots = np.zeros((64, 64), dtype=np.float32)
    rng = np.random.default_rng(7)
    coords = rng.choice(64 * 64, size=19, replace=False)
    surf_dots.ravel()[coords] = 1.0

    w_line, wand_line = oriented_worm_persistence(surf_line, fp, half_len_px=7)
    w_dots, _ = oriented_worm_persistence(surf_dots, fp, half_len_px=7)
    assert float(w_line.max()) > 2.2 * float(w_dots.max())
    assert float(wand_line.max()) > 0.75 * float(w_line.max())


def test_geophysical_trunk_relay_bridge_and_tip_lobe() -> None:
    fp = np.ones((80, 80), dtype=bool)
    score = np.zeros((80, 80), dtype=np.float32)
    # Two sub-parallel N-S trunks separated by a 10-px relay bridge and overlapping
    score[15:48, 34] = 5.0
    score[32:65, 44] = 5.0

    relay, tip = extract_geophysical_trunk_topology(score, fp, quantile=95.0, min_component_px=12)
    # Relay bridge between col 34 and col 44 around row 38..42 must exceed far-field background
    bridge_peak = float(relay[36:44, 37:42].max())
    far_field = float(relay[10:20, 5:15].max())
    assert bridge_peak > 0.30
    assert bridge_peak > far_field + 0.25

    # Outward tip lobes ahead of row 15 col 34 (northward: rows 4..13, col 33..35)
    north_tip_lobe = float(tip[4:13, 33:36].max())
    lateral_flank = float(tip[25:30, 20:25].max())
    assert north_tip_lobe > 0.35
    assert north_tip_lobe > lateral_flank + 0.30


def test_gdr_csv_dictreader_handles_commas_and_strips_dist_known_fault(tmp_path: Path) -> None:
    ext = tmp_path / "external"
    ext.mkdir(parents=True)
    # Quoted name with embedded commas that broke legacy naive split(",")!
    csv_text = (
        "source,name,latitude,longitude,row,col,in_footprint,dist_known_fault_px,"
        "temp_c,depth_m,ph,tds_ppm,sio2_ppm,na_ppm,k_ppm,ca_ppm,mg_ppm,cl_ppm,so4_ppm,"
        "hco3_ppm,li_ppm,b_ppm,f_ppm,geothermquartz_c,geothermchalc_c,geothermcat_c\n"
        'nbmg,"Dixie Valley, Well 42-A, North",39.5,-118.0,25,30,1,0.0,'
        "45.0,100,7.2,500,120,80,10,20,5,100,50,200,1,1,1,165.0,140.0,150.0\n"
    )
    (ext / "gdr_wellspring_in_footprint.csv").write_text(csv_text, encoding="utf-8")
    fp = np.ones((50, 60), dtype=bool)
    out, stats = _build_anisotropic_gdr_geotherm(tmp_path, fp)
    assert stats["gdr_thermal_sites_used"] == 1
    assert float(out[25, 30]) > 0.60
    assert float(out[0, 0]) == 0.0


def test_submodular_dti_emit_beats_clumped_topk_on_wide_ridge() -> None:
    H, W = 60, 60
    allowed = np.ones((H, W), dtype=bool)
    # True fault centerline at col 30, surrounded by a 3-px wide smooth probability ridge
    gt = np.zeros((H, W), dtype=bool)
    gt[10:50, 30] = True

    prob = np.zeros((H, W), dtype=np.float32)
    for r in range(10, 50):
        # Slight intensity gradient along strike so naive top-K dumps all 18 dots into rows 10..15!
        along_boost = 0.12 if r < 18 else 0.0
        for c in range(28, 33):
            prob[r, c] = np.float32((0.42 + along_boost) * np.exp(-0.5 * ((c - 30) / 1.8) ** 2))

    # Budget of 18 dots: naive top-K wastes all 18 dots clumped along col 30 adjacent pixels,
    # whereas submodular spaces them ~2-3 px apart to cover the entire 40-px fault trace!
    n_budget = 14
    sub_pred = submodular_dti_emit(
        prob, allowed, footprint=allowed, n_dots=n_budget, dstar_ref=0.22
    )
    flat_order = np.argsort(prob.ravel())[::-1][:n_budget]
    topk_pred = np.zeros((H, W), dtype=np.float32)
    topk_pred.ravel()[flat_order] = 1.0

    score_sub = dti_score_fast(sub_pred > 0.5, gt)["dti"]
    score_topk = dti_score_fast(topk_pred > 0.5, gt)["dti"]
    assert int((sub_pred > 0.5).sum()) == n_budget
    assert score_sub > score_topk + 0.10


def test_submodular_dti_emit_rejects_flat_2d_blob_interior() -> None:
    H, W = 80, 80
    fp = np.ones((H, W), dtype=bool)
    prob = np.zeros((H, W), dtype=np.float32)
    # Broad flat 2D caldera/basin plateau (rows 20..60, cols 20..60) = 1,600 px
    prob[20:60, 20:60] = 0.75
    pred = submodular_dti_emit(prob, fp, footprint=fp, n_dots=100, dstar_ref=0.22)
    # Deep flat interior (rows 28..52, cols 28..52) has zero curvature and must NOT be lattice-tiled!
    assert int((pred[28:52, 28:52] > 0.5).sum()) == 0


def test_helpers_finite() -> None:
    fp = np.ones((32, 32), dtype=bool)
    arr = np.ones((32, 32), dtype=np.float32)
    arr[0, 0] = -3.4028235e38
    fp[0, 0] = False
    clean = fill_nearest_valid(arr, fp)
    assert np.isfinite(clean).all()
    h = hessian_curvilinear_response(clean, sigma=1.5)
    c2, s2, coh = structure_double_angle(clean)
    assert np.isfinite(h).all()
    assert np.isfinite(c2).all() and np.isfinite(s2).all() and np.isfinite(coh).all()
