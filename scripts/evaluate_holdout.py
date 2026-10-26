#!/usr/bin/env python3
"""Parallel-Run Holdout Evaluation, Leakage Canary, 107-Raster Uniqueness Gate,
and Automated Submission Bundle Builder for GEMSDOE36 (H36-CTRB).

Strictly respects:
  - Frozen preregistration: docs/research/preregistration_2026-10-25.md
  - Experiment budget: <= 3 experiments (EXP-1, EXP-2, EXP-3) + 2 leak-free controls
  - Shared evaluator: SegmentHoldout ('gems-segment-pooled-v1', 60,988 withheld positives,
    3,199 components, 15 px = 1.5 km spatial buffer, alpha=0.2, beta=0.8, R=300 m)
  - Single-feature two-polarity leakage canary (AUC <= 0.90 on all 25 features)
  - 107-raster registry novelty gate on BOTH pre-placement continuous surface AND final dots
"""

from __future__ import annotations

import gc
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

from gems.holdout import SegmentHoldout
from gems.metric import ridge_nms, select_top_positive
from gems.novelty import compare_registry
from gems.submission import check_variants as gems_check_variants
from gemsdoe36.ctrb import (
    ALL_FEATURE_NAMES,
    LOCAL_FEATURE_NAMES,
    RAW_BAND_NAMES,
    build_or_load_feature_stack,
    fill_nearest_valid,
    fit_predict_nsq_pcc_fold,
    submodular_dti_emit,
    unsupervised_concordance_surface,
)
from gemsdoe36.submission import validate_submission, write_submission_bundle

FULL_GRID_DOT_BUDGET = 36_800
DSTAR_REF = 0.22


def _load_footprint_and_catalogue(raw_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(raw_dir / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    lbl_path = (
        raw_dir / "labels.tif"
        if (raw_dir / "labels.tif").is_file()
        else raw_dir / "existing_faults.tif"
    )
    with rasterio.open(lbl_path) as ds:
        lbl = ds.read(1)
        catalogue = footprint & np.isfinite(lbl) & (lbl > 0.5)
    return footprint, catalogue


def run_batched_canary(
    holdout: SegmentHoldout,
    X_fp: np.ndarray,
    footprint: np.ndarray,
    batch_size: int = 5,
) -> dict[str, Any]:
    """Run SegmentHoldout.canary across all 25 features in 5-feature batches (<250 MB RAM)."""
    fp_ids = np.flatnonzero(footprint)
    merged_features: dict[str, Any] = {}
    meta_out: dict[str, Any] = {}
    for b0 in range(0, len(ALL_FEATURE_NAMES), batch_size):
        names = ALL_FEATURE_NAMES[b0 : b0 + batch_size]
        batch_dict: dict[str, np.ndarray] = {}
        for nm in names:
            col = ALL_FEATURE_NAMES.index(nm)
            g = np.zeros(footprint.shape, dtype=np.float32)
            g.ravel()[fp_ids] = X_fp[:, col]
            batch_dict[nm] = g
        res = holdout.canary(batch_dict, seed=20261025)
        merged_features.update(res["features"])
        meta_out = res
        del batch_dict
        gc.collect()

    max_sym = max(
        max(
            [max(v["pooled_auc"], 1.0 - v["pooled_auc"])]
            + [max(f["auc"], 1.0 - f["auc"]) for f in v["folds"]]
        )
        for v in merged_features.values()
    )
    passed = not any(v["leakage_suspected"] for v in merged_features.values())
    return {
        "diagnostic": meta_out["diagnostic"],
        "evaluator_version": meta_out["evaluator_version"],
        "threshold": meta_out["threshold"],
        "two_polarities_checked": True,
        "passed": passed,
        "max_symmetric_auc": round(float(max_sym), 6),
        "n_features_checked": len(merged_features),
        "features": merged_features,
    }


def eval_ctrl_legacy_h6_static_and_nosgmc(
    holdout: SegmentHoldout, raw_dir: Path
) -> dict[str, Any]:
    """CTRL-1: Evaluate the prior repo's static H6 submission on SegmentHoldout (without copying)."""
    h6_path = (
        ROOT
        / "docs/downloads/GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif"
    )
    with rasterio.open(h6_path) as ds:
        h6_bin = (np.isfinite(ds.read(1)) & (ds.read(1) > 0.5)).astype(np.float32)

    preds = []
    for fold in holdout.folds:
        d_vis = distance_transform_edt(~fold["visible"])
        p = np.where(fold["valid"] & (d_vis > 2.0), h6_bin, 0.0).astype(np.uint8)
        preds.append(p)
    return {
        "id": "CTRL-1-Legacy-H6",
        "role": "prior_repo_line_a_reference_control",
        "summary": holdout.summarize(preds),
        "predictions": preds,
    }


def eval_ctrl_raw19_hgb_oof(
    holdout: SegmentHoldout, raw_dir: Path, footprint: np.ndarray
) -> dict[str, Any]:
    """CTRL-2: Reconstructed 19-band raw official training_features HGB(d=3) + ridge NMS OOF control."""
    fp_ids = np.flatnonzero(footprint)
    n_fp = fp_ids.size
    raw_idx = distance_transform_edt(~footprint, return_distances=False, return_indices=True)
    nearest_yx = (raw_idx[0].astype(np.int16), raw_idx[1].astype(np.int16))
    del raw_idx
    X19 = np.empty((n_fp, len(RAW_BAND_NAMES)), dtype=np.float32)
    with rasterio.open(raw_dir / "training_features.tif") as ds:
        for i in range(len(RAW_BAND_NAMES)):
            arr = fill_nearest_valid(
                ds.read(i + 1).astype(np.float32), footprint, nearest_yx=nearest_yx
            )
            X19[:, i] = arr.ravel()[fp_ids]
            del arr
    del nearest_yx
    gc.collect()

    preds = []
    for fold in holdout.folds:
        rng = np.random.default_rng(20261025 + fold["id"])
        tr_fp = fold["train"].ravel()[fp_ids]
        vis_fp = fold["visible"].ravel()[fp_ids]
        pos_ids = np.flatnonzero(tr_fp & vis_fp)
        neg_pool = np.flatnonzero(tr_fp & (~vis_fp))
        neg_ids = rng.choice(neg_pool, size=min(neg_pool.size, pos_ids.size * 4), replace=False)
        s_ids = np.concatenate([pos_ids, neg_ids])
        y_s = np.concatenate(
            [np.ones(pos_ids.size, dtype=np.int32), np.zeros(neg_ids.size, dtype=np.int32)]
        )
        clf = HistGradientBoostingClassifier(
            max_iter=150, max_depth=3, learning_rate=0.06, random_state=20261025 + fold["id"]
        )
        clf.fit(X19[s_ids], y_s)

        val_fp_mask = fold["valid"].ravel()[fp_ids]
        val_idx = np.flatnonzero(val_fp_mask)
        p_val = clf.predict_proba(X19[val_idx])[:, 1].astype(np.float32)
        surf = np.zeros(footprint.shape, dtype=np.float32)
        surf.ravel()[fp_ids[val_idx]] = p_val

        d_vis = distance_transform_edt(~fold["visible"])
        skel = ridge_nms(surf, fold["valid"], sigma=1.0)
        elig = skel & fold["valid"] & (d_vis > 2.0)
        k_fold = round(FULL_GRID_DOT_BUDGET * (float(fold["valid"].sum()) / float(n_fp)))
        sel = select_top_positive(surf, elig, k_fold)
        preds.append(sel.astype(np.uint8))

    del X19
    gc.collect()
    return {
        "id": "CTRL-2-Raw19-HGB-d3-OOF",
        "role": "raw_19band_hgb_ridge_nms_control",
        "summary": holdout.summarize(preds),
        "predictions": preds,
    }


def eval_exp1_unsupervised(
    holdout: SegmentHoldout, X_fp: np.ndarray, footprint: np.ndarray
) -> dict[str, Any]:
    """EXP-1 (1/3 budget): Label-free 4-pillar concordance + Dinkelbach-Submodular 300 m emission."""
    t0 = time.time()
    surf = unsupervised_concordance_surface(X_fp, footprint)
    n_fp = float(footprint.sum())
    preds = []
    for fold in holdout.folds:
        d_vis = distance_transform_edt(~fold["visible"])
        allowed = fold["valid"] & (d_vis > 2.0)
        k_fold = round(FULL_GRID_DOT_BUDGET * (float(fold["valid"].sum()) / n_fp))
        p_fold = submodular_dti_emit(
            surf,
            allowed,
            footprint=footprint,
            n_dots=k_fold,
            dstar_ref=DSTAR_REF,
            min_gain=0.0,
        )
        preds.append((p_fold > 0.5).astype(np.uint8))
    return {
        "id": "EXP-1-H36-Unsup-Submod",
        "experiment_index": 1,
        "elapsed_sec": round(time.time() - t0, 2),
        "summary": holdout.summarize(preds),
        "predictions": preds,
    }


def eval_nsq_pcc_experiment(
    exp_id: str,
    exp_index: int,
    feature_names: tuple[str, ...],
    holdout: SegmentHoldout,
    X_fp: np.ndarray,
    footprint: np.ndarray,
    *,
    return_oof_surface: bool = False,
) -> dict[str, Any]:
    """Run NSQ-PCC 4-fold spatial holdout + Dinkelbach-Submodular 300 m emission."""
    t0 = time.time()
    f_idx = [ALL_FEATURE_NAMES.index(nm) for nm in feature_names]
    n_fp = float(footprint.sum())
    preds = []
    fold_diagnostics = []
    oof_raw_sub = np.zeros(footprint.shape, dtype=np.float32) if return_oof_surface else None

    for fold in holdout.folds:
        prob_2d, raw_sub_2d, f_info = fit_predict_nsq_pcc_fold(
            X_fp,
            footprint,
            holdout.fold_grid,
            fold["train"],
            fold["visible"],
            fold["id"],
            feature_indices=f_idx,
            seed=20261025,
            neg_pos_ratio=4,
        )
        if oof_raw_sub is not None:
            oof_raw_sub[fold["valid"]] = raw_sub_2d[fold["valid"]]
        del raw_sub_2d

        d_vis = distance_transform_edt(~fold["visible"])
        allowed = fold["valid"] & (d_vis > 2.0)
        k_fold = round(FULL_GRID_DOT_BUDGET * (float(fold["valid"].sum()) / n_fp))
        p_fold = submodular_dti_emit(
            prob_2d,
            allowed,
            footprint=footprint,
            n_dots=k_fold,
            dstar_ref=DSTAR_REF,
            min_gain=0.0,
        )
        preds.append((p_fold > 0.5).astype(np.uint8))
        fold_diagnostics.append(
            {
                "fold": fold["name"],
                **f_info,
                "fold_dot_budget": k_fold,
                "fold_dots_emitted": int((p_fold > 0.5).sum()),
            }
        )
        del prob_2d, p_fold
        gc.collect()

    out: dict[str, Any] = {
        "id": exp_id,
        "experiment_index": exp_index,
        "n_features": len(feature_names),
        "feature_names": list(feature_names),
        "elapsed_sec": round(time.time() - t0, 2),
        "fold_diagnostics": fold_diagnostics,
        "summary": holdout.summarize(preds),
        "predictions": preds,
    }
    if oof_raw_sub is not None:
        out["oof_raw_sub"] = oof_raw_sub
    return out


def summarize_novelty_compact(nov: dict[str, Any], top_k: int = 8) -> dict[str, Any]:
    rows = nov["rows"]
    comp_rows = [r for r in rows if r.get("comparator_class") == "competing_method"]
    by_overlap = sorted(
        comp_rows,
        key=lambda r: float(r["candidate_dot_overlap_within_3px"] or -1.0),
        reverse=True,
    )
    by_rank = sorted(
        rows,
        key=lambda r: max(
            abs(float(r["raw_spearman"] or 0.0)),
            abs(float(r["kernel_spearman"] or 0.0)),
        ),
        reverse=True,
    )
    out = {k: v for k, v in nov.items() if k != "rows"}
    out["top_competing_by_overlap"] = by_overlap[:top_k]
    out["top_all_by_abs_rank_corr"] = by_rank[:top_k]
    return out


def main() -> None:
    t_start = time.time()
    raw_dir = ROOT / "data" / "raw"
    cache_dir = ROOT / "data" / "prepared"
    reg_file = ROOT / "registry" / "priority_rasters.json"

    print("[1/7] Loading footprint, catalogue, and SegmentHoldout ('gems-segment-pooled-v1')...")
    footprint, catalogue = _load_footprint_and_catalogue(raw_dir)
    holdout = SegmentHoldout(footprint, catalogue, buffer_px=15)

    # Verify exact disjoint valid partition
    valid_sum = sum(int(f["valid"].sum()) for f in holdout.folds)
    assert valid_sum == int(footprint.sum()) == 5_167_373

    print("[2/7] Building or loading 25-feature cached physical/structural stack...")
    X_fp, feat_meta = build_or_load_feature_stack(raw_dir, cache_dir)
    print(
        f"      Cached stack ready: shape={X_fp.shape}, sha256={feat_meta['features_sha256'][:16]}..."
    )

    print("[3/7] Running Gate 1: Two-polarity single-feature leakage canary across all 25 features...")
    canary_report = run_batched_canary(holdout, X_fp, footprint, batch_size=2)
    print(
        f"      Canary passed={canary_report['passed']}, max_symmetric_auc={canary_report['max_symmetric_auc']:.4f} (limit <= 0.90)"
    )
    if not canary_report["passed"]:
        raise SystemExit("FAIL-CLOSED: Leakage canary flagged a feature > 0.90 AUC!")

    print("[4/7] Evaluating leak-free reference controls (0 experiments of 3-experiment budget)...")
    ctrl1 = eval_ctrl_legacy_h6_static_and_nosgmc(holdout, raw_dir)
    print(f"      CTRL-1 (Legacy H6): HOLDOUT-DTI = {ctrl1['summary']['dti']:.6f}")
    ctrl2 = eval_ctrl_raw19_hgb_oof(holdout, raw_dir, footprint)
    print(
        f"      CTRL-2 (Raw19 HGB d=3 OOF): HOLDOUT-DTI = {ctrl2['summary']['dti']:.5f}, CI95={ctrl2['summary']['ci95']['interval']}"
    )

    print("[5/7] Executing locked 3-experiment budget (EXP-1, EXP-2, EXP-3)...")
    exp1 = eval_exp1_unsupervised(holdout, X_fp, footprint)
    print(
        f"      EXP-1 (Unsup Concordance + Submod): HOLDOUT-DTI = {exp1['summary']['dti']:.5f}, CI95={exp1['summary']['ci95']['interval']}"
    )

    exp2 = eval_nsq_pcc_experiment(
        "EXP-2-H36-Local17-NSQPCC",
        2,
        LOCAL_FEATURE_NAMES,
        holdout,
        X_fp,
        footprint,
        return_oof_surface=False,
    )
    print(
        f"      EXP-2 (Local17 NSQ-PCC + Submod):  HOLDOUT-DTI = {exp2['summary']['dti']:.5f}, CI95={exp2['summary']['ci95']['interval']}"
    )

    exp3 = eval_nsq_pcc_experiment(
        "EXP-3-H36-CTRB-25-NSQPCC",
        3,
        ALL_FEATURE_NAMES,
        holdout,
        X_fp,
        footprint,
        return_oof_surface=True,
    )
    print(
        f"      EXP-3 (Full 25-feat H36-CTRB):     HOLDOUT-DTI = {exp3['summary']['dti']:.5f}, CI95={exp3['summary']['ci95']['interval']}"
    )
    for f_row in exp3["summary"]["folds"]:
        print(
            f"        - Fold {f_row['fold']}: HOLDOUT-DTI = {f_row['dti']:.5f} (emitted={int(f_row['n_emitted'])}, truth={int(f_row['n_truth'])})"
        )

    paired_vs_ctrl1 = holdout.compare_paired(exp3["predictions"], ctrl1["predictions"])
    paired_vs_ctrl2 = holdout.compare_paired(exp3["predictions"], ctrl2["predictions"])
    paired_vs_exp1 = holdout.compare_paired(exp3["predictions"], exp1["predictions"])
    paired_vs_exp2 = holdout.compare_paired(exp3["predictions"], exp2["predictions"])

    # Seamless full-footprint out-of-fold probability calibration (zero quadrant stitch seams!)
    oof_raw_sub_2d: np.ndarray = exp3.pop("oof_raw_sub")
    global_base_rate = float(catalogue.sum() / max(int(footprint.sum()), 1))
    sample_prior = 0.20
    p64 = np.clip(oof_raw_sub_2d.astype(np.float64), 1e-6, 1.0 - 1e-6)
    num = p64 * (global_base_rate / sample_prior)
    den = num + (1.0 - p64) * ((1.0 - global_base_rate) / (1.0 - sample_prior))
    oof_surface_2d = np.where(
        footprint, (num / np.maximum(den, 1e-12)).astype(np.float32), 0.0
    ).astype(np.float32)
    del oof_raw_sub_2d, p64, num, den
    gc.collect()

    d_cat_full = distance_transform_edt(~catalogue)
    full_allowed = footprint & (d_cat_full > 2.0)
    full_pred_2d = submodular_dti_emit(
        oof_surface_2d,
        full_allowed,
        footprint=footprint,
        n_dots=FULL_GRID_DOT_BUDGET,
        dstar_ref=DSTAR_REF,
        min_gain=0.0,
    )
    n_emitted_full = int((full_pred_2d > 0.5).sum())
    on_cat_full = int(((full_pred_2d > 0.5) & catalogue).sum())
    near_cat_le2 = int(((full_pred_2d > 0.5) & (d_cat_full <= 2.0)).sum())
    assert on_cat_full == 0 and near_cat_le2 == 0

    print(
        f"[6/7] Running Gate 2: 107-raster registry novelty check on pre-placement surface AND {n_emitted_full:,} final dots..."
    )
    reg_data = json.loads(reg_file.read_text())
    reg_entries = reg_data["unique_rasters"]

    nov_surface = compare_registry(
        oof_surface_2d,
        footprint,
        reg_entries,
        ROOT,
        dots=None,
        separate_calibration_controls=True,
    )
    nov_dots = compare_registry(
        full_pred_2d,
        footprint,
        reg_entries,
        ROOT,
        dots=(full_pred_2d > 0.5),
        separate_calibration_controls=True,
    )
    print(
        f"      Surface novelty passed={nov_surface['passed']}, max |rho|={nov_surface['max_abs_rank_correlation']:.4f} (limit <= 0.90)"
    )
    print(
        f"      Dots novelty competing_method_passed={nov_dots['competing_method_passed']}, "
        f"max |rho|={nov_dots['max_abs_rank_correlation']:.4f} (limit <= 0.90), "
        f"max competing 3-px overlap={nov_dots['max_competing_dot_overlap']:.4f} (limit <= 0.70)"
    )

    # Gate 3: Emit submission bundle & run dual independent validators
    print("[7/7] Emitting paired GeoTIFF submission bundle and running automated validators...")
    timestamp_tag = "20261025T000000Z"
    submission_note = (
        f"GEMSDOE36 H36-CTRB | 1.5km strike-worm+trunk relay+NSQ-PCC submod | "
        f"{n_emitted_full}px d_cat>2 | HOLDOUT-DTI {exp3['summary']['dti']:.4f}"
    )
    assert len(submission_note) <= 140, f"Note too long ({len(submission_note)} > 140)"

    out_dl = ROOT / "docs" / "downloads"
    # Clean any partial prior run of identical prefix/timestamp
    for stale in out_dl.glob(f"gemsdoe36-h36-ctrb-submod-*-{timestamp_tag}-*"):
        stale.unlink()

    bundle = write_submission_bundle(
        full_pred_2d,
        raw_dir / "sample_submission.tif",
        out_dl,
        prefix="gemsdoe36-h36-ctrb-submod",
        timestamp_tag=timestamp_tag,
        submission_name="GEMSDOE36-H36-CTRB-Submod",
        note=submission_note,
        meta={
            "evaluator_version": exp3["summary"]["evaluator_version"],
            "holdout_dti": float(exp3["summary"]["dti"]),
            "holdout_ci95": exp3["summary"]["ci95"]["interval"],
        },
    )

    zeros_path = Path(bundle["zeros_tif"]["path"])
    nan_path = Path(bundle["nan_tif"]["path"])
    tmpl_path = raw_dir / "sample_submission.tif"

    val_zeros_repo = validate_submission(
        zeros_path, tmpl_path, require_nonfinite_outside=False
    ).to_dict()
    val_nan_repo = validate_submission(
        nan_path, tmpl_path, require_nonfinite_outside=True
    ).to_dict()
    val_zeros_shared = gems_check_variants(zeros_path, tmpl_path)
    val_nan_shared = gems_check_variants(nan_path, tmpl_path)

    format_gate_pass = bool(
        val_zeros_repo["passed"]
        and val_nan_repo["passed"]
        and val_zeros_shared["format_valid"]
        and val_zeros_shared["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]
        and val_nan_shared["official_format_compliant"]
        and on_cat_full == 0
        and near_cat_le2 == 0
    )
    novelty_gate_pass = bool(nov_surface["passed"] and nov_dots["competing_method_passed"])
    dti_gate_pass = bool(
        exp3["summary"]["dti"] > ctrl1["summary"]["dti"]
        and exp3["summary"]["dti"] > ctrl2["summary"]["dti"]
        and exp3["summary"]["dti"] > exp1["summary"]["dti"]
        and paired_vs_ctrl2["ci95_strictly_positive"]
        and paired_vs_ctrl2["fold_wins"] >= 3
    )
    verdict = (
        "promote"
        if (canary_report["passed"] and novelty_gate_pass and format_gate_pass and dti_gate_pass)
        else "negative"
    )

    # Strip bulky fold binary arrays before JSON serialization
    for obj in (ctrl1, ctrl2, exp1, exp2, exp3):
        obj.pop("predictions", None)

    run_card = {
        "schema": "gems-parallel-run-card-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "GEMSDOE36",
        "branch": "arena/b0ff24db-gemsdoe36",
        "hypothesis": "H36-CTRB (Curvature-Tapered 1.5 km Strike-Worm, Geophysical Trunk Relay-Bridge & Tip-Lobe Concordance with NSQ-PCC & Dinkelbach-Submodular 300 m Emission)",
        "mechanism": (
            "Combines 12-azimuth antialiased 1.5 km potential-field/hydrothermal/contour-orthogonal "
            "strike-worm line integrals, cross-horizon double-angle structure-tensor coherence, and "
            "label-free geophysical basement-trunk opposing-EDT relay bridges + cos^4(psi) tip lobes; "
            "excludes raw det_elev and det_elev_slope upland confounds; calibrates probabilities via "
            "Nested Spatial-Quadrant Purged Cross-Calibration (NSQ-PCC) and places centerline dots "
            "by exact Minoux lazy-greedy Dinkelbach-Submodular 300 m triangular-kernel maximization "
            "outside d_cat <= 2.0 px (200 m)."
        ),
        "non_fault_mimic_process": (
            "Steep range-interior crystalline bedrock slopes (erosional cliffs/talus accessibility bias), "
            "unfaulted Tertiary volcanic flow margins & calderas (curved magnetic contacts without basement "
            "density step), flight-line magnetic tie artifacts, and alluvial fan distributary channels / "
            "playa shorelines (down-fan radial gradients rather than contour-parallel scarps)."
        ),
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": exp3["summary"]["evaluator_version"],
            "dti": round(float(exp3["summary"]["dti"]), 6),
            "ci95": [round(float(x), 6) for x in exp3["summary"]["ci95"]["interval"]],
            "n_withheld_positive_pixels": exp3["summary"]["n_withheld_positive_pixels"],
            "n_unique_withheld_components": exp3["summary"]["n_unique_withheld_components"],
            "TP_w": round(float(exp3["summary"]["TP_w"]), 3),
            "FP_w": round(float(exp3["summary"]["FP_w"]), 3),
            "FN_w": round(float(exp3["summary"]["FN_w"]), 3),
            "n_emitted_pooled": int(exp3["summary"]["n_emitted"]),
            "folds": exp3["summary"]["folds"],
        },
        "benchmarks_and_ablations": {
            "ctrl_1_prior_repo_h6": ctrl1["summary"],
            "ctrl_2_raw19_hgb_d3_oof": ctrl2["summary"],
            "sibling_gemsdoe24_oof_multiphysics_hgb_d3_reference": {
                "label": "HOLDOUT-DTI",
                "evaluator_version": "gems-segment-pooled-v1",
                "dti": 0.13000,
                "ci95": [0.11565, 0.14396],
                "source": "GEMSDOE24/evidence/rshg1_run_card_20261025.json",
            },
            "exp_1_unsupervised_concordance": exp1["summary"],
            "exp_2_local17_nsqpcc": exp2["summary"],
            "exp_3_full25_h36_ctrb": exp3["summary"],
            "paired_exp3_vs_ctrl1": paired_vs_ctrl1,
            "paired_exp3_vs_ctrl2": paired_vs_ctrl2,
            "paired_exp3_vs_exp1": paired_vs_exp1,
            "paired_exp3_vs_exp2": paired_vs_exp2,
        },
        "experiment_budget": {
            "max_experiments_allowed": 3,
            "experiments_executed": 3,
            "max_walltime_seconds": 7200,
            "elapsed_walltime_seconds": round(time.time() - t_start, 2),
        },
        "leakage_canary": {
            "passed": canary_report["passed"],
            "threshold": canary_report["threshold"],
            "max_symmetric_auc": canary_report["max_symmetric_auc"],
            "n_features_checked": canary_report["n_features_checked"],
            "per_feature_pooled_auc": {
                k: round(float(v["pooled_auc"]), 5) for k, v in canary_report["features"].items()
            },
        },
        "registry_uniqueness": {
            "registry_snapshot": "registry/priority_rasters.json",
            "unique_registry_rasters_checked": len(reg_entries),
            "surface_before_placement": summarize_novelty_compact(nov_surface),
            "final_dots": summarize_novelty_compact(nov_dots),
            "passed": novelty_gate_pass,
        },
        "submission": {
            "submission_name": bundle["zeros_tif"]["filename"],
            "companion_nan_name": bundle["nan_tif"]["filename"],
            "zip_archive_name": bundle["zip_archive"]["filename"],
            "note": submission_note,
            "note_length_chars": len(submission_note),
            "raster_sha256": bundle["zeros_tif"]["sha256"],
            "companion_nan_sha256": bundle["nan_tif"]["sha256"],
            "zip_sha256": bundle["zip_archive"]["sha256"],
            "emitted_positive_pixels": n_emitted_full,
            "on_catalogue_predictions": on_cat_full,
            "near_catalogue_le_2px_predictions": near_cat_le2,
        },
        "validator_output": {
            "automated_gate_passed": format_gate_pass,
            "safe_to_download_and_submit": bool(
                format_gate_pass and novelty_gate_pass and canary_report["passed"]
            ),
            "zeros_outside_primary": {
                "repo_validator": val_zeros_repo,
                "shared_gems_validator": {
                    "format_valid": val_zeros_shared["format_valid"],
                    "hard_failures": val_zeros_shared["hard_failures"],
                    "variant_strict_whole_array_no_nan_allowed": val_zeros_shared["checks"][
                        "variant_strict_whole_array_no_nan_allowed"
                    ]["pass"],
                    "variant_nan_aware_whole_array": val_zeros_shared["checks"][
                        "variant_nan_aware_whole_array"
                    ]["pass"],
                    "footprint_all_finite": val_zeros_shared["checks"]["footprint_all_finite"][
                        "pass"
                    ],
                    "footprint_range_0_1": val_zeros_shared["checks"]["footprint_range_0_1"][
                        "pass"
                    ],
                    "crs_epsg_32611": val_zeros_shared["checks"]["crs_epsg_32611"]["pass"],
                    "shape_matches_template": val_zeros_shared["checks"][
                        "shape_matches_template"
                    ]["pass"],
                    "geotransform_matches_template": val_zeros_shared["checks"][
                        "geotransform_matches_template"
                    ]["pass"],
                },
            },
            "nan_outside_companion": {
                "repo_validator": val_nan_repo,
                "shared_gems_validator": {
                    "format_valid": val_nan_shared["format_valid"],
                    "official_format_compliant": val_nan_shared["official_format_compliant"],
                    "hard_failures": val_nan_shared["hard_failures"],
                },
            },
        },
        "feature_stack_metadata": feat_meta,
        "verdict": verdict,
    }

    ev_dir = ROOT / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    ev_card_path = ev_dir / "h36_ctrb_run_card_20261025.json"
    dl_card_path = out_dl / "run_card.json"
    canary_detail_path = ev_dir / "h36_ctrb_canary_20261025.json"

    ev_card_path.write_text(json.dumps(run_card, indent=2) + "\n")
    dl_card_path.write_text(json.dumps(run_card, indent=2) + "\n")
    canary_detail_path.write_text(json.dumps(canary_report, indent=2) + "\n")

    # Update registry/submission_build.json and docs/downloads/submissions_manifest.json
    manifest_payload = {
        "schema_version": 2,
        "updated_utc": run_card["generated_utc"],
        "recommended_primary_download": {
            "candidate_id": "GEMSDOE36-H36-CTRB-Submod",
            "verdict": verdict,
            "automated_validation_passed": run_card["validator_output"][
                "safe_to_download_and_submit"
            ],
            "uniqueness_verified_against_107_rasters": novelty_gate_pass,
            "zeros_tif": bundle["zeros_tif"],
            "nan_tif": bundle["nan_tif"],
            "zip_archive": bundle["zip_archive"],
            "note": submission_note,
            "holdout_dti": run_card["holdout_dti"],
            "registry_uniqueness_summary": {
                "surface_max_abs_spearman": round(
                    float(nov_surface["max_abs_rank_correlation"]), 5
                ),
                "dots_max_abs_spearman": round(float(nov_dots["max_abs_rank_correlation"]), 5),
                "dots_max_competing_3px_overlap": round(
                    float(nov_dots["max_competing_dot_overlap"]), 5
                ),
            },
        },
        "historical_archived_artifacts_do_not_submit": [
            {
                "filename": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
                "organizer_confirmed_dti": 0.2750,
                "status": "ARCHIVED_DUPLICATE_DO_NOT_RESUBMIT",
                "reason": "96.91% 3-px dot overlap with GEMSDOE32 h33-2-b2 (copied 37,654 pixels + 1,200 radial IDW pixels).",
            },
            {
                "filename": "GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif",
                "organizer_confirmed_dti": 0.0512,
                "holdout_dti": round(float(ctrl1["summary"]["dti"]), 6),
                "status": "ARCHIVED_SGMC_LEAK_NEGATIVE",
                "reason": "Circular sgmc_off_catalogue self-recovery (0.0512 / 0.0492 ORGANIZER-CONFIRMED).",
            },
        ],
    }
    (ROOT / "registry" / "submission_build.json").write_text(
        json.dumps(manifest_payload, indent=2) + "\n"
    )
    (out_dl / "submissions_manifest.json").write_text(
        json.dumps(manifest_payload, indent=2) + "\n"
    )

    print(f"\n=== DONE in {time.time() - t_start:.1f}s | VERDICT: {verdict.upper()} ===")
    print(f"Run card written to: {ev_card_path}")


if __name__ == "__main__":
    main()
