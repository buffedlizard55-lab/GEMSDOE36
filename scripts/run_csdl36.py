#!/usr/bin/env python3
"""End-to-end execution of Preregistered Lane CSDL-36:
Cross-Strike Displaced-Lag Shear/Offset Coherence, Co-Signed Basement-Gravity Throw
Covariance, 3-D Euler Sheet Structural Index & Two-Regime Submodular Synthesis.

Protocol & Audit-Remediation Compliance (IR-GVSC36-01 .. IR-GVSC36-04):
1. Strict single-factor experimental ablation within the <= 3 experiment budget:
   - Control B0: 59 BASE_FEATURES + top-K emit_dots (identical control to GVSC-36).
   - EXP-1 (CSDL-Structural-75): 59 BASE + 16 CSDL_STRUCTURAL_FEATURES (zero hydrothermal
     conduit features) + stratified near/far negative sampling + Prentice-Pyke calibration
     + 8-azimuth OOF ridge sharpening + single-regime 300 m CELF submodular cover.
   - EXP-2 (CSDL-Conduit-87): 75 EXP-1 features + 12 mineralogically deconfounded
     CSDL_CONDUIT_FEATURES (fixing IR-GVSC36-02: zero det_elev shoreline threshold) under
     identical training and single-regime 300 m CELF submodular cover.
   - EXP-3 (CSDL-TwoRegime-Bridge-87): 87-feature M_full + 73-feature strictly LiDAR-blind
     M_blind (fixing IR-GVSC36-04: exact 87 - 14 = 73 count) + 3-tier relief-conditioned
     LiDAR-gap log-odds calibration + Two-Regime 300 m CELF submodular cover (74% primary
     ridge + 26% concealed subsurface/conduit regime).
2. Single-feature leakage canary across all 87 features (symmetric AUC <= 0.90).
3. Pre-placement surface rank-correlation screening (|rho| <= 0.90) executed and
   UTC-timestamped strictly BEFORE full-footprint dot placement (fixing IR-GVSC36-03).
4. Automated GeoTIFF validation ([0, 1] range, EPSG:32611, 3730x3292, template transform)
   and JSON run card with automatic promotion gate verdict.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", "2")

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.special import expit, logit
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems.holdout import SegmentHoldout  # noqa: E402
from gems.novelty import compare_registry  # noqa: E402
from gems.submission import check_variants, write_submission, zip_single  # noqa: E402
from gemsdoe36.csdl_features import (  # noqa: E402
    BASE_FEATURES,
    CSDL_CONDUIT_FEATURES,
    CSDL_STRUCTURAL_FEATURES,
    CSDL_SUBSURFACE_GATE_NAMES,
    CSDL_UPFLOW_GATE_NAMES,
    EXP1_FEATURES,
    EXP2_FEATURES,
    EXP3_BLIND_FEATURES,
    LIDAR_FEATURE_SET,
    FeatureStore,
    build_csdl_feature_store,
)
from gemsdoe36.h36_emission import emit_dots  # noqa: E402
from gemsdoe36.submission import sha256_file, validate_submission  # noqa: E402
from gemsdoe36.submodular_emit import emit_submodular_cover  # noqa: E402

LANE_ID = "CSDL-36"
TOTAL_BUDGET = 37_654

# Identical B0 control hyperparameters to GVSC-36 for exact apples-to-apples comparison
B0_SEED = 20261025
B0_N_POS = 50_000
B0_N_NEG = 300_000
B0_HGB = dict(
    max_iter=250,
    learning_rate=0.06,
    max_leaf_nodes=48,
    min_samples_leaf=200,
    l2_regularization=1.0,
    early_stopping=False,
)

CSDL_SEEDS = (20261026, 20261126)
CSDL_N_POS = 55_000  # Retains 100% of training positives in each 3-fold pool (~50,823)
CSDL_N_NEG = 320_000
CSDL_NEAR_NEG_SHARE = 0.22
CSDL_HGB = dict(
    max_iter=310,
    learning_rate=0.05,
    max_leaf_nodes=63,
    min_samples_leaf=240,
    l2_regularization=2.0,
    max_features=0.75,
    early_stopping=False,
)

RECORDED_REPO_B0 = 0.133749
RECORDED_PREV_REPO_BEST_GVSC36 = 0.158855
RECORDED_GROUP_BEST_GVC1 = 0.148763
RECORDED_GROUP_BEST_DPRF1 = 0.1637924

CACHE_DIR = ROOT / ".cache" / "csdl36_features"
PREREG_MD = ROOT / "docs" / "research" / "preregistration-csdl36-20261026.md"
PREREG_JSON = ROOT / "evidence" / "csdl36_preregistration_20261026.json"
CANARY_OUT = ROOT / "evidence" / "csdl36_canary_20261026.json"
HOLDOUT_OUT = ROOT / "evidence" / "csdl36_holdout_experiments_20261026.json"
CROSSCHECK_OUT = ROOT / "evidence" / "csdl36_crosscheck_20261026.json"
WALLTIME_OUT = ROOT / "evidence" / "csdl36_walltime_accounting_20261026.json"
RUN_CARD_OUT = ROOT / "evidence" / "csdl36_run_card_20261026.json"


def verify_preregistration_contract() -> dict[str, Any]:
    """Verify frozen preregistration file and exact feature counts before running."""
    if not PREREG_JSON.is_file() or not PREREG_MD.is_file():
        raise RuntimeError("Missing frozen preregistration files for CSDL-36")
    prereg = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    actual_md_sha = sha256_file(PREREG_MD)
    if prereg.get("markdown_spec_sha256") != actual_md_sha:
        raise RuntimeError(
            f"Preregistration markdown SHA-256 mismatch: "
            f"{prereg.get('markdown_spec_sha256')} != {actual_md_sha}"
        )
    fc = prereg["feature_counts"]
    assert fc["base"] == len(BASE_FEATURES) == 59
    assert fc["csdl_structural"] == len(CSDL_STRUCTURAL_FEATURES) == 16
    assert fc["csdl_conduit"] == len(CSDL_CONDUIT_FEATURES) == 12
    assert fc["exp1_total"] == len(EXP1_FEATURES) == 75
    assert fc["exp2_total"] == len(EXP2_FEATURES) == 87
    assert fc["lidar_features_removed"] == len(LIDAR_FEATURE_SET) == 14
    assert fc["exp3_blind_total"] == len(EXP3_BLIND_FEATURES) == 73
    return prereg


def load_labels(data_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(data_dir / "labels.tif") as src:
        lab = src.read(1)
    return lab >= 0, lab == 1


def fold_budgets(holdout: SegmentHoldout) -> list[int]:
    n_fp = int(holdout.footprint.sum())
    return [int(round(TOTAL_BUDGET * int(f["valid"].sum()) / n_fp)) for f in holdout.folds]


def prentice_pyke_calibrate(q: np.ndarray, pi_pos: float, pi_neg: float) -> np.ndarray:
    """Exact Bayes case-control inverse link mapping sampled posterior q(x) to population p(x)."""
    r = float(pi_pos / max(pi_neg, 1e-12))
    qc = np.clip(np.asarray(q, dtype=np.float64), 1e-7, 1.0 - 1e-7)
    p = qc / (qc + r * (1.0 - qc))
    return p.astype(np.float32)


def unfold_column(store: FeatureStore, name: str, fp: np.ndarray) -> np.ndarray:
    full = np.full(fp.size, np.nan, dtype=np.float32)
    full[np.flatnonzero(fp.ravel())] = np.asarray(store.column(name), dtype=np.float32)
    return full.reshape(fp.shape)


def sharpen_ridge_coherence(
    prob_2d: np.ndarray, valid_mask: np.ndarray, *, half_len_px: int = 4
) -> np.ndarray:
    """8-azimuth (900 m) directional ridge-coherence sharpening computed strictly inside valid_mask."""
    v = np.asarray(valid_mask, dtype=bool)
    if not v.any():
        return np.zeros(prob_2d.shape, dtype=np.float32)
    p_in = np.where(v & np.isfinite(prob_2d), np.clip(prob_2d, 0.0, 1.0), 0.0).astype(np.float32)

    h, w = p_in.shape
    pad = int(half_len_px)
    p_pad = np.pad(p_in, pad, mode="edge")
    t = np.arange(-half_len_px, half_len_px + 1, dtype=np.float64)
    inv_n = np.float32(1.0 / len(t))

    r_max = np.full((h, w), -np.inf, dtype=np.float32)
    r_sum = np.zeros((h, w), dtype=np.float32)
    for k in range(8):
        theta = k * (np.pi / 8.0)
        dys = np.rint(t * np.sin(theta)).astype(np.int32)
        dxs = np.rint(t * np.cos(theta)).astype(np.int32)
        acc = np.zeros((h, w), dtype=np.float32)
        for dy, dx in zip(dys.tolist(), dxs.tolist(), strict=True):
            acc += p_pad[pad + dy : pad + dy + h, pad + dx : pad + dx + w]
        resp = acc * inv_n
        np.maximum(r_max, resp, out=r_max)
        r_sum += resp
    r_mean = r_sum * np.float32(0.125)
    delta_r = np.maximum(r_max - r_mean, 0.0)
    p99 = max(float(np.percentile(delta_r[v], 99.0)), 1e-6)
    boost = np.clip(delta_r / np.float32(p99), 0.0, 1.5)
    out = np.where(v, np.clip(0.80 * p_in + 0.20 * p_in * boost, 0.0, 1.0), 0.0)
    return out.astype(np.float32)


def debiased_apron_surface(
    prob_2d: np.ndarray,
    valid_mask: np.ndarray,
    visible_faults: np.ndarray,
    *,
    near_lo_px: float = 2.0,
    near_hi_px: float = 9.0,
    far_ref_px: float = 12.0,
) -> np.ndarray:
    """Map near-catalogue (2-9 px) quantiles onto the out-of-fold far-field (>12 px) distribution."""
    out = np.asarray(prob_2d, dtype=np.float32).copy()
    vis = np.asarray(visible_faults, dtype=bool)
    val = np.asarray(valid_mask, dtype=bool)
    if not vis.any() or not val.any():
        return out
    d_vis = distance_transform_edt(~vis)
    near_mask = val & (~vis) & (d_vis > near_lo_px) & (d_vis <= near_hi_px)
    far_mask = val & (~vis) & (d_vis > far_ref_px)
    n_near = int(near_mask.sum())
    n_far = int(far_mask.sum())
    if n_near < 100 or n_far < 500:
        return out

    near_vals = out[near_mask]
    far_vals = out[far_mask]
    q_grid = np.linspace(0.0, 1.0, 2001, dtype=np.float64)
    far_q = np.quantile(far_vals.astype(np.float64), q_grid)
    order = np.argsort(near_vals, kind="mergesort")
    ranks = np.empty(n_near, dtype=np.float64)
    ranks[order] = np.linspace(0.0, 1.0, n_near, dtype=np.float64)
    mapped = np.interp(ranks, q_grid, far_q).astype(np.float32)
    out[near_mask] = np.minimum(near_vals, mapped)
    return out


def compute_regime_b_multiplier(
    store: FeatureStore,
    fp_pos: np.ndarray,
    train_mask: np.ndarray,
    visible_mask: np.ndarray,
    eval_mask: np.ndarray,
) -> np.ndarray:
    """Fit robust channel medians/IQRs strictly on training background rows and score Regime-B gate."""
    bg_flat = np.flatnonzero((train_mask & ~visible_mask).ravel())
    rng = np.random.default_rng(20261026)
    bg_sel = (
        rng.choice(bg_flat, size=min(40_000, len(bg_flat)), replace=False)
        if len(bg_flat) > 40_000
        else bg_flat
    )
    bg_idx = fp_pos[bg_sel]

    eval_flat = np.flatnonzero(eval_mask.ravel())
    eval_idx = fp_pos[eval_flat]
    n_eval = len(eval_flat)

    def _sig_channel(col_name: str) -> np.ndarray:
        col_all = np.asarray(store.column(col_name), dtype=np.float32)
        bg_vals = col_all[bg_idx]
        obs_bg = bg_vals[np.isfinite(bg_vals)]
        if len(obs_bg) >= 32:
            med = float(np.median(obs_bg))
            q25, q75 = np.percentile(obs_bg, [25.0, 75.0])
            iqr = max(float(q75 - q25), 1e-5)
        else:
            med, iqr = 0.0, 1.0
        ev_vals = col_all[eval_idx]
        obs_ev = np.isfinite(ev_vals)
        out = np.full(n_eval, 0.5, dtype=np.float32)
        if obs_ev.any():
            z = np.clip((ev_vals[obs_ev] - med) / iqr, -6.0, 6.0)
            out[obs_ev] = expit(z).astype(np.float32)
        return out

    b_sub = np.zeros(n_eval, dtype=np.float32)
    for nm in CSDL_SUBSURFACE_GATE_NAMES:
        b_sub += _sig_channel(nm)
    b_sub /= float(len(CSDL_SUBSURFACE_GATE_NAMES))

    h_up = np.zeros(n_eval, dtype=np.float32)
    for nm in CSDL_UPFLOW_GATE_NAMES:
        h_up += _sig_channel(nm)
    h_up /= float(len(CSDL_UPFLOW_GATE_NAMES))

    s_steep = _sig_channel("org_det_elev_slope")
    mult_1d = (0.30 + 0.70 * b_sub) * (0.30 + 0.70 * h_up) * (1.0 - 0.50 * s_steep)

    out_2d = np.zeros(eval_mask.size, dtype=np.float32)
    out_2d[eval_flat] = mult_1d.astype(np.float32)
    return out_2d.reshape(eval_mask.shape)


def emit_two_regime_submodular_cover(
    p_sharp_2d: np.ndarray,
    p_conduit_2d: np.ndarray,
    eligible_mask: np.ndarray,
    *,
    budget: int,
    valid_footprint: np.ndarray,
    primary_share: float = 0.74,
    min_spacing_px: float = 2.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Two-Regime 300 m CELF submodular cover:
    Stage A allocates primary_share on p_sharp_2d;
    Stage B allocates (1 - primary_share) on residual uncovered p_conduit_2d.
    """
    b_a = int(round(float(primary_share) * budget))
    b_a = max(0, min(budget, b_a))
    cov_a = emit_submodular_cover(
        p_sharp_2d,
        eligible_mask,
        budget=b_a,
        valid_footprint=valid_footprint,
        gamma=1.0,
        min_spacing_px=min_spacing_px,
    )
    n_a = int(cov_a.mask.sum())
    b_b = budget - n_a
    if b_b <= 0:
        return cov_a.mask, {
            "n_dots_primary": n_a,
            "n_dots_conduit": 0,
            "obj_primary": round(float(cov_a.objective_value), 2),
            "obj_conduit": 0.0,
        }

    d_a = distance_transform_edt(~cov_a.mask)
    rem_frac = np.clip(d_a / 3.0, 0.0, 1.0).astype(np.float32)
    p_stage_b = (p_conduit_2d * rem_frac).astype(np.float32)
    elig_b = eligible_mask & (~cov_a.mask) & (d_a > min_spacing_px)

    cov_b = emit_submodular_cover(
        p_stage_b,
        elig_b,
        budget=b_b,
        valid_footprint=valid_footprint,
        gamma=1.0,
        min_spacing_px=min_spacing_px,
    )
    combined = cov_a.mask | cov_b.mask
    return combined, {
        "n_dots_primary": n_a,
        "n_dots_conduit": int(cov_b.mask.sum()),
        "obj_primary": round(float(cov_a.objective_value), 2),
        "obj_conduit": round(float(cov_b.objective_value), 2),
    }


def fuse_relief_conditioned_lidar_bridge(
    p_full_2d: np.ndarray,
    p_blind_2d: np.ndarray,
    lid_valid_2d: np.ndarray,
    det_slope_2d: np.ndarray,
    det_elev_2d: np.ndarray,
    eval_mask: np.ndarray,
) -> np.ndarray:
    """3-tier relief-conditioned LiDAR-gap log-odds calibration + M_blind bridge."""
    has_lid = np.isfinite(lid_valid_2d) & (lid_valid_2d > 0.5)
    low_relief = np.nan_to_num(det_slope_2d, nan=0.0) < 4.0
    w_blind = np.where(~has_lid, 0.55, np.where(low_relief, 0.30, 0.15)).astype(np.float32)
    blended = (1.0 - w_blind) * p_full_2d + w_blind * p_blind_2d

    ev = np.asarray(eval_mask, dtype=bool)
    p_ev = np.clip(blended[ev], 1e-5, 1.0 - 1e-5)
    ell = logit(p_ev).astype(np.float32)
    hl_ev = has_lid[ev]

    if (~hl_ev).any() and hl_ev.any():
        slp_ev = np.nan_to_num(det_slope_2d[ev], nan=0.0)
        rel_ev = np.abs(np.nan_to_num(det_elev_2d[ev], nan=0.0))
        s_iqr = max(float(np.percentile(slp_ev, 75.0) - np.percentile(slp_ev, 25.0)), 1e-4)
        r_iqr = max(float(np.percentile(rel_ev, 75.0) - np.percentile(rel_ev, 25.0)), 1e-4)
        rscore = 0.5 * ((slp_ev - np.median(slp_ev)) / s_iqr) + 0.5 * (
            (rel_ev - np.median(rel_ev)) / r_iqr
        )
        t0, t1 = np.percentile(rscore, [33.33, 66.67])
        tiers = np.zeros(len(rscore), dtype=np.int8)
        tiers[rscore >= t0] = 1
        tiers[rscore >= t1] = 2

        for t in (0, 1, 2):
            m_l = hl_ev & (tiers == t)
            m_g = (~hl_ev) & (tiers == t)
            if int(m_l.sum()) >= 100 and int(m_g.sum()) >= 50:
                med_l = float(np.median(ell[m_l]))
                spr_l = max(float(np.percentile(ell[m_l], 99.0) - med_l), 0.25)
                med_g = float(np.median(ell[m_g]))
                spr_g = max(float(np.percentile(ell[m_g], 99.0) - med_g), 0.25)
                z_gap = (ell[m_g] - med_g) / spr_g
                ell[m_g] = 0.65 * ell[m_g] + 0.35 * (med_l + spr_l * z_gap)

    out = np.zeros_like(p_full_2d, dtype=np.float32)
    out[ev] = np.clip(expit(ell), 0.0, 1.0).astype(np.float32)
    return out


def train_predict_b0(
    store: FeatureStore,
    fp_pos: np.ndarray,
    fold: dict[str, Any],
    labels: np.ndarray,
    seed: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    rng = np.random.default_rng(seed)
    train = fold["train"]
    vis = fold["visible"]
    pos_flat = np.flatnonzero((labels & train).ravel())
    far = distance_transform_edt(~vis) > 3.0
    neg_flat = np.flatnonzero((train & ~labels & far).ravel())
    pos_sel = rng.choice(pos_flat, min(B0_N_POS, len(pos_flat)), replace=False)
    neg_sel = rng.choice(neg_flat, min(B0_N_NEG, len(neg_flat)), replace=False)
    idx = np.r_[fp_pos[pos_sel], fp_pos[neg_sel]]
    y = np.r_[np.ones(len(pos_sel), dtype=np.float32), np.zeros(len(neg_sel), dtype=np.float32)]
    names = list(BASE_FEATURES)
    X = store.rows(idx, names)
    clf = HistGradientBoostingClassifier(**B0_HGB, random_state=B0_SEED)
    clf.fit(X, y)
    del X

    valid_flat = np.flatnonzero(fold["valid"].ravel())
    score = np.zeros(fold["valid"].size, dtype=np.float32)
    for s in range(0, len(valid_flat), 450_000):
        chunk = valid_flat[s : s + 450_000]
        score[chunk] = clf.predict_proba(store.rows(fp_pos[chunk], names))[:, 1].astype(np.float32)
    del clf
    gc.collect()
    return score.reshape(fold["valid"].shape), {
        "n_pos_train": int(len(pos_sel)),
        "n_neg_train": int(len(neg_sel)),
    }


def train_predict_csdl_expert(
    store: FeatureStore,
    feature_names: tuple[str, ...],
    fp_pos: np.ndarray,
    train_mask: np.ndarray,
    visible_mask: np.ndarray,
    eval_mask: np.ndarray,
    labels: np.ndarray,
    fold_idx: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Train 2-seed regularized HGB ensemble with stratified near+far negatives + Prentice-Pyke calibration."""
    pos_pool = np.flatnonzero((labels & train_mask).ravel())
    d_vis = distance_transform_edt(~visible_mask)
    near_neg_pool = np.flatnonzero((train_mask & ~labels & (d_vis > 3.0) & (d_vis < 10.0)).ravel())
    far_neg_pool = np.flatnonzero((train_mask & ~labels & (d_vis >= 10.0)).ravel())
    total_neg_pool_len = len(near_neg_pool) + len(far_neg_pool)
    del d_vis

    names = list(feature_names)
    eval_flat = np.flatnonzero(eval_mask.ravel())
    prob_acc = np.zeros(len(eval_flat), dtype=np.float64)

    models: list[tuple[HistGradientBoostingClassifier, float, float]] = []
    pi_pos_last = 1.0
    pi_neg_last = 1.0
    n_pos_used = 0
    n_neg_used = 0
    n_near_used = 0
    for m_i, base_seed in enumerate(CSDL_SEEDS):
        rng = np.random.default_rng(base_seed + 17 * fold_idx + 101 * m_i)
        pos_sel = (
            pos_pool
            if len(pos_pool) <= CSDL_N_POS
            else rng.choice(pos_pool, CSDL_N_POS, replace=False)
        )
        n_near_target = int(round(CSDL_NEAR_NEG_SHARE * CSDL_N_NEG))
        take_near = min(len(near_neg_pool), n_near_target)
        take_far = min(len(far_neg_pool), CSDL_N_NEG - take_near)
        s_near = (
            rng.choice(near_neg_pool, take_near, replace=False)
            if len(near_neg_pool) > take_near
            else near_neg_pool
        )
        s_far = (
            rng.choice(far_neg_pool, take_far, replace=False)
            if len(far_neg_pool) > take_far
            else far_neg_pool
        )
        neg_sel = np.concatenate([s_near, s_far])

        pi_pos = float(len(pos_sel)) / float(max(len(pos_pool), 1))
        pi_neg = float(len(neg_sel)) / float(max(total_neg_pool_len, 1))
        pi_pos_last, pi_neg_last = pi_pos, pi_neg
        n_pos_used, n_neg_used, n_near_used = len(pos_sel), len(neg_sel), len(s_near)

        idx = np.r_[fp_pos[pos_sel], fp_pos[neg_sel]]
        y = np.r_[
            np.ones(len(pos_sel), dtype=np.float32),
            np.zeros(len(neg_sel), dtype=np.float32),
        ]
        X = store.rows(idx, names)
        clf = HistGradientBoostingClassifier(
            **CSDL_HGB, random_state=base_seed + 31 * fold_idx + m_i
        )
        clf.fit(X, y)
        models.append((clf, pi_pos, pi_neg))
        del X, y
        gc.collect()

    for s in range(0, len(eval_flat), 450_000):
        chunk = eval_flat[s : s + 450_000]
        X_chunk = store.rows(fp_pos[chunk], names)
        for clf, pi_pos, pi_neg in models:
            q_chunk = clf.predict_proba(X_chunk)[:, 1].astype(np.float32)
            p_chunk = prentice_pyke_calibrate(q_chunk, pi_pos=pi_pos, pi_neg=pi_neg)
            prob_acc[s : s + len(chunk)] += p_chunk.astype(np.float64)
        del X_chunk
    del models
    gc.collect()

    out = np.zeros(eval_mask.size, dtype=np.float32)
    out[eval_flat] = (prob_acc / float(len(CSDL_SEEDS))).astype(np.float32)
    return out.reshape(eval_mask.shape), {
        "n_pos_pool": int(len(pos_pool)),
        "n_neg_pool": int(total_neg_pool_len),
        "n_pos_train": int(n_pos_used),
        "n_neg_train": int(n_neg_used),
        "n_near_neg_train": int(n_near_used),
        "pi_pos": round(pi_pos_last, 6),
        "pi_neg": round(pi_neg_last, 6),
        "bayes_odds_ratio_r": round(pi_pos_last / max(pi_neg_last, 1e-12), 4),
    }


def run_canary_stage(
    store: FeatureStore,
    holdout: SegmentHoldout,
    fp: np.ndarray,
) -> dict[str, Any]:
    """Run single-feature holdout.canary on all 87 features (reuse verified 59 base features)."""
    if CANARY_OUT.is_file():
        existing = json.loads(CANARY_OUT.read_text(encoding="utf-8"))
        if existing.get("passed") and existing.get("total_features_tested") == 87:
            print(
                f"[canary] Restored verified 87-feature canary from {CANARY_OUT.name}: "
                f"max_sym_auc={existing['max_symmetric_auc']:.4f} ({existing['max_symmetric_auc_feature']})",
                flush=True,
            )
            return existing
    t0 = time.time()
    h, w = fp.shape
    flat_fp = np.flatnonzero(fp.ravel())

    features_report: dict[str, Any] = {}
    base_canary_path = ROOT / "evidence" / "gvsc36_canary_20261026.json"
    cached_base: dict[str, Any] = {}
    if base_canary_path.is_file():
        prev = json.loads(base_canary_path.read_text(encoding="utf-8"))
        cached_base = prev.get("features", {})

    to_compute = [
        n
        for n in EXP2_FEATURES
        if (n not in cached_base)
        or (n in CSDL_STRUCTURAL_FEATURES)
        or (n in CSDL_CONDUIT_FEATURES)
    ]
    for n in BASE_FEATURES:
        if n in cached_base and n not in to_compute:
            features_report[n] = cached_base[n]

    batch: dict[str, np.ndarray] = {}
    ev_version = "gems-segment-pooled-v1"
    for idx, name in enumerate(to_compute, start=1):
        full = np.zeros(h * w, dtype=np.float32)
        col = np.asarray(store.column(name), dtype=np.float32)
        full[flat_fp] = np.nan_to_num(col, nan=0.0)
        batch[name] = full.reshape(h, w)
        if len(batch) == 8 or idx == len(to_compute):
            res = holdout.canary(batch)
            ev_version = str(res.get("evaluator_version", ev_version))
            features_report.update(res["features"])
            print(
                f"[canary] checked {idx}/{len(to_compute)} new CSDL features "
                f"(batch passed={res['passed']})",
                flush=True,
            )
            batch.clear()
            gc.collect()

    max_sym_auc = 0.5
    max_feat = ""
    any_flagged = False
    for fname, info in features_report.items():
        p_auc = float(info["pooled_auc"])
        s_auc = max(p_auc, 1.0 - p_auc)
        for f_info in info["folds"]:
            f_auc = float(f_info["auc"])
            s_auc = max(s_auc, f_auc, 1.0 - f_auc)
        if s_auc > max_sym_auc:
            max_sym_auc = s_auc
            max_feat = fname
        if info.get("leakage_suspected", False) or s_auc > 0.90:
            any_flagged = True

    report = {
        "lane_id": LANE_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evaluator_version": ev_version,
        "total_features_tested": len(features_report),
        "newly_computed_features": len(to_compute),
        "reused_verified_base_features": len(features_report) - len(to_compute),
        "passed": (not any_flagged) and (max_sym_auc <= 0.90) and (len(features_report) == 87),
        "max_symmetric_auc": round(max_sym_auc, 6),
        "max_symmetric_auc_feature": max_feat,
        "elapsed_seconds": round(time.time() - t0, 2),
        "features": features_report,
    }
    CANARY_OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"[canary] PASS={report['passed']} | n={report['total_features_tested']} | "
        f"max_sym_auc={report['max_symmetric_auc']:.4f} ({max_feat}) | "
        f"{report['elapsed_seconds']}s",
        flush=True,
    )
    if not report["passed"]:
        raise RuntimeError(f"Leakage canary FAILED: max_sym_auc={max_sym_auc} on {max_feat}")
    return report


def run_holdout_stage(
    store: FeatureStore,
    holdout: SegmentHoldout,
    fp: np.ndarray,
    labels: np.ndarray,
    inv_stats: dict[str, Any],
) -> tuple[dict[str, Any], str, np.ndarray, np.ndarray]:
    """Execute frozen B0 + EXP-1 + EXP-2 + EXP-3 on SegmentHoldout."""
    t0 = time.time()
    h, w = fp.shape
    fp_pos = np.full(h * w, -1, dtype=np.int64)
    fp_pos[np.flatnonzero(fp.ravel())] = np.arange(store.n_fp, dtype=np.int64)
    budgets = fold_budgets(holdout)

    lid_valid_2d = unfold_column(store, "lid_valid", fp)
    det_slope_2d = unfold_column(store, "org_det_elev_slope", fp)
    det_elev_2d = unfold_column(store, "org_det_elev", fp)

    preds: dict[str, list[np.ndarray]] = {"B0": [], "EXP-1": [], "EXP-2": [], "EXP-3": []}
    oof_surfaces: dict[str, np.ndarray] = {
        "EXP-1": np.zeros((h, w), dtype=np.float32),
        "EXP-2": np.zeros((h, w), dtype=np.float32),
        "EXP-3": np.zeros((h, w), dtype=np.float32),
        "EXP-3-CONDUIT": np.zeros((h, w), dtype=np.float32),
    }
    fold_logs: list[dict[str, Any]] = []

    for f_i, fold in enumerate(holdout.folds):
        fname = fold["name"]
        ckpt_npz = CACHE_DIR / f"csdl_holdout_fold_{f_i}.npz"
        ckpt_json = CACHE_DIR / f"csdl_holdout_fold_{f_i}.json"
        if ckpt_npz.is_file() and ckpt_json.is_file():
            f_rec = json.loads(ckpt_json.read_text(encoding="utf-8"))
            with np.load(ckpt_npz) as z:
                for arm in ("B0", "EXP-1", "EXP-2", "EXP-3"):
                    preds[arm].append(z[f"pred_{arm}"])
                v_idx = fold["valid"]
                for arm in ("EXP-1", "EXP-2", "EXP-3", "EXP-3-CONDUIT"):
                    oof_surfaces[arm][v_idx] = z[f"surf_{arm}"]
            fold_logs.append(f_rec)
            print(
                f"[holdout] {fname} restored from checkpoint: "
                f"B0={f_rec['B0']['fold_dti']:.5f} EXP-1={f_rec['EXP-1']['fold_dti']:.5f} "
                f"EXP-2={f_rec['EXP-2']['fold_dti']:.5f} EXP-3={f_rec['EXP-3']['fold_dti']:.5f}",
                flush=True,
            )
            continue

        b_fold = budgets[f_i]
        d_vis = distance_transform_edt(~fold["visible"])
        elig = fold["valid"] & (d_vis > 2.0)
        f_rec: dict[str, Any] = {
            "fold": fname,
            "budget": b_fold,
            "valid_px": int(fold["valid"].sum()),
            "withheld_positive_px": int(fold["truth"].sum()),
        }

        # Control B0: 59 BASE_FEATURES + top-K emit_dots
        tb = time.time()
        s_b0, m_b0 = train_predict_b0(store, fp_pos, fold, labels, B0_SEED + f_i)
        d_b0 = emit_dots(s_b0, fold["valid"], b_fold)
        pred_b0_u8 = d_b0.astype(np.uint8)
        preds["B0"].append(pred_b0_u8)
        ref_b0, _ = holdout.score_fold(d_b0, fold)
        f_rec["B0"] = {
            **m_b0,
            "n_dots": int(d_b0.sum()),
            "fold_dti": round(float(ref_b0["dti"]), 6),
            "seconds": round(time.time() - tb, 1),
        }
        del s_b0, d_b0
        print(f"[holdout] {fname} B0: DTI={f_rec['B0']['fold_dti']:.5f}", flush=True)

        # EXP-1: 75 features (59 BASE + 16 CSDL_STRUCTURAL_FEATURES, zero hydrothermal conduit)
        t1 = time.time()
        p_raw1, m_exp1 = train_predict_csdl_expert(
            store, EXP1_FEATURES, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, f_i
        )
        p_exp1 = sharpen_ridge_coherence(p_raw1, fold["valid"], half_len_px=4)
        oof_surfaces["EXP-1"] += np.where(fold["valid"], p_exp1, 0.0)
        cov1 = emit_submodular_cover(
            p_exp1, elig, budget=b_fold, valid_footprint=fold["valid"], gamma=1.0, min_spacing_px=2.0
        )
        pred_1_u8 = cov1.mask.astype(np.uint8)
        preds["EXP-1"].append(pred_1_u8)
        ref_1, _ = holdout.score_fold(cov1.mask, fold)
        f_rec["EXP-1"] = {
            **m_exp1,
            "n_features": len(EXP1_FEATURES),
            "n_dots": int(cov1.mask.sum()),
            "expected_tp_obj": round(float(cov1.objective_value), 2),
            "fold_dti": round(float(ref_1["dti"]), 6),
            "seconds": round(time.time() - t1, 1),
        }
        surf_1_val = p_exp1[fold["valid"]].astype(np.float32)
        del p_raw1, p_exp1, cov1
        print(f"[holdout] {fname} EXP-1: DTI={f_rec['EXP-1']['fold_dti']:.5f}", flush=True)

        # EXP-2: 87 features (75 EXP-1 + 12 deconfounded CSDL_CONDUIT_FEATURES)
        t2 = time.time()
        p_raw2, m_exp2 = train_predict_csdl_expert(
            store, EXP2_FEATURES, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, f_i
        )
        p_exp2 = sharpen_ridge_coherence(p_raw2, fold["valid"], half_len_px=4)
        oof_surfaces["EXP-2"] += np.where(fold["valid"], p_exp2, 0.0)
        cov2 = emit_submodular_cover(
            p_exp2, elig, budget=b_fold, valid_footprint=fold["valid"], gamma=1.0, min_spacing_px=2.0
        )
        pred_2_u8 = cov2.mask.astype(np.uint8)
        preds["EXP-2"].append(pred_2_u8)
        ref_2, _ = holdout.score_fold(cov2.mask, fold)
        f_rec["EXP-2"] = {
            **m_exp2,
            "n_features": len(EXP2_FEATURES),
            "n_dots": int(cov2.mask.sum()),
            "expected_tp_obj": round(float(cov2.objective_value), 2),
            "fold_dti": round(float(ref_2["dti"]), 6),
            "seconds": round(time.time() - t2, 1),
        }
        surf_2_val = p_exp2[fold["valid"]].astype(np.float32)
        print(f"[holdout] {fname} EXP-2: DTI={f_rec['EXP-2']['fold_dti']:.5f}", flush=True)

        # EXP-3: 3-tier relief-conditioned LiDAR-gap bridge (M_full 87 + M_blind 73)
        # + Two-Regime 300 m CELF submodular allocation (74% primary ridge + 26% concealed conduit)
        t3 = time.time()
        p_blind_raw, m_blind = train_predict_csdl_expert(
            store,
            EXP3_BLIND_FEATURES,
            fp_pos,
            fold["train"],
            fold["visible"],
            fold["valid"],
            labels,
            f_i + 10,
        )
        p_fused = fuse_relief_conditioned_lidar_bridge(
            p_raw2,
            p_blind_raw,
            lid_valid_2d,
            det_slope_2d,
            det_elev_2d,
            fold["valid"],
        )
        p_exp3_sharp = sharpen_ridge_coherence(p_fused, fold["valid"], half_len_px=4)
        mult_b = compute_regime_b_multiplier(
            store, fp_pos, fold["train"], fold["visible"], fold["valid"]
        )
        p_exp3_conduit = (p_exp3_sharp * mult_b).astype(np.float32)

        oof_surfaces["EXP-3"] += np.where(fold["valid"], p_exp3_sharp, 0.0)
        oof_surfaces["EXP-3-CONDUIT"] += np.where(fold["valid"], p_exp3_conduit, 0.0)

        mask3, alloc_meta = emit_two_regime_submodular_cover(
            p_exp3_sharp,
            p_exp3_conduit,
            elig,
            budget=b_fold,
            valid_footprint=fold["valid"],
            primary_share=0.74,
            min_spacing_px=2.0,
        )
        pred_3_u8 = mask3.astype(np.uint8)
        preds["EXP-3"].append(pred_3_u8)
        ref_3, _ = holdout.score_fold(mask3, fold)
        f_rec["EXP-3"] = {
            "m_blind": m_blind,
            "n_features_full": len(EXP2_FEATURES),
            "n_features_blind": len(EXP3_BLIND_FEATURES),
            **alloc_meta,
            "n_dots": int(mask3.sum()),
            "fold_dti": round(float(ref_3["dti"]), 6),
            "seconds": round(time.time() - t3, 1),
        }
        surf_3_val = p_exp3_sharp[fold["valid"]].astype(np.float32)
        surf_3_cond_val = p_exp3_conduit[fold["valid"]].astype(np.float32)
        print(f"[holdout] {fname} EXP-3: DTI={f_rec['EXP-3']['fold_dti']:.5f}", flush=True)

        np.savez_compressed(
            ckpt_npz,
            **{
                "pred_B0": pred_b0_u8,
                "pred_EXP-1": pred_1_u8,
                "pred_EXP-2": pred_2_u8,
                "pred_EXP-3": pred_3_u8,
                "surf_EXP-1": surf_1_val,
                "surf_EXP-2": surf_2_val,
                "surf_EXP-3": surf_3_val,
                "surf_EXP-3-CONDUIT": surf_3_cond_val,
            },
        )
        ckpt_json.write_text(json.dumps(f_rec, indent=2) + "\n", encoding="utf-8")

        del (
            p_raw2,
            p_blind_raw,
            p_fused,
            p_exp2,
            p_exp3_sharp,
            p_exp3_conduit,
            mult_b,
            cov2,
            mask3,
            d_vis,
            elig,
            pred_b0_u8,
            pred_1_u8,
            pred_2_u8,
            pred_3_u8,
            surf_1_val,
            surf_2_val,
            surf_3_val,
            surf_3_cond_val,
        )
        gc.collect()
        fold_logs.append(f_rec)

    summaries = {arm: holdout.summarize(preds[arm], ci_draws=1999) for arm in preds}
    paired_vs_b0 = {
        arm: holdout.compare_paired(preds[arm], preds["B0"], ci_draws=1999)
        for arm in ("EXP-1", "EXP-2", "EXP-3")
    }
    paired_exp2_vs_exp1 = holdout.compare_paired(preds["EXP-2"], preds["EXP-1"], ci_draws=1999)
    paired_exp3_vs_exp2 = holdout.compare_paired(preds["EXP-3"], preds["EXP-2"], ci_draws=1999)

    best_arm = max(("EXP-1", "EXP-2", "EXP-3"), key=lambda a: float(summaries[a]["dti"]))
    np.save(CACHE_DIR / f"csdl_oof_surface_{best_arm}.npy", oof_surfaces[best_arm])

    for arm in ("B0", "EXP-1", "EXP-2", "EXP-3"):
        s = summaries[arm]
        print(
            f"[summary] {arm:5s}: HOLDOUT-DTI = {s['dti']:.6f} "
            f"95% CI [{s['ci95']['interval'][0]:.6f}, {s['ci95']['interval'][1]:.6f}] "
            f"TPw={s['TP_w']:.1f}",
            flush=True,
        )

    out = {
        "lane_id": LANE_ID,
        "label": "HOLDOUT-DTI",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration_path": str(PREREG_JSON.relative_to(ROOT)),
        "preregistration_sha256": sha256_file(PREREG_JSON),
        "evaluator": "gems.holdout.SegmentHoldout (byte-pinned template GEMSDOE24@fc2bc6f)",
        "evaluator_version": summaries["B0"]["evaluator_version"],
        "buffer_px": 15,
        "buffer_m": 1500.0,
        "withheld_positives": int(labels[fp].sum()),
        "total_components": int(holdout.n_components),
        "fold_budgets": budgets,
        "total_budget": int(sum(budgets)),
        "experiments_executed": 3,
        "elapsed_seconds": round(time.time() - t0, 2),
        "python": platform.python_version(),
        "geothermal_inventory": inv_stats,
        "feature_counts": {
            "base": len(BASE_FEATURES),
            "csdl_structural": len(CSDL_STRUCTURAL_FEATURES),
            "csdl_conduit": len(CSDL_CONDUIT_FEATURES),
            "exp1_total": len(EXP1_FEATURES),
            "exp2_total": len(EXP2_FEATURES),
            "lidar_features_removed": len(LIDAR_FEATURE_SET),
            "exp3_blind_total": len(EXP3_BLIND_FEATURES),
        },
        "recorded_benchmarks": {
            "repo_B0": RECORDED_REPO_B0,
            "prev_repo_best_GVSC36": RECORDED_PREV_REPO_BEST_GVSC36,
            "group_best_GEMSDOE24_GVC1": RECORDED_GROUP_BEST_GVC1,
            "group_best_GEMSDOE24_DPRF1": RECORDED_GROUP_BEST_DPRF1,
        },
        "best_candidate_arm": best_arm,
        "folds": fold_logs,
        "summaries": summaries,
        "paired_vs_B0": paired_vs_b0,
        "paired_EXP2_minus_EXP1_conduit_lift": paired_exp2_vs_exp1,
        "paired_EXP3_minus_EXP2_two_regime_bridge_lift": paired_exp3_vs_exp2,
    }
    HOLDOUT_OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out, best_arm, oof_surfaces[best_arm], oof_surfaces["EXP-3-CONDUIT"]


def build_registry_entries_with_local() -> list[dict[str, Any]]:
    """Use the pinned expanded registry plus every distinct prior local full-grid TIFF."""
    entries = json.loads(
        (ROOT / "registry" / "uniqueness_registry.json").read_text(encoding="utf-8")
    )["entries"]
    seen_sha = {e.get("file_sha256") for e in entries if e.get("file_sha256")}
    with rasterio.open(ROOT / "data/raw/sample_submission.tif") as src:
        footprint = np.isfinite(src.read(1))
    for tif_path in sorted((ROOT / "docs/downloads").glob("*.tif")):
        if (
            "FORMAT_TEST" in tif_path.name
            or "csdl36" in tif_path.name
            or tif_path.name.endswith("-nan.tif")
        ):
            continue
        full_sha = sha256_file(tif_path)
        if full_sha in seen_sha:
            continue
        with rasterio.open(tif_path) as src:
            if src.count != 1 or src.shape != footprint.shape:
                continue
            arr = src.read(1).astype("<f4", copy=False)
        fp_sha = hashlib.sha256(np.ascontiguousarray(arr[footprint]).tobytes()).hexdigest()
        entries.append(
            {
                "id": f"local-{tif_path.stem[:32]}",
                "file": f"GEMSDOE36/docs/downloads/{tif_path.name}",
                "cache_path": str(tif_path.relative_to(ROOT)),
                "footprint_sha256": fp_sha,
                "file_sha256": full_sha,
                "source": "local-prior-research",
                "site": "GEMSDOE36",
            }
        )
        seen_sha.add(full_sha)
    return entries


def run_deploy_stage(
    holdout_report: dict[str, Any],
    canary_report: dict[str, Any],
    best_arm: str,
    oof_best: np.ndarray,
    oof_conduit: np.ndarray,
    fp: np.ndarray,
    labels: np.ndarray,
    t_features: float,
    t_canary: float,
    t_holdout: float,
    t_pipeline_start: float,
) -> dict[str, Any]:
    vis_faults = labels & fp
    surface = debiased_apron_surface(oof_best, fp, vis_faults)
    conduit_surface = debiased_apron_surface(oof_conduit, fp, vis_faults)

    # Protocol §1 & IR-GVSC36-03: surface rank-correlation screen MUST happen before any dot placement.
    t_pre_surface_utc = datetime.now(timezone.utc).isoformat()
    entries = build_registry_entries_with_local()
    surf_nov = compare_registry(
        surface, fp, entries, ROOT, dots=None, separate_calibration_controls=True
    )
    max_surf_corr = float(surf_nov["max_abs_rank_correlation"] or 0.0)
    print(
        f"[deploy-pre-screen] {t_pre_surface_utc} | max_abs_rank_corr={max_surf_corr:.6f} "
        f"(passed={surf_nov['passed']}, entries={len(entries)})",
        flush=True,
    )
    if max_surf_corr > 0.90:
        raise RuntimeError("Pre-placement surface correlation exceeded 0.90; stop before emitting dots")

    # Dot placement starts strictly AFTER surface correlation gate passes
    t_emit_start_utc = datetime.now(timezone.utc).isoformat()
    d_cat = distance_transform_edt(~vis_faults)
    elig = fp & (d_cat > 2.0)

    if best_arm == "EXP-3":
        dots, deploy_alloc_meta = emit_two_regime_submodular_cover(
            surface,
            conduit_surface,
            elig,
            budget=TOTAL_BUDGET,
            valid_footprint=elig,
            primary_share=0.74,
            min_spacing_px=2.0,
        )
    else:
        cov = emit_submodular_cover(
            surface,
            elig,
            budget=TOTAL_BUDGET,
            valid_footprint=elig,
            gamma=1.0,
            min_spacing_px=2.0,
        )
        dots = cov.mask
        deploy_alloc_meta = {
            "n_dots_primary": int(dots.sum()),
            "n_dots_conduit": 0,
            "obj_primary": round(float(cov.objective_value), 2),
            "obj_conduit": 0.0,
        }
    t_emit_done_utc = datetime.now(timezone.utc).isoformat()

    d_dots = d_cat[dots]
    d_cat_stats = {
        "n_dots": int(dots.sum()),
        "min_d_cat_px": round(float(d_dots.min()), 3),
        "p10_d_cat_px": round(float(np.percentile(d_dots, 10)), 2),
        "median_d_cat_px": round(float(np.median(d_dots)), 2),
        "p90_d_cat_px": round(float(np.percentile(d_dots, 90)), 2),
        "share_le_2px": round(float((d_dots <= 2.0).mean()), 6),
        "share_le_5px": round(float((d_dots <= 5.0).mean()), 4),
    }
    print(f"[deploy] emitted {d_cat_stats['n_dots']} dots | d_cat={d_cat_stats}", flush=True)

    rc_bytes = np.argwhere(dots).astype(np.int32).tobytes()
    run_uid = hashlib.sha256(rc_bytes).hexdigest()[:12]
    stem = f"gemsdoe36-csdl36-{best_arm.lower().replace('-', '')}-20261026-{run_uid}-zeros"
    dl_dir = ROOT / "docs" / "downloads"
    dl_dir.mkdir(parents=True, exist_ok=True)
    for old_f in dl_dir.glob("gemsdoe36-csdl36-*"):
        old_f.unlink()

    tif_path = dl_dir / f"{stem}.tif"
    zip_path = dl_dir / f"{stem}.zip"
    tmpl_path = ROOT / "data" / "raw" / "sample_submission.tif"

    write_submission(dots.astype(np.float32), tmpl_path, tif_path, outside="zero")
    zip_single(tif_path, zip_path)
    write_info = {
        "path": str(tif_path.relative_to(ROOT)),
        "sha256": sha256_file(tif_path),
        "bytes": tif_path.stat().st_size,
    }
    zip_info = {
        "path": str(zip_path.relative_to(ROOT)),
        "sha256": sha256_file(zip_path),
        "bytes": zip_path.stat().st_size,
    }
    repo_val = validate_submission(
        tif_path, tmpl_path, require_nonfinite_outside=False
    ).to_dict()
    gems_val = check_variants(tif_path, tmpl_path)

    t_post_dots_utc = datetime.now(timezone.utc).isoformat()
    dots_comp = compare_registry(
        surface, fp, entries, ROOT, dots=dots, separate_calibration_controls=True
    )
    dots_literal = dots_comp

    focus_sites = tuple(f"GEMSDOE{n}/" for n in (24, 25, 27, 28, 30, 31, 32, 33, 36))
    focus_rows = [r for r in dots_comp["rows"] if any(site in r["file"] for site in focus_sites)]
    focus9_max_ov = max(
        (float(r["candidate_dot_overlap_within_3px"]) for r in focus_rows), default=0.0
    )
    b2_row = next(
        (r for r in dots_comp["rows"] if "gemsdoe32-h33-h33-2-b2-" in r["file"]), None
    )
    ov_vs_b2 = (
        float(b2_row["candidate_dot_overlap_within_3px"])
        if b2_row is not None
        else None
    )
    gvsc_row = next(
        (r for r in dots_comp["rows"] if "gvsc36" in r["file"]), None
    )
    ov_vs_gvsc = (
        float(gvsc_row["candidate_dot_overlap_within_3px"])
        if gvsc_row is not None
        else None
    )
    comp_rows = [r for r in dots_comp["rows"] if r["comparator_class"] == "competing_method"]
    top_competing = sorted(
        comp_rows,
        key=lambda r: float(r["candidate_dot_overlap_within_3px"] or 0.0),
        reverse=True,
    )[:15]
    top_corr = sorted(
        surf_nov["rows"],
        key=lambda r: max(abs(r["raw_spearman"] or 0.0), abs(r["kernel_spearman"] or 0.0)),
        reverse=True,
    )[:5]

    best_summary = holdout_report["summaries"][best_arm]
    paired_b0 = holdout_report["paired_vs_B0"][best_arm]
    dti_val = float(best_summary["dti"])

    g1_canary = bool(canary_report["passed"])
    g2_beats_b0 = (dti_val > RECORDED_REPO_B0) and (float(paired_b0["paired_delta_ci95"][0]) > 0.0)
    g2_beats_prev_repo_best = dti_val > RECORDED_PREV_REPO_BEST_GVSC36
    g2_beats_group_gvc1 = dti_val > RECORDED_GROUP_BEST_GVC1
    g2_beats_group_dprf1 = dti_val > RECORDED_GROUP_BEST_DPRF1
    g3_format = (
        bool(repo_val["passed"])
        and bool(gems_val["format_valid"])
        and bool(gems_val["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"])
        and d_cat_stats["share_le_2px"] == 0.0
    )
    g4_surf = bool(surf_nov["passed"]) and max_surf_corr <= 0.90
    g4_focus9 = focus9_max_ov <= 0.70
    g4_competing = bool(dots_comp["competing_method_passed"])
    g4_literal = bool(dots_literal["literal_unseparated_passed"])

    all_gates_pass = (
        g1_canary
        and g2_beats_b0
        and g2_beats_group_dprf1
        and g3_format
        and g4_surf
        and g4_competing
        and g4_literal
    )
    verdict = "promote" if all_gates_pass else "negative"
    status_tag = "PROMOTE" if verdict == "promote" else "NEGATIVE research only"
    emit_tag = "2reg" if best_arm == "EXP-3" else "submod300m"
    note = (
        f"GEMSDOE36 CSDL-36 {best_arm} | displaced-lag+throw-cov+{emit_tag} | "
        f"HOLDOUT-DTI {dti_val:.4f} | {status_tag} | {run_uid}"
    )
    if len(note) > 140:
        note = note[:140]

    crosscheck_doc = {
        "lane_id": LANE_ID,
        "best_arm": best_arm,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "total_registry_entries_checked": len(entries),
        "chronology_proof": {
            "pre_placement_surface_check_utc": t_pre_surface_utc,
            "dot_emission_started_utc": t_emit_start_utc,
            "dot_emission_completed_utc": t_emit_done_utc,
            "post_placement_dot_check_utc": t_post_dots_utc,
            "surface_checked_strictly_before_dot_placement": t_pre_surface_utc <= t_emit_start_utc,
        },
        "surface_before_placement": {
            "passed": g4_surf,
            "max_abs_rank_correlation": surf_nov["max_abs_rank_correlation"],
            "top_5_by_abs_corr": top_corr,
        },
        "final_dots_summary": {
            "focus_9_sites_max_overlap_3px": round(focus9_max_ov, 6),
            "focus_9_sites_rasters_compared": len(focus_rows),
            "focus_9_sites_passed": g4_focus9,
            "overlap_vs_GEMSDOE32_B2_3px": round(ov_vs_b2, 6) if ov_vs_b2 is not None else None,
            "overlap_vs_GVSC36_3px": round(ov_vs_gvsc, 6) if ov_vs_gvsc is not None else None,
            "max_competing_method_overlap_3px": dots_comp["max_competing_dot_overlap"],
            "competing_method_passed": g4_competing,
            "literal_all_entry_max_overlap_3px": dots_literal["max_dot_overlap"],
            "literal_all_entry_passed": g4_literal,
            "pigeonhole_bound_reg052_at_37654": round((37654 - 6649) / 37654, 6),
            "calibration_control_rasters": dots_comp["calibration_control_rasters"],
            "all_entry_count": dots_comp["registry_unique_rasters"],
        },
        "top_15_competing_by_overlap": top_competing,
    }
    CROSSCHECK_OUT.write_text(json.dumps(crosscheck_doc, indent=2) + "\n", encoding="utf-8")

    prereg_doc = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    elapsed_total = round(time.time() - t_pipeline_start, 2)
    if elapsed_total > 7200:
        raise RuntimeError("Registered two-hour walltime budget exceeded; stop without promotion")
    if holdout_report.get("experiments_executed") != 3:
        raise RuntimeError("Run card requires exactly the preregistered three candidate experiments")

    run_card = {
        "schema": "gems.parallel_run_card.v1",
        "lane_id": LANE_ID,
        "best_arm": best_arm,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "safe_to_download_for_research": bool(g3_format),
        "safe_to_submit_live_slot": verdict == "promote",
        "hypothesis": (
            "CSDL-36 (CSDL-36-A/B/C): Buried Basin-and-Range normal faults and oblique Walker "
            "Lane strike-slip relays offset magnetic/gravity horizons across +/-200-500 m "
            "cross-strike lags and +/-300 m along-strike shear lags, drop denser basement with "
            "opposite-signed gravity throw, satisfy thin-sheet 3-D Euler homogeneity (N~0.85), "
            "and focus convective hydrothermal upflow; reserving 26% of the 300 m submodular "
            "budget for low-slope concealed conduits prevents steep range fronts from starving "
            "SW Walker Lane and SE intrabasin step-overs."
        ),
        "mechanism": (
            "Combine 59 base channels with 16 CSDL structural channels (cross-strike RTP/gravity/"
            "basement steps at 200-500 m lag, +/-300 m along-strike shear offset coherence, "
            "co-signed ReLU(-Delta_perp D_base * Delta_perp g_iso) throw covariance, 3-D Euler "
            "sheet selectivity, 1 m LiDAR polarity worm, and relief-deconfounded piedmont break) "
            "plus 12 mineralogically deconfounded INGENIOUS hydrothermal conduit channels "
            "(fixing IR-GVSC36-02); train 2-seed HGB with 22% stratified near-apron negatives "
            "and Prentice-Pyke calibration; bridge the 24.63% LiDAR gap with a 73-feature "
            "LiDAR-blind expert and 3-tier relief-conditioned log-odds alignment; sharpen 8-azimuth "
            "ridge continuity; screen surface rank correlation strictly before placement "
            "(fixing IR-GVSC36-03); and allocate 37,654 dots via Two-Regime 300 m CELF submodular cover."
        ),
        "named_non_fault_mimic": (
            "Mesozoic pluton margins, Miocene diabase dike swarms, equidimensional volcanic plugs "
            "(Euler N>=2.0), Pleistocene Lake Lahontan shoreline tufa terraces, and steep "
            "un-faulted granitic range crests."
        ),
        "audit_remediations": prereg_doc["audit_remediations"],
        "feature_counts": prereg_doc["feature_counts"],
        "chronology_proof": crosscheck_doc["chronology_proof"],
        "deployment_allocation": deploy_alloc_meta,
        "preregistration": {
            "path": str(PREREG_JSON.relative_to(ROOT)),
            "sha256": sha256_file(PREREG_JSON),
            "markdown_path": "docs/research/preregistration-csdl36-20261026.md",
        },
        "experiment_budget": {
            "max_experiments_allowed": 3,
            "experiments_executed": 3,
            "max_walltime_seconds": 7200,
            "elapsed_walltime_seconds": elapsed_total,
        },
        "leakage_canary": {
            "passed": g1_canary,
            "threshold": 0.90,
            "total_features_tested": canary_report["total_features_tested"],
            "max_symmetric_auc": canary_report["max_symmetric_auc"],
            "max_symmetric_auc_feature": canary_report["max_symmetric_auc_feature"],
            "evidence_path": str(CANARY_OUT.relative_to(ROOT)),
        },
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator": "gems.holdout.SegmentHoldout",
            "evaluator_version": holdout_report["evaluator_version"],
            "withheld_positives": holdout_report["withheld_positives"],
            "total_components": holdout_report["total_components"],
            "buffer_m": 1500.0,
            "B0": {
                "dti": round(float(holdout_report["summaries"]["B0"]["dti"]), 6),
                "ci95": holdout_report["summaries"]["B0"]["ci95"]["interval"],
                "folds": {
                    r["fold"]: round(float(r["dti"]), 6)
                    for r in holdout_report["summaries"]["B0"]["folds"]
                },
            },
            "EXP-1": {
                "dti": round(float(holdout_report["summaries"]["EXP-1"]["dti"]), 6),
                "ci95": holdout_report["summaries"]["EXP-1"]["ci95"]["interval"],
                "folds": {
                    r["fold"]: round(float(r["dti"]), 6)
                    for r in holdout_report["summaries"]["EXP-1"]["folds"]
                },
                "paired_vs_B0": holdout_report["paired_vs_B0"]["EXP-1"],
            },
            "EXP-2": {
                "dti": round(float(holdout_report["summaries"]["EXP-2"]["dti"]), 6),
                "ci95": holdout_report["summaries"]["EXP-2"]["ci95"]["interval"],
                "folds": {
                    r["fold"]: round(float(r["dti"]), 6)
                    for r in holdout_report["summaries"]["EXP-2"]["folds"]
                },
                "paired_vs_B0": holdout_report["paired_vs_B0"]["EXP-2"],
                "paired_vs_EXP1_conduit_lift": holdout_report[
                    "paired_EXP2_minus_EXP1_conduit_lift"
                ],
            },
            "EXP-3": {
                "dti": round(float(holdout_report["summaries"]["EXP-3"]["dti"]), 6),
                "ci95": holdout_report["summaries"]["EXP-3"]["ci95"]["interval"],
                "folds": {
                    r["fold"]: round(float(r["dti"]), 6)
                    for r in holdout_report["summaries"]["EXP-3"]["folds"]
                },
                "paired_vs_B0": holdout_report["paired_vs_B0"]["EXP-3"],
                "paired_vs_EXP2_two_regime_bridge_lift": holdout_report[
                    "paired_EXP3_minus_EXP2_two_regime_bridge_lift"
                ],
            },
            "recorded_repo_B0": RECORDED_REPO_B0,
            "recorded_prev_repo_best_GVSC36": RECORDED_PREV_REPO_BEST_GVSC36,
            "recorded_group_best_GEMSDOE24_GVC1": RECORDED_GROUP_BEST_GVC1,
            "recorded_group_best_GEMSDOE24_DPRF1": RECORDED_GROUP_BEST_DPRF1,
        },
        "deployed_d_cat_profile": d_cat_stats,
        "registry_uniqueness": crosscheck_doc["final_dots_summary"]
        | {
            "surface_max_abs_rank_corr": surf_nov["max_abs_rank_correlation"],
            "surface_passed": g4_surf,
            "evidence_path": str(CROSSCHECK_OUT.relative_to(ROOT)),
        },
        "gates": {
            "G1_leakage_canary_le_0p90": g1_canary,
            "G2a_beats_repo_B0_paired_ci_gt_0": g2_beats_b0,
            "G2b_beats_prev_repo_best_GVSC36_0p15886": g2_beats_prev_repo_best,
            "G2c_beats_group_GVC1_0p14876": g2_beats_group_gvc1,
            "G2d_beats_group_DPRF1_0p16379": g2_beats_group_dprf1,
            "G3_format_and_strict_whole_array_0_1": g3_format,
            "G4a_surface_rank_corr_le_0p90": g4_surf,
            "G4b_focus9_3px_overlap_le_0p70": g4_focus9,
            "G4c_competing_methods_3px_overlap_le_0p70": g4_competing,
            "G4d_literal_all_registry_3px_overlap_le_0p70": g4_literal,
        },
        "validator_output": {
            "repo_validate_submission": repo_val,
            "shared_gems_check_variants": gems_val,
            "write_submission": write_info,
            "safe_to_download_and_submit": verdict == "promote",
        },
        "submission": {
            "submission_name": stem,
            "zeros_filename": tif_path.name,
            "zip_archive_name": zip_path.name,
            "tif_relpath": f"downloads/{tif_path.name}",
            "zip_relpath": f"downloads/{zip_path.name}",
            "run_card_relpath": "downloads/csdl36-run-card.json",
            "raster_sha256": write_info["sha256"],
            "zip_sha256": zip_info["sha256"],
            "raster_bytes": tif_path.stat().st_size,
            "zip_bytes": zip_path.stat().st_size,
            "n_dots": int(dots.sum()),
            "note": note,
            "note_length": len(note),
        },
    }
    rc_json = json.dumps(run_card, indent=2, allow_nan=False) + "\n"
    RUN_CARD_OUT.write_text(rc_json, encoding="utf-8")
    (dl_dir / "csdl36-run-card.json").write_text(rc_json, encoding="utf-8")
    (dl_dir / f"{stem}.receipt.json").write_text(rc_json, encoding="utf-8")

    walltime_payload = {
        "lane_id": LANE_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "experiments_executed": 3,
        "budget_max_experiments": 3,
        "budget_max_seconds": 7200,
        "stage_seconds": {
            "feature_store": t_features,
            "leakage_canary": t_canary,
            "holdout_evaluation": t_holdout,
            "total_elapsed": elapsed_total,
        },
        "within_budget": elapsed_total <= 7200.0,
    }
    WALLTIME_OUT.write_text(json.dumps(walltime_payload, indent=2) + "\n", encoding="utf-8")

    print(
        f"[deploy] COMPLETE | verdict={verdict} | {tif_path.name} "
        f"(sha256={write_info['sha256'][:12]}) | HOLDOUT-DTI={dti_val:.6f}",
        flush=True,
    )
    return run_card


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--stage",
        choices=("canary", "holdout", "deploy", "all"),
        default="all",
    )
    args = ap.parse_args()

    t_start = time.time()
    verify_preregistration_contract()
    data_raw = ROOT / "data" / "raw"

    t_f0 = time.time()
    store, grid, inv_stats = build_csdl_feature_store(CACHE_DIR, data_raw)
    mmap_cols = {n: store.column(n) for n in store.names}
    store.column = mmap_cols.__getitem__  # type: ignore[method-assign]
    t_features = round(time.time() - t_f0, 2)
    print(f"[features] ready: {len(store.names)} columns ({t_features}s) | inventory={inv_stats}", flush=True)

    fp_lbl, labels = load_labels(data_raw)
    if not np.array_equal(fp_lbl, grid.footprint):
        raise RuntimeError("Footprint mismatch between sample_submission.tif and labels.tif")
    holdout = SegmentHoldout(grid.footprint, labels, buffer_px=15)

    t_c0 = time.time()
    if args.stage in ("canary", "all"):
        canary_rep = run_canary_stage(store, holdout, grid.footprint)
    else:
        canary_rep = json.loads(CANARY_OUT.read_text(encoding="utf-8"))
    t_canary = round(time.time() - t_c0, 2)

    if args.stage == "canary":
        return 0

    t_h0 = time.time()
    if args.stage in ("holdout", "all"):
        holdout_rep, best_arm, oof_best, oof_conduit = run_holdout_stage(
            store, holdout, grid.footprint, labels, inv_stats.__dict__
        )
    else:
        holdout_rep = json.loads(HOLDOUT_OUT.read_text(encoding="utf-8"))
        best_arm = holdout_rep["best_candidate_arm"]
        oof_best = np.load(CACHE_DIR / f"csdl_oof_surface_{best_arm}.npy")
        oof_conduit = np.zeros_like(oof_best)
    t_holdout = round(time.time() - t_h0, 2)

    if args.stage == "holdout":
        return 0

    run_deploy_stage(
        holdout_rep,
        canary_rep,
        best_arm,
        oof_best,
        oof_conduit,
        grid.footprint,
        labels,
        t_features,
        t_canary,
        t_holdout,
        t_start,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
