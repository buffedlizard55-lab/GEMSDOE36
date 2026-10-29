#!/usr/bin/env python3
"""Run the preregistered GSEWC36-EXP1 research-only holdout experiment.

Uses the shared ATVR feature cache, segment holdout plan, canary, HGB fit,
pooled evaluator, and paired spatial-cell bootstrap from scripts/evaluate_holdout.py.
No competition submission is written. The literal registry gate is checked against
reg-052 before any OOF dots are selected; final-map construction is forbidden if
that gate fails.
"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_holdout import (  # noqa: E402
    COLLAR_PX,
    TOTAL_DOT_BUDGET,
    _allocate_quadrant_budgets,
    _evaluate_arm_diagnostics,
    _fit_predict_calibrated_hgb,
    _paired_bootstrap_delta,
    _top_k_mask,
    build_whole_segment_holdout_plan,
)

from gemsdoe36.atvr_features import (  # noqa: E402
    RAW19_NAMES,
    build_or_load_static_feature_cache,
)
from gemsdoe36.protocol import EVALUATOR_VERSION, feature_canary  # noqa: E402
from gemsdoe36.scale_space import scale_space_edge_width_concordance  # noqa: E402

EXPERIMENT_ID = "GSEWC36-EXP1"
MAX_SECONDS = 7_200
EXPECTED_PREREG_SHA256 = "36dcd8732702585dea031fc7dc9bbe7e0f8f2b75e3a7a5f8a46af1fca68623a0"
EXPECTED_LABEL_SHA256 = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
EXPECTED_LATTICE_SHA256 = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
PREREG_PATH = ROOT / "evidence" / "hypothesis_screen_20261029.json"
RUN_CARD_PATH = ROOT / "evidence" / "gsewc36_run_card_20261029.json"
BANDS_DIR = ROOT / ".cache" / "gems_work" / "bands"
LATTICE_PATH = ROOT / "data" / "raw" / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _sha256_array(array: np.ndarray, dtype: str) -> str:
    a = np.ascontiguousarray(array, dtype=np.dtype(dtype))
    return hashlib.sha256(a.tobytes()).hexdigest()


def _write_card(card: dict[str, Any]) -> None:
    RUN_CARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = RUN_CARD_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(RUN_CARD_PATH)


def _rank_correlation_with_binary_reference(
    surface: np.ndarray, reference: np.ndarray, footprint: np.ndarray
) -> float:
    """Exact Spearman rho with a 0/1 raster, using its equivalent rank correlation."""
    x = np.asarray(surface[footprint], dtype=np.float32)
    y = np.asarray(reference[footprint], dtype=np.float64)
    if not np.isfinite(x).all() or not np.isfinite(y).all() or np.unique(y).size != 2:
        raise ValueError("rank-correlation inputs must be finite and the reference nonconstant")
    ranks = rankdata(x, method="average")
    ranks -= ranks.mean()
    y -= y.mean()
    denom = float(np.sqrt(np.dot(ranks, ranks) * np.dot(y, y)))
    if denom == 0:
        raise ValueError("rank-correlation denominator is zero")
    return float(np.dot(ranks, y) / denom)


def _base_card(prereg_sha: str, feature_sha: str, script_sha: str) -> dict[str, Any]:
    return {
        "schema": "gemsdoe36.experiment-run-card.v1",
        "experiment_id": EXPERIMENT_ID,
        "date_utc": "2026-10-29",
        "status": "running",
        "verdict": "negative_pending",
        "scope": "one preregistered research experiment; no method-lane assignment and no slot selection",
        "hypothesis": "Cross-sensor Gaussian scale-space edge-width concordance improves whole-segment hide-and-recover DTI over the matched raw-19-band HGB baseline.",
        "mechanism": "A buried fault-related property boundary can create spatially coincident magnetic and gravity gradient edges with concordant apparent width and axial normal.",
        "named_non_fault_mimic": "Intrusive/lithologic contacts, magnetization contrasts, and flight-line levelling seams.",
        "inputs": {
            "magnetic_band": "14_tmi",
            "gravity_band": "13_iso_grav_anom",
            "bands_dir": str(BANDS_DIR.relative_to(ROOT)),
            "feature_stack": "19 prepared bands; shared static cache for matched raw-19 baseline",
            "feature_cache_not_saved_in_git": True,
            "training_labels_sha256": EXPECTED_LABEL_SHA256,
            "labels_existing_faults_relationship": "byte-identical owner-mirror files; source alias, not independent corroboration",
            "prepared_manifest_sha256": _sha256_file(ROOT / "data" / "prepared_manifest.json"),
            "restore_receipt_sha256": _sha256_file(ROOT / "data" / "restore_receipt.json"),
            "provenance": "SHA-pinned owner GitHub mirrors; hashes prove mirror consistency only, not organizer authentication",
        },
        "preregistration": {
            "path": str(PREREG_PATH.relative_to(ROOT)),
            "sha256": prereg_sha,
            "expected_sha256": EXPECTED_PREREG_SHA256,
            "candidate_feature_source_sha256": feature_sha,
            "runner_sha256": script_sha,
        },
        "evaluator": {
            "label": "HOLDOUT-DTI",
            "version": EVALUATOR_VERSION,
            "holdout": "whole 8-connected segments assigned to four spatial quadrants; 30 px / 3 km training collar",
            "visible_fault_scoring_mask": "pixel-exact exclusion from scoring; no buffer in scoring mask",
            "metric": "pooled distance-weighted Tversky; alpha=0.2, beta=0.8, 300 m triangular kernel",
            "withheld_positive_expected": 60988,
            "segment_count_expected": 3199,
            "dot_budget": TOTAL_DOT_BUDGET,
            "paired_uncertainty": "2000-replicate paired 16-cell spatial bootstrap; seed 36",
        },
        "feature_canary": {
            "features": [],
            "threshold": "symmetric AUC > 0.90 is a hard stop",
            "status": "not_run",
        },
        "results": {
            "baseline": None,
            "candidate": None,
            "paired_delta_vs_baseline": None,
            "same_evaluator_historical_best": {
                "label": "HOLDOUT-DTI",
                "evaluator_version": EVALUATOR_VERSION,
                "dti": 0.114542,
                "ci95": [0.078547, 0.151221],
                "withheld_positives": 60988,
                "source": "evidence/atvr36_run_card_20261026.json",
            },
            "projection_or_leaderboard_score": None,
        },
        "registry_gate": {
            "status": "not_run",
            "registry_raster": None,
            "surface_rank_correlation": None,
            "oof_dot_overlap_within_3px": None,
            "mathematical_lower_bound_overlap_at_37654_dots": 0.823418,
            "literal_overlap_limit": 0.70,
            "literal_abs_rank_correlation_limit": 0.90,
            "note": "reg-052 is a 5-pixel calibration lattice, not an independent geological detector; it remains binding under the unrevised literal protocol.",
        },
        "submission": {
            "submission_tif_written": False,
            "submission_zip_written": False,
            "writer_invoked": False,
            "validator_output": None,
            "name": None,
            "note": None,
            "raster_sha256": None,
            "download_status": "NO; research-only; no candidate submission raster exists",
            "weekly_slot_selected": False,
        },
        "elapsed_seconds": None,
        "errors": [],
    }


def run() -> int:
    started = time.monotonic()
    stage = "preregistration_lock"
    prereg_sha = _sha256_file(PREREG_PATH)
    feature_path = ROOT / "src" / "gemsdoe36" / "scale_space.py"
    script_path = Path(__file__).resolve()
    feature_sha = _sha256_file(feature_path)
    script_sha = _sha256_file(script_path)
    card = _base_card(prereg_sha, feature_sha, script_sha)
    _write_card(card)

    try:
        if prereg_sha != EXPECTED_PREREG_SHA256:
            raise RuntimeError(f"Preregistration hash mismatch: {prereg_sha}")
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        if prereg.get("experiment", {}).get("id") != EXPERIMENT_ID:
            raise RuntimeError("Preregistration experiment ID does not match runner")
        if prereg.get("experiment", {}).get("submission_tif_written") is not False:
            raise RuntimeError("Preregistration lock must explicitly forbid pre-run TIFF creation")
        if _sha256_file(ROOT / "data" / "raw" / "labels.tif") != EXPECTED_LABEL_SHA256:
            raise RuntimeError("labels.tif does not match the pinned preregistered SHA-256")
        if _sha256_file(ROOT / "data" / "raw" / "existing_faults.tif") != EXPECTED_LABEL_SHA256:
            raise RuntimeError("existing_faults.tif is no longer byte-identical to labels.tif")
        if _sha256_file(LATTICE_PATH) != EXPECTED_LATTICE_SHA256:
            raise RuntimeError("reg-052 comparison raster does not match its pinned SHA-256")
        if time.monotonic() - started > MAX_SECONDS:
            raise TimeoutError("2-hour experiment cap exceeded before cache construction")

        stage = "shared_cache"
        cache = build_or_load_static_feature_cache(
            bands_dir=BANDS_DIR,
            ext_root=ROOT / "data" / "raw",
            cache_dir=ROOT / ".cache" / "gems_work" / "atvr_features_v1",
        )
        if tuple(cache.feature_names[: len(RAW19_NAMES)]) != RAW19_NAMES:
            raise RuntimeError("shared cached feature ordering differs from the raw-19 baseline")
        plan = build_whole_segment_holdout_plan(
            cache.labels > 0.5,
            cache.footprint,
            buffer_px=30,
        )
        if int(plan.truth.sum()) != 60988 or plan.n_segments != 3199:
            raise RuntimeError(
                f"Holdout differs from preregistration: positives={plan.truth.sum()}, segments={plan.n_segments}"
            )
        card["holdout_plan"] = {
            "n_segments": plan.n_segments,
            "withheld_positive_pixels": int(plan.truth.sum()),
            "n_folds": plan.n_folds,
            "buffer_px": 30,
            "segment_split_count": 0,
            "positive_count_matches_preregistration": True,
        }
        _write_card(card)

        stage = "feature_construction"
        magnetic = np.load(BANDS_DIR / "14_tmi.npy", mmap_mode="r")
        gravity = np.load(BANDS_DIR / "13_iso_grav_anom.npy", mmap_mode="r")
        candidate_feature, feature_diagnostics = scale_space_edge_width_concordance(
            magnetic,
            gravity,
            plan.footprint,
        )
        del magnetic, gravity
        gc.collect()
        card["candidate_feature_diagnostics"] = feature_diagnostics
        card["candidate_feature_diagnostics"]["candidate_feature_sha256_f32_le"] = _sha256_array(
            candidate_feature, "<f4"
        )
        card["candidate_feature_diagnostics"]["label_reads"] = 0
        card["candidate_feature_diagnostics"]["external_data_reads"] = 0
        card["candidate_feature_diagnostics"]["registry_or_submission_raster_reads"] = 0
        _write_card(card)

        stage = "per_feature_canaries"
        matrix = cache.open_matrix()
        name_to_col = {name: i for i, name in enumerate(cache.feature_names)}
        canary_results: list[dict[str, Any]] = []
        canary_names = list(RAW19_NAMES) + ["gsewc36_edge_width_concordance"]
        candidate_grid = candidate_feature
        for feature_name in canary_names:
            if feature_name == "gsewc36_edge_width_concordance":
                grid = candidate_grid
            else:
                grid = np.zeros(plan.footprint.shape, dtype=np.float32)
                grid[cache.foot_rows, cache.foot_cols] = matrix[
                    :, name_to_col[feature_name]
                ]
            per_fold: list[dict[str, Any]] = []
            for fold in range(plan.n_folds):
                res = feature_canary(
                    grid,
                    plan.hidden_by_fold[fold],
                    plan.eval_mask_by_fold[fold],
                )
                per_fold.append(
                    {
                        "fold": fold,
                        "auc": round(float(res["auc"]), 6),
                        "two_polarity_auc": round(float(res["two_polarity_auc"]), 6),
                        "passed": bool(res["passed"]),
                    }
                )
            entry = {
                "feature": feature_name,
                "max_two_polarity_auc": max(x["two_polarity_auc"] for x in per_fold),
                "passed": all(x["passed"] for x in per_fold),
                "folds": per_fold,
            }
            canary_results.append(entry)
            card["feature_canary"] = {
                "features": canary_results,
                "threshold": "symmetric AUC > 0.90 is a hard stop",
                "status": "running",
            }
            _write_card(card)
            if not entry["passed"]:
                card["feature_canary"]["status"] = "stopped_hard_fail"
                card["status"] = "stopped_canary"
                card["verdict"] = "negative"
                card["verdict_reason"] = f"Presumptive leakage canary exceeded 0.90 on {feature_name}."
                card["elapsed_seconds"] = round(time.monotonic() - started, 2)
                _write_card(card)
                print(f"STOP: leakage canary failed for {feature_name}")
                return 0
            if time.monotonic() - started > MAX_SECONDS:
                raise TimeoutError("2-hour cap exceeded during feature-alone canaries")
        card["feature_canary"]["status"] = "passed_all_raw19_and_candidate"
        _write_card(card)

        stage = "registry_reference_preflight"
        with rasterio.open(LATTICE_PATH) as src:
            if (
                src.shape != plan.footprint.shape
                or src.count != 1
                or src.crs is None
                or src.crs.to_epsg() != 32611
            ):
                raise RuntimeError("reg-052 grid is not aligned to the prepared competition grid")
            lattice = src.read(1)
        lattice_mask = (lattice > 0) & plan.footprint
        if int(lattice_mask.sum()) != 206895:
            raise RuntimeError(f"reg-052 positive count changed: {int(lattice_mask.sum())}")
        del lattice
        card["registry_gate"].update(
            {
                "status": "reference_verified_surface_not_yet_compared",
                "registry_raster": {
                    "id": "reg-052",
                    "path": str(LATTICE_PATH.relative_to(ROOT)),
                    "sha256": EXPECTED_LATTICE_SHA256,
                    "label": "owner-mirror 5-pixel calibration lattice; comparison only",
                    "positive_pixels": int(lattice_mask.sum()),
                },
                "candidate_oof_surface_abs_spearman_rho": None,
                "surface_is_final_submission_surface": False,
                "oof_dot_overlap_within_3px": None,
                "mathematical_lower_bound_overlap_at_37654_dots": 0.823418,
                "literal_overlap_limit": 0.70,
                "literal_abs_rank_correlation_limit": 0.90,
                "all_198_registry_rasters_checked": False,
                "early_stop_policy": "Compare the OOF prediction surface before top-k placement; stop on first literal registry violation.",
            }
        )
        _write_card(card)

        stage = "matched_holdout_models"
        fold_eligible: list[np.ndarray] = []
        fold_train: list[np.ndarray] = []
        fold_visible: list[np.ndarray] = []
        fold_d_visible: list[np.ndarray] = []
        fold_target_foot: list[np.ndarray] = []
        for fold in range(plan.n_folds):
            visible = plan.visible_by_fold[fold]
            d_visible = distance_transform_edt(~visible).astype(np.float32)
            eligible = plan.eval_mask_by_fold[fold] & (d_visible > COLLAR_PX)
            fold_eligible.append(eligible)
            fold_train.append(plan.train_mask_by_fold[fold][cache.foot_rows, cache.foot_cols])
            fold_visible.append(visible[cache.foot_rows, cache.foot_cols])
            fold_d_visible.append(d_visible[cache.foot_rows, cache.foot_cols])
            fold_target_foot.append(eligible[cache.foot_rows, cache.foot_cols])
            del d_visible
        fold_budgets = _allocate_quadrant_budgets(fold_eligible, TOTAL_DOT_BUDGET)
        if sum(fold_budgets) != TOTAL_DOT_BUDGET:
            raise RuntimeError("fold dot-budget allocation does not sum to preregistered budget")

        baseline_surface = np.zeros(plan.footprint.shape, dtype=np.float32)
        candidate_oof_surface = np.zeros(plan.footprint.shape, dtype=np.float32)
        candidate_column = candidate_feature[cache.foot_rows, cache.foot_cols].astype(
            np.float32, copy=False
        )
        for fold in range(plan.n_folds):
            if time.monotonic() - started > MAX_SECONDS:
                raise TimeoutError("2-hour cap exceeded before a model fold")
            common = {
                "train_foot": fold_train[fold],
                "vis_fault_foot": fold_visible[fold],
                "d_vis_foot": fold_d_visible[fold],
                "target_foot_mask": fold_target_foot[fold],
                "seed": 3610 + fold,
            }
            base_pred, _, _ = _fit_predict_calibrated_hgb(
                cache,
                list(RAW19_NAMES),
                [],
                **common,
            )
            cand_pred, _, _ = _fit_predict_calibrated_hgb(
                cache,
                list(RAW19_NAMES),
                [candidate_column],
                **common,
            )
            base_grid = np.zeros(plan.footprint.shape, dtype=np.float32)
            cand_grid = np.zeros(plan.footprint.shape, dtype=np.float32)
            base_grid[cache.foot_rows, cache.foot_cols] = base_pred
            cand_grid[cache.foot_rows, cache.foot_cols] = cand_pred
            eligible = fold_eligible[fold]
            baseline_surface[eligible] = base_grid[eligible]
            candidate_oof_surface[eligible] = cand_grid[eligible]
            del base_pred, cand_pred, base_grid, cand_grid
            gc.collect()
            print(f"Completed matched fold {fold + 1}/{plan.n_folds} | elapsed={time.monotonic()-started:.1f}s")

        if not np.isfinite(candidate_oof_surface).all() or not np.isfinite(baseline_surface).all():
            raise RuntimeError("OOF probability surface contains a non-finite value")

        stage = "registry_surface_gate"
        # Compare the model's complete OOF probability surface BEFORE selecting any dots.
        surface_rho = _rank_correlation_with_binary_reference(
            candidate_oof_surface, lattice_mask, plan.footprint
        )
        card["registry_gate"].update(
            {
                "status": "surface_checked",
                "candidate_oof_surface_abs_spearman_rho": round(abs(surface_rho), 6),
                "surface_gate_passed": abs(surface_rho) <= 0.90,
                "surface_is_final_submission_surface": False,
            }
        )
        _write_card(card)
        if abs(surface_rho) > 0.90:
            card["registry_gate"]["status"] = "stopped_surface_duplicate_gate"
            card["status"] = "stopped_registry_surface"
            card["verdict"] = "negative"
            card["verdict_reason"] = (
                "Candidate OOF prediction surface exceeds the literal |rho| <= 0.90 registry gate "
                "against reg-052. No top-k dots were placed."
            )
            card["elapsed_seconds"] = round(time.monotonic() - started, 2)
            _write_card(card)
            print(f"STOP: candidate OOF surface |rho|={abs(surface_rho):.6f} > 0.90 vs reg-052")
            return 0

        # The OOF surface passed the pre-placement check; now allocate the fixed-budget dots.
        stage = "oof_dot_placement"
        baseline_dots = np.zeros(plan.footprint.shape, dtype=bool)
        candidate_oof_dots = np.zeros(plan.footprint.shape, dtype=bool)
        for fold in range(plan.n_folds):
            baseline_dots |= _top_k_mask(
                baseline_surface, fold_eligible[fold], fold_budgets[fold]
            )
            candidate_oof_dots |= _top_k_mask(
                candidate_oof_surface, fold_eligible[fold], fold_budgets[fold]
            )
        if int(candidate_oof_dots.sum()) != TOTAL_DOT_BUDGET or int(baseline_dots.sum()) != TOTAL_DOT_BUDGET:
            raise RuntimeError("OOF dot emission did not match the preregistered budget")

        stage = "holdout_metrics"
        baseline_result = _evaluate_arm_diagnostics(baseline_dots, plan, cache)
        candidate_result = _evaluate_arm_diagnostics(candidate_oof_dots, plan, cache)
        paired_delta = _paired_bootstrap_delta(
            candidate_oof_dots,
            baseline_dots,
            plan,
            bootstrap=2000,
            seed=36,
        )
        card["results"]["baseline"] = baseline_result
        card["results"]["candidate"] = candidate_result
        card["results"]["paired_delta_vs_baseline"] = paired_delta
        card["results"]["candidate_surface_sha256_f32_le"] = _sha256_array(
            candidate_oof_surface, "<f4"
        )
        card["results"]["baseline_surface_sha256_f32_le"] = _sha256_array(
            baseline_surface, "<f4"
        )
        card["results"]["candidate_oof_dots_sha256_u8"] = _sha256_array(
            candidate_oof_dots, "u1"
        )
        card["results"]["baseline_oof_dots_sha256_u8"] = _sha256_array(baseline_dots, "u1")
        card["results"]["candidate_vs_best_exact_evaluator"] = {
            "best_prior_dti": 0.114542,
            "candidate_minus_best": round(
                float(candidate_result["pooled_16block_dti"]) - 0.114542, 6
            ),
            "beats_best": bool(candidate_result["pooled_16block_dti"] > 0.114542),
        }
        card["results"]["scientific_holdout_gate_passed"] = bool(
            paired_delta["delta_ci95_lo"] > 0.0
            and candidate_result["pooled_16block_dti"] > 0.114542
        )
        _write_card(card)

        stage = "registry_dot_gate"
        # OOF dots are never a submission. This is a diagnostic of the same fixed budget;
        # the pre-existing geometric lower bound already proves a final 37,654-dot map fails.
        distance_to_lattice = distance_transform_edt(~lattice_mask)
        within_3px = candidate_oof_dots & (distance_to_lattice <= 3.0)
        overlap_count = int(within_3px.sum())
        overlap_fraction = float(overlap_count / TOTAL_DOT_BUDGET)
        card["registry_gate"].update(
            {
                "status": "stopped_dot_overlap_gate" if overlap_fraction > 0.70 else "reg052_checked",
                "oof_dot_overlap_within_3px": {
                    "overlap_dots": overlap_count,
                    "candidate_oof_dots": TOTAL_DOT_BUDGET,
                    "fraction": round(overlap_fraction, 6),
                },
                "dot_gate_passed_for_oof_diagnostic": overlap_fraction <= 0.70,
                "candidate_oof_dot_surface_is_final_submission": False,
                "final_submission_dots_generated": False,
                "all_198_registry_rasters_checked": False,
            }
        )
        del distance_to_lattice, within_3px, lattice_mask
        gc.collect()
        _write_card(card)

        if overlap_fraction > 0.70:
            card["status"] = "stopped_registry_dot_overlap"
            card["verdict"] = "negative"
            card["verdict_reason"] = (
                f"Candidate OOF dots have {overlap_fraction:.1%} within-3px overlap with reg-052, "
                "exceeding the literal 70% gate. The geometric lower bound also rules out any "
                "37,654-dot final map; no full-map model or submission TIFF was created."
            )
        else:
            card["status"] = "holdout_complete_uniqueness_unresolved"
            card["verdict"] = "negative"
            card["verdict_reason"] = (
                "OOF overlap did not trip reg-052, but the literal full-registry check and final-map "
                "placement were not run; automatic promotion remains fail-closed."
            )
        card["holdout_dti_label"] = "HOLDOUT-DTI; never an organizer/leaderboard score"
        card["elapsed_seconds"] = round(time.monotonic() - started, 2)
        _write_card(card)
        print(
            f"DONE: candidate HOLDOUT-DTI={candidate_result['pooled_16block_dti']:.6f}; "
            f"baseline={baseline_result['pooled_16block_dti']:.6f}; "
            f"delta={paired_delta['delta_point']:.6f}; literal verdict={card['verdict']}"
        )
        return 0

    except Exception as exc:
        card["status"] = "error_or_budget_stop"
        card["verdict"] = "negative"
        card["verdict_reason"] = "Experiment did not complete all preregistered gates; fail closed."
        card["errors"].append(
            {
                "stage": stage,
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(limit=8),
            }
        )
        card["elapsed_seconds"] = round(time.monotonic() - started, 2)
        _write_card(card)
        raise


if __name__ == "__main__":
    raise SystemExit(run())
