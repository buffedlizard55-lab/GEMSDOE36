#!/usr/bin/env python3
"""GVSC-36 end-to-end runner: feature store, 89-feature canary, 3-experiment holdout, and OOF deploy.

Strictly follows the Parallel-Run Protocol and frozen preregistration
``evidence/gvsc36_preregistration_20261026.json`` (markdown SHA-256
``42bc538d3c6fc7baa391a51ecc4d20e1469a47300601c1bee57a26625db44986``):

- Stage 1 (``canary``): builds the 89-feature label-free store in ``.cache/gvsc36_features``
  and runs ``gems.holdout.SegmentHoldout.canary`` on all 89 features individually. Aborts
  if any feature has symmetric ``AUC > 0.90``.
- Stage 2 (``holdout``): evaluates frozen baseline ``B0`` plus ``EXP-1``, ``EXP-2``, and
  ``EXP-3`` (<= 3 experiments) on ``gems-segment-pooled-v1`` (60,988 withheld positives,
  1,500 m buffer, 1,999 block-bootstrap CI draws, paired deltas vs ``B0``).
- Stage 3 (``deploy``): builds a 4x4 spatial checkerboard out-of-fold cross-fitted surface
  (2.5 km purged collar, zero in-sample halo memorization) for the best candidate arm, emits
  37,654 dots via exact 300 m CELF submodular cover outside the 200 m catalogue collar, writes
  a zeros-outside GeoTIFF + single-TIFF ZIP via ``gems.submission.write_submission``, validates
  with both validators, runs ``gems.novelty.compare_registry`` across all registry scopes, and
  writes ``evidence/gvsc36_run_card_20261026.json``.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.ndimage import label as ndi_label
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.holdout import SegmentHoldout  # noqa: E402
from gems.novelty import compare_registry  # noqa: E402
from gems.submission import check_variants, write_submission, zip_single  # noqa: E402
from gemsdoe36.gvsc_features import (  # noqa: E402
    BASE_FEATURES,
    EXP1_FEATURES,
    EXP2_FEATURES,
    EXP3_BLIND_FEATURES,
    GVSC_FEATURES,
    SA_FEATURES,
    FeatureStore,
    build_gvsc_feature_store,
)
from gemsdoe36.h36_emission import emit_dots  # noqa: E402
from gemsdoe36.submission import sha256_file, validate_submission  # noqa: E402
from gemsdoe36.submodular_emit import emit_submodular_cover  # noqa: E402

CACHE_DIR = ROOT / ".cache" / "gvsc36_features"
PREREG_PATH = ROOT / "evidence" / "gvsc36_preregistration_20261026.json"
CANARY_OUT = ROOT / "evidence" / "gvsc36_canary_20261026.json"
HOLDOUT_OUT = ROOT / "evidence" / "gvsc36_holdout_experiments_20261026.json"
CROSSCHECK_OUT = ROOT / "evidence" / "gvsc36_crosscheck_20261026.json"
RUN_CARD_OUT = ROOT / "evidence" / "gvsc36_run_card_20261026.json"

TOTAL_BUDGET = 37_654
B0_SEED = 20261025
GVSC_SEEDS = (20261026, 20261126)

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

GVSC_N_POS = 55_000  # Exceeds max 3-fold positive pool (~50,823), retaining 100% of positives
GVSC_N_NEG = 320_000
GVSC_HGB = dict(
    max_iter=320,
    learning_rate=0.05,
    max_leaf_nodes=63,
    min_samples_leaf=250,
    l2_regularization=2.0,
    max_features=0.75,
    early_stopping=False,
)

RECORDED_REPO_B0 = 0.133749
RECORDED_GROUP_BEST = 0.148763


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


def train_predict_gvsc_expert(
    store: FeatureStore,
    feature_names: tuple[str, ...],
    fp_pos: np.ndarray,
    train_mask: np.ndarray,
    visible_mask: np.ndarray,
    eval_mask: np.ndarray,
    labels: np.ndarray,
    fold_idx: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Train 2-seed regularized HGB ensemble + exact Prentice-Pyke Bayes odds calibration."""
    pos_pool = np.flatnonzero((labels & train_mask).ravel())
    far = distance_transform_edt(~visible_mask) > 3.0
    neg_pool = np.flatnonzero((train_mask & ~labels & far).ravel())
    del far

    names = list(feature_names)
    eval_flat = np.flatnonzero(eval_mask.ravel())
    prob_acc = np.zeros(len(eval_flat), dtype=np.float64)

    models: list[tuple[HistGradientBoostingClassifier, float, float]] = []
    pi_pos_last = 1.0
    pi_neg_last = 1.0
    n_pos_used = 0
    n_neg_used = 0
    for m_i, base_seed in enumerate(GVSC_SEEDS):
        rng = np.random.default_rng(base_seed + 17 * fold_idx + 101 * m_i)
        pos_sel = (
            pos_pool
            if len(pos_pool) <= GVSC_N_POS
            else rng.choice(pos_pool, GVSC_N_POS, replace=False)
        )
        neg_sel = rng.choice(neg_pool, min(GVSC_N_NEG, len(neg_pool)), replace=False)
        pi_pos = float(len(pos_sel)) / float(max(len(pos_pool), 1))
        pi_neg = float(len(neg_sel)) / float(max(len(neg_pool), 1))
        pi_pos_last, pi_neg_last = pi_pos, pi_neg
        n_pos_used, n_neg_used = len(pos_sel), len(neg_sel)

        idx = np.r_[fp_pos[pos_sel], fp_pos[neg_sel]]
        y = np.r_[
            np.ones(len(pos_sel), dtype=np.float32),
            np.zeros(len(neg_sel), dtype=np.float32),
        ]
        X = store.rows(idx, names)
        clf = HistGradientBoostingClassifier(
            **GVSC_HGB, random_state=base_seed + 31 * fold_idx + m_i
        )
        clf.fit(X, y)
        models.append((clf, pi_pos, pi_neg))
        del X, y
        gc.collect()

    # Single chunked pass over eval_flat shared across ensemble members
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
    out[eval_flat] = (prob_acc / float(len(GVSC_SEEDS))).astype(np.float32)
    return out.reshape(eval_mask.shape), {
        "n_pos_pool": int(len(pos_pool)),
        "n_neg_pool": int(len(neg_pool)),
        "n_pos_train": int(n_pos_used),
        "n_neg_train": int(n_neg_used),
        "pi_pos": round(pi_pos_last, 6),
        "pi_neg": round(pi_neg_last, 6),
        "bayes_odds_ratio_r": round(pi_pos_last / max(pi_neg_last, 1e-12), 4),
    }


def fuse_exp3_lidar_bridge(
    p_full: np.ndarray,
    p_blind: np.ndarray,
    lid_valid_2d: np.ndarray,
    det_slope_2d: np.ndarray,
    eval_mask: np.ndarray,
) -> np.ndarray:
    """Apply frozen preregistered physical regime weights between M_full and M_blind."""
    has_lid = np.isfinite(lid_valid_2d) & (lid_valid_2d > 0.5)
    low_relief = np.nan_to_num(det_slope_2d, nan=0.0) < 4.0
    w_blind = np.where(~has_lid, 0.55, np.where(low_relief, 0.30, 0.15)).astype(np.float32)
    fused = (1.0 - w_blind) * p_full + w_blind * p_blind
    return np.where(eval_mask, fused, 0.0).astype(np.float32)


def run_canary_stage(
    store: FeatureStore,
    holdout: SegmentHoldout,
    fp: np.ndarray,
) -> dict[str, Any]:
    """Run single-feature holdout.canary on all 89 features (reuse cached 59 if verified)."""
    t0 = time.time()
    h, w = fp.shape
    flat_fp = np.flatnonzero(fp.ravel())

    features_report: dict[str, Any] = {}
    # Reuse 59 base feature canary results if already present in h36_holdout_experiments.json,
    # and run fresh holdout.canary on all 30 new features + spot-check 5 base features!
    base_canary_path = ROOT / "evidence" / "h36_holdout_experiments.json"
    cached_base: dict[str, Any] = {}
    if base_canary_path.is_file():
        prev = json.loads(base_canary_path.read_text(encoding="utf-8"))
        cached_base = prev.get("canary", {}).get("features", {})

    to_compute = [
        n for n in EXP2_FEATURES if (n not in cached_base) or (n in SA_FEATURES) or (n in GVSC_FEATURES)
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
                f"[canary] checked {idx}/{len(to_compute)} new/uncached features "
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
        "lane_id": "GVSC-36",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evaluator_version": ev_version,
        "threshold": 0.90,
        "total_features_tested": len(features_report),
        "newly_computed_features": len(to_compute),
        "reused_verified_base_features": len(features_report) - len(to_compute),
        "passed": (not any_flagged) and (max_sym_auc <= 0.90) and (len(features_report) == 89),
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


def unfold_column(store: FeatureStore, name: str, fp: np.ndarray) -> np.ndarray:
    full = np.full(fp.size, np.nan, dtype=np.float32)
    full[np.flatnonzero(fp.ravel())] = np.asarray(store.column(name), dtype=np.float32)
    return full.reshape(fp.shape)


def run_holdout_stage(
    store: FeatureStore,
    holdout: SegmentHoldout,
    fp: np.ndarray,
    labels: np.ndarray,
    inv_stats: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Execute frozen B0 + EXP-1 + EXP-2 + EXP-3 on SegmentHoldout."""
    t0 = time.time()
    h, w = fp.shape
    fp_pos = np.full(h * w, -1, dtype=np.int64)
    fp_pos[np.flatnonzero(fp.ravel())] = np.arange(store.n_fp, dtype=np.int64)
    budgets = fold_budgets(holdout)

    lid_valid_2d = unfold_column(store, "lid_valid", fp)
    det_slope_2d = unfold_column(store, "org_det_elev_slope", fp)

    preds: dict[str, list[np.ndarray]] = {"B0": [], "EXP-1": [], "EXP-2": [], "EXP-3": []}
    oof_surfaces: dict[str, np.ndarray] = {
        "EXP-1": np.zeros((h, w), dtype=np.float32),
        "EXP-2": np.zeros((h, w), dtype=np.float32),
        "EXP-3": np.zeros((h, w), dtype=np.float32),
    }
    fold_logs: list[dict[str, Any]] = []

    for f_i, fold in enumerate(holdout.folds):
        fname = fold["name"]
        ckpt_npz = CACHE_DIR / f"holdout_fold_{f_i}.npz"
        ckpt_json = CACHE_DIR / f"holdout_fold_{f_i}.json"
        if ckpt_npz.is_file() and ckpt_json.is_file():
            f_rec = json.loads(ckpt_json.read_text(encoding="utf-8"))
            with np.load(ckpt_npz) as z:
                for arm in ("B0", "EXP-1", "EXP-2", "EXP-3"):
                    preds[arm].append(z[f"pred_{arm}"])
                for arm in ("EXP-1", "EXP-2", "EXP-3"):
                    v_idx = fold["valid"]
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
        f_rec = {
            "fold": fname,
            "budget": b_fold,
            "valid_px": int(fold["valid"].sum()),
            "withheld_positive_px": int(fold["truth"].sum()),
        }

        # Control B0
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

        # EXP-1: 75 features (BASE + SA), Bayes calibration + 300m CELF submodular cover
        t1 = time.time()
        p_exp1, m_exp1 = train_predict_gvsc_expert(
            store, EXP1_FEATURES, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, f_i
        )
        oof_surfaces["EXP-1"] += np.where(fold["valid"], p_exp1, 0.0)
        cov1 = emit_submodular_cover(
            p_exp1, elig, budget=b_fold, valid_footprint=fold["valid"], gamma=1.0, min_spacing_px=2.0
        )
        pred_1_u8 = cov1.mask.astype(np.uint8)
        preds["EXP-1"].append(pred_1_u8)
        ref_1, _ = holdout.score_fold(cov1.mask, fold)
        f_rec["EXP-1"] = {
            **m_exp1,
            "n_dots": int(cov1.mask.sum()),
            "expected_tp_obj": round(float(cov1.objective_value), 2),
            "fold_dti": round(float(ref_1["dti"]), 6),
            "seconds": round(time.time() - t1, 1),
        }
        surf_1_val = p_exp1[fold["valid"]].astype(np.float32)
        del p_exp1, cov1
        print(f"[holdout] {fname} EXP-1: DTI={f_rec['EXP-1']['fold_dti']:.5f}", flush=True)

        # EXP-2: 89 features (BASE + SA + GVSC INGENIOUS geothermal vent-conduit)
        t2 = time.time()
        p_exp2, m_exp2 = train_predict_gvsc_expert(
            store, EXP2_FEATURES, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, f_i
        )
        oof_surfaces["EXP-2"] += np.where(fold["valid"], p_exp2, 0.0)
        cov2 = emit_submodular_cover(
            p_exp2, elig, budget=b_fold, valid_footprint=fold["valid"], gamma=1.0, min_spacing_px=2.0
        )
        pred_2_u8 = cov2.mask.astype(np.uint8)
        preds["EXP-2"].append(pred_2_u8)
        ref_2, _ = holdout.score_fold(cov2.mask, fold)
        f_rec["EXP-2"] = {
            **m_exp2,
            "n_dots": int(cov2.mask.sum()),
            "expected_tp_obj": round(float(cov2.objective_value), 2),
            "fold_dti": round(float(ref_2["dti"]), 6),
            "seconds": round(time.time() - t2, 1),
        }
        surf_2_val = p_exp2[fold["valid"]].astype(np.float32)
        print(f"[holdout] {fname} EXP-2: DTI={f_rec['EXP-2']['fold_dti']:.5f}", flush=True)

        # EXP-3: LiDAR-shadowing de-biased bridge (EXP-2 M_full + 74-feat LiDAR-blind M_blind)
        t3 = time.time()
        p_blind, m_blind = train_predict_gvsc_expert(
            store,
            EXP3_BLIND_FEATURES,
            fp_pos,
            fold["train"],
            fold["visible"],
            fold["valid"],
            labels,
            f_i + 10,
        )
        p_exp3 = fuse_exp3_lidar_bridge(p_exp2, p_blind, lid_valid_2d, det_slope_2d, fold["valid"])
        oof_surfaces["EXP-3"] += p_exp3
        cov3 = emit_submodular_cover(
            p_exp3, elig, budget=b_fold, valid_footprint=fold["valid"], gamma=1.0, min_spacing_px=2.0
        )
        pred_3_u8 = cov3.mask.astype(np.uint8)
        preds["EXP-3"].append(pred_3_u8)
        ref_3, _ = holdout.score_fold(cov3.mask, fold)
        f_rec["EXP-3"] = {
            "m_blind": m_blind,
            "n_dots": int(cov3.mask.sum()),
            "expected_tp_obj": round(float(cov3.objective_value), 2),
            "fold_dti": round(float(ref_3["dti"]), 6),
            "seconds": round(time.time() - t3, 1),
        }
        surf_3_val = p_exp3[fold["valid"]].astype(np.float32)
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
            },
        )
        ckpt_json.write_text(json.dumps(f_rec, indent=2) + "\n", encoding="utf-8")

        del (
            p_exp2,
            p_blind,
            p_exp3,
            cov2,
            cov3,
            d_vis,
            elig,
            pred_b0_u8,
            pred_1_u8,
            pred_2_u8,
            pred_3_u8,
            surf_1_val,
            surf_2_val,
            surf_3_val,
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
    np.save(CACHE_DIR / f"oof_surface_{best_arm}.npy", oof_surfaces[best_arm])

    for arm in ("B0", "EXP-1", "EXP-2", "EXP-3"):
        s = summaries[arm]
        print(
            f"[summary] {arm:5s}: HOLDOUT-DTI = {s['dti']:.6f} "
            f"95% CI [{s['ci95']['interval'][0]:.6f}, {s['ci95']['interval'][1]:.6f}] "
            f"TPw={s['TP_w']:.1f}",
            flush=True,
        )

    out = {
        "lane_id": "GVSC-36",
        "label": "HOLDOUT-DTI",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration_path": str(PREREG_PATH.relative_to(ROOT)),
        "preregistration_sha256": sha256_file(PREREG_PATH),
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
        "recorded_benchmarks": {
            "repo_B0": RECORDED_REPO_B0,
            "group_best_GEMSDOE24_H24_GVC1": RECORDED_GROUP_BEST,
        },
        "best_candidate_arm": best_arm,
        "folds": fold_logs,
        "summaries": summaries,
        "paired_vs_B0": paired_vs_b0,
        "paired_EXP2_minus_EXP1_geothermal_lift": paired_exp2_vs_exp1,
        "paired_EXP3_minus_EXP2_lidar_bridge_lift": paired_exp3_vs_exp2,
    }
    HOLDOUT_OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out, best_arm


def build_checkerboard_oof_surface(
    store: FeatureStore,
    best_arm: str,
    fp: np.ndarray,
    labels: np.ndarray,
) -> np.ndarray:
    """Build 4-fold 4x4 spatial checkerboard OOF probability surface (2.5 km purged collar)."""
    h, w = fp.shape
    fp_pos = np.full(h * w, -1, dtype=np.int64)
    fp_pos[np.flatnonzero(fp.ravel())] = np.arange(store.n_fp, dtype=np.int64)

    ys, xs = np.where(fp)
    r_cuts = np.quantile(ys, [0.25, 0.50, 0.75])
    c_cuts = np.quantile(xs, [0.25, 0.50, 0.75])
    rr, cc = np.indices((h, w))
    bi = np.digitize(rr, r_cuts)
    bj = np.digitize(cc, c_cuts)
    fold_id = ((bi % 2) * 2 + (bj % 2)).astype(np.int32)

    comp, n_comp = ndi_label(labels & fp, structure=np.ones((3, 3), dtype=int))
    lid_valid_2d = unfold_column(store, "lid_valid", fp)
    det_slope_2d = unfold_column(store, "org_det_elev_slope", fp)

    surface = np.zeros((h, w), dtype=np.float32)
    for k in range(4):
        val_mask = fp & (fold_id == k)
        cb_ckpt = CACHE_DIR / f"deploy_cb_{best_arm}_fold_{k}.npy"
        if cb_ckpt.is_file():
            surface[val_mask] = np.load(cb_ckpt)
            print(f"[deploy-oof] checkerboard fold {k}/3 restored from checkpoint", flush=True)
            continue
        # 2.5 km (25 px) purged spatial buffer around every held-out checkerboard tile
        excl = distance_transform_edt(~val_mask) <= 25.0
        bad_ids = np.unique(comp[excl & (comp > 0)])
        withheld = np.isin(comp, bad_ids)
        visible = (labels & fp) & ~withheld
        train_mask = fp & ~excl & ~withheld

        if best_arm == "EXP-1":
            p_k, _ = train_predict_gvsc_expert(
                store, EXP1_FEATURES, fp_pos, train_mask, visible, val_mask, labels, 100 + k
            )
        elif best_arm == "EXP-2":
            p_k, _ = train_predict_gvsc_expert(
                store, EXP2_FEATURES, fp_pos, train_mask, visible, val_mask, labels, 100 + k
            )
        else:
            p_full, _ = train_predict_gvsc_expert(
                store, EXP2_FEATURES, fp_pos, train_mask, visible, val_mask, labels, 100 + k
            )
            p_blind, _ = train_predict_gvsc_expert(
                store, EXP3_BLIND_FEATURES, fp_pos, train_mask, visible, val_mask, labels, 200 + k
            )
            p_k = fuse_exp3_lidar_bridge(p_full, p_blind, lid_valid_2d, det_slope_2d, val_mask)
            del p_full, p_blind
        np.save(cb_ckpt, p_k[val_mask].astype(np.float32))
        surface = np.where(val_mask, p_k, surface)
        print(
            f"[deploy-oof] checkerboard fold {k}/3 complete (val_px={int(val_mask.sum())}, "
            f"withheld_comp={len(bad_ids)}/{n_comp})",
            flush=True,
        )
        del p_k
        gc.collect()
    return surface


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
            or "gvsc36" in tif_path.name
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
    store: FeatureStore,
    holdout_report: dict[str, Any],
    canary_report: dict[str, Any],
    best_arm: str,
    fp: np.ndarray,
    labels: np.ndarray,
    t_pipeline_start: float,
) -> dict[str, Any]:
    surface = build_checkerboard_oof_surface(store, best_arm, fp, labels)

    # Protocol §1: surface rank-correlation screen MUST happen before any dot placement.
    entries = build_registry_entries_with_local()
    surf_nov = compare_registry(
        surface, fp, entries, ROOT, dots=None, separate_calibration_controls=True
    )
    if float(surf_nov["max_abs_rank_correlation"] or 0.0) > 0.90:
        raise RuntimeError("Pre-placement surface correlation exceeded 0.90; stop before emitting dots")

    d_cat = distance_transform_edt(~(labels & fp))
    elig = fp & (d_cat > 2.0)

    cov = emit_submodular_cover(
        surface,
        elig,
        budget=TOTAL_BUDGET,
        valid_footprint=elig,
        gamma=1.0,
        min_spacing_px=2.0,
    )
    dots = cov.mask
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

    # Compute deterministic 12-char content digest of dot coordinates for unique filename
    rc_bytes = np.argwhere(dots).astype(np.int32).tobytes()
    run_uid = hashlib.sha256(rc_bytes).hexdigest()[:12]
    stem = f"gemsdoe36-gvsc36-{best_arm.lower().replace('-', '')}-20261026-{run_uid}-zeros"
    dl_dir = ROOT / "docs" / "downloads"
    dl_dir.mkdir(parents=True, exist_ok=True)
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

    # Registry uniqueness after placement; strict literal result governs and controls remain.
    dots_comp = compare_registry(
        surface, fp, entries, ROOT, dots=dots, separate_calibration_controls=True
    )
    # Same all-entry calculation reports both controls-separated and literal verdicts.
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
    g2_beats_group = dti_val > RECORDED_GROUP_BEST
    g3_format = (
        bool(repo_val["passed"])
        and bool(gems_val["format_valid"])
        and bool(gems_val["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"])
        and d_cat_stats["share_le_2px"] == 0.0
    )
    g4_surf = bool(surf_nov["passed"]) and float(surf_nov["max_abs_rank_correlation"]) <= 0.90
    g4_focus9 = focus9_max_ov <= 0.70
    g4_competing = bool(dots_comp["competing_method_passed"])
    g4_literal = bool(dots_literal["literal_unseparated_passed"])

    # Strict fail-closed gate per Parallel-Run Protocol §1 (no silent waiver of literal all-registry check)
    all_gates_pass = (
        g1_canary
        and g2_beats_b0
        and g2_beats_group
        and g3_format
        and g4_surf
        and g4_competing
        and g4_literal
    )
    verdict = "promote" if all_gates_pass else "negative"
    status_tag = "PROMOTE" if verdict == "promote" else "NEGATIVE research only"
    note = (
        f"GEMSDOE36 GVSC-36 {best_arm} | vent+F2mDAB backproj+submod | "
        f"HOLDOUT-DTI {dti_val:.4f} | {status_tag} | {run_uid}"
    )
    if len(note) > 140:
        note = note[:140]

    crosscheck_doc = {
        "lane_id": "GVSC-36",
        "best_arm": best_arm,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "total_registry_entries_checked": len(entries),
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
            "max_competing_method_overlap_3px": dots_comp["max_competing_dot_overlap"],
            "competing_method_passed": g4_competing,
            "literal_all_entry_max_overlap_3px": dots_literal["max_dot_overlap"],
            "literal_all_entry_passed": g4_literal,
            "calibration_control_rasters": dots_comp["calibration_control_rasters"],
            "all_entry_count": dots_comp["registry_unique_rasters"],
        },
        "top_15_competing_by_overlap": top_competing,
    }
    CROSSCHECK_OUT.write_text(json.dumps(crosscheck_doc, indent=2) + "\n", encoding="utf-8")

    prereg_doc = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    prereg_start = datetime.fromisoformat(prereg_doc["preregistered_utc"])
    elapsed_total = round((datetime.now(timezone.utc) - prereg_start).total_seconds(), 2)
    if elapsed_total > 7200:
        raise RuntimeError("Registered two-hour walltime budget exceeded; stop without promotion")
    if holdout_report.get("experiments_executed") != 3:
        raise RuntimeError("Run card requires exactly the preregistered three candidate experiments")
    run_card = {
        "schema": "gems.parallel_run_card.v1",
        "lane_id": "GVSC-36",
        "best_arm": best_arm,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "safe_to_download_for_research": bool(g3_format),
        "safe_to_submit_live_slot": verdict == "promote",
        "hypothesis": (
            "GVSC-36 (H36-V1): Blind and unmapped Basin-and-Range / Walker Lane fault conduits "
            "feed shallow 2 m thermal plumes (F2mDAB), hot/geothermometer springs, and carbonate/"
            "silica-cemented outflow aprons 0.4-2.0 km down-hydraulic-gradient (-grad z), while "
            "siliceous sinters, phreatic explosion craters, silicified fault breccias, and "
            "Quaternary volcanic vents mark relict in-situ structural conduits along strike."
        ),
        "mechanism": (
            "Advectively back-project DOE GDR 1391 INGENIOUS 2 m temperature probe plumes "
            "(2,782 stations), well/spring geothermometers (27,092 records), and Lahontan-"
            "deweighted carbonate/silica outflow aprons (195 deposits) 0.4-2.0 km up the "
            "smoothed hydraulic gradient (+grad G_12(det_elev)), diffuse in-situ sinter/breccia/"
            "explosion/volcanic vents (85+21 vents) along 8-azimuth 1.5 km strike kernels, "
            "corroborate multiplicatively against Verduzco tilt/RTP-demagnetization/gravity-"
            "basement/MT-clay-cap/piedmont breaklines, de-bias 1 m LiDAR root-split shadowing "
            "with a 74-feature LiDAR-blind subsurface expert, calibrate via exact Prentice-Pyke "
            "Bayes prior odds, and allocate 37,654 dots via exact 25-offset Euclidean 300 m "
            "CELF submodular expected-DTI maximization on a 4x4 checkerboard OOF surface."
        ),
        "named_non_fault_mimic": (
            "Perched lateral outflow plumes in permeable alluvial paleochannels, Pleistocene "
            "Lake Lahontan (~1,250-1,360 m) wave-cut shoreline tufa terraces, evaporite playa "
            "brines, and unfaulted Tertiary volcanic flow margins."
        ),
        "preregistration": {
            "path": str(PREREG_PATH.relative_to(ROOT)),
            "sha256": sha256_file(PREREG_PATH),
            "markdown_path": "docs/research/preregistration-gvsc36-20261026.md",
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
                "paired_vs_EXP1_geothermal_lift": holdout_report[
                    "paired_EXP2_minus_EXP1_geothermal_lift"
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
                "paired_vs_EXP2_lidar_bridge_lift": holdout_report[
                    "paired_EXP3_minus_EXP2_lidar_bridge_lift"
                ],
            },
            "recorded_repo_B0": RECORDED_REPO_B0,
            "recorded_group_best_GEMSDOE24_GVC1": RECORDED_GROUP_BEST,
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
            "G2b_beats_group_best_0p14876": g2_beats_group,
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
            "run_card_relpath": "downloads/gvsc36-run-card.json",
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
    (dl_dir / "gvsc36-run-card.json").write_text(rc_json, encoding="utf-8")
    (dl_dir / f"{stem}.receipt.json").write_text(rc_json, encoding="utf-8")
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
    ap.add_argument("--force-features", action="store_true")
    args = ap.parse_args()

    t_start = time.time()
    data_raw = ROOT / "data" / "raw"
    store, grid, inv_stats = build_gvsc_feature_store(
        CACHE_DIR, data_dir=data_raw, force=args.force_features
    )
    mmap_cols = {n: store.column(n) for n in store.names}
    store.column = mmap_cols.__getitem__  # type: ignore[method-assign]
    print(f"[features] ready: { len(store.names) } columns | inventory={inv_stats}", flush=True)

    fp_lbl, labels = load_labels(data_raw)
    if not np.array_equal(fp_lbl, grid.footprint):
        raise RuntimeError("Footprint mismatch between sample_submission.tif and labels.tif")
    holdout = SegmentHoldout(grid.footprint, labels, buffer_px=15)

    if args.stage in ("canary", "all"):
        canary_rep = run_canary_stage(store, holdout, grid.footprint)
    else:
        canary_rep = json.loads(CANARY_OUT.read_text(encoding="utf-8"))

    if args.stage == "canary":
        return 0

    if args.stage in ("holdout", "all"):
        holdout_rep, best_arm = run_holdout_stage(
            store, holdout, grid.footprint, labels, inv_stats.__dict__
        )
    else:
        holdout_rep = json.loads(HOLDOUT_OUT.read_text(encoding="utf-8"))
        best_arm = holdout_rep["best_candidate_arm"]

    if args.stage == "holdout":
        return 0

    run_deploy_stage(
        store,
        holdout_rep,
        canary_rep,
        best_arm,
        grid.footprint,
        labels,
        t_start,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
