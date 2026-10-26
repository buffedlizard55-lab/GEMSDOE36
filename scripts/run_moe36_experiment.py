#!/usr/bin/env python3
"""MOE36: cross-fitted regime-gated mixture of complementary fault experts.

Lane (preregistered in evidence/moe36_preregistration_20261026.json):
  Experts (disjoint physical feature sets, all from official competition /
  USGS-derived inputs already restored in data/raw; NO prior submission
  raster, NO SGMC catalogue raster, NO qfaults traces):
    E_RAW   : 19 GeoDAWN competition bands (training_features.tif)
    E_LOCAL : 17 CTRB local potential-field / hydrothermal / LiDAR features
    E_STRUCT:  8 CTRB 1.5 km strike-worm / relay-bridge / tip-lobe features
  Holdout: shared template gems.holdout.SegmentHoldout
    (gems-segment-pooled-v1, whole segments, 15 px buffer, alpha .2 beta .8,
     300 m triangular kernel). Features for a fold use visible faults only
    for labels/sampling; static physical features are label-free.
  Experiments (<=3): EXP-1 equal rank fusion; EXP-2 cross-fitted fold/regime
    gated fusion; EXP-3 EXP-2 + agreement bonus.
  Emission: gemsdoe36.ctrb.submodular_dti_emit outside d_visible > 2 px.
Outputs: evidence/moe36_holdout_20261026.json (+ OOF surfaces in .cache),
         and, for the winning experiment, a full-catalogue refit surface
         saved to .cache/moe36/full_surface.npy for the submission builder.
"""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems.holdout import SegmentHoldout  # noqa: E402
from gemsdoe36.ctrb import (  # noqa: E402
    ALL_FEATURE_NAMES,
    LOCAL_FEATURE_NAMES,
    STRUCTURAL_FEATURE_NAMES,
    build_or_load_feature_stack,
    submodular_dti_emit,
)

RAW_DIR = ROOT / "data" / "raw"
CACHE = ROOT / ".cache" / "moe36"
BUDGET = 37_654
SEED = 20261026
B0_REF = 0.13375


def load_grid():
    with rasterio.open(RAW_DIR / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(RAW_DIR / "labels.tif") as ds:
        lbl = ds.read(1)
    catalogue = footprint & np.isfinite(lbl) & (lbl > 0.5)
    return footprint, catalogue


def raw19_matrix(footprint):
    """Footprint-indexed (N_fp,19) float32 memmap from training_features.tif."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / "raw19_fp.npy"
    fp_ids = np.flatnonzero(footprint)
    if f.exists():
        return np.load(f, mmap_mode="r")
    out = np.lib.format.open_memmap(f, mode="w+", dtype=np.float32, shape=(len(fp_ids), 19))
    with rasterio.open(RAW_DIR / "training_features.tif") as ds:
        for b in range(1, 20):
            band = ds.read(b)
            vals = band.ravel()[fp_ids].astype(np.float32)
            vals[~np.isfinite(vals) | (vals < -1e30)] = np.nan
            out[:, b - 1] = vals
            del band
    out.flush()
    return np.load(f, mmap_mode="r")


def fit_predict(X, cols, train_fp, vis_fp, dvis_fp, target_fp, seed):
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(train_fp & vis_fp)
    neg_pool = np.flatnonzero(train_fp & (~vis_fp) & (dvis_fp >= 3.0))
    neg = rng.choice(neg_pool, size=min(len(neg_pool), 4 * len(pos)), replace=False)
    idx = np.sort(np.concatenate([pos, neg]))
    y = vis_fp[idx].astype(np.int32)
    clf = HistGradientBoostingClassifier(
        max_iter=180, learning_rate=0.055, max_leaf_nodes=31, max_depth=6,
        min_samples_leaf=80, l2_regularization=2.5, random_state=seed,
    )
    clf.fit(np.asarray(X[idx][:, cols], dtype=np.float32), y)
    pred = np.zeros(len(train_fp), dtype=np.float32)
    tgt = np.flatnonzero(target_fp)
    for s in range(0, len(tgt), 300_000):
        sub = tgt[s:s + 300_000]
        pred[sub] = clf.predict_proba(np.asarray(X[sub][:, cols], dtype=np.float32))[:, 1]
    del clf
    gc.collect()
    return pred


def rank_norm(vals, mask_fp):
    out = np.zeros_like(vals)
    idx = np.flatnonzero(mask_fp)
    v = vals[idx]
    order = np.argsort(v, kind="mergesort")
    r = np.empty(len(v), dtype=np.float32)
    r[order] = (np.arange(len(v), dtype=np.float32) + 0.5) / len(v)
    out[idx] = r
    return out


def topk_dti(surface2d, fold, holdout, k):
    d = distance_transform_edt(~fold["visible"])
    allowed = fold["valid"] & (d > 2.0)
    cand = np.where(allowed, surface2d, -1.0)
    flat = np.argpartition(cand.ravel(), -k)[-k:] if k < cand.size else np.arange(cand.size)
    pred = np.zeros(cand.size, dtype=np.uint8)
    pred[flat] = 1
    res, _ = holdout.score_fold(pred.reshape(cand.shape), fold)
    return float(res["dti"])


def emit_fold(surface2d, fold, k):
    d = distance_transform_edt(~fold["visible"])
    allowed = fold["valid"] & (d > 2.0)
    p = submodular_dti_emit(surface2d, allowed, footprint=None, n_dots=k,
                             dstar_ref=0.22, min_gain=0.0)
    return (p > 0.5).astype(np.uint8)


def main():
    t0 = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    footprint, catalogue = load_grid()
    holdout = SegmentHoldout(footprint, catalogue, buffer_px=15)
    fp_ids = np.flatnonzero(footprint)
    n_fp = len(fp_ids)
    print(f"[moe36] holdout: {holdout.n_components} components, {n_fp:,} fp px", flush=True)

    Xc, _meta = build_or_load_feature_stack(RAW_DIR, ROOT / "data" / "prepared")
    Xr = raw19_matrix(footprint)
    print("[moe36] feature stacks ready", flush=True)

    # ---- leakage canary on all 44 features (batched, shared template) ----
    canary_file = CACHE / "canary.json"
    if canary_file.exists():
        canary = json.loads(canary_file.read_text())
    else:
        feats = {}
        names19 = [f"raw19_b{b:02d}" for b in range(1, 20)]
        for j, nm in enumerate(names19):
            g = np.zeros(footprint.shape, dtype=np.float32)
            g.ravel()[fp_ids] = np.nan_to_num(np.asarray(Xr[:, j]), nan=0.0)
            feats[nm] = g
        for j, nm in enumerate(ALL_FEATURE_NAMES):
            g = np.zeros(footprint.shape, dtype=np.float32)
            g.ravel()[fp_ids] = np.asarray(Xc[:, j])
            feats[nm] = g
        canary = holdout.canary(feats, seed=SEED)
        canary_file.write_text(json.dumps(canary, indent=1, default=float))
        del feats
        gc.collect()
    max_auc = max(
        max([max(v["pooled_auc"], 1 - v["pooled_auc"])]
            + [max(f["auc"], 1 - f["auc"]) for f in v["folds"]])
        for v in canary["features"].values()
    )
    print(f"[moe36] canary max two-polarity AUC={max_auc:.4f} (cap 0.90)", flush=True)
    if max_auc > 0.90:
        raise SystemExit("LEAKAGE CANARY TRIPPED")

    lidar_valid = None
    with rasterio.open(RAW_DIR / "external" / "lidar_scarp_features_u8.tif") as ds:
        arr = ds.read()
        lidar_valid = np.any(arr > 0, axis=0) & footprint
    del arr

    experts = {
        "E_RAW": (Xr, list(range(19))),
        "E_LOCAL": (Xc, [ALL_FEATURE_NAMES.index(n) for n in LOCAL_FEATURE_NAMES]),
        "E_STRUCT": (Xc, [ALL_FEATURE_NAMES.index(n) for n in STRUCTURAL_FEATURE_NAMES]),
    }

    # ---- OOF expert surfaces (rank-normalised per fold) ----
    oof_ranks = {k: np.zeros(n_fp, dtype=np.float32) for k in experts}
    expert_fold_dti = {k: [] for k in experts}
    expert_fold_dti_lidar = {k: [] for k in experts}   # lidar-covered part
    expert_fold_dti_gap = {k: [] for k in experts}     # lidar-gap part
    fold_budgets = []
    for fold in holdout.folds:
        valid_fp = fold["valid"].ravel()[fp_ids]
        train_fp = fold["train"].ravel()[fp_ids]
        vis_fp = fold["visible"].ravel()[fp_ids]
        dvis = distance_transform_edt(~fold["visible"])
        dvis_fp = dvis.ravel()[fp_ids]
        k_fold = round(BUDGET * float(fold["valid"].sum()) / float(footprint.sum()))
        fold_budgets.append(k_fold)
        from gems.metric import dti_score_fast
        for ei, (ename, (X, cols)) in enumerate(experts.items()):
            surf_file = CACHE / f"oof_{ename}_fold{fold['id']}.npy"
            if surf_file.exists():
                rank_fp = np.load(surf_file)
            else:
                pred = fit_predict(X, cols, train_fp, vis_fp, dvis_fp, valid_fp,
                                   seed=SEED + 100 * fold["id"] + ei)
                rank_fp = rank_norm(pred, valid_fp)
                np.save(surf_file, rank_fp)
                del pred
            oof_ranks[ename][valid_fp] = rank_fp[valid_fp]
            surf2d = np.zeros(footprint.shape, dtype=np.float32)
            surf2d.ravel()[fp_ids] = rank_fp
            expert_fold_dti[ename].append(topk_dti(surf2d, fold, holdout, k_fold))
            for _regime, rmask, store in (
                ("lidar", lidar_valid, expert_fold_dti_lidar),
                ("gap", ~lidar_valid, expert_fold_dti_gap),
            ):
                allowed = fold["valid"] & rmask & (dvis > 2.0)
                kk = max(50, round(k_fold * float(allowed.sum()) / max(1.0, float((fold["valid"] & (dvis > 2.0)).sum()))))
                cand = np.where(allowed, surf2d, -1.0)
                flat = np.argpartition(cand.ravel(), -kk)[-kk:]
                pred_bin = np.zeros(cand.size, dtype=np.uint8)
                pred_bin[flat] = 1
                store[ename].append(float(dti_score_fast(
                    pred_bin.reshape(cand.shape), fold["truth"],
                    valid_mask=fold["valid"] & rmask)["dti"]))
            del surf2d
            print(f"[moe36] fold {fold['name']} {ename} topk-DTI={expert_fold_dti[ename][-1]:.4f}", flush=True)
        del dvis
        gc.collect()

    def gated_weights(fold_id, regime_store=None):
        # weights from OTHER folds only (cross-fitted gating)
        w = {}
        for ename in experts:
            src = (regime_store or expert_fold_dti)[ename]
            others = [src[j] for j in range(4) if j != fold_id]
            w[ename] = float(np.mean(others))
        m = max(w.values())
        ex = {k: float(np.exp((v - m) / 0.02)) for k, v in w.items()}
        s = sum(ex.values())
        return {k: v / s for k, v in ex.items()}

    experiments = {}
    surfaces = {}
    for exp_id in ("EXP-1", "EXP-2", "EXP-3"):
        fused = np.zeros(n_fp, dtype=np.float32)
        for fold in holdout.folds:
            valid_fp = fold["valid"].ravel()[fp_ids]
            lid_fp = lidar_valid.ravel()[fp_ids]
            if exp_id == "EXP-1":
                wts = [(e, 1 / 3) for e in experts]
                fused[valid_fp] = sum(w * oof_ranks[e][valid_fp] for e, w in wts)
            else:
                wl = gated_weights(fold["id"], expert_fold_dti_lidar)
                wg = gated_weights(fold["id"], expert_fold_dti_gap)
                f = np.zeros(int(valid_fp.sum()), dtype=np.float32)
                idxv = np.flatnonzero(valid_fp)
                for e in experts:
                    f += np.where(lid_fp[idxv], wl[e], wg[e]) * oof_ranks[e][idxv]
                if exp_id == "EXP-3":
                    agree = np.minimum.reduce([oof_ranks[e][idxv] for e in experts])
                    f = f + 0.25 * agree
                fused[idxv] = f
        surfaces[exp_id] = fused
        preds = []
        for fold in holdout.folds:
            surf2d = np.zeros(footprint.shape, dtype=np.float32)
            surf2d.ravel()[fp_ids] = fused
            preds.append(emit_fold(surf2d, fold, fold_budgets[fold["id"]]))
            del surf2d
        experiments[exp_id] = holdout.summarize(preds)
        experiments[exp_id]["predictions_dots"] = [int(p.sum()) for p in preds]
        print(f"[moe36] {exp_id} HOLDOUT-DTI={experiments[exp_id]['dti']:.6f} "
              f"CI={experiments[exp_id]['ci95']}", flush=True)
        del preds
        gc.collect()

    # each expert alone with same emission (control)
    controls = {}
    for ename in experts:
        preds = []
        for fold in holdout.folds:
            surf2d = np.zeros(footprint.shape, dtype=np.float32)
            surf2d.ravel()[fp_ids] = oof_ranks[ename]
            preds.append(emit_fold(surf2d, fold, fold_budgets[fold["id"]]))
            del surf2d
        controls[ename] = holdout.summarize(preds)
        print(f"[moe36] control {ename} HOLDOUT-DTI={controls[ename]['dti']:.6f}", flush=True)
        del preds
        gc.collect()

    best_id = max(experiments, key=lambda k: experiments[k]["dti"])
    # paired comparison best vs strongest expert control
    def emit_set(fused):
        out = []
        for fold in holdout.folds:
            s2 = np.zeros(footprint.shape, dtype=np.float32)
            s2.ravel()[fp_ids] = fused
            out.append(emit_fold(s2, fold, fold_budgets[fold["id"]]))
            del s2
        return out
    best_ctrl = max(controls, key=lambda k: controls[k]["dti"])
    paired = holdout.compare_paired(emit_set(surfaces[best_id]),
                                    emit_set(oof_ranks[best_ctrl]))
    result = {
        "schema": "gemsdoe36-moe36-holdout-v1",
        "label": "HOLDOUT-DTI",
        "evaluator_version": experiments[best_id]["evaluator_version"],
        "n_withheld_positives": experiments[best_id]["n_withheld_positive_pixels"],
        "canary_max_two_polarity_auc": float(max_auc),
        "canary_passed": bool(max_auc <= 0.90),
        "expert_fold_topk_dti_diag": expert_fold_dti,
        "expert_fold_topk_dti_lidar": expert_fold_dti_lidar,
        "expert_fold_topk_dti_gap": expert_fold_dti_gap,
        "controls_single_expert_emission": {
            k: {"dti": v["dti"], "ci95": v["ci95"]} for k, v in controls.items()
        },
        "experiments": {
            k: {"dti": v["dti"], "ci95": v["ci95"], "folds": v["folds"],
                "dots": v["predictions_dots"]} for k, v in experiments.items()
        },
        "best_experiment": best_id,
        "best_dti": experiments[best_id]["dti"],
        "paired_vs_best_single_expert": paired,
        "B0_reference_dti_same_evaluator": B0_REF,
        "beats_B0": bool(experiments[best_id]["dti"] > B0_REF),
        "elapsed_sec": round(time.time() - t0, 1),
    }
    (ROOT / "evidence" / "moe36_holdout_20261026.json").write_text(
        json.dumps(result, indent=1, default=float) + "\n")
    np.save(CACHE / "oof_surface_best.npy", surfaces[best_id])
    (CACHE / "best_experiment.txt").write_text(best_id + "\n")
    print(json.dumps({"best": best_id, "dti": result["best_dti"],
                      "beats_B0": result["beats_B0"]}, indent=1))


if __name__ == "__main__":
    main()
