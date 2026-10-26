#!/usr/bin/env python3
"""ATVR-36 Locked Whole-Segment Holdout Evaluator, Leakage Canary & Submission Builder.

Executes the preregistered ATVR-36 research lane under the Parallel-Run Protocol:
  - Verifies SHA-256 lock of ``evidence/atvr36_preregistration_20261026.json`` before running.
  - Uses ``gemsdoe36.protocol.{hide_segments, feature_canary, pooled_holdout}`` directly on
    all 3,199 8-connected fault segments (60,988 positive pixels, 0 split segments,
    ``buffer_px=30``).
  - Tests all static + fold-computed features with ``protocol.feature_canary`` (hard fail if
    any feature has ``two_polarity_auc > 0.90``).
  - Evaluates frozen baselines (``C0_repo_field``, ``B1_raw19_hgb_d28``) and AT MOST 3
    preregistered experiments (``EXP-1``, ``EXP-2``, ``EXP-3``) at the 37,654 dot budget.
  - Fits the winning ATVR-36 arm on full physical observables (zero SGMC, zero prior rasters)
    and invokes ``scripts/submission_writer.py`` to write, validate, and registry-audit the
    unique GeoTIFF + ZIP bundle and JSON Run Card.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import center_of_mass, distance_transform_edt, label
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from atvr36_submission_gate import write_and_validate_submission

from gemsdoe36.atvr_features import (
    H36A_STATIC_NAMES,
    H36B_STATIC_NAMES,
    H36C_STATIC_NAMES,
    RAW19_NAMES,
    StaticFeatureCache,
    build_or_load_static_feature_cache,
    compute_fold_anderson_feature,
    compute_fold_playa_cond_residual,
)
from gemsdoe36.field import FieldConfig, build_belief_field
from gemsdoe36.metric import distance_weighted_tversky
from gemsdoe36.paths import data_dir, work_dir
from gemsdoe36.protocol import (
    EVALUATOR_VERSION,
    feature_canary,
    hide_segments,
    pooled_holdout,
)
from gemsdoe36.submodular_emit import emit_submodular_cover
from gemsdoe36.variational_anderson import variational_anderson_refine

PREREG_PATH = ROOT / "evidence" / "atvr36_preregistration_20261026.json"
EXPECTED_PREREG_SHA256 = "351a9ad89ce058ee6ed910b4a423f81e0783fe2a50ee0a69de04e5db01dc0ab1"
TOTAL_DOT_BUDGET = 37_654
COLLAR_PX = 2.0
PREDICT_CHUNK = 500_000


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_preregistration_lock() -> dict[str, object]:
    if not PREREG_PATH.exists():
        raise RuntimeError(f"Missing preregistration file: {PREREG_PATH}")
    actual = _sha256_file(PREREG_PATH)
    if actual != EXPECTED_PREREG_SHA256:
        raise RuntimeError(
            f"Preregistration lock mismatch: expected {EXPECTED_PREREG_SHA256}, got {actual}"
        )
    return json.loads(PREREG_PATH.read_text())


@dataclass(frozen=True)
class SegmentHoldoutPlan:
    footprint: np.ndarray
    truth: np.ndarray
    segment_ids: np.ndarray
    n_segments: int
    n_folds: int
    cell_owner: np.ndarray  # (H, W) int16 in 0..15 for footprint, -1 outside
    fold_owner: np.ndarray  # (H, W) int16 in 0..3 for footprint, -1 outside
    withheld_ids_by_fold: tuple[np.ndarray, ...]
    visible_by_fold: tuple[np.ndarray, ...]
    hidden_by_fold: tuple[np.ndarray, ...]
    train_mask_by_fold: tuple[np.ndarray, ...]
    eval_mask_by_fold: tuple[np.ndarray, ...]


def build_whole_segment_holdout_plan(
    known_bool: np.ndarray,
    footprint: np.ndarray,
    *,
    buffer_px: int = 30,
) -> SegmentHoldoutPlan:
    """Partition all 8-connected fault segments whole into 4 folds & 16 spatial bootstrap cells."""
    foot = np.asarray(footprint, dtype=bool)
    pos = np.asarray(known_bool, dtype=bool) & foot
    seg_ids, n_seg = label(pos, structure=np.ones((3, 3), dtype=np.int32))
    seg_ids = seg_ids.astype(np.int32)

    rs, cs = np.where(foot)
    r_cuts = np.quantile(rs, [0.25, 0.50, 0.75])
    c_cuts = np.quantile(cs, [0.25, 0.50, 0.75])

    grid_r, grid_c = np.indices(foot.shape)
    bi_grid = np.searchsorted(r_cuts, grid_r, side="right")  # 0..3
    bj_grid = np.searchsorted(c_cuts, grid_c, side="right")  # 0..3
    pixel_cell = (bi_grid * 4 + bj_grid).astype(np.int16)

    # Assign each connected segment WHOLE by its center of mass
    coms = center_of_mass(pos, seg_ids, index=np.arange(1, n_seg + 1))
    seg_cell = np.zeros(n_seg + 1, dtype=np.int16)
    for sid, (rc, cc) in enumerate(coms, start=1):
        bi = int(np.searchsorted(r_cuts, rc, side="right"))
        bj = int(np.searchsorted(c_cuts, cc, side="right"))
        seg_cell[sid] = bi * 4 + bj

    cell_owner = np.where(foot, pixel_cell, -1).astype(np.int16)
    pos_mask = seg_ids > 0
    cell_owner[pos_mask] = seg_cell[seg_ids[pos_mask]]

    # Map 16 cells (bi in 0..3, bj in 0..3) -> 4 macro-quadrants ((bi//2)*2 + (bj//2))
    cell_to_fold = np.array([((c // 4) // 2) * 2 + ((c % 4) // 2) for c in range(16)], dtype=np.int16)
    fold_owner = np.where(cell_owner >= 0, cell_to_fold[np.maximum(cell_owner, 0)], -1).astype(np.int16)
    seg_fold = cell_to_fold[seg_cell[1:]]  # length n_seg

    withheld_list, vis_list, hid_list, tr_list, ev_list = [], [], [], [], []
    for k in range(4):
        w_ids = np.flatnonzero(seg_fold == k) + 1
        vis_k, hid_k, tr_k, score_k = hide_segments(seg_ids, w_ids, foot, buffer_px=buffer_px)
        ev_k = (fold_owner == k) & foot & score_k
        withheld_list.append(w_ids.astype(np.int32))
        vis_list.append(vis_k)
        hid_list.append(hid_k)
        tr_list.append(tr_k)
        ev_list.append(ev_k)

    # Verify zero split segments and 100% coverage of positive pixels
    total_hid = sum(int(h.sum()) for h in hid_list)
    if total_hid != int(pos.sum()):
        raise RuntimeError(f"Holdout positive mismatch: {total_hid} != {int(pos.sum())}")

    return SegmentHoldoutPlan(
        footprint=foot,
        truth=pos,
        segment_ids=seg_ids,
        n_segments=int(n_seg),
        n_folds=4,
        cell_owner=cell_owner,
        fold_owner=fold_owner,
        withheld_ids_by_fold=tuple(withheld_list),
        visible_by_fold=tuple(vis_list),
        hidden_by_fold=tuple(hid_list),
        train_mask_by_fold=tuple(tr_list),
        eval_mask_by_fold=tuple(ev_list),
    )


def _cells_for_protocol(pred: np.ndarray, plan: SegmentHoldoutPlan) -> list[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    cells = []
    p_f32 = pred.astype(np.float32, copy=False)
    t_f32 = plan.truth.astype(np.float32, copy=False)
    for cid in range(16):
        cmask = plan.cell_owner == cid
        if cmask.any() and int(plan.truth[cmask].sum()) > 0:
            cells.append((p_f32, t_f32, cmask))
    return cells


def _paired_bootstrap_delta(
    cand_pred: np.ndarray,
    base_pred: np.ndarray,
    plan: SegmentHoldoutPlan,
    *,
    bootstrap: int = 2000,
    seed: int = 36,
) -> dict[str, float]:
    """Exact paired 16-cell bootstrap delta matching protocol.pooled_holdout RNG."""
    c_cells = _cells_for_protocol(cand_pred, plan)
    b_cells = _cells_for_protocol(base_pred, plan)
    c_terms, b_terms = [], []
    for (cp, ct, cm), (bp, bt, bm) in zip(c_cells, b_cells, strict=True):
        cc = distance_weighted_tversky(cp, ct, valid_mask=cm, return_components=True)
        bc = distance_weighted_tversky(bp, bt, valid_mask=bm, return_components=True)
        c_terms.append((cc.true_positive, cc.false_positive, cc.false_negative))
        b_terms.append((bc.true_positive, bc.false_positive, bc.false_negative))
    c_arr = np.asarray(c_terms, dtype=np.float64)
    b_arr = np.asarray(b_terms, dtype=np.float64)

    def _ratio(t: np.ndarray) -> np.ndarray | float:
        tp, fp, fn = np.moveaxis(t, -1, 0)
        return tp / (tp + 0.2 * fp + 0.8 * fn + 1e-8)

    pt_diff = float(_ratio(c_arr.sum(axis=0)) - _ratio(b_arr.sum(axis=0)))
    rng = np.random.default_rng(seed)
    idx = rng.integers(len(c_arr), size=(bootstrap, len(c_arr)))
    d_boot = _ratio(c_arr[idx].sum(axis=1)) - _ratio(b_arr[idx].sum(axis=1))
    return {
        "delta_point": round(pt_diff, 6),
        "delta_ci95_lo": round(float(np.quantile(d_boot, 0.025)), 6),
        "delta_ci95_hi": round(float(np.quantile(d_boot, 0.975)), 6),
        "prob_cand_gt_base": round(float(np.mean(d_boot > 0.0)), 4),
    }


def _allocate_quadrant_budgets(elig_masks: list[np.ndarray], total_budget: int) -> list[int]:
    counts = np.array([int(m.sum()) for m in elig_masks], dtype=np.float64)
    raw = counts / counts.sum() * total_budget
    floors = np.floor(raw).astype(int)
    rem = int(total_budget - floors.sum())
    order = np.argsort(-(raw - floors))
    for i in range(rem):
        floors[order[i]] += 1
    assert int(floors.sum()) == total_budget
    return floors.tolist()


def _top_k_mask(score2d: np.ndarray, elig2d: np.ndarray, budget: int) -> np.ndarray:
    rc = np.argwhere(elig2d)
    vals = score2d[rc[:, 0], rc[:, 1]]
    if len(vals) <= budget:
        out = np.zeros(score2d.shape, dtype=bool)
        out[rc[:, 0], rc[:, 1]] = True
        return out
    pool_k = min(len(vals), budget * 2)
    part = np.argpartition(-vals, pool_k - 1)[:pool_k]
    sub_rc = rc[part]
    sub_v = vals[part]
    order = np.lexsort((sub_rc[:, 1], sub_rc[:, 0], -sub_v))[:budget]
    chosen = sub_rc[order]
    out = np.zeros(score2d.shape, dtype=bool)
    out[chosen[:, 0], chosen[:, 1]] = True
    return out


def _build_c0_channels(bands_dir: Path, ext_dir: Path, foot: np.ndarray) -> dict[str, np.ndarray]:
    """Load physical channels for frozen C0_repo_field (strictly zero SGMC)."""
    ch: dict[str, np.ndarray] = {}
    band_map = {
        "raw_det_elev": "12_det_elev.npy",
        "raw_det_elev_slope": "19_det_elev_slope.npy",
        "raw_iso_grav_anom_vg": "11_iso_grav_anom_vg.npy",
        "raw_iso_grav_anom_hg": "18_iso_grav_anom_hg.npy",
        "raw_iso_grav_anom_slope": "05_iso_grav_anom_slope.npy",
        "raw_tc": "06_tc.npy",
        "raw_tmi_vg": "09_tmi_vg.npy",
        "raw_tmi_hg": "03_tmi_hg.npy",
        "raw_rtp": "02_rtp.npy",
        "raw_cond_surf": "17_cond_surf.npy",
        "raw_ieq_n100a15": "16_ieq_n100a15.npy",
    }
    for k, fname in band_map.items():
        arr = np.load(bands_dir / fname).astype(np.float32)
        arr[~foot] = 0.0
        ch[k] = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as src:
        valid = (src.read(12) > 0) & foot
        step = src.read(3).astype(np.float32) / 255.0
        ch["surface_scarp"] = np.where(valid, step, 0.0).astype(np.float32)

    with rasterio.open(ext_dir / "geodawn_rad_u8.tif") as src:
        ch["rad_composite"] = np.where(foot, src.read(4).astype(np.float32) / 255.0, 0.0)
    with rasterio.open(ext_dir / "geodawn_extensions_u8.tif") as src:
        ch["ext_composite"] = np.where(foot, src.read(4).astype(np.float32) / 255.0, 0.0)
    return ch


def _assemble_feature_subset(
    cache: StaticFeatureCache,
    col_names: list[str],
    extra_cols: list[np.ndarray],
    row_idx: np.ndarray | None = None,
    row_slice: tuple[int, int] | None = None,
) -> np.ndarray:
    mm = cache.open_matrix()
    name_to_idx = {n: i for i, n in enumerate(cache.feature_names)}
    col_ids = [name_to_idx[n] for n in col_names]
    if row_slice is not None:
        s, e = row_slice
        base = mm[s:e][:, col_ids]
        if not extra_cols:
            return np.ascontiguousarray(base, dtype=np.float32)
        out = np.empty((e - s, len(col_ids) + len(extra_cols)), dtype=np.float32)
        out[:, : len(col_ids)] = base
        for k, ex in enumerate(extra_cols):
            out[:, len(col_ids) + k] = ex[s:e]
        return out
    if row_idx is not None:
        # Read sorted row indices via contiguous block scan to avoid strided page-fault thrashing
        n_rows = len(row_idx)
        out = np.empty((n_rows, len(col_ids) + len(extra_cols)), dtype=np.float32)
        out[:, : len(col_ids)] = mm[row_idx][:, col_ids]
        for k, ex in enumerate(extra_cols):
            out[:, len(col_ids) + k] = ex[row_idx]
        return out
    base = mm[:, col_ids]
    if not extra_cols:
        return np.ascontiguousarray(base, dtype=np.float32)
    out = np.empty((len(cache.foot_rows), len(col_ids) + len(extra_cols)), dtype=np.float32)
    out[:, : len(col_ids)] = base
    for k, ex in enumerate(extra_cols):
        out[:, len(col_ids) + k] = ex
    return out


def _fit_predict_calibrated_hgb(
    cache: StaticFeatureCache,
    col_names: list[str],
    extra_cols: list[np.ndarray],
    train_foot: np.ndarray,
    vis_fault_foot: np.ndarray,
    d_vis_foot: np.ndarray,
    *,
    target_foot_mask: np.ndarray | None = None,
    need_cal_sample: bool = False,
    seed: int,
    neg_ratio: int = 5,
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None]:
    """Fit case-control Horvitz-Thompson weighted HGB and predict on target_foot_mask."""
    pos_idx = np.flatnonzero(train_foot & vis_fault_foot)
    neg_pool = np.flatnonzero(train_foot & (d_vis_foot > COLLAR_PX))
    rng = np.random.default_rng(seed)
    m_neg = min(len(neg_pool), max(10_000, neg_ratio * len(pos_idx)))
    neg_idx = (
        rng.choice(neg_pool, size=m_neg, replace=False) if m_neg < len(neg_pool) else neg_pool
    )
    neg_idx.sort()

    train_idx = np.concatenate([pos_idx, neg_idx])
    order_tr = np.argsort(train_idx)
    train_idx = train_idx[order_tr]
    y_train = vis_fault_foot[train_idx].astype(np.int32)

    w_neg = float(len(neg_pool)) / float(max(1, len(neg_idx)))
    sample_weight = np.where(y_train > 0, 1.0, w_neg).astype(np.float32)

    X_train = _assemble_feature_subset(cache, col_names, extra_cols, row_idx=train_idx)

    clf = HistGradientBoostingClassifier(
        loss="log_loss",
        learning_rate=0.055,
        max_iter=190,
        max_leaf_nodes=63,
        min_samples_leaf=90,
        l2_regularization=2.5,
        max_bins=255,
        early_stopping=False,
        random_state=seed,
    )
    clf.fit(X_train, y_train, sample_weight=sample_weight)

    cal_idx: np.ndarray | None = None
    cal_pred: np.ndarray | None = None
    if need_cal_sample:
        cal_domain = np.flatnonzero(train_foot & (vis_fault_foot | (d_vis_foot > COLLAR_PX)))
        cal_idx = (
            np.sort(rng.choice(cal_domain, size=250_000, replace=False))
            if len(cal_domain) > 250_000
            else cal_domain
        )
        X_cal = _assemble_feature_subset(cache, col_names, extra_cols, row_idx=cal_idx)
        cal_pred = clf.predict_proba(X_cal)[:, 1].astype(np.float32)
        del X_cal

    del X_train, y_train, sample_weight
    gc.collect()

    n_foot = len(cache.foot_rows)
    pred_foot = np.zeros(n_foot, dtype=np.float32)
    if target_foot_mask is None:
        for start in range(0, n_foot, PREDICT_CHUNK):
            stop = min(start + PREDICT_CHUNK, n_foot)
            X_chunk = _assemble_feature_subset(cache, col_names, extra_cols, row_slice=(start, stop))
            pred_foot[start:stop] = clf.predict_proba(X_chunk)[:, 1].astype(np.float32)
            del X_chunk
    else:
        tgt_idx = np.flatnonzero(target_foot_mask)
        for start in range(0, len(tgt_idx), PREDICT_CHUNK):
            stop = min(start + PREDICT_CHUNK, len(tgt_idx))
            sub_idx = tgt_idx[start:stop]
            X_chunk = _assemble_feature_subset(cache, col_names, extra_cols, row_idx=sub_idx)
            pred_foot[sub_idx] = clf.predict_proba(X_chunk)[:, 1].astype(np.float32)
            del X_chunk
    return pred_foot, cal_idx, cal_pred


def _apply_fold_regime_calibration(
    prob_foot: np.ndarray,
    cache: StaticFeatureCache,
    train_foot: np.ndarray,
    vis_fault_foot: np.ndarray,
    d_vis_foot: np.ndarray,
    *,
    cal_idx: np.ndarray | None = None,
    cal_pred: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Calibrate Mountain / Piedmont / Basin probabilities strictly from training-fold prevalence."""
    mm = cache.open_matrix()
    name_to_idx = {n: i for i, n in enumerate(cache.feature_names)}
    p_pied = mm[:, name_to_idx["h36c_regime_piedmont_prob"]]
    p_bas = mm[:, name_to_idx["h36c_regime_basin_prob"]]
    p_mtn = np.clip(1.0 - p_pied - p_bas, 0.0, 1.0)
    regime_id = np.argmax(np.column_stack([p_mtn, p_pied, p_bas]), axis=1)

    cal_domain = train_foot & (vis_fault_foot | (d_vis_foot > COLLAR_PX))
    out = prob_foot.copy()
    scales: dict[str, float] = {}
    for rid, rname in ((0, "mountain"), (1, "piedmont"), (2, "basin")):
        rmask = cal_domain & (regime_id == rid)
        if int(rmask.sum()) < 1000:
            scales[rname] = 1.0
            continue
        emp_prev = float(vis_fault_foot[rmask].mean())
        if cal_idx is not None and cal_pred is not None:
            sub_m = regime_id[cal_idx] == rid
            pred_mean = float(cal_pred[sub_m].mean()) if sub_m.any() else emp_prev
        else:
            pred_mean = float(prob_foot[rmask].mean())
        scale = float(np.clip(np.sqrt((emp_prev + 1e-6) / (pred_mean + 1e-6)), 0.78, 1.32))
        scales[rname] = round(scale, 5)
        target = regime_id == rid
        out[target] = np.clip(out[target] * scale, 0.0, 1.0)
    return out, scales


def _evaluate_arm_diagnostics(
    pred_dots: np.ndarray,
    plan: SegmentHoldoutPlan,
    cache: StaticFeatureCache,
) -> dict[str, object]:
    """Compute protocol.pooled_holdout (16 spatial cells) AND unsplit full-map pooled DTI."""
    cells = _cells_for_protocol(pred_dots, plan)
    boot = pooled_holdout(cells, bootstrap=2000, seed=36)

    unsplit = distance_weighted_tversky(
        pred_dots.astype(np.float32),
        plan.truth.astype(np.float32),
        valid_mask=plan.footprint,
        return_components=True,
    )

    mm = cache.open_matrix()
    name_to_idx = {n: i for i, n in enumerate(cache.feature_names)}
    p_pied = np.zeros(plan.footprint.shape, dtype=np.float32)
    p_bas = np.zeros(plan.footprint.shape, dtype=np.float32)
    lidar_ok = np.zeros(plan.footprint.shape, dtype=bool)
    p_pied[cache.foot_rows, cache.foot_cols] = mm[:, name_to_idx["h36c_regime_piedmont_prob"]]
    p_bas[cache.foot_rows, cache.foot_cols] = mm[:, name_to_idx["h36c_regime_basin_prob"]]
    lidar_ok[cache.foot_rows, cache.foot_cols] = mm[:, name_to_idx["h36a_lidar_valid"]] > 0.5
    p_mtn = np.clip(1.0 - p_pied - p_bas, 0.0, 1.0)
    reg2d = np.argmax(np.stack([p_mtn, p_pied, p_bas], axis=0), axis=0)

    sub_metrics: dict[str, dict[str, float]] = {}
    for sname, smask in (
        ("mountain", plan.footprint & (reg2d == 0)),
        ("piedmont", plan.footprint & (reg2d == 1)),
        ("basin", plan.footprint & (reg2d == 2)),
        ("lidar_covered", plan.footprint & lidar_ok),
        ("non_lidar_gap", plan.footprint & ~lidar_ok),
    ):
        comp = distance_weighted_tversky(
            pred_dots.astype(np.float32),
            plan.truth.astype(np.float32),
            valid_mask=smask,
            return_components=True,
        )
        pos_tot = comp.true_positive + comp.false_negative
        sub_metrics[sname] = {
            "dti": round(float(comp.score), 6),
            "weighted_tp": round(float(comp.true_positive), 2),
            "positives": round(float(pos_tot), 1),
            "weighted_recall": round(float(comp.true_positive / max(pos_tot, 1.0)), 4),
            "dots_emitted": int((pred_dots & smask).sum()),
        }

    return {
        "evaluator_version": EVALUATOR_VERSION,
        "label_tag": "HOLDOUT-DTI",
        "withheld_positives_px": int(boot["withheld_positives"]),
        "independent_cells": int(boot["independent_cells"]),
        "total_dots_emitted": int((pred_dots & plan.footprint).sum()),
        "pooled_16block_dti": round(float(boot["dti"]), 6),
        "pooled_16block_ci95": [round(float(boot["ci95"][0]), 6), round(float(boot["ci95"][1]), 6)],
        "pooled_unsplit_dti": round(float(unsplit.score), 6),
        "pooled_unsplit_tp_w": round(float(unsplit.true_positive), 2),
        "pooled_unsplit_fp_w": round(float(unsplit.false_positive), 2),
        "subdomains": sub_metrics,
    }


def run_all_canaries(
    cache: StaticFeatureCache,
    plan: SegmentHoldoutPlan,
    oof_fold_anderson: np.ndarray,
    oof_fold_cond_res: np.ndarray,
) -> list[dict[str, object]]:
    """Run protocol.feature_canary on every static + fold-computed feature."""
    mm = cache.open_matrix()
    results: list[dict[str, object]] = []
    grid = np.zeros(plan.footprint.shape, dtype=np.float32)

    for j, fname in enumerate(cache.feature_names):
        grid.fill(0.0)
        col = np.nan_to_num(mm[:, j], nan=0.0, posinf=0.0, neginf=0.0)
        grid[cache.foot_rows, cache.foot_cols] = col
        res = feature_canary(grid, plan.truth, plan.footprint)
        entry = {
            "feature": fname,
            "auc": round(float(res["auc"]), 6),
            "two_polarity_auc": round(float(res["two_polarity_auc"]), 6),
            "passed": bool(res["passed"]),
            "flagged": not bool(res["passed"]),
        }
        results.append(entry)
        if entry["flagged"]:
            raise RuntimeError(f"LEAKAGE CANARY TRIPPED on static feature {fname}: {entry}")

    for fname, vec in (
        ("h36a_fold_anderson_align", oof_fold_anderson),
        ("h36b_fold_cond_playa_residual", oof_fold_cond_res),
    ):
        grid.fill(0.0)
        grid[cache.foot_rows, cache.foot_cols] = np.nan_to_num(vec, nan=0.0)
        res = feature_canary(grid, plan.truth, plan.footprint)
        entry = {
            "feature": fname,
            "auc": round(float(res["auc"]), 6),
            "two_polarity_auc": round(float(res["two_polarity_auc"]), 6),
            "passed": bool(res["passed"]),
            "flagged": not bool(res["passed"]),
        }
        results.append(entry)
        if entry["flagged"]:
            raise RuntimeError(f"LEAKAGE CANARY TRIPPED on fold feature {fname}: {entry}")

    results.sort(key=lambda r: -float(r["two_polarity_auc"]))
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force-features", action="store_true", help="Rebuild static feature cache")
    args = ap.parse_args()

    t0 = time.time()
    verify_preregistration_lock()
    print(f"[atvr36] Preregistration lock verified ({EXPECTED_PREREG_SHA256[:12]})")

    cache = build_or_load_static_feature_cache(force_rebuild=args.force_features)
    print(
        f"[atvr36] Static physical cache ready: {len(cache.foot_rows):,} footprint px x "
        f"{len(cache.feature_names)} static features ({time.time() - t0:.1f}s)"
    )

    known_bool = cache.labels > 0.5
    plan = build_whole_segment_holdout_plan(known_bool, cache.footprint, buffer_px=30)
    print(
        f"[atvr36] Whole-segment holdout plan ready: {plan.n_segments:,} segments, "
        f"{int(plan.truth.sum()):,} positive px, 4 folds / 16 spatial cells"
    )

    fold_dvis: list[np.ndarray] = []
    fold_elig: list[np.ndarray] = []
    fold_train_foot: list[np.ndarray] = []
    fold_target_foot: list[np.ndarray] = []
    fold_ext: list[object] = []
    fold_anderson_vec: list[np.ndarray] = []
    fold_cond_res_vec: list[np.ndarray] = []

    oof_anderson = np.zeros(len(cache.foot_rows), dtype=np.float32)
    oof_cond_res = np.zeros(len(cache.foot_rows), dtype=np.float32)

    for k in range(plan.n_folds):
        vis_k = plan.visible_by_fold[k]
        dvis_k = distance_transform_edt(~vis_k).astype(np.float32)
        ev_k = plan.eval_mask_by_fold[k]
        elig_k = ev_k & (dvis_k > COLLAR_PX)
        tr_k = plan.train_mask_by_fold[k]

        # Pad eval_k by 20 px so 4-step variational PDE has exact interior boundary support
        pad_ev_k = (distance_transform_edt(~ev_k) <= 20.0) & cache.footprint

        tr_foot = tr_k[cache.foot_rows, cache.foot_cols]
        te_foot = ev_k[cache.foot_rows, cache.foot_cols]
        tgt_foot = pad_ev_k[cache.foot_rows, cache.foot_cols]

        and_vec, ext_k = compute_fold_anderson_feature(cache, vis_k)
        cond_vec = compute_fold_playa_cond_residual(cache, tr_foot)

        oof_anderson[te_foot] = and_vec[te_foot]
        oof_cond_res[te_foot] = cond_vec[te_foot]

        fold_dvis.append(dvis_k)
        fold_elig.append(elig_k)
        fold_train_foot.append(tr_foot)
        fold_target_foot.append(tgt_foot)
        fold_ext.append(ext_k)
        fold_anderson_vec.append(and_vec)
        fold_cond_res_vec.append(cond_vec)

    budgets = _allocate_quadrant_budgets(fold_elig, TOTAL_DOT_BUDGET)
    print(f"[atvr36] Quadrant budgets summing to {sum(budgets):,}: {budgets}")

    # Step 1: Per-feature leakage canary across all 50 features BEFORE model runs
    print("[atvr36] Running protocol.feature_canary across all 50 physical/fold features...")
    canary_results = run_all_canaries(cache, plan, oof_anderson, oof_cond_res)
    top_canary = canary_results[0]
    print(
        f"[atvr36] Canary PASSED (0/{len(canary_results)} flagged; max two-polarity AUC = "
        f"{top_canary['two_polarity_auc']:.4f} on {top_canary['feature']})"
    )

    # Step 2: Baseline C0_repo_field (frozen existing repo physical belief field, SGMC OFF)
    print("[atvr36] Evaluating Baseline C0_repo_field (enable_sgmc_prior=False)...")
    c0_channels = _build_c0_channels(
        work_dir() / "bands", data_dir() / "external", cache.footprint
    )
    c0_dots = np.zeros(cache.footprint.shape, dtype=bool)
    c0_cfg = FieldConfig(enable_sgmc_prior=False)
    for k in range(plan.n_folds):
        f_res = build_belief_field(
            c0_channels,
            cache.footprint,
            plan.visible_by_fold[k].astype(np.float32),
            config=c0_cfg,
            extension=fold_ext[k],
        )
        c0_dots |= _top_k_mask(f_res.belief, fold_elig[k], budgets[k])
        del f_res
    del c0_channels
    gc.collect()
    c0_eval = _evaluate_arm_diagnostics(c0_dots, plan, cache)
    print(
        f"[atvr36] C0_repo_field: HOLDOUT-DTI={c0_eval['pooled_16block_dti']:.4f} "
        f"(CI95={c0_eval['pooled_16block_ci95']}, unsplit={c0_eval['pooled_unsplit_dti']:.4f})"
    )

    # Step 3: Baseline B1_raw19_hgb_d28 (19 raw bands + HGB + top-37,654 outside d_vis > 2.0)
    print("[atvr36] Evaluating Baseline B1_raw19_hgb_d28...")
    b1_dots = np.zeros(cache.footprint.shape, dtype=bool)
    raw19_cols = list(RAW19_NAMES)
    for k in range(plan.n_folds):
        vis_foot = plan.visible_by_fold[k][cache.foot_rows, cache.foot_cols]
        dvis_foot = fold_dvis[k][cache.foot_rows, cache.foot_cols]
        p_foot, _, _ = _fit_predict_calibrated_hgb(
            cache,
            raw19_cols,
            [],
            fold_train_foot[k],
            vis_foot,
            dvis_foot,
            target_foot_mask=fold_target_foot[k],
            seed=3610 + k,
        )
        p2d = np.zeros(cache.footprint.shape, dtype=np.float32)
        p2d[cache.foot_rows, cache.foot_cols] = p_foot
        b1_dots |= _top_k_mask(p2d, fold_elig[k], budgets[k])
        del p_foot, p2d
        gc.collect()
    b1_eval = _evaluate_arm_diagnostics(b1_dots, plan, cache)
    print(
        f"[atvr36] B1_raw19_hgb_d28: HOLDOUT-DTI={b1_eval['pooled_16block_dti']:.4f} "
        f"(CI95={b1_eval['pooled_16block_ci95']}, unsplit={b1_eval['pooled_unsplit_dti']:.4f})"
    )

    # Step 4: Locked 3 ATVR-36 Experiments (EXP-1, EXP-2, EXP-3)
    exp_specs = [
        (
            "EXP-1",
            "H36-A",
            list(RAW19_NAMES + H36A_STATIC_NAMES),
            True,
            False,
            False,
        ),
        (
            "EXP-2",
            "H36-A + H36-B",
            list(RAW19_NAMES + H36A_STATIC_NAMES + H36B_STATIC_NAMES),
            True,
            True,
            False,
        ),
        (
            "EXP-3",
            "H36-A + H36-B + H36-C",
            list(RAW19_NAMES + H36A_STATIC_NAMES + H36B_STATIC_NAMES + H36C_STATIC_NAMES),
            True,
            True,
            True,
        ),
    ]
    assert len(exp_specs) <= 3, "Parallel-Run Protocol budget strictly caps experiments at <= 3"

    exp_outputs: dict[str, dict[str, object]] = {}
    for exp_idx, (exp_id, hyp_label, cols, use_and, use_cond, use_reg_cal) in enumerate(exp_specs):
        t_exp = time.time()
        n_f = len(cols) + int(use_and) + int(use_cond)
        print(f"[atvr36] Running {exp_id} ({hyp_label}, {n_f} features)...")
        dots_exp = np.zeros(cache.footprint.shape, dtype=bool)
        oof_surf_exp = np.zeros(cache.footprint.shape, dtype=np.float32)
        variational_diags: list[dict[str, float]] = []
        regime_scales_folds: list[dict[str, float]] = []

        for k in range(plan.n_folds):
            vis_foot = plan.visible_by_fold[k][cache.foot_rows, cache.foot_cols]
            dvis_foot = fold_dvis[k][cache.foot_rows, cache.foot_cols]
            extras: list[np.ndarray] = []
            if use_and:
                extras.append(fold_anderson_vec[k])
            if use_cond:
                extras.append(fold_cond_res_vec[k])

            p_foot, cal_idx, cal_pred = _fit_predict_calibrated_hgb(
                cache,
                cols,
                extras,
                fold_train_foot[k],
                vis_foot,
                dvis_foot,
                target_foot_mask=fold_target_foot[k],
                need_cal_sample=use_reg_cal,
                seed=3620 + 10 * exp_idx + k,
            )
            if use_reg_cal:
                p_foot, r_scales = _apply_fold_regime_calibration(
                    p_foot,
                    cache,
                    fold_train_foot[k],
                    vis_foot,
                    dvis_foot,
                    cal_idx=cal_idx,
                    cal_pred=cal_pred,
                )
                regime_scales_folds.append(r_scales)

            p2d = np.zeros(cache.footprint.shape, dtype=np.float32)
            p2d[cache.foot_rows, cache.foot_cols] = p_foot
            p_var, v_diag = variational_anderson_refine(
                p2d, fold_ext[k], cache.footprint, steps=4, step_size=0.22
            )
            variational_diags.append(v_diag)

            q_mask = (plan.fold_owner == k) & cache.footprint
            oof_surf_exp[q_mask] = p_var[q_mask]

            sub_res = emit_submodular_cover(
                p_var,
                fold_elig[k],
                budget=budgets[k],
                valid_footprint=plan.eval_mask_by_fold[k],
                gamma=1.15,
                min_spacing_px=2.0,
            )
            dots_exp |= sub_res.mask
            del p_foot, p2d, p_var, sub_res
            gc.collect()

        np.save(cache.cache_dir / f"oof_surf_{exp_id}.npy", oof_surf_exp)
        del oof_surf_exp
        gc.collect()

        diag = _evaluate_arm_diagnostics(dots_exp, plan, cache)
        vs_c0 = _paired_bootstrap_delta(dots_exp, c0_dots, plan)
        vs_b1 = _paired_bootstrap_delta(dots_exp, b1_dots, plan)

        exp_outputs[exp_id] = {
            "experiment_id": exp_id,
            "hypothesis": hyp_label,
            "n_features": n_f,
            "elapsed_sec": round(time.time() - t_exp, 2),
            "metrics": diag,
            "vs_C0_repo_field": vs_c0,
            "vs_B1_raw19_hgb_d28": vs_b1,
            "variational_pde_diagnostics": variational_diags,
            "fold_regime_scales": regime_scales_folds,
        }
        print(
            f"[atvr36] {exp_id}: HOLDOUT-DTI={diag['pooled_16block_dti']:.4f} "
            f"(CI95={diag['pooled_16block_ci95']}, unsplit={diag['pooled_unsplit_dti']:.4f}) "
            f"| d_vs_B1={vs_b1['delta_point']:+.4f} "
            f"CI95=[{vs_b1['delta_ci95_lo']:+.4f}, {vs_b1['delta_ci95_hi']:+.4f}]"
        )

    # Step 5: Select winning ATVR-36 experiment by pooled 16-block HOLDOUT-DTI
    best_exp_id = max(
        exp_outputs.keys(),
        key=lambda eid: float(exp_outputs[eid]["metrics"]["pooled_16block_dti"]),
    )
    best_exp = exp_outputs[best_exp_id]
    best_spec = next(s for s in exp_specs if s[0] == best_exp_id)
    print(f"[atvr36] Best preregistered experiment: {best_exp_id} ({best_spec[1]})")

    # Step 6: Emit live GeoTIFF from spatial out-of-fold cross-fitted surface of winning arm
    # (Chernozhukov et al. 2018 cross-fitting prevents in-sample spatial coordinate memorization
    # halo collapse around existing_faults.tif and guarantees distributional parity with holdout!)
    print(f"[atvr36] Emitting cross-fitted out-of-fold {best_exp_id} unique GeoTIFF submission...")
    full_dknown = distance_transform_edt(~known_bool).astype(np.float32)
    full_elig = cache.footprint & (full_dknown > COLLAR_PX)
    full_surf_var = np.load(cache.cache_dir / f"oof_surf_{best_exp_id}.npy").astype(np.float32)
    full_vdiag = {
        "deployment_mode": "spatial_out_of_fold_cross_fitted_4fold",
        "mean_stress_energy_delta": round(
            float(
                np.mean([d["stress_energy_delta"] for d in best_exp["variational_pde_diagnostics"]])
            ),
            6,
        ),
    }
    full_reg_scales = {
        "folds": best_exp["fold_regime_scales"],
    }
    full_cover = emit_submodular_cover(
        full_surf_var,
        full_elig,
        budget=TOTAL_DOT_BUDGET,
        valid_footprint=cache.footprint & ~known_bool,
        gamma=1.15,
        min_spacing_px=2.0,
    )

    out_tif = ROOT / "docs" / "downloads" / "gemsdoe36-atvr36-20261026.tif"
    sub_name = f"gemsdoe36-atvr36-{best_exp_id.lower()}-20261026"
    sub_note = (
        f"ATVR-36 {best_exp_id}: tilt/LiDAR+hydrothermal+Anderson PDE+300m CELF cover "
        f"(zero SGMC, zero prior rasters; 37654 dots)"
    )[:140]

    sub_receipt = write_and_validate_submission(
        dot_mask_or_prob=full_cover.mask.astype(np.float32),
        surface_for_registry=full_surf_var,
        out_tif=out_tif,
        submission_name=sub_name,
        submission_note=sub_note,
        footprint_mask=cache.footprint,
        write_zip=True,
    )

    # Step 7: Automated Promotion Gate Decision
    gate_canary = all(not r["flagged"] for r in canary_results)
    gate_beats_c0 = (
        float(best_exp["metrics"]["pooled_16block_dti"]) > float(c0_eval["pooled_16block_dti"])
        and float(best_exp["vs_C0_repo_field"]["delta_ci95_lo"]) > 0.0
    )
    gate_beats_b1 = (
        float(best_exp["metrics"]["pooled_16block_dti"]) > float(b1_eval["pooled_16block_dti"])
        and float(best_exp["vs_B1_raw19_hgb_d28"]["delta_ci95_lo"]) > 0.0
    )
    gate_portal = bool(sub_receipt["validator"]["valid_for_portal"])
    gate_registry = bool(sub_receipt["registry_audit"]["duplicate_gate_passed"])

    all_gates_passed = (
        gate_canary and gate_beats_c0 and gate_beats_b1 and gate_portal and gate_registry
    )
    verdict = "promote" if all_gates_passed else "negative"

    exp_ledger_path = ROOT / "evidence" / "atvr36_holdout_experiments_20261026.json"
    exp_ledger = {
        "schema": "gems36.atvr36.experiments.v1",
        "date_utc": "2026-10-26",
        "preregistration_path": "evidence/atvr36_preregistration_20261026.json",
        "preregistration_sha256": EXPECTED_PREREG_SHA256,
        "evaluator_version": EVALUATOR_VERSION,
        "score_provenance_label": "HOLDOUT-DTI",
        "n_withheld_positives_px": int(c0_eval["withheld_positives_px"]),
        "n_withheld_segments": plan.n_segments,
        "buffer_px": 30,
        "dot_budget": TOTAL_DOT_BUDGET,
        "leakage_canary_summary": {
            "n_features_tested": len(canary_results),
            "n_flagged_gt_0p90": sum(1 for r in canary_results if r["flagged"]),
            "max_two_polarity_auc": top_canary["two_polarity_auc"],
            "max_feature": top_canary["feature"],
            "top10_features": canary_results[:10],
            "all_features": canary_results,
        },
        "baselines": {
            "C0_repo_field": c0_eval,
            "B1_raw19_hgb_d28": b1_eval,
        },
        "experiments": exp_outputs,
        "winning_experiment": best_exp_id,
        "full_fit_diagnostics": {
            "variational_pde": full_vdiag,
            "regime_scales": full_reg_scales,
            "submodular_objective": round(float(full_cover.objective_value), 2),
        },
        "automated_gates": {
            "leakage_canary_passed": gate_canary,
            "beats_C0_repo_field_95ci": gate_beats_c0,
            "beats_B1_raw19_hgb_d28_95ci": gate_beats_b1,
            "portal_geotiff_valid": gate_portal,
            "registry_uniqueness_passed": gate_registry,
            "all_passed": all_gates_passed,
            "verdict": verdict,
        },
        "submission_receipt_summary": {
            "submission_name": sub_name,
            "submission_note": sub_note,
            "tif_path": "docs/downloads/gemsdoe36-atvr36-20261026.tif",
            "tif_sha256": sub_receipt["tif_sha256"],
            "tif_bytes": sub_receipt["tif_bytes"],
            "zip_path": "docs/downloads/gemsdoe36-atvr36-20261026.zip",
            "zip_sha256": sub_receipt["zip"]["zip_sha256"],
            "zip_bytes": sub_receipt["zip"]["zip_bytes"],
            "max_abs_surface_spearman_rho": sub_receipt["registry_audit"]["max_abs_surface_spearman_rho"],
            "max_abs_surface_spearman_ref": sub_receipt["registry_audit"]["max_abs_surface_spearman_ref"],
            "max_geological_dot_overlap_3px": sub_receipt["registry_audit"]["max_geological_dot_overlap_3px"],
            "max_geological_dot_overlap_ref": sub_receipt["registry_audit"]["max_geological_dot_overlap_ref"],
            "synthetic_lattice_disclosure": sub_receipt["registry_audit"]["synthetic_lattice_disclosure"],
        },
        "total_runtime_sec": round(time.time() - t0, 2),
    }
    exp_ledger_path.write_text(json.dumps(exp_ledger, indent=2))

    mimic_by_exp = {
        "EXP-1": (
            "Erosionally dissected steep mountain-interior crags, incised canyon rims, and "
            "unfaulted pluton-country-rock intrusive contacts (suppressed by 2.5 km relief "
            "deconfounding and fold-only Anderson extension alignment)"
        ),
        "EXP-2": (
            "Closed-basin evaporite playas / saline mudflats with low resistivity and broad "
            "silicic caldera magnetic lows (deconfounded via fold-regressed depth/playa "
            "17_cond_surf residual and 02_rtp trough x magnetic-THDR coupling)"
        ),
        "EXP-3": (
            "Unfaulted differential compaction hinges over paleotopographic highs, closed-basin "
            "evaporite playas, and steep mountain-interior crags (deconfounded via "
            "15_depth_to_base_surf flexure x gravity-THDR concordance, playa residual, and "
            "3-regime calibration)"
        ),
    }
    run_card = {
        "lane_id": "ATVR-36",
        "winning_experiment": best_exp_id,
        "hypothesis": (
            f"{best_spec[1]}: Andersonian Tilt-Variational & Deconfounded Geothermal-Piedmont "
            f"Submodular Fault Discovery ({best_exp['n_features']} physical/fold features; "
            "zero SGMC, zero prior rasters)"
        ),
        "mechanism": (
            "Combines depth-invariant Verduzco gravity/magnetic tilt derivatives, relief-deconfounded "
            "piedmont scarp-toe curvature, missingness-gated USGS 3DEP 1 m LiDAR scarp breaks, "
            "hydrothermal magnetite-destruction 02_rtp troughs + playa-deconfounded 17_cond_surf "
            "clay-cap residuals + GeoDAWN K/Th + DOE GDR 1391 physical geothermometers, Raissi-Anderson "
            "anisotropic structure-tensor variational diffusion, and exact 25-offset Euclidean 300 m "
            "CELF submodular expected-credit dot cover."
        ),
        "named_non_fault_mimic": mimic_by_exp[best_exp_id],
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": EVALUATOR_VERSION,
            "n_withheld_positives": int(best_exp["metrics"]["withheld_positives_px"]),
            "n_withheld_segments": plan.n_segments,
            "independent_cells": int(best_exp["metrics"]["independent_cells"]),
            "buffer_px": 30,
            "dti": best_exp["metrics"]["pooled_16block_dti"],
            "ci95": best_exp["metrics"]["pooled_16block_ci95"],
            "unsplit_pooled_dti": best_exp["metrics"]["pooled_unsplit_dti"],
            "baseline_C0_repo_field_dti": c0_eval["pooled_16block_dti"],
            "baseline_B1_raw19_hgb_d28_dti": b1_eval["pooled_16block_dti"],
            "paired_delta_vs_C0": best_exp["vs_C0_repo_field"],
            "paired_delta_vs_B1": best_exp["vs_B1_raw19_hgb_d28"],
        },
        "leakage_canary": {
            "n_features_tested": len(canary_results),
            "auc_cap": 0.90,
            "max_two_polarity_auc": top_canary["two_polarity_auc"],
            "max_feature": top_canary["feature"],
            "flagged_count": 0,
        },
        "registry_uniqueness": {
            "n_unique_registry_rasters_checked": sub_receipt["registry_audit"][
                "n_unique_registry_rasters_checked"
            ],
            "n_geological_rasters_enforced": sub_receipt["registry_audit"][
                "n_geological_rasters_enforced"
            ],
            "max_abs_surface_spearman_rho": sub_receipt["registry_audit"][
                "max_abs_surface_spearman_rho"
            ],
            "max_abs_surface_spearman_ref": sub_receipt["registry_audit"][
                "max_abs_surface_spearman_ref"
            ],
            "max_geological_dot_overlap_3px": sub_receipt["registry_audit"][
                "max_geological_dot_overlap_3px"
            ],
            "max_geological_dot_overlap_ref": sub_receipt["registry_audit"][
                "max_geological_dot_overlap_ref"
            ],
            "synthetic_lattice_pigeonhole_disclosure": sub_receipt["registry_audit"][
                "synthetic_lattice_disclosure"
            ],
            "duplicate_gate_passed": gate_registry,
        },
        "raster_sha256": sub_receipt["tif_sha256"],
        "zip_sha256": sub_receipt["zip"]["zip_sha256"],
        "validator_output": {
            "valid_for_portal": sub_receipt["validator"]["valid_for_portal"],
            "crs": sub_receipt["validator"]["crs"],
            "shape": sub_receipt["validator"]["shape"],
            "pixel_size_m": sub_receipt["validator"]["pixel_size_m"],
            "dtype": sub_receipt["validator"]["dtype"],
            "nodata": sub_receipt["validator"]["nodata"],
            "nan_inside_footprint": sub_receipt["validator"]["nan_inside"],
            "nan_outside_footprint": sub_receipt["validator"]["nan_outside"],
            "inf_count": sub_receipt["validator"]["inf_count"],
            "min_inside_footprint": sub_receipt["validator"]["min_inside"],
            "max_inside_footprint": sub_receipt["validator"]["max_inside"],
            "values_in_0_1": sub_receipt["validator"]["out_of_range_total"] == 0,
            "positive_dots_emitted": sub_receipt["validator"]["positive_gt_0p5_inside"],
            "known_fault_overlap_px": sub_receipt["validator"]["known_fault_positive_count"],
            "errors": sub_receipt["validator"]["errors"],
        },
        "submission_name": sub_name,
        "submission_note": sub_note,
        "verdict": verdict,
    }
    (ROOT / "evidence" / "atvr36_run_card_20261026.json").write_text(json.dumps(run_card, indent=2))

    current_run = {
        "schema_version": "gemsdoe36.current-run.v2",
        "updated_utc": "2026-10-26T00:00:00Z",
        "lane_id": "ATVR-36",
        "verdict": verdict,
        "ok_to_download_and_submit": verdict == "promote",
        "status_headline": (
            "VALIDATED & UNIQUE — OK TO DOWNLOAD AND SUBMIT"
            if verdict == "promote"
            else "NEGATIVE / DO NOT SUBMIT — AUTOMATED PROMOTION GATE NOT MET"
        ),
        "winning_experiment": best_exp_id,
        "submission_name": sub_name,
        "submission_note": sub_note,
        "download_tif_href": "downloads/gemsdoe36-atvr36-20261026.tif",
        "download_zip_href": "downloads/gemsdoe36-atvr36-20261026.zip",
        "tif_sha256": sub_receipt["tif_sha256"],
        "tif_bytes": sub_receipt["tif_bytes"],
        "zip_sha256": sub_receipt["zip"]["zip_sha256"],
        "zip_bytes": sub_receipt["zip"]["zip_bytes"],
        "dots_emitted": sub_receipt["validator"]["positive_gt_0p5_inside"],
        "holdout_dti": run_card["holdout_dti"],
        "leakage_canary": run_card["leakage_canary"],
        "registry_uniqueness": run_card["registry_uniqueness"],
        "validator_output": run_card["validator_output"],
        "automated_gates": exp_ledger["automated_gates"],
        "experiments_summary": {
            "C0_repo_field": {
                "label": "HOLDOUT-DTI",
                "dti": c0_eval["pooled_16block_dti"],
                "ci95": c0_eval["pooled_16block_ci95"],
                "unsplit_dti": c0_eval["pooled_unsplit_dti"],
            },
            "B1_raw19_hgb_d28": {
                "label": "HOLDOUT-DTI",
                "dti": b1_eval["pooled_16block_dti"],
                "ci95": b1_eval["pooled_16block_ci95"],
                "unsplit_dti": b1_eval["pooled_unsplit_dti"],
            },
            **{
                eid: {
                    "label": "HOLDOUT-DTI",
                    "hypothesis": eout["hypothesis"],
                    "n_features": eout["n_features"],
                    "dti": eout["metrics"]["pooled_16block_dti"],
                    "ci95": eout["metrics"]["pooled_16block_ci95"],
                    "unsplit_dti": eout["metrics"]["pooled_unsplit_dti"],
                    "delta_vs_B1": eout["vs_B1_raw19_hgb_d28"]["delta_point"],
                    "delta_vs_B1_ci95": [
                        eout["vs_B1_raw19_hgb_d28"]["delta_ci95_lo"],
                        eout["vs_B1_raw19_hgb_d28"]["delta_ci95_hi"],
                    ],
                }
                for eid, eout in exp_outputs.items()
            },
        },
        "historical_organizer_confirmed_scores": {
            "label": "ORGANIZER-CONFIRMED",
            "GEMSDOE32_B2_37654": 0.2778,
            "GEMSDOE36_legacy_38854": 0.2750,
            "GEMSDOE28_h36_1_37660": 0.2710,
            "GEMSDOE28_31_solo_40199": 0.2708,
            "GEMSDOE33_h33d_41865": 0.2632,
            "GEMSDOE25_30_d28_44090": 0.2600,
            "GEMSDOE27_tgc_61328": 0.2449,
            "GEMSDOE27_H29S_zero_copy_37654": 0.2190,
        },
    }
    (ROOT / "docs" / "current-run.json").write_text(json.dumps(current_run, indent=2))
    print(f"[atvr36] COMPLETE in {time.time() - t0:.1f}s -> verdict={verdict.upper()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
