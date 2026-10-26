#!/usr/bin/env python3
"""Preregistered MTO-36 single-experiment, shared-template holdout and research TIFF.

Reads competition-band cache produced by scripts/prepare_data.py; uses exactly
one E1 candidate/control comparison. Historical rasters are READ ONLY inside
shared template novelty checks, never inputs to the predictor. A negative run
may publish a format-safe research TIFF, but never authorizes a live slot.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.holdout import SegmentHoldout  # noqa: E402
from gems.novelty import compare_registry  # noqa: E402
from gems.submission import check_variants, scored_content_id, write_submission, zip_single  # noqa: E402
from gemsdoe36.h36_emission import emit_dots  # noqa: E402
from gemsdoe36.mto_contact import magnetic_gravity_contact  # noqa: E402
from gemsdoe36.submission import sha256_file, validate_submission  # noqa: E402

BANDS = ROOT / ".cache/gems_work/bands"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
KNOWN = ROOT / "data/raw/existing_faults.tif"
OUTPUT = ROOT / "evidence/mto36_run_card_20261026.json"
REGISTRY = ROOT / "registry/uniqueness_registry.json"
DL = ROOT / "docs/downloads"
TOTAL_DOTS = 37_654
GROUP_BEST = 0.14876  # recorded in GEMSDOE24, not rerun or a live score
MAX_SECONDS = 7200


def record(obj: dict) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def verify_inputs() -> tuple[np.ndarray, np.ndarray, dict[str, str]]:
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text())
    pinned = {r["dest"]: r["sha256"] for r in manifest["files"]}
    paths = {
        "training_features.tif": ROOT / "data/raw/training_features.tif",
        "labels.tif": LABELS,
        "existing_faults.tif": KNOWN,
        "sample_submission.tif": TEMPLATE,
    }
    hashes = {}
    for name, p in paths.items():
        actual = sha256_file(p)
        if actual != pinned[name]:
            raise RuntimeError(f"SHA-256 mismatch on pinned mirror {name}: {actual}")
        hashes[name] = actual
    with rasterio.open(TEMPLATE) as template, rasterio.open(LABELS) as lab, rasterio.open(KNOWN) as existing:
        if not (lab.shape == existing.shape == template.shape and lab.crs == existing.crs == template.crs
                and lab.transform == existing.transform == template.transform):
            raise RuntimeError("Label/catalogue/template grid differs")
        foot = np.isfinite(template.read(1))
        labels = lab.read(1) == 1
        known = existing.read(1) == 1
    if not np.array_equal(labels, known) or np.any(labels & ~foot):
        raise RuntimeError("Catalogue mirror inconsistency or faults outside footprint")
    if not (foot.sum() == 5_167_373 and labels.sum() == 60_988):
        raise RuntimeError("Pinned footprint/fault count mismatch")
    prepared_foot = np.load(BANDS / "_footprint.npy", allow_pickle=False)
    if not np.array_equal(prepared_foot, foot):
        raise RuntimeError("Stale prepared feature-cache footprint; rerun scripts/prepare_data.py")
    return foot, labels, hashes


def verified_registry(foot: np.ndarray) -> list[dict]:
    pinned = json.loads(REGISTRY.read_text())["entries"]
    if len(pinned) != 198:
        raise RuntimeError(f"Registry changed: {len(pinned)} entries; review before running")
    for r in pinned:
        p = ROOT / r["cache_path"]
        if not p.is_file() or sha256_file(p) != r["file_sha256"]:
            raise RuntimeError(f"Missing/bad registry file: {p}; run scripts/fetch_registry_rasters.py")
    # Add current GEMSDOE36 research rasters that predate this lane but were
    # not present when registry/uniqueness_registry.json was built.
    existing_ids = {r["footprint_sha256"] for r in pinned}
    extras = []
    for p in sorted(DL.glob("*.tif")):
        with rasterio.open(p) as src:
            if src.shape != foot.shape or src.count != 1 or src.crs is None \
                    or src.crs.to_epsg() != 32611:
                continue  # format-demo fixture, not a real comparator
            arr = src.read(1)
        if not np.isfinite(arr[foot]).all() or np.any((arr[foot] < 0) | (arr[foot] > 1)):
            raise RuntimeError(f"Existing GEMSDOE36 comparator invalid inside footprint: {p}")
        content = hashlib.sha256(np.asarray(arr[foot], dtype="<f4").tobytes()).hexdigest()
        if content in existing_ids:
            continue
        existing_ids.add(content)
        extras.append({
            "id": f"local-mto-{len(extras) + 1:03d}",
            "file": f"GEMSDOE36/docs/downloads/{p.name}",
            "cache_path": str(p.relative_to(ROOT)),
            "footprint_sha256": content,
            "file_sha256": sha256_file(p),
            "source": "local-preexisting-research",
        })
    return pinned + extras


def _summarize_registry(res: dict, *, stage: str) -> dict:
    rows = res["rows"]
    focus_sites = {f"GEMSDOE{x}" for x in (24, 25, 27, 28, 30, 31, 32, 33, 36)}
    focus = [r for r in rows if r["file"].split("/", 1)[0] in focus_sites]
    # The 13GEMSDOE 5px calibration lattice is INCLUDED in the literal gate.
    # Report method-only descriptive numbers separately, never waive this gate.
    non_lattice = [r for r in rows if "lattice-s5" not in r["file"].lower()]
    def maxov(subset):
        return max((r["candidate_dot_overlap_within_3px"] for r in subset
                    if r["candidate_dot_overlap_within_3px"] is not None), default=None)
    return {
        "stage": stage,
        "all_entries_passed_literal": bool(res["passed"]),
        "n_registry_rasters_verified": res["registry_unique_rasters"],
        "full_footprint_spearman_pixels": res["raw_rank_pixels"],
        "max_abs_rank_correlation": res["max_abs_rank_correlation"],
        "max_dot_overlap_3px_all": res["max_dot_overlap"],
        "max_dot_overlap_3px_focus9": maxov(focus),
        "max_dot_overlap_3px_non_lattice_descriptive_only": maxov(non_lattice),
        "overlap_vs_champion_B2": next(
            (r["candidate_dot_overlap_within_3px"] for r in rows if r["file"].startswith("GEMSDOE32/") and "h33-h33-2-b2" in r["file"]), None
        ),
        "literal_duplicates": sorted(
            [{"file": r["file"], "rho_raw": r["raw_spearman"],
              "rho_kernel_sample": r["kernel_spearman"],
              "overlap_3px": r["candidate_dot_overlap_within_3px"]}
             for r in rows if r["duplicate"]],
            key=lambda d: -(d["overlap_3px"] or 0),
        ),
        "registry_scope_note": "Every pinned owner-scored/priority raster, plus pre-existing local rasters; no control waiver in the literal gate.",
    }


def budgets_for_folds(holdout: SegmentHoldout) -> list[int]:
    pixels = np.array([int(f["valid"].sum()) for f in holdout.folds], dtype=np.int64)
    shares = pixels.astype(np.float64) * TOTAL_DOTS / pixels.sum()
    budgets = np.floor(shares).astype(int)
    remainder = TOTAL_DOTS - int(budgets.sum())
    for ix in np.argsort(-(shares - budgets), kind="stable")[:remainder]:
        budgets[ix] += 1
    if int(budgets.sum()) != TOTAL_DOTS:
        raise AssertionError("Fold budgets must add up to locked total")
    return budgets.tolist()


def check_format(path: Path, foot: np.ndarray, known: np.ndarray) -> dict:
    v = check_variants(path, TEMPLATE)
    second = validate_submission(path, TEMPLATE, require_nonfinite_outside=False)
    with rasterio.open(path) as src:
        arr = src.read(1, masked=False)
        strict = bool(np.isfinite(arr).all() and np.all((arr >= 0) & (arr <= 1)))
        grid = src.shape == foot.shape and src.crs is not None and src.crs.to_epsg() == 32611
        single_float32 = src.count == 1 and src.dtypes == ("float32",)
    report = {
        "no_nan_inside_footprint": bool(np.isfinite(arr[foot]).all()),
        "nan_count_entire_array": int(np.isnan(arr).sum()),
        "in_0_1_entire_array": strict,
        "min": float(arr.min()),
        "max": float(arr.max()),
        "crs_shape_transform_match": bool(grid and second.template_match),
        "single_band_float32": bool(single_float32),
        "strict_template_format_valid": bool(v["format_valid"]),
        "strict_whole_array_check_passed": bool(v["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]),
        "independent_repo_validator_passed": bool(second.passed),
        "template_sha256": sha256_file(TEMPLATE),
        "known_fault_positive_count": int((arr[known] > 0).sum()),
        "outside_positive_count": int((arr[~foot] > 0).sum()),
        "errors": list(second.errors) + v["hard_failures"],
    }
    report["all_passed"] = bool(
        report["no_nan_inside_footprint"] and strict and report["crs_shape_transform_match"]
        and report["single_band_float32"] and report["strict_template_format_valid"]
        and report["strict_whole_array_check_passed"] and report["independent_repo_validator_passed"]
        and report["known_fault_positive_count"] == 0 and report["outside_positive_count"] == 0
    )
    return report


def main() -> int:
    start = time.monotonic()
    prereg = ROOT / "knowledge/mtop36_preregistration_2026-10-26.md"
    prereg_sha = sha256_file(prereg)
    foot, labels, core_hashes = verify_inputs()
    entries = verified_registry(foot)
    from gemsdoe36.paths import work_dir  # noqa: E402
    cache = work_dir() / "mtop36_v1"
    cache.mkdir(parents=True, exist_ok=True)

    # Only two pinned physical bands. No labels enter magnetic_gravity_contact.
    rtp = np.load(BANDS / "02_rtp.npy", mmap_mode="r", allow_pickle=False)
    gravity = np.load(BANDS / "13_iso_grav_anom.npy", mmap_mode="r", allow_pickle=False)
    t_feat = time.monotonic()
    features = magnetic_gravity_contact(rtp, gravity, foot)
    print(f"[MTO-36] Label-free contact features in {time.monotonic()-t_feat:.1f}s", flush=True)

    holdout = SegmentHoldout(foot, labels, buffer_px=15)
    # The shared template samples the same withheld positives/background for
    # each individual feature and checks both AUC polarities, each fold and pooled.
    canary_features = {name: getattr(features, name) for name in (
        "rtp_edge", "gravity_edge", "rtp_tangent_asymmetry", "mag_termination",
        "contact_orthogonality", "orthogonal_crosscut", "mtop36_field",
    )}
    canary_features["raw_rtp"] = np.nan_to_num(rtp, nan=0.0, posinf=0.0, neginf=0.0)
    canary_features["raw_gravity"] = np.nan_to_num(gravity, nan=0.0, posinf=0.0, neginf=0.0)
    canary = holdout.canary(canary_features)
    max_auc = max(max(max(r["pooled_auc"], 1-r["pooled_auc"]),
                      *(max(x["auc"], 1-x["auc"]) for x in r["folds"]))
                  for r in canary["features"].values())
    print(f"[MTO-36] {len(canary_features)} feature canaries; max two-polarity AUC={max_auc:.4f}; pass={canary['passed']}", flush=True)
    if not canary["passed"]:
        raise RuntimeError("Suspected leakage in one-feature canary: no holdout result is trusted")

    budgets = budgets_for_folds(holdout)
    base_preds, candidate_preds = [], []
    for f, k in zip(holdout.folds, budgets, strict=True):
        eligible = f["valid"] & ~f["visible"] & features.support
        # Emission uses the same feature support and equal budget in both arms;
        # no full-catalogue exclusion or distance feature is available here.
        base = emit_dots(features.rtp_edge, eligible, k, support=features.support)
        cand = emit_dots(features.mtop36_field, eligible, k, support=features.support)
        base_preds.append(base.astype(np.uint8))
        candidate_preds.append(cand.astype(np.uint8))
        print(f"[MTO-36] {f['name']}: {int(f['truth'].sum())} withheld; "+
              f"budget {k}; control {int(base.sum())}, candidate {int(cand.sum())}", flush=True)
    comparison = holdout.compare_paired(candidate_preds, base_preds)
    result = holdout.summarize(candidate_preds)
    baseline = holdout.summarize(base_preds)
    if result["n_withheld_positive_pixels"] != int(labels.sum()):
        raise RuntimeError("Whole-component fold holdout lost/repeated positive pixels")
    np.savez_compressed(cache / "e1_predictions.npz", **{
        **{f"candidate_{i}": a for i, a in enumerate(candidate_preds)},
        **{f"control_{i}": a for i, a in enumerate(base_preds)},
    })
    print(f"[MTO-36] E1 HOLDOUT-DTI candidate {result['dti']:.6f} CI {result['ci95']['interval']} "+
          f"control {baseline['dti']:.6f}; paired {comparison['paired_delta_dti']:+.6f} CI {comparison['paired_delta_ci95']}", flush=True)

    card = {
        "schema": "gems-parallel-run-card-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "branch": "arena/cee70ea1-gemsdoe36",
        "lane": "MTO-36, one E1 magnetic-contact-termination × orthogonal-gravity experiment",
        "preregistration": {"path": str(prereg.relative_to(ROOT)), "sha256": prereg_sha},
        "hypothesis": "Fault-truncated RTP lithologic contact intersecting an orthogonal gravity edge under unmapped basin cover",
        "mechanism": "One-sided tangent-arm magnetic gradient loss at ±600 m across an RTP contact, corroborated by a nearly orthogonal gravity anomaly gradient. Frozen 0.75 crossing / 0.25 termination field; no copied surface or supervised tuning.",
        "named_non_fault_process": "Intrusive/plutonic contact junction or caldera ring margin; survey striping can also terminate apparent magnetic contacts.",
        "inputs": {"owner_mirror_sha256": core_hashes, "reused_cache": "scripts/prepare_data.py -> .cache/gems_work/bands", "label_based_features": 0, "mag_scale_p95": features.mag_scale_p95, "grav_scale_p95": features.grav_scale_p95},
        "budget": {"max_experiments": 3, "experiments_run": 1, "max_wall_seconds": MAX_SECONDS, "dot_budget": TOTAL_DOTS, "fold_dot_budgets": budgets},
        "holdout_dti": {
            "label": "HOLDOUT-DTI", "evaluator_version": result["evaluator_version"],
            "withheld_positives": result["n_withheld_positive_pixels"],
            "withheld_whole_components": result["n_unique_withheld_components"],
            "buffer_m": result["protocol"]["buffer_m"],
            "pooled_candidate": result["dti"], "ci95_candidate": result["ci95"]["interval"],
            "pooled_control": baseline["dti"], "ci95_control": baseline["ci95"]["interval"],
            "paired_delta": comparison["paired_delta_dti"], "paired_ci95": comparison["paired_delta_ci95"],
            "fold_wins": comparison["fold_wins"], "folds": comparison["folds"],
            "recorded_group_best_not_recomputed": GROUP_BEST,
            "score_is_not_a_leaderboard_projection": True,
        },
        "leakage_canary": {"passed": bool(canary["passed"]), "n_features": len(canary_features),
                           "max_two_polarity_auc": max_auc, "threshold": 0.90, "details": canary["features"]},
        "organizer_receipt_for_this_file": None,
        "registry": None, "raster_sha256": None, "validator_output": None,
        "submission_name": None, "submission_note": None,
        "gates": {}, "verdict": "negative",
        "download_ok_for_research": False, "submit_ok": False,
    }

    # First registry check BEFORE any full-map dot placement. Every SHA-pinned
    # registry raster is compared on the exact footprint by the shared tool.
    surf_cmp = compare_registry(features.mtop36_field, foot, entries, ROOT)
    surf_audit = _summarize_registry(surf_cmp, stage="surface_before_placement")
    print(f"[MTO-36] Pre-placement registry surface pass={surf_audit['all_entries_passed_literal']} "+
          f"max|rho|={surf_audit['max_abs_rank_correlation']:.4f} n={len(entries)}", flush=True)
    card["registry"] = {"surface_before_placement": surf_audit, "final_dots": None}
    if not surf_audit["all_entries_passed_literal"]:
        card["duplicate_stop_stage"] = "surface_before_placement"
        card["elapsed_wall_seconds"] = time.monotonic() - start
        record(card)
        return 0  # Literal lane rule: do not place any dots after a duplicate surface.

    # Final physical field = E1 untrained candidate, never a copied raster.
    dcat = distance_transform_edt(~labels)
    eligible = foot & features.support & ~labels & (dcat > 2.0)
    del dcat
    dots = emit_dots(features.mtop36_field, eligible, TOTAL_DOTS, support=features.support)
    if not dots.any() or np.any(dots & labels):
        raise RuntimeError("No off-catalogue dots or catalogue masking failed")
    # Compute literal all-entry novelty; the synthetic lattice is disclosed,
    # but still fails the user's unqualified <=70% overlap rule.
    dot_cmp = compare_registry(features.mtop36_field, foot, entries, ROOT, dots=dots)
    dot_audit = _summarize_registry(dot_cmp, stage="final_dots")
    card["registry"]["final_dots"] = dot_audit
    card["duplicate_stop_stage"] = "final_dots" if not dot_cmp["passed"] else None
    print(f"[MTO-36] Post-placement all-entry overlap={dot_audit['max_dot_overlap_3px_all']:.4f} "+
          f"focus9={dot_audit['max_dot_overlap_3px_focus9']:.4f} literal pass={dot_cmp['passed']}", flush=True)

    # Archive exactly the evaluated dots as a RESEARCH artifact, even if the
    # final uniqueness check forces a negative stop. This fulfills the owner
    # request for a download while explicitly refusing slot authorization.
    prediction = dots.astype(np.float32)
    content_id = scored_content_id(prediction, foot, labels)
    stem = f"gemsdoe36-mto36-ortho-contact-20261026-{content_id}-zeros"
    note = f"GEMSDOE36 MTO-36 contact-crosscut | HOLDOUT-DTI {result['dti']:.4f} | NEGATIVE; research only | id {content_id}"
    if len(note) > 140:
        raise RuntimeError(f"Note too long ({len(note)})")
    tif = DL / f"{stem}.tif"
    if tif.exists():
        raise RuntimeError(f"Refusing to overwrite prior output: {tif}")
    write_submission(prediction, TEMPLATE, tif, outside="zero")
    val = check_format(tif, foot, labels)
    if not val["all_passed"]:
        tif.unlink(missing_ok=True)  # never publish an invalid draft
        raise RuntimeError(f"New TIFF failed format validation: {val}")
    zip_path = zip_single(tif)
    with zipfile.ZipFile(zip_path) as z:
        if z.namelist() != [tif.name]:
            raise RuntimeError("ZIP must contain exactly the GeoTIFF")
    card["raster_sha256"] = sha256_file(tif)
    card["validator_output"] = val
    card["submission_name"] = stem
    card["submission_note"] = note
    card["submission_note_length"] = len(note)
    card["download"] = {
        "tif": str(tif.relative_to(ROOT)), "tif_bytes": tif.stat().st_size,
        "zip": str(zip_path.relative_to(ROOT)), "zip_sha256": sha256_file(zip_path),
        "dot_count": int(dots.sum()), "sha256": card["raster_sha256"],
    }
    card["gates"] = {
        "E1_matched_control_paired_ci_strictly_positive_and_three_folds": bool(
            comparison["paired_delta_ci95"][0] > 0 and comparison["fold_wins"] >= 3),
        "E1_beats_recorded_shared_holdout_best": bool(result["dti"] > GROUP_BEST),
        "single_feature_canary_pass": bool(canary["passed"]),
        "preplacement_surface_literal_unique": bool(surf_cmp["passed"]),
        "final_dots_literal_unique": bool(dot_cmp["passed"]),
        "format_safe_full_grid_01": bool(val["all_passed"]),
        "time_and_experiment_cap": bool(time.monotonic() - start <= MAX_SECONDS),
    }
    card["verdict"] = "promote" if all(card["gates"].values()) else "negative"
    card["download_ok_for_research"] = True
    card["submit_ok"] = False  # A separate weekly selector is always required.
    card["elapsed_wall_seconds"] = round(time.monotonic() - start, 1)
    record(card)
    (DL / f"{stem}.receipt.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(f"[MTO-36] {card['verdict'].upper()} · DOWNLOAD: YES · LIVE SLOT: DO NOT SUBMIT; "+
          f"{tif.name} sha256={card['raster_sha256']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
