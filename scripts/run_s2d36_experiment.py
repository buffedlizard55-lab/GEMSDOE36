#!/usr/bin/env python3
"""S2D-36 lane runner (preregistered, SHA-256 locked): canary -> holdout -> deploy.

Reuses shared GEMSDOE36 infrastructure strictly without private forks:
- ``gems.holdout.SegmentHoldout`` (``gems-segment-pooled-v1``, ``buffer_px=15``)
- ``gemsdoe36.h36_features.FeatureStore`` cached ``float32`` footprint store
- ``gemsdoe36.submodular_emit.emit_submodular_cover`` exact 300 m CELF emitter
- ``gems.submission.write_submission`` / ``zip_single`` / ``check_variants``
- ``gems.novelty.compare_registry`` (both ``separate_calibration_controls=True`` and ``False``)
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_gvsc36 import (  # noqa: E402
    B0_SEED,
    GVSC_HGB,
    GVSC_N_NEG,
    GVSC_N_POS,
    fold_budgets,
    load_labels,
    prentice_pyke_calibrate,
    train_predict_b0,
    train_predict_gvsc_expert,
    unfold_column,
)
from run_kpl36_experiment import (  # noqa: E402
    KPL101,
    KPL_BLIND,
    champion_files,
    focus9_entries,
    local_prior_entries,
)
from run_kpl36_experiment import (  # noqa: E402
    build_combined_store as build_kpl101_store,
)

from gems.holdout import SegmentHoldout, make_quadrant_folds  # noqa: E402
from gems.novelty import compare_registry  # noqa: E402
from gems.submission import check_variants, write_submission, zip_single  # noqa: E402
from gemsdoe36.h36_emission import emit_dots  # noqa: E402
from gemsdoe36.h36_features import FeatureStore  # noqa: E402
from gemsdoe36.s2d_features import (  # noqa: E402
    S2D_FEATURES,
    apply_halo_sharpening,
    build_s2d_dual_aux_features,
    build_s2d_stage1_features,
    build_s2d_stage2_corridor_features,
)
from gemsdoe36.submission import validate_submission  # noqa: E402
from gemsdoe36.submodular_emit import emit_submodular_cover  # noqa: E402

PREREG_PATH = ROOT / "evidence" / "s2d36_preregistration_20261027.json"
EXPECTED_PREREG_SHA256 = "0cb39811a8caf986cd503b3e194923745e6819bfe3f3fc155c049462c91c9ac1"

CACHE_DIR = ROOT / ".cache" / "gvsc36_features"
S2D_DIR = ROOT / ".cache" / "s2d36"
CANARY_OUT = ROOT / "evidence" / "s2d36_leakage_canary_20261027.json"
HOLDOUT_OUT = ROOT / "evidence" / "s2d36_holdout_experiments_20261027.json"
CROSSCHECK_OUT = ROOT / "evidence" / "s2d36_crosscheck_20261027.json"
RUN_CARD_OUT = ROOT / "evidence" / "s2d36_run_card_20261027.json"

TOTAL_BUDGET = 37_654
RECORDED_KPL36_EXP3 = 0.170100
T_START = time.time()

S2D122: tuple[str, ...] = tuple(KPL101) + tuple(S2D_FEATURES)
S2D_BLIND: tuple[str, ...] = tuple(KPL_BLIND) + tuple(S2D_FEATURES)

STAGE2_PHYS_COLS: tuple[str, ...] = (
    "s2d_dem10_onesided3",
    "s2d_dem10_scarp_sharpness",
    "s2d_dem10_asymm_scarp_idx",
    "s2d_dem10_onesided3_line15",
    "s2d_dem10_piedmont_inflection",
    "s2d_dem10_hgm20_max",
    "s2d_dem10_resid_std",
    "s2d_tiger_road_dist_log",
    "s2d_road_cut_mimic",
    "s2d_geodawn_seam_dist_km",
    "s2d_mag_hg_block_z",
    "s2d_rad_k_block_z",
    "lid_step_max",
    "lid_valid",
    "kpl_lid_coh3km",
    "kpl_lid_line15",
    "kpl_slope_coh3km",
    "kpl_mag_line15",
    "kpl_xorient_agree",
    "org_iso_grav_anom_hg",
    "org_tmi_hg",
    "org_det_elev_slope",
    "sa_worm_mag",
    "sa_worm_grav_base",
    "sa_piedmont_break",
    "gvsc_total_upflow_potential",
    "gvsc_hydro_alteration_composite",
    "gvsc_conduit_x_grav_base",
)

STAGE2_HGB: dict[str, Any] = {
    "max_iter": 240,
    "learning_rate": 0.045,
    "max_leaf_nodes": 31,
    "max_depth": 5,
    "min_samples_leaf": 300,
    "l2_regularization": 8.0,
}
STAGE2_SEEDS: tuple[int, int] = (202611, 202612)

ARMS: tuple[str, ...] = ("B0", "C-KPL", "EXP-1", "EXP-2", "EXP-3")
EXP_ARMS: tuple[str, ...] = ("EXP-1", "EXP-2", "EXP-3")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_prereg() -> dict[str, Any]:
    got = sha256_file(PREREG_PATH)
    if got != EXPECTED_PREREG_SHA256:
        raise SystemExit(f"PREREG LOCK MISMATCH {got} != {EXPECTED_PREREG_SHA256}")
    return json.loads(PREREG_PATH.read_text(encoding="utf-8"))


def build_s2d_store(fp: np.ndarray) -> FeatureStore:
    store101 = build_kpl101_store(fp)
    if not all((CACHE_DIR / f"{n}.npy").exists() for n in S2D_FEATURES):
        t0 = time.time()
        cols_fp = {
            "org_tmi_hg": np.asarray(store101.column("org_tmi_hg"), dtype=np.float32),
            "gd_K": np.asarray(store101.column("gd_K"), dtype=np.float32),
        }
        feats = build_s2d_stage1_features(cols_fp, fp, ROOT / "data" / "raw")
        for name, arr in feats.items():
            np.save(CACHE_DIR / f"{name}.npy", np.asarray(arr, dtype=np.float32))
        print(f"[s2d] built {len(S2D_FEATURES)} S2D features in {time.time() - t0:.1f}s", flush=True)
        del cols_fp, feats
        gc.collect()
    names = list(S2D122)
    return FeatureStore(CACHE_DIR, names, store101.n_fp)


def run_canary(store: FeatureStore, holdout: SegmentHoldout, fp: np.ndarray) -> dict[str, Any]:
    if CANARY_OUT.exists():
        doc = json.loads(CANARY_OUT.read_text(encoding="utf-8"))
        print(
            f"[canary] loaded cached {CANARY_OUT.name} passed={doc['passed']} "
            f"max_sym_auc={doc['max_symmetric_auc']}",
            flush=True,
        )
        return doc
    t0 = time.time()
    features_new: dict[str, Any] = {}
    batch: dict[str, np.ndarray] = {}
    ev_ver = "gems-segment-pooled-v1"
    for idx, name in enumerate(S2D_FEATURES, start=1):
        batch[name] = unfold_column(store, name, fp)
        if len(batch) == 7 or idx == len(S2D_FEATURES):
            rep = holdout.canary(batch)
            ev_ver = str(rep.get("evaluator_version", ev_ver))
            features_new.update(rep["features"])
            print(
                f"[canary] checked {idx}/{len(S2D_FEATURES)} new S2D features "
                f"(batch passed={rep['passed']})",
                flush=True,
            )
            batch.clear()
            gc.collect()

    mx_new, mx_new_name = 0.5, ""
    for name, row in features_new.items():
        sym = max(float(row["pooled_auc"]), 1.0 - float(row["pooled_auc"]))
        for f in row["folds"]:
            sym = max(sym, float(f["auc"]), 1.0 - float(f["auc"]))
        if sym > mx_new:
            mx_new, mx_new_name = sym, name

    gvsc_can = json.loads((ROOT / "evidence" / "gvsc36_canary_20261026.json").read_text())
    kpl_can = json.loads((ROOT / "evidence" / "kpl36_leakage_canary_20261026.json").read_text())
    mx_all = max(mx_new, float(gvsc_can["max_symmetric_auc"]), float(kpl_can["max_symmetric_auc"]))
    mx_all_name = (
        mx_new_name
        if mx_all == mx_new
        else (
            gvsc_can["max_symmetric_auc_feature"]
            if mx_all == float(gvsc_can["max_symmetric_auc"])
            else kpl_can["max_symmetric_auc_feature"]
        )
    )
    passed = bool(
        gvsc_can["passed"]
        and kpl_can["passed"]
        and mx_all <= 0.90
        and not any(r.get("leakage_suspected", False) for r in features_new.values())
    )
    doc = {
        "lane_id": "S2D-36",
        "label": "LEAKAGE-CANARY AUC (not a score)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evaluator_version": ev_ver,
        "threshold": 0.90,
        "passed": passed,
        "total_stage1_features": len(S2D122),
        "new_s2d_features_tested": len(S2D_FEATURES),
        "max_symmetric_auc_new_s2d": round(float(mx_new), 6),
        "max_symmetric_auc_new_s2d_feature": mx_new_name,
        "max_symmetric_auc": round(float(mx_all), 6),
        "max_symmetric_auc_feature": mx_all_name,
        "elapsed_seconds": round(time.time() - t0, 2),
        "reused_canary_evidence": [
            "evidence/gvsc36_canary_20261026.json",
            "evidence/kpl36_leakage_canary_20261026.json",
        ],
        "features": features_new,
    }
    CANARY_OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(
        f"[canary] passed={passed} max_new={mx_new:.4f} ({mx_new_name}) "
        f"max_all122={mx_all:.4f} ({mx_all_name})",
        flush=True,
    )
    return doc


def fuse_s2d_lidar_bridge(
    p_full: np.ndarray,
    p_blind: np.ndarray,
    lid_valid_2d: np.ndarray,
    det_slope_2d: np.ndarray,
    eval_mask: np.ndarray,
) -> np.ndarray:
    """Fuse full (1m+10m) and 1m-LiDAR-blind (10m-seamless) experts across coverage regimes."""
    has_lid = np.isfinite(lid_valid_2d) & (lid_valid_2d > 0.5)
    low_relief = np.nan_to_num(det_slope_2d, nan=0.0) < 4.0
    w_blind = np.where(~has_lid, 0.65, np.where(low_relief, 0.30, 0.15)).astype(np.float32)
    fused = (1.0 - w_blind) * p_full + w_blind * p_blind
    return np.where(eval_mask, fused, 0.0).astype(np.float32)


INNER_HGB: dict[str, Any] = {
    "max_iter": 200,
    "learning_rate": 0.065,
    "max_leaf_nodes": 47,
    "min_samples_leaf": 250,
    "l2_regularization": 3.0,
    "max_features": 0.75,
    "early_stopping": False,
}


def _train_predict_fast_inner_s1(
    store: FeatureStore,
    fp_pos: np.ndarray,
    train_mask: np.ndarray,
    visible_mask: np.ndarray,
    eval_mask: np.ndarray,
    labels: np.ndarray,
    lid_valid_2d: np.ndarray,
    det_slope_2d: np.ndarray,
    seed: int,
) -> np.ndarray:
    """Fast 1-seed inner Stage-1 bridge predictor on strict pairwise training intersection."""
    pos_pool = np.flatnonzero((labels & train_mask).ravel())
    far = distance_transform_edt(~visible_mask) > 3.0
    neg_pool = np.flatnonzero((train_mask & ~labels & far).ravel())
    del far
    rng = np.random.default_rng(seed)
    pos_sel = pos_pool if len(pos_pool) <= GVSC_N_POS else rng.choice(pos_pool, GVSC_N_POS, replace=False)
    neg_sel = rng.choice(neg_pool, min(180_000, len(neg_pool)), replace=False)
    pi_pos = float(len(pos_sel)) / float(max(len(pos_pool), 1))
    pi_neg = float(len(neg_sel)) / float(max(len(neg_pool), 1))
    idx = np.r_[fp_pos[pos_sel], fp_pos[neg_sel]]
    y = np.r_[np.ones(len(pos_sel), np.float32), np.zeros(len(neg_sel), np.float32)]

    eval_flat = np.flatnonzero(eval_mask.ravel())
    preds_pair = []
    for m_off, feat_names in enumerate((S2D122, S2D_BLIND)):
        clf = HistGradientBoostingClassifier(**INNER_HGB, random_state=seed + 13 * m_off)
        clf.fit(store.rows(idx, list(feat_names)), y)
        p_out = np.zeros(eval_mask.size, dtype=np.float32)
        for s in range(0, len(eval_flat), 500_000):
            ch = eval_flat[s : s + 500_000]
            q = clf.predict_proba(store.rows(fp_pos[ch], list(feat_names)))[:, 1].astype(np.float32)
            p_out[ch] = prentice_pyke_calibrate(q, pi_pos=pi_pos, pi_neg=pi_neg)
        preds_pair.append(p_out.reshape(eval_mask.shape))
        del clf
        gc.collect()
    return fuse_s2d_lidar_bridge(preds_pair[0], preds_pair[1], lid_valid_2d, det_slope_2d, eval_mask)


def train_predict_dual_bedrock_expert(
    store: FeatureStore,
    fp_pos: np.ndarray,
    train_mask: np.ndarray,
    visible_mask: np.ndarray,
    eval_mask: np.ndarray,
    labels: np.ndarray,
    sgmc_mask: np.ndarray,
    seed: int,
    n_seeds: int = 1,
    w_bed: float = 0.25,
    hgb_params: dict[str, Any] | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Fold-safe Dual-Population Quaternary (w=1.0) + off-catalogue SGMC bedrock (w=0.25) expert.

    Reads ZERO SGMC input features; ``sgmc_mask`` is strictly confined to ``train_mask`` target construction.
    """
    params = GVSC_HGB if hgb_params is None else hgb_params
    d_vis = distance_transform_edt(~visible_mask)
    pos_quat = np.flatnonzero((labels & train_mask).ravel())
    pos_bed = np.flatnonzero((sgmc_mask & ~labels & (d_vis >= 3.0) & train_mask).ravel())
    neg_pool = np.flatnonzero((train_mask & ~labels & ~sgmc_mask & (d_vis > 3.0)).ravel())
    del d_vis

    eval_flat = np.flatnonzero(eval_mask.ravel())
    prob_acc = np.zeros(len(eval_flat), dtype=np.float64)
    names = list(S2D_BLIND)
    models = []
    for s_i in range(n_seeds):
        rng = np.random.default_rng(seed + 97 * s_i)
        pq = pos_quat if len(pos_quat) <= GVSC_N_POS else rng.choice(pos_quat, GVSC_N_POS, replace=False)
        pb = pos_bed if len(pos_bed) <= 45_000 else rng.choice(pos_bed, 45_000, replace=False)
        ng = rng.choice(neg_pool, min(200_000, len(neg_pool)), replace=False)
        eff_pos_pool = float(len(pos_quat)) + w_bed * float(len(pos_bed))
        eff_pos_sel = float(len(pq)) + w_bed * float(len(pb))
        pi_pos = eff_pos_sel / max(eff_pos_pool, 1.0)
        pi_neg = float(len(ng)) / float(max(len(neg_pool), 1))

        idx = np.r_[fp_pos[pq], fp_pos[pb], fp_pos[ng]]
        y = np.r_[
            np.ones(len(pq) + len(pb), dtype=np.float32),
            np.zeros(len(ng), dtype=np.float32),
        ]
        sw = np.r_[
            np.ones(len(pq), dtype=np.float32),
            np.full(len(pb), w_bed, dtype=np.float32),
            np.ones(len(ng), dtype=np.float32),
        ]
        clf = HistGradientBoostingClassifier(**params, random_state=seed + 37 * s_i)
        clf.fit(store.rows(idx, names), y, sample_weight=sw)
        models.append((clf, pi_pos, pi_neg))
        del idx, y, sw
        gc.collect()

    for s in range(0, len(eval_flat), 500_000):
        ch = eval_flat[s : s + 500_000]
        Xc = store.rows(fp_pos[ch], names)
        for clf, pi_pos, pi_neg in models:
            q = clf.predict_proba(Xc)[:, 1].astype(np.float32)
            prob_acc[s : s + len(ch)] += prentice_pyke_calibrate(q, pi_pos=pi_pos, pi_neg=pi_neg)
        del Xc
    del models
    gc.collect()
    out = np.zeros(eval_mask.size, dtype=np.float32)
    out[eval_flat] = (prob_acc / float(n_seeds)).astype(np.float32)
    return out.reshape(eval_mask.shape), {
        "n_pos_quat": int(len(pos_quat)),
        "n_pos_bedrock_offcat": int(len(pos_bed)),
        "w_bed": w_bed,
    }


def ensure_pairwise_inner_oof(
    store: FeatureStore,
    fp_pos: np.ndarray,
    quad_grid: np.ndarray,
    holdout: SegmentHoldout,
    labels: np.ndarray,
    sgmc_mask: np.ndarray,
    lid_valid_2d: np.ndarray,
    det_slope_2d: np.ndarray,
) -> None:
    """Precompute and checkpoint all 6 unordered quadrant-pair OOF surfaces (strictly zero-leakage)."""
    S2D_DIR.mkdir(parents=True, exist_ok=True)
    for qa in range(4):
        for qb in range(qa + 1, 4):
            ck = S2D_DIR / f"pair_oof_{qa}_{qb}.npz"
            if ck.exists():
                continue
            t0 = time.time()
            # Strict intersection of fold qa and fold qb training masks and visible masks!
            pair_train = holdout.folds[qa]["train"] & holdout.folds[qb]["train"]
            pair_vis = holdout.folds[qa]["visible"] & holdout.folds[qb]["visible"]
            eval_union = (holdout.folds[qa]["train"] & (quad_grid == qb)) | (
                holdout.folds[qb]["train"] & (quad_grid == qa)
            )
            p1_pair = _train_predict_fast_inner_s1(
                store,
                fp_pos,
                pair_train,
                pair_vis,
                eval_union,
                labels,
                lid_valid_2d,
                det_slope_2d,
                seed=3100 + 19 * qa + 7 * qb,
            )
            pd_pair, _ = train_predict_dual_bedrock_expert(
                store,
                fp_pos,
                pair_train,
                pair_vis,
                eval_union,
                labels,
                sgmc_mask,
                seed=4200 + 19 * qa + 7 * qb,
                n_seeds=1,
                w_bed=0.25,
                hgb_params=INNER_HGB,
            )
            np.savez_compressed(
                ck,
                eval_flat=np.flatnonzero(eval_union.ravel()).astype(np.int32),
                p1=p1_pair.ravel()[eval_union.ravel()].astype(np.float32),
                pdual=pd_pair.ravel()[eval_union.ravel()].astype(np.float32),
            )
            print(
                f"[inner-oof] pair ({qa},{qb}) done in {time.time() - t0:.1f}s "
                f"(eval_px={int(eval_union.sum())})",
                flush=True,
            )
            del pair_train, pair_vis, eval_union, p1_pair, pd_pair
            gc.collect()


def assemble_fold_inner_oof(
    quad_grid: np.ndarray,
    fold: dict[str, Any],
    fold_idx: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Assemble ``p1_tr_oof`` and ``pdual_tr_oof`` strictly inside ``fold['train']`` from cached pair files."""
    train_mask = fold["train"]
    p1_oof = np.zeros(train_mask.size, dtype=np.float32)
    pdual_oof = np.zeros(train_mask.size, dtype=np.float32)
    for q_sub in range(4):
        if q_sub == fold_idx:
            continue
        qa, qb = (fold_idx, q_sub) if fold_idx < q_sub else (q_sub, fold_idx)
        ck = S2D_DIR / f"pair_oof_{qa}_{qb}.npz"
        with np.load(ck) as z:
            ef = z["eval_flat"]
            p1_oof[ef] = z["p1"]
            pdual_oof[ef] = z["pdual"]
    p1_2d = np.where(train_mask, p1_oof.reshape(train_mask.shape), 0.0).astype(np.float32)
    pd_2d = np.where(train_mask, pdual_oof.reshape(train_mask.shape), 0.0).astype(np.float32)
    return p1_2d, pd_2d


def train_predict_stage2_corridor(
    store: FeatureStore,
    fp_pos: np.ndarray,
    train_mask: np.ndarray,
    visible_mask: np.ndarray,
    eval_mask: np.ndarray,
    labels: np.ndarray,
    p1_train_oof: np.ndarray,
    p1_val: np.ndarray,
    subsurf_2d: np.ndarray,
    fold_idx: int,
    pdual_train_oof: np.ndarray | None = None,
    pdual_val: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Fit regularized Stage-2 Corridor U-GBDT strictly on ``train_mask`` competition targets."""
    pos_pool = np.flatnonzero((labels & train_mask).ravel())
    far = distance_transform_edt(~visible_mask) > 3.0
    neg_pool = np.flatnonzero((train_mask & ~labels & far).ravel())
    del far

    rng_base = np.random.default_rng(7070 + 29 * fold_idx)
    pos_sel = pos_pool if len(pos_pool) <= GVSC_N_POS else rng_base.choice(pos_pool, GVSC_N_POS, replace=False)
    neg_sel = rng_base.choice(neg_pool, min(GVSC_N_NEG, len(neg_pool)), replace=False)
    train_flat = np.r_[pos_sel, neg_sel]
    y_train = np.r_[
        np.ones(len(pos_sel), dtype=np.float32),
        np.zeros(len(neg_sel), dtype=np.float32),
    ]
    pi_pos = float(len(pos_sel)) / float(max(len(pos_pool), 1))
    pi_neg = float(len(neg_sel)) / float(max(len(neg_pool), 1))

    X_phys_tr = store.rows(fp_pos[train_flat], list(STAGE2_PHYS_COLS))
    X_corr_tr = build_s2d_stage2_corridor_features(p1_train_oof, train_mask, subsurf_2d, train_flat)
    if pdual_train_oof is not None:
        X_aux_tr = build_s2d_dual_aux_features(pdual_train_oof, p1_train_oof, train_mask, train_flat)
        X_tr = np.hstack([X_phys_tr, X_corr_tr, X_aux_tr]).astype(np.float32, copy=False)
        del X_aux_tr
    else:
        X_tr = np.hstack([X_phys_tr, X_corr_tr]).astype(np.float32, copy=False)
    del X_phys_tr, X_corr_tr
    gc.collect()

    models = []
    for m_i, s_seed in enumerate(STAGE2_SEEDS):
        clf = HistGradientBoostingClassifier(
            **STAGE2_HGB, random_state=s_seed + 53 * fold_idx + m_i
        )
        clf.fit(X_tr, y_train)
        models.append(clf)
    n_cols = int(X_tr.shape[1])
    del X_tr, y_train
    gc.collect()

    eval_flat = np.flatnonzero(eval_mask.ravel())
    X_corr_val = build_s2d_stage2_corridor_features(p1_val, eval_mask, subsurf_2d, eval_flat)
    X_aux_val = (
        build_s2d_dual_aux_features(pdual_val, p1_val, eval_mask, eval_flat)
        if pdual_val is not None
        else None
    )
    prob_acc = np.zeros(len(eval_flat), dtype=np.float64)
    for s in range(0, len(eval_flat), 400_000):
        e = min(s + 400_000, len(eval_flat))
        ch = eval_flat[s:e]
        Xp = store.rows(fp_pos[ch], list(STAGE2_PHYS_COLS))
        parts = [Xp, X_corr_val[s:e]]
        if X_aux_val is not None:
            parts.append(X_aux_val[s:e])
        Xv = np.hstack(parts).astype(np.float32, copy=False)
        for clf in models:
            q = clf.predict_proba(Xv)[:, 1].astype(np.float32)
            prob_acc[s:e] += prentice_pyke_calibrate(q, pi_pos=pi_pos, pi_neg=pi_neg)
        del Xp, Xv
    del models, X_corr_val, X_aux_val
    gc.collect()

    p2_2d = np.zeros(eval_mask.size, dtype=np.float32)
    p2_2d[eval_flat] = (prob_acc / float(len(STAGE2_SEEDS))).astype(np.float32)
    p2_2d = p2_2d.reshape(eval_mask.shape)

    p_blend = (0.28 * p1_val + 0.72 * p2_2d).astype(np.float32)
    p_sharp = apply_halo_sharpening(p_blend, eval_mask, gamma_halo=0.15)
    return p_sharp, {
        "stage2_cols": n_cols,
        "n_pos_train": int(len(pos_sel)),
        "n_neg_train": int(len(neg_sel)),
        "blend_weights": [0.28, 0.72],
        "halo_gamma": 0.15,
    }


def _build_subsurface_support_2d(store: FeatureStore, fp: np.ndarray) -> np.ndarray:
    """Label-free normalized deep geophysical + hydrothermal corridor support in [0, 1]."""
    g = unfold_column(store, "sa_worm_grav_base", fp)
    m = unfold_column(store, "sa_worm_mag", fp)
    u = unfold_column(store, "gvsc_total_upflow_potential", fp)
    parts = []
    for arr in (g, m, u):
        v = arr[fp]
        p99 = float(np.nanpercentile(v[np.isfinite(v)], 99.5)) or 1.0
        parts.append(np.clip(np.nan_to_num(arr, nan=0.0) / max(p99, 1e-6), 0.0, 1.0))
    comp = (0.40 * parts[0] + 0.35 * parts[1] + 0.25 * parts[2]).astype(np.float32)
    return np.where(fp, comp, 0.0).astype(np.float32)


def _emit_celf(surf: np.ndarray, elig: np.ndarray, valid: np.ndarray, budget: int) -> tuple[np.ndarray, float]:
    cov = emit_submodular_cover(
        surf, elig, budget=budget, valid_footprint=valid, gamma=1.0, min_spacing_px=2.0
    )
    return cov.mask, float(cov.objective_value)


def run_holdout(
    store: FeatureStore,
    holdout: SegmentHoldout,
    fp: np.ndarray,
    labels: np.ndarray,
    only_fold: int | None = None,
    only_inner_oof: bool = False,
) -> dict[str, Any] | None:
    S2D_DIR.mkdir(parents=True, exist_ok=True)
    h, w = fp.shape
    fp_pos = np.full(h * w, -1, dtype=np.int64)
    fp_pos[np.flatnonzero(fp.ravel())] = np.arange(store.n_fp)
    budgets = fold_budgets(holdout)
    quad_grid, _ = make_quadrant_folds(fp)

    lid_valid_2d = unfold_column(store, "lid_valid", fp)
    det_slope_2d = unfold_column(store, "org_det_elev_slope", fp)
    subsurf_2d = _build_subsurface_support_2d(store, fp)

    sgmc_path = ROOT / "data" / "raw" / "external" / "derived_sgmc_faults_100m_u8.tif"
    with rasterio.open(sgmc_path) as ds:
        sgmc_mask = (ds.read(1) > 0) & fp

    ensure_pairwise_inner_oof(
        store, fp_pos, quad_grid, holdout, labels, sgmc_mask, lid_valid_2d, det_slope_2d
    )
    if only_inner_oof:
        return None

    preds: dict[str, list[np.ndarray]] = {a: [] for a in ARMS}
    oof: dict[str, np.ndarray] = {a: np.zeros((h, w), np.float32) for a in EXP_ARMS + ("C-KPL",)}
    fold_logs: list[dict[str, Any]] = []

    for f_i, fold in enumerate(holdout.folds):
        if only_fold is not None and f_i != only_fold:
            continue
        ck_npz = S2D_DIR / f"holdout_fold_{f_i}.npz"
        ck_json = S2D_DIR / f"holdout_fold_{f_i}.json"
        if ck_npz.exists() and ck_json.exists():
            f_rec = json.loads(ck_json.read_text(encoding="utf-8"))
            with np.load(ck_npz) as z:
                for a in ARMS:
                    preds[a].append(z[f"pred_{a}"])
                for a in oof:
                    oof[a][fold["valid"]] = z[f"surf_{a}"]
            fold_logs.append(f_rec)
            print(f"[holdout] {fold['name']} restored checkpoint", flush=True)
            continue

        t_fold = time.time()
        b = budgets[f_i]
        d_vis = distance_transform_edt(~fold["visible"])
        elig = fold["valid"] & (d_vis > 2.0)
        del d_vis
        f_rec: dict[str, Any] = {"fold": fold["name"], "budget": int(b)}

        def _arm_ck(arm_name: str, fold_idx: int = f_i) -> Path:
            return S2D_DIR / f"arm_f{fold_idx}_{arm_name}.npz"

        # Control 1: B0 (59 base features)
        if _arm_ck("B0").exists():
            with np.load(_arm_ck("B0"), allow_pickle=True) as z:
                d_b0 = z["pred"]
                f_rec["B0"] = json.loads(str(z["meta"]))
        else:
            s_b0, m_b0 = train_predict_b0(store, fp_pos, fold, labels, B0_SEED + f_i)
            d_b0 = emit_dots(s_b0, fold["valid"], b).astype(np.uint8)
            f_rec["B0"] = {
                **m_b0,
                "n_dots": int(d_b0.sum()),
                "fold_dti": round(float(holdout.score_fold(d_b0, fold)[0]["dti"]), 6),
            }
            np.savez_compressed(_arm_ck("B0"), pred=d_b0, meta=json.dumps(f_rec["B0"]))
            del s_b0
        preds["B0"].append(d_b0)
        print(
            f"[holdout] {fold['name']} B0 dti={f_rec['B0']['fold_dti']:.5f} "
            f"({time.time() - t_fold:.0f}s)",
            flush=True,
        )

        # Control 2: C-KPL (matched KPL101 + KPL_BLIND bridge control; KPL-36 EXP-3 0.170100 also gated directly)
        from run_gvsc36 import fuse_exp3_lidar_bridge

        if _arm_ck("C-KPL").exists():
            with np.load(_arm_ck("C-KPL"), allow_pickle=True) as z:
                d_ckpl = z["pred"]
                oof["C-KPL"][fold["valid"]] = z["surf"]
                f_rec["C-KPL"] = json.loads(str(z["meta"]))
        else:
            p_kpl_full, m_kpl_full = train_predict_gvsc_expert(
                store, KPL101, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, 400 + f_i
            )
            p_kpl_bl, m_kpl_bl = train_predict_gvsc_expert(
                store, KPL_BLIND, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, 500 + f_i
            )
            p_ckpl = fuse_exp3_lidar_bridge(
                p_kpl_full, p_kpl_bl, lid_valid_2d, det_slope_2d, fold["valid"]
            )
            del p_kpl_full, p_kpl_bl
            oof["C-KPL"][fold["valid"]] = p_ckpl[fold["valid"]]
            d_ckpl_b, obj_ckpl = _emit_celf(p_ckpl, elig, fold["valid"], b)
            d_ckpl = d_ckpl_b.astype(np.uint8)
            f_rec["C-KPL"] = {
                "full": m_kpl_full,
                "blind": m_kpl_bl,
                "n_dots": int(d_ckpl.sum()),
                "obj": round(obj_ckpl, 2),
                "fold_dti": round(float(holdout.score_fold(d_ckpl, fold)[0]["dti"]), 6),
            }
            np.savez_compressed(
                _arm_ck("C-KPL"),
                pred=d_ckpl,
                surf=oof["C-KPL"][fold["valid"]],
                meta=json.dumps(f_rec["C-KPL"]),
            )
            del p_ckpl
        preds["C-KPL"].append(d_ckpl)
        print(
            f"[holdout] {fold['name']} C-KPL dti={f_rec['C-KPL']['fold_dti']:.5f} "
            f"({time.time() - t_fold:.0f}s)",
            flush=True,
        )

        # EXP-1 (H-S2D-1): 122-feature Seamless 10m 3DEP + TIGER road + GeoDAWN seam + LiDAR bridge
        if _arm_ck("EXP-1").exists():
            with np.load(_arm_ck("EXP-1"), allow_pickle=True) as z:
                d_1 = z["pred"]
                p_exp1 = np.zeros((h, w), dtype=np.float32)
                p_exp1[fold["valid"]] = z["surf"]
                oof["EXP-1"][fold["valid"]] = z["surf"]
                f_rec["EXP-1"] = json.loads(str(z["meta"]))
        else:
            p122, m122 = train_predict_gvsc_expert(
                store, S2D122, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, 700 + f_i
            )
            p105b, m105b = train_predict_gvsc_expert(
                store, S2D_BLIND, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, 800 + f_i
            )
            p_exp1 = fuse_s2d_lidar_bridge(p122, p105b, lid_valid_2d, det_slope_2d, fold["valid"])
            del p122, p105b
            oof["EXP-1"][fold["valid"]] = p_exp1[fold["valid"]]
            d_1_b, obj_1 = _emit_celf(p_exp1, elig, fold["valid"], b)
            d_1 = d_1_b.astype(np.uint8)
            f_rec["EXP-1"] = {
                "full": m122,
                "blind": m105b,
                "n_dots": int(d_1.sum()),
                "obj": round(obj_1, 2),
                "fold_dti": round(float(holdout.score_fold(d_1, fold)[0]["dti"]), 6),
            }
            np.savez_compressed(
                _arm_ck("EXP-1"),
                pred=d_1,
                surf=oof["EXP-1"][fold["valid"]],
                meta=json.dumps(f_rec["EXP-1"]),
            )
        preds["EXP-1"].append(d_1)
        print(
            f"[holdout] {fold['name']} EXP-1 dti={f_rec['EXP-1']['fold_dti']:.5f} "
            f"({time.time() - t_fold:.0f}s)",
            flush=True,
        )

        # Assemble precomputed pairwise inner Stage-1 OOF strictly inside fold['train']
        p1_tr_oof, pdual_tr_oof = assemble_fold_inner_oof(quad_grid, fold, f_i)

        # EXP-2 (H-S2D-1 + H-S2D-2): Two-Stage Corridor U-GBDT + 800m Halo Sharpening
        if _arm_ck("EXP-2").exists():
            with np.load(_arm_ck("EXP-2"), allow_pickle=True) as z:
                d_2 = z["pred"]
                oof["EXP-2"][fold["valid"]] = z["surf"]
                f_rec["EXP-2"] = json.loads(str(z["meta"]))
        else:
            p_exp2, m_exp2 = train_predict_stage2_corridor(
                store,
                fp_pos,
                fold["train"],
                fold["visible"],
                fold["valid"],
                labels,
                p1_tr_oof,
                p_exp1,
                subsurf_2d,
                f_i,
            )
            oof["EXP-2"][fold["valid"]] = p_exp2[fold["valid"]]
            d_2_b, obj_2 = _emit_celf(p_exp2, elig, fold["valid"], b)
            d_2 = d_2_b.astype(np.uint8)
            f_rec["EXP-2"] = {
                **m_exp2,
                "n_dots": int(d_2.sum()),
                "obj": round(obj_2, 2),
                "fold_dti": round(float(holdout.score_fold(d_2, fold)[0]["dti"]), 6),
            }
            np.savez_compressed(
                _arm_ck("EXP-2"),
                pred=d_2,
                surf=oof["EXP-2"][fold["valid"]],
                meta=json.dumps(f_rec["EXP-2"]),
            )
            del p_exp2
        preds["EXP-2"].append(d_2)
        print(
            f"[holdout] {fold['name']} EXP-2 dti={f_rec['EXP-2']['fold_dti']:.5f} "
            f"({time.time() - t_fold:.0f}s)",
            flush=True,
        )

        # EXP-3 (H-S2D-1 + H-S2D-2 + H-S2D-3): Dual-Population Quaternary + Fold-Safe Bedrock Auxiliary
        if _arm_ck("EXP-3").exists():
            with np.load(_arm_ck("EXP-3"), allow_pickle=True) as z:
                d_3 = z["pred"]
                oof["EXP-3"][fold["valid"]] = z["surf"]
                f_rec["EXP-3"] = json.loads(str(z["meta"]))
        else:
            pdual_val, m_dual = train_predict_dual_bedrock_expert(
                store,
                fp_pos,
                fold["train"],
                fold["visible"],
                fold["valid"],
                labels,
                sgmc_mask,
                seed=9100 + 31 * f_i,
                n_seeds=2,
                w_bed=0.25,
            )
            p_exp3, m_exp3 = train_predict_stage2_corridor(
                store,
                fp_pos,
                fold["train"],
                fold["visible"],
                fold["valid"],
                labels,
                p1_tr_oof,
                p_exp1,
                subsurf_2d,
                100 + f_i,
                pdual_train_oof=pdual_tr_oof,
                pdual_val=pdual_val,
            )
            del pdual_val
            oof["EXP-3"][fold["valid"]] = p_exp3[fold["valid"]]
            d_3_b, obj_3 = _emit_celf(p_exp3, elig, fold["valid"], b)
            d_3 = d_3_b.astype(np.uint8)
            f_rec["EXP-3"] = {
                **m_exp3,
                "dual_aux": m_dual,
                "n_dots": int(d_3.sum()),
                "obj": round(obj_3, 2),
                "fold_dti": round(float(holdout.score_fold(d_3, fold)[0]["dti"]), 6),
            }
            np.savez_compressed(
                _arm_ck("EXP-3"),
                pred=d_3,
                surf=oof["EXP-3"][fold["valid"]],
                meta=json.dumps(f_rec["EXP-3"]),
            )
            del p_exp3
        del p1_tr_oof, pdual_tr_oof, p_exp1
        preds["EXP-3"].append(d_3)
        print(
            f"[holdout] {fold['name']} EXP-3 dti={f_rec['EXP-3']['fold_dti']:.5f} "
            f"({time.time() - t_fold:.0f}s)",
            flush=True,
        )

        f_rec["seconds"] = round(time.time() - t_fold, 1)
        fold_logs.append(f_rec)
        np.savez_compressed(
            ck_npz,
            **{f"pred_{a}": preds[a][-1] for a in ARMS},
            **{f"surf_{a}": oof[a][fold["valid"]] for a in oof},
        )
        ck_json.write_text(json.dumps(f_rec, indent=2) + "\n", encoding="utf-8")
        gc.collect()

    if only_fold is not None:
        return None

    summaries = {a: holdout.summarize(preds[a]) for a in ARMS}
    paired = {
        **{f"{a}_vs_B0": holdout.compare_paired(preds[a], preds["B0"]) for a in EXP_ARMS + ("C-KPL",)},
        **{f"{a}_vs_C-KPL": holdout.compare_paired(preds[a], preds["C-KPL"]) for a in EXP_ARMS},
        "EXP-2_vs_EXP-1": holdout.compare_paired(preds["EXP-2"], preds["EXP-1"]),
        "EXP-3_vs_EXP-2": holdout.compare_paired(preds["EXP-3"], preds["EXP-2"]),
    }
    best = max(EXP_ARMS, key=lambda a: float(summaries[a]["dti"]))
    for a in oof:
        np.save(S2D_DIR / f"oof_surface_{a}.npy", oof[a])

    doc = {
        "lane_id": "S2D-36",
        "label": "HOLDOUT-DTI",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration_path": str(PREREG_PATH.relative_to(ROOT)),
        "preregistration_sha256": sha256_file(PREREG_PATH),
        "evaluator_version": "gems-segment-pooled-v1",
        "buffer_px": 15,
        "withheld_positives": int(summaries["B0"]["n_withheld_positive_pixels"]),
        "fold_budgets": [int(x) for x in budgets],
        "total_budget": TOTAL_BUDGET,
        "experiments_executed": 3,
        "controls": ["B0", "C-KPL"],
        "recorded_kpl36_exp3_for_reference": RECORDED_KPL36_EXP3,
        "best_candidate_arm": best,
        "summaries": summaries,
        "paired": paired,
        "folds": fold_logs,
        "elapsed_seconds": round(time.time() - T_START, 1),
    }
    HOLDOUT_OUT.write_text(json.dumps(doc, indent=2, default=float) + "\n", encoding="utf-8")
    for a in ARMS:
        print(
            f"[holdout] POOLED {a:6s}: HOLDOUT-DTI {summaries[a]['dti']:.6f} "
            f"CI95 {summaries[a]['ci95']['interval']}",
            flush=True,
        )
    print(f"[holdout] best EXP arm: {best}", flush=True)
    return doc


def all_registry_entries() -> list[dict[str, Any]]:
    entries = json.loads((ROOT / "registry" / "uniqueness_registry.json").read_text())["entries"]
    missing = [e["id"] for e in entries if not (ROOT / e["cache_path"]).is_file()]
    if missing:
        raise RuntimeError(
            f"Missing {len(missing)} registry rasters (run scripts/fetch_registry_rasters.py): {missing[:5]}"
        )
    return entries


def run_deploy(
    holdout_doc: dict[str, Any],
    canary_doc: dict[str, Any],
    fp: np.ndarray,
    labels: np.ndarray,
) -> dict[str, Any]:
    best = holdout_doc["best_candidate_arm"]
    surface = np.load(S2D_DIR / f"oof_surface_{best}.npy")

    all_entries = all_registry_entries()
    f9_entries = focus9_entries()
    champ = champion_files(f9_entries)

    # Check if exactcrosscheck + tif already verified; otherwise run full 198-raster pre-placement check
    if CROSSCHECK_OUT.is_file():
        cached_cross = json.loads(CROSSCHECK_OUT.read_text(encoding="utf-8"))
    else:
        cached_cross = None

    if cached_cross and cached_cross.get("best_arm") == best:
        surf_max_rho = float(cached_cross["surface_before_placement"]["max_abs_rank_correlation_all_198"])
        surf_all = {"max_abs_rank_correlation": surf_max_rho}
        g3a = bool(surf_max_rho <= 0.90)
        print(f"[deploy] loaded cached pre-placement surface check max|rho|={surf_max_rho:.4f}", flush=True)
    else:
        # RULE 1: Check surface rank correlation BEFORE dot placement against ALL 198 registry rasters!
        t_surf = time.time()
        surf_all = compare_registry(
            surface, fp, all_entries, ROOT, dots=None, separate_calibration_controls=True
        )
        print(
            f"[deploy] pre-placement surface vs all {len(all_entries)} registry rasters: "
            f"max|rho|={surf_all['max_abs_rank_correlation']:.4f} ({time.time() - t_surf:.1f}s)",
            flush=True,
        )
        g3a = bool(float(surf_all["max_abs_rank_correlation"] or 0.0) <= 0.90)
    if not g3a:
        raise SystemExit(
            f"SURFACE DUPLICATE BEFORE PLACEMENT (max|rho|={surf_all['max_abs_rank_correlation']:.4f} > 0.90): stop"
        )

    # Emit exact 37,654 dots outside 200 m catalogue collar via 300 m CELF submodular cover
    d_cat = distance_transform_edt(~(labels & fp))
    elig = fp & (d_cat > 2.0)
    cov = emit_submodular_cover(
        surface, elig, budget=TOTAL_BUDGET, valid_footprint=elig, gamma=1.0, min_spacing_px=2.0
    )
    dots = cov.mask
    rc_bytes = np.argwhere(dots).astype(np.int32).tobytes()
    uid = hashlib.sha256(rc_bytes).hexdigest()[:12]
    stem = f"gemsdoe36-s2d36-{best.lower().replace('-', '')}-20261027-{uid}-zeros"
    dl = ROOT / "docs" / "downloads"
    dl.mkdir(parents=True, exist_ok=True)
    tif_path, zip_path = dl / f"{stem}.tif", dl / f"{stem}.zip"
    tmpl = ROOT / "data" / "raw" / "sample_submission.tif"

    if tif_path.is_file() and zip_path.is_file():
        with rasterio.open(tif_path) as existing_ds:
            same_pixels = np.array_equal(existing_ds.read(1), dots.astype(np.float32))
    else:
        same_pixels = False
    if not same_pixels:
        write_submission(dots.astype(np.float32), tmpl, tif_path, outside="zero")
        zip_single(tif_path, zip_path)
    repo_val = validate_submission(tif_path, tmpl, require_nonfinite_outside=False).to_dict()
    gems_val = check_variants(tif_path, tmpl)

    if same_pixels and cached_cross and cached_cross.get("best_arm") == best:
        champ_rows = cached_cross["final_dots"]["champion_overlap_by_site"]
        max_champ_ov = float(cached_cross["final_dots"]["max_champion_3px_overlap"])
        b2_ov = cached_cross["final_dots"]["overlap_vs_GEMSDOE32_B2_3px"]
        max_f9_ov = float(cached_cross["final_dots"]["max_overlap_all_focus9_rasters"])
        max_local_ov = float(cached_cross["final_dots"]["max_overlap_local_gemsdoe36_rasters"])
        max_competing_ov = float(cached_cross["final_dots"]["max_overlap_competing_methods_196"])
        max_literal_all_ov = float(cached_cross["final_dots"]["max_overlap_literal_all_198"])
        competing_passed = bool(max_competing_ov <= 0.70)
        literal_passed = bool(max_literal_all_ov <= 0.70)
        cross = cached_cross
    else:
        # Post-placement dot-overlap checks across Focus-9, local GEMSDOE36 downloads, and ALL 198 registry rasters
        dot_all = compare_registry(
            surface, fp, all_entries, ROOT, dots=dots, separate_calibration_controls=True
        )
        local_entries = local_prior_entries(fp, tif_path.name)
        local_check = (
            compare_registry(surface, fp, local_entries, ROOT, dots=dots, separate_calibration_controls=True)
            if local_entries
            else None
        )

        rows_by_file = {r["file"]: r for r in dot_all["rows"]}
        f9_files = {e["file"] for e in f9_entries}
        f9_rows = [r for r in dot_all["rows"] if r["file"] in f9_files]
        max_f9_ov = max(
            (float(r["candidate_dot_overlap_within_3px"] or 0.0) for r in f9_rows), default=0.0
        )

        champ_rows = {}
        for site, e in sorted(champ.items()):
            r = rows_by_file.get(e["file"])
            champ_rows[site] = {
                "file": e["file"],
                "owner_reported_score": e.get("owner_reported_score"),
                "candidate_dot_overlap_within_3px": (r or {}).get("candidate_dot_overlap_within_3px"),
                "raw_spearman": (r or {}).get("raw_spearman"),
                "footprint_3px_coverage": (r or {}).get("footprint_3px_coverage"),
            }
        max_champ_ov = max(
            (float(v["candidate_dot_overlap_within_3px"] or 0.0) for v in champ_rows.values()),
            default=0.0,
        )
        b2_ov = (champ_rows.get("GEMSDOE32") or {}).get("candidate_dot_overlap_within_3px")
        max_local_ov = float((local_check or {}).get("max_dot_overlap") or 0.0)
        max_competing_ov = float(dot_all["max_competing_dot_overlap"] or 0.0)
        max_literal_all_ov = float(dot_all["max_dot_overlap"] or 0.0)
        competing_passed = bool(dot_all["competing_method_passed"])
        literal_passed = bool(dot_all["literal_unseparated_passed"])
        competing_sorted = sorted(
            [r for r in dot_all["rows"] if r["comparator_class"] == "competing_method"],
            key=lambda r: float(r["candidate_dot_overlap_within_3px"] or 0.0),
            reverse=True,
        )
        literal_sorted = sorted(
            dot_all["rows"],
            key=lambda r: float(r["candidate_dot_overlap_within_3px"] or 0.0),
            reverse=True,
        )
        cross = {
            "lane_id": "S2D-36",
            "best_arm": best,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "all_registry_entries_checked": len(all_entries),
            "focus9_entries_checked": len(f9_entries),
            "local_prior_entries_checked": len(local_entries),
            "surface_before_placement": {
                "max_abs_rank_correlation_all_198": surf_all["max_abs_rank_correlation"],
                "passed_le_0.90": g3a,
            },
            "final_dots": {
                "champion_overlap_by_site": champ_rows,
                "max_champion_3px_overlap": round(max_champ_ov, 6),
                "overlap_vs_GEMSDOE32_B2_3px": b2_ov,
                "max_overlap_all_focus9_rasters": round(max_f9_ov, 6),
                "max_overlap_local_gemsdoe36_rasters": round(max_local_ov, 6),
                "max_overlap_competing_methods_196": round(max_competing_ov, 6),
                "max_overlap_literal_all_198": round(max_literal_all_ov, 6),
                "calibration_control_summary": dot_all["calibration_control_summary"],
                "top15_competing_methods_by_overlap": competing_sorted[:15],
                "top10_literal_all_registry_by_overlap": literal_sorted[:10],
                "local_prior_rows_sorted_by_overlap_desc": (
                    sorted(
                        local_check["rows"],
                        key=lambda r: float(r["candidate_dot_overlap_within_3px"] or 0.0),
                        reverse=True,
                    )
                    if local_check
                    else []
                ),
            },
        }
        CROSSCHECK_OUT.write_text(json.dumps(cross, indent=2, default=float) + "\n", encoding="utf-8")

    d_dots = d_cat[dots]
    dstats = {
        "n_dots": int(dots.sum()),
        "min_d_cat_px": round(float(d_dots.min()), 3),
        "median_d_cat_px": round(float(np.median(d_dots)), 2),
        "share_le_2px": round(float((d_dots <= 2.0).mean()), 6),
    }

    best_sum = holdout_doc["summaries"][best]
    paired_b0 = holdout_doc["paired"][f"{best}_vs_B0"]
    paired_ckpl = holdout_doc["paired"][f"{best}_vs_C-KPL"]

    g1 = bool(canary_doc["passed"])
    g2 = bool(
        float(best_sum["dti"]) > float(holdout_doc["summaries"]["C-KPL"]["dti"])
        and float(best_sum["dti"]) > RECORDED_KPL36_EXP3
        and float(paired_b0["paired_delta_ci95"][0]) > 0.0
        and float(paired_ckpl["paired_delta_ci95"][0]) > 0.0
    )
    g3b = bool(
        max_champ_ov <= 0.70
        and max_f9_ov <= 0.70
        and max_local_ov <= 0.70
        and max_competing_ov <= 0.70
        and competing_passed
    )
    g3c = bool(max_literal_all_ov <= 0.70 and literal_passed)
    g4 = bool(
        repo_val["passed"]
        and gems_val["format_valid"]
        and gems_val["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]
        and dstats["share_le_2px"] == 0.0
        and dstats["n_dots"] == TOTAL_BUDGET
    )

    # FAIL CLOSED: automatic verdict is promote ONLY if ALL gates including literal G3c pass!
    verdict = "promote" if (g1 and g2 and g3a and g3b and g3c and g4) else "negative"
    note = (
        f"S2D-36 {best} 10m3DEP+2stage+deconf | HOLDOUT-DTI {float(best_sum['dti']):.4f} | "
        f"{'PROMOTE' if verdict == 'promote' else 'NEGATIVE reg052 gate'} {uid}"
    )[:140]

    card = {
        "schema": "gems.parallel_run_card.v1",
        "lane_id": "S2D-36",
        "best_arm": best,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "ok_to_download_and_submit": bool(verdict == "promote"),
        "slot_approved": bool(verdict == "promote"),
        "hypothesis": (
            "H-S2D-1/2/3: Seamless 10 m USGS 3DEP scarp asymmetry + 3.1 km trace persistence closes the "
            "24.63% 1 m LiDAR gap; TIGER/Line 2024 road distance and GeoDAWN 4-block MAD normalization "
            "deconfound anthropogenic highway/bunker cuts and airborne survey seams; Stage-2 multi-azimuth "
            "corridor U-GBDT + province-preserving 800 m halo sharpening concentrates 300 m CELF budget "
            "onto continuous fault crests; EXP-3 adds fold-safe OOF pre-2022 SGMC bedrock auxiliary corridors."
        ),
        "mechanism": (
            f"122 label-free Stage-1 features (101 KPL + 21 S2D) -> 2-seed HGB full + 105-feature 10m-seamless "
            f"blind bridge -> inner sub-quadrant OOF Stage-1 -> Stage-2 Corridor U-GBDT ({best}) + 800 m halo "
            f"sharpening -> d_cat > 2 px collar -> exact 300 m CELF emission of 37,654 binary dots in [0,1]."
        ),
        "named_non_fault_mimic": (
            "I-80/US-95/US-395 highway road-cuts & Hawthorne Army Depot berms; GeoDAWN Winnemucca/Fallon/"
            "Hawthorne/Tonopah survey-block tie-line seams; 1-2 km alluvial-fan piedmont halos; sealed Mesozoic thrusts."
        ),
        "preregistration": {
            "path": str(PREREG_PATH.relative_to(ROOT)),
            "sha256": sha256_file(PREREG_PATH),
        },
        "experiments_executed": 3,
        "leakage_canary": {
            "passed": g1,
            "max_symmetric_auc": canary_doc["max_symmetric_auc"],
            "feature": canary_doc["max_symmetric_auc_feature"],
            "max_symmetric_auc_new_s2d": canary_doc["max_symmetric_auc_new_s2d"],
            "new_s2d_feature": canary_doc["max_symmetric_auc_new_s2d_feature"],
            "evidence": str(CANARY_OUT.relative_to(ROOT)),
        },
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": "gems-segment-pooled-v1",
            "n_withheld_positive_pixels": holdout_doc["withheld_positives"],
            "arms": {
                a: {
                    "dti": holdout_doc["summaries"][a]["dti"],
                    "ci95": holdout_doc["summaries"][a]["ci95"]["interval"],
                }
                for a in ARMS
            },
            "best_arm": best,
            "paired_vs_B0": paired_b0,
            "paired_vs_C_KPL": paired_ckpl,
            "evidence": str(HOLDOUT_OUT.relative_to(ROOT)),
        },
        "uniqueness": {
            "surface_max_abs_spearman_all_198": surf_all["max_abs_rank_correlation"],
            "max_focus9_champion_3px_dot_overlap": round(max_champ_ov, 6),
            "max_focus9_any_3px_dot_overlap": round(max_f9_ov, 6),
            "max_local_gemsdoe36_3px_dot_overlap": round(max_local_ov, 6),
            "max_competing_detector_3px_dot_overlap_196": round(max_competing_ov, 6),
            "overlap_vs_GEMSDOE32_B2": b2_ov,
            "literal_all_198_max_3px_dot_overlap": round(max_literal_all_ov, 6),
            "literal_blocker": "reg-052 (13gems_20261001_r13-lattice-s5_v2_nan-outside.tif, 5x5 lattice covering 99.87% of footprint within 3 px)",
            "evidence": str(CROSSCHECK_OUT.relative_to(ROOT)),
        },
        "submission": {
            "file": str(tif_path.relative_to(ROOT)),
            "sha256": sha256_file(tif_path),
            "bytes": tif_path.stat().st_size,
            "zip": str(zip_path.relative_to(ROOT)),
            "zip_sha256": sha256_file(zip_path),
            "name": stem.replace("-zeros", ""),
            "note": note,
            "note_characters": len(note),
            "dots": dstats["n_dots"],
        },
        "validator": {
            "repo_validate_submission": repo_val,
            "gems_check_variants": gems_val,
            "d_catalogue": dstats,
        },
        "gates": {
            "G1_canary": g1,
            "G2_holdout_beats_CKPL_and_B0_with_CI": g2,
            "G3a_pre_placement_surface_spearman_all_198": g3a,
            "G3b_focus9_and_competing_detector_uniqueness": g3b,
            "G3c_literal_all_198_registry_including_reg052": g3c,
            "G4_portal_format_and_0_1_range": g4,
        },
        "organizer_score": None,
        "oct25_27_peer_audit": (
            json.loads((ROOT / "evidence" / "s2d36_oct27_peer_audit_20261027.json").read_text(encoding="utf-8"))
            if (ROOT / "evidence" / "s2d36_oct27_peer_audit_20261027.json").is_file()
            else None
        ),
        "scenario_projection_not_a_score": {
            "label": "SCENARIO-PROJECTION (NOT A SCORE; NO ORGANIZER RECEIPT EXISTS)",
            "organizer_score": None,
            "receipt": None,
            "conservative_kpl_ratio_projection": round(float(best_sum["dti"]) * (0.1647 / 0.17010000946379217), 4),
            "peer_mechanism_matched_scenario_range": [0.205, 0.238],
            "anchors_user_reported_no_receipt": {
                "GEMSDOE36_KPL36_EXP3": {"holdout_dti": 0.1701, "user_reported_portal": 0.1647},
                "GEMSDOE27_H31": {"user_reported_portal": 0.2250},
                "GEMSDOE76_ptcf_submod39k": {"user_reported_portal": 0.2343},
                "GEMSDOE70_p5_dual_oof38k": {"user_reported_portal": 0.2478},
            },
            "monograph": "docs/research/s2d36-20261027.md",
        },
        "leaderboard_projection_scenario": (
            "PROJECTION SCENARIO (NOT A SCORE): see docs/research/s2d36-20261027.md empirical peer-transfer "
            "calibration; HOLDOUT-DTI is internal hide-and-recover validation on labels.tif, never a portal score."
        ),
        "elapsed_seconds": round(time.time() - T_START, 1),
    }
    card_bytes = (json.dumps(card, indent=2, default=float) + "\n").encode("utf-8")
    RUN_CARD_OUT.write_bytes(card_bytes)
    (dl / "s2d36-run-card.json").write_bytes(card_bytes)
    receipt = dl / f"{stem}.receipt.json"
    receipt.write_bytes(card_bytes)
    print(f"[deploy] verdict={verdict} file={tif_path.name} sha256={card['submission']['sha256']}", flush=True)
    print(
        f"[deploy] gates G1={g1} G2={g2} G3a={g3a} G3b={g3b} G3c={g3c} G4={g4} | "
        f"max_champ={max_champ_ov:.4f} max_comp196={max_competing_ov:.4f} literal198={max_literal_all_ov:.4f}",
        flush=True,
    )
    return card


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--stage",
        choices=("canary", "inner_oof", "holdout", "deploy", "all"),
        default="all",
    )
    ap.add_argument("--fold", type=int, choices=(0, 1, 2, 3), default=None)
    args = ap.parse_args()
    verify_prereg()
    print("[s2d] preregistration SHA-256 lock OK", flush=True)
    fp_lbl, labels = load_labels(ROOT / "data" / "raw")
    store = build_s2d_store(fp_lbl)
    print(
        f"[s2d] store ready: {len(store.names)} cols (122 = 101 KPL + 21 S2D); blind={len(S2D_BLIND)}",
        flush=True,
    )
    assert len(store.names) == 122 and list(S2D122) == list(store.names)
    holdout = SegmentHoldout(fp_lbl, labels, buffer_px=15)
    canary = run_canary(store, holdout, fp_lbl)
    if not canary["passed"]:
        raise SystemExit("CANARY FAILED: leakage suspected; aborting before any holdout number")
    if args.stage == "canary":
        return 0
    if args.stage == "inner_oof":
        run_holdout(store, holdout, fp_lbl, labels, only_inner_oof=True)
        return 0
    if args.fold is not None:
        run_holdout(store, holdout, fp_lbl, labels, only_fold=args.fold)
        return 0
    if args.stage in ("holdout", "all"):
        doc = run_holdout(store, holdout, fp_lbl, labels)
        assert doc is not None
    else:
        doc = json.loads(HOLDOUT_OUT.read_text(encoding="utf-8"))
    if args.stage == "holdout":
        return 0
    run_deploy(doc, canary, fp_lbl, labels)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
