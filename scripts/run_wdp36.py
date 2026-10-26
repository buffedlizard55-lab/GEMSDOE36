#!/usr/bin/env python3
"""WDP-36 preregistered pipeline: persistence surfaces -> canary -> buffered
whole-segment holdout (A0 control + EXP-1..3) -> winner emission -> strict
[0,1] zeros GeoTIFF + ZIP -> registry uniqueness -> JSON run card.

Fail-closed throughout: verifies the preregistration SHA-256 lock first, uses
only the shared template evaluator/writer/novelty tools, and never authorises
a weekly slot unless every preregistered gate passes.  No human step.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.holdout import SegmentHoldout  # noqa: E402
from gems.novelty import compare_registry, dot_overlap  # noqa: E402
from gems.submission import check_variants, write_submission, zip_single  # noqa: E402
from gemsdoe36.submission import sha256_file, validate_submission  # noqa: E402
from gemsdoe36.submodular_emit import emit_submodular_cover  # noqa: E402
from gemsdoe36.wdp_features import (  # noqa: E402
    clean_band,
    footprint_percentile_ranks,
    gradient_rank_surface,
    persistence_from_ranks,
    thdr_ranks_by_height,
    weighted_rank_fusion,
)

PREREG = ROOT / "evidence/wdp36_preregistration_20261026.json"
PREREG_SHA256 = "860f7a3565735ae7837aa62a48c5457fc2ab9398e066c89b8f564409b659076f"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
FEATURES = ROOT / "data/raw/training_features.tif"
CACHE = ROOT / ".cache/gems_work/wdp36"
DOWNLOADS = ROOT / "docs/downloads"
TOTAL_BUDGET = 37_654
GROUP_BEST = 0.14876
REPO_B0 = 0.13375
EXPECTED_BANDS = {
    4: "geod_2ndinv",
    7: "geod_shearrate",
    8: "geod_dilaterate",
    10: "deq_n100a15",
    13: "iso_grav_anom",
    14: "tmi",
    16: "ieq_n100a15",
}
FOCUS_SITES = {
    "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
    "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
}


def _log(msg: str, t0: float) -> None:
    print(f"[{time.time() - t0:7.1f}s] {msg}", flush=True)


def _save(name: str, arr: np.ndarray) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{name}.npy"
    np.save(p, np.asarray(arr, dtype=np.float32))
    return p


def _load(name: str) -> np.memmap:
    return np.load(CACHE / f"{name}.npy", mmap_mode="r")


def build_surfaces(footprint: np.ndarray, t0: float, reuse: bool) -> dict[str, str]:
    names = ["p_tmi", "p_grav", "a0", "pers", "strain", "seis", "exp2", "exp3"]
    if reuse and all((CACHE / f"{n}.npy").is_file() for n in names):
        _log("reusing cached WDP-36 surfaces", t0)
        return {n: n for n in names}
    with rasterio.open(FEATURES) as src:
        for idx, expected in EXPECTED_BANDS.items():
            got = src.tags(idx).get("band_name")
            if got != expected:
                raise RuntimeError(f"band {idx} is {got!r}, expected {expected!r}; aborting")
        bands = {idx: src.read(idx) for idx in (13, 14)}
    pers_parts: dict[str, np.ndarray] = {}
    a0_ranks: dict[str, np.ndarray] = {}
    for key, idx in (("tmi", 14), ("grav", 13)):
        filled = clean_band(bands.pop(idx), footprint)
        ranks = thdr_ranks_by_height(filled, footprint)
        del filled
        gc.collect()
        a0_ranks[key] = ranks[0.0]
        pers_parts[key] = persistence_from_ranks(ranks)
        del ranks
        gc.collect()
        _log(f"{key}: continuation worms + persistence done", t0)
    _save("p_tmi", pers_parts["tmi"])
    _save("p_grav", pers_parts["grav"])
    a0 = weighted_rank_fusion([(a0_ranks["tmi"], 0.5), (a0_ranks["grav"], 0.5)], footprint)
    _save("a0", a0)
    del a0, a0_ranks
    pers = weighted_rank_fusion([(pers_parts["tmi"], 0.5), (pers_parts["grav"], 0.5)], footprint)
    _save("pers", pers)
    del pers, pers_parts
    gc.collect()
    _log("PERS + A0 done", t0)

    with rasterio.open(FEATURES) as src:
        strain_ranks = []
        for idx in (4, 7, 8):
            filled = clean_band(src.read(idx), footprint)
            strain_ranks.append(gradient_rank_surface(filled, footprint, sigma_px=1.5))
            del filled
        _log("strain gradient ridges done", t0)
        deq = clean_band(src.read(10), footprint)
        ieq = clean_band(src.read(16), footprint)
    strain = weighted_rank_fusion([(r, 1.0) for r in strain_ranks], footprint)
    _save("strain", strain)
    del strain, strain_ranks
    seis_raw = weighted_rank_fusion(
        [
            (footprint_percentile_ranks(ieq, footprint), 0.5),
            (footprint_percentile_ranks(-deq, footprint), 0.5),
        ],
        footprint,
    )
    del deq, ieq
    from scipy.ndimage import gaussian_filter

    seis = footprint_percentile_ranks(
        gaussian_filter(np.asarray(seis_raw, dtype=np.float32), sigma=2.0, mode="nearest"),
        footprint,
    )
    _save("seis", seis)
    del seis, seis_raw
    gc.collect()
    _log("STRAIN + SEIS done", t0)

    exp2 = weighted_rank_fusion(
        [(np.asarray(_load("pers")), 0.70), (np.asarray(_load("strain")), 0.30)], footprint
    )
    _save("exp2", exp2)
    del exp2
    exp3 = weighted_rank_fusion(
        [
            (np.asarray(_load("pers")), 0.60),
            (np.asarray(_load("strain")), 0.25),
            (np.asarray(_load("seis")), 0.15),
        ],
        footprint,
    )
    _save("exp3", exp3)
    del exp3
    gc.collect()
    _log("EXP-2/EXP-3 fusions done", t0)
    return {n: n for n in names}


def emit_for_folds(surface: np.ndarray, holdout: SegmentHoldout, footprint: np.ndarray):
    preds = []
    n_fp = int(footprint.sum())
    for fold in holdout.folds:
        d_vis = distance_transform_edt(~fold["visible"])
        eligible = fold["valid"] & (d_vis > 2.0)
        del d_vis
        budget = int(round(TOTAL_BUDGET * int(fold["valid"].sum()) / n_fp))
        res = emit_submodular_cover(
            np.asarray(surface, dtype=np.float32),
            eligible,
            budget=budget,
            valid_footprint=fold["valid"],
        )
        preds.append(res.mask.astype(np.uint8))
        del res, eligible
        gc.collect()
    return preds


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reuse-cache", action="store_true", help="reuse cached surfaces if present")
    ap.add_argument("--skip-registry", action="store_true", help="skip expanded registry compare")
    args = ap.parse_args()
    t0 = time.time()

    if sha256_file(PREREG) != PREREG_SHA256:
        raise RuntimeError("preregistration SHA-256 lock mismatch; refusing to run")
    _log("preregistration lock verified", t0)

    with rasterio.open(TEMPLATE) as t:
        footprint = np.isfinite(t.read(1))
    with rasterio.open(LABELS) as s:
        catalogue = (s.read(1) == 1) & footprint
    _log(f"footprint={int(footprint.sum())} catalogue={int(catalogue.sum())}", t0)

    build_surfaces(footprint, t0, reuse=args.reuse_cache)

    holdout = SegmentHoldout(footprint, catalogue, buffer_px=15)
    _log(f"SegmentHoldout ready: {holdout.n_components} components, 4 folds", t0)

    canary_features = {
        "p_tmi": _load("p_tmi"),
        "p_grav": _load("p_grav"),
        "a0_single_scale": _load("a0"),
        "pers_exp1": _load("pers"),
        "strain": _load("strain"),
        "seis": _load("seis"),
        "exp2": _load("exp2"),
        "exp3": _load("exp3"),
    }
    canary = holdout.canary(canary_features)
    max_auc2 = 0.0
    worst = None
    for name, row in canary["features"].items():
        cand = [max(row["pooled_auc"], 1 - row["pooled_auc"])] + [
            max(f["auc"], 1 - f["auc"]) for f in row["folds"]
        ]
        if max(cand) > max_auc2:
            max_auc2, worst = float(max(cand)), name
    _log(f"canary passed={canary['passed']} max two-polarity AUC={max_auc2:.4f} ({worst})", t0)

    results: dict[str, dict] = {}
    preds_by_arm: dict[str, list] = {}
    for arm, surf_name in (("A0", "a0"), ("EXP-1", "pers"), ("EXP-2", "exp2"), ("EXP-3", "exp3")):
        preds = emit_for_folds(np.asarray(_load(surf_name)), holdout, footprint)
        summary = holdout.summarize(preds)
        results[arm] = summary
        preds_by_arm[arm] = preds
        _log(
            f"{arm}: HOLDOUT-DTI={summary['dti']:.6f} CI={summary['ci95']['interval']} "
            f"withheld={summary['n_withheld_positive_pixels']}",
            t0,
        )
    winner = max(("EXP-1", "EXP-2", "EXP-3"), key=lambda a: results[a]["dti"])
    paired = holdout.compare_paired(preds_by_arm[winner], preds_by_arm["A0"])
    _log(f"winner={winner}; paired vs A0 delta={paired['paired_delta_dti']:+.6f} {paired['paired_delta_ci95']}", t0)

    surf_file = {"EXP-1": "pers", "EXP-2": "exp2", "EXP-3": "exp3"}[winner]
    surface = np.asarray(_load(surf_file), dtype=np.float32)

    # --- Uniqueness stage 1: surface before placement (rank correlation) ---
    reg_entries = json.loads((ROOT / "registry/uniqueness_registry.json").read_text())["entries"]
    available, missing = [], []
    for e in reg_entries:
        (available if (ROOT / e["cache_path"]).is_file() else missing).append(e)
    _log(f"registry entries available={len(available)} missing={len(missing)}", t0)
    surface_check = None
    if available and not args.skip_registry:
        surface_check = compare_registry(surface, footprint, available, ROOT, dots=None)
        _log(
            f"surface uniqueness passed={surface_check['passed']} "
            f"max|rho|={surface_check['max_abs_rank_correlation']}",
            t0,
        )

    # --- Final deployment emission (full catalogue exclusion) ---
    d_cat = distance_transform_edt(~catalogue)
    eligible_final = footprint & (d_cat > 2.0)
    final = emit_submodular_cover(
        surface, eligible_final, budget=TOTAL_BUDGET, valid_footprint=footprint
    )
    dots = final.mask
    n_dots = int(dots.sum())
    dcat_dots = d_cat[dots]
    boundary_dist = distance_transform_edt(footprint)[dots]
    pts = np.argwhere(dots)
    nn = cKDTree(pts).query(pts, k=2)[0][:, 1] if len(pts) > 1 else np.array([])
    _log(f"final dots={n_dots} min d_cat={float(dcat_dots.min())} median={float(np.median(dcat_dots))}", t0)

    exp_slug = winner.lower().replace("-", "")
    tif_name = f"gemsdoe36-wdp36-{exp_slug}-20261026-zeros.tif"
    tif_path = DOWNLOADS / tif_name
    write_submission(dots.astype(np.float32), TEMPLATE, tif_path, outside="zero")
    zip_path = zip_single(tif_path, DOWNLOADS / (tif_path.stem + ".zip"))
    raster_sha = sha256_file(tif_path)
    zip_sha = sha256_file(zip_path)
    _log(f"wrote {tif_name} sha256={raster_sha}", t0)

    fmt = check_variants(tif_path, TEMPLATE)
    rep = validate_submission(tif_path, TEMPLATE, require_nonfinite_outside=False)
    with rasterio.open(tif_path) as s:
        arr = s.read(1)
        crs_ok = s.crs is not None and s.crs.to_epsg() == 32611
        shape = list(s.shape)
        nodata = s.nodata
    strict = bool(np.isfinite(arr).all() and float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0)

    # --- Uniqueness stage 2: final dots ---
    dots_check = None
    focus_rows = []
    if available and not args.skip_registry:
        dots_check = compare_registry(
            surface, footprint, available, ROOT, dots=dots, separate_calibration_controls=True
        )
        _log(
            f"dots uniqueness competing_passed={dots_check.get('competing_method_passed')} "
            f"literal_passed={dots_check.get('literal_unseparated_passed')} "
            f"max_competing_overlap={dots_check.get('max_competing_dot_overlap')}",
            t0,
        )
        by_file = {r["file"]: r for r in dots_check["rows"]}
        for e in available:
            if e.get("site") in FOCUS_SITES:
                r = by_file.get(e["file"])
                if r:
                    focus_rows.append(r)
    # Individual overlaps vs this repo's own published lanes (local files).
    local_overlaps = {}
    for p in sorted(DOWNLOADS.glob("*.tif")):
        if p.name in (tif_name,) or p.stat().st_size < 50_000:
            continue
        with rasterio.open(p) as s:
            if s.shape != dots.shape:
                continue
            a = s.read(1)
        ref = footprint & np.isfinite(a) & (a > 0)
        local_overlaps[p.name] = dot_overlap(dots, ref)["candidate_within_3px_of_reference"]

    win = results[winner]
    g1 = bool(canary["passed"])
    g2 = bool(win["dti"] > GROUP_BEST and paired["paired_delta_dti"] > 0)
    g3_surface = bool(surface_check and surface_check["passed"])
    g3_dots = bool(dots_check and dots_check.get("competing_method_passed"))
    g3 = bool(g3_surface and g3_dots and not missing)
    g4 = bool(fmt["format_valid"] and rep.passed and strict and n_dots == TOTAL_BUDGET
              and float(dcat_dots.min()) > 2.0 and crs_ok)
    verdict = "promote" if (g1 and g2 and g3 and g4) else "negative"

    arm_desc = {
        "EXP-1": "worm persistence 0-800m only",
        "EXP-2": "worm persistence 0-800m+strain ridges",
        "EXP-3": "worm persistence 0-800m+strain+seis",
    }[winner]
    note = (
        f"GEMSDOE36 WDP-36 {winner} | {arm_desc} | "
        f"HOLDOUT-DTI {win['dti']:.4f} | {'PROMOTE' if verdict == 'promote' else 'NEGATIVE hold slot'}"
    )
    if len(note) > 140:
        raise RuntimeError(f"submission note exceeds 140 chars ({len(note)})")

    def arm_block(arm: str) -> dict:
        s = results[arm]
        return {
            "label": "HOLDOUT-DTI",
            "evaluator_version": s["evaluator_version"],
            "dti": s["dti"],
            "ci95": s["ci95"]["interval"],
            "n_withheld_positive_pixels": s["n_withheld_positive_pixels"],
            "n_unique_withheld_components": s["n_unique_withheld_components"],
            "folds": [
                {"fold": f["fold"], "dti": f["dti"], "n_truth": f["n_truth"],
                 "n_emitted": f["n_emitted"]}
                for f in s["folds"]
            ],
        }

    max_focus_overlap = max(
        (r["candidate_dot_overlap_within_3px"] or 0.0) for r in focus_rows
    ) if focus_rows else None
    card = {
        "schema": "gems-parallel-run-card-v1",
        "generated_utc": "2026-10-26",
        "lane": "GEMSDOE36 / WDP-36",
        "branch": "arena/b8f55e32-gemsdoe36",
        "preregistration": {
            "file": "evidence/wdp36_preregistration_20261026.json",
            "sha256": PREREG_SHA256,
            "locked_before_holdout": True,
        },
        "hypothesis": (
            "H-WDP-A (+B/C add-ons): basement faults buried under basin fill persist as "
            "potential-field THDR worms under 0-800 m upward continuation while shallow "
            "sources decay; strain-rate gradient ridges and seismic composites add "
            "present-day activity evidence for blind structures."
        ),
        "mechanism": (
            "Unsupervised geometric-mean percentile persistence of spectral THDR across "
            "continuation heights (TMI band14 + gravity band13), optional rank fusion with "
            "strain gradient ridges (04/07/08) and seismic composite (16/-10), exact 300 m "
            "CELF submodular emission outside d_cat<=2px. No catalogue-trained parameter."
        ),
        "named_non_fault_mimic": (
            "Deep non-fault basement lithologic contacts (pluton margins) persist identically; "
            "smooth regional strain gradients/volcanic inflation mimic strain ridges; "
            "aftershock clouds/induced seismicity mimic blind-fault lineaments."
        ),
        "winning_experiment": winner,
        "holdout_dti": {
            "winner": arm_block(winner),
            "all_arms": {a: arm_block(a) for a in ("A0", "EXP-1", "EXP-2", "EXP-3")},
            "paired_winner_vs_A0": paired,
            "promotion_bars": {"repo_B0": REPO_B0, "group_best": GROUP_BEST,
                               "beats_repo_B0": bool(win["dti"] > REPO_B0),
                               "beats_group_best": bool(win["dti"] > GROUP_BEST)},
        },
        "experiment_budget": {
            "max_experiments_allowed": 3,
            "experiments_executed": 3,
            "max_walltime_seconds": 7200,
            "elapsed_walltime_seconds": round(time.time() - t0, 1),
        },
        "leakage_canary": {
            "passed": g1,
            "n_features_tested": len(canary["features"]),
            "auc_cap": 0.90,
            "max_two_polarity_auc": max_auc2,
            "max_feature": worst,
            "detail_file": "evidence/wdp36_holdout_experiments_20261026.json",
        },
        "registry_uniqueness": {
            "entries_in_registry": len(reg_entries),
            "entries_available_on_disk": len(available),
            "entries_missing_on_disk": len(missing),
            "surface_before_placement": None if surface_check is None else {
                "passed": surface_check["passed"],
                "max_abs_rank_correlation": surface_check["max_abs_rank_correlation"],
                "rasters_compared": surface_check["registry_unique_rasters"],
            },
            "final_dots": None if dots_check is None else {
                "competing_method_passed": dots_check.get("competing_method_passed"),
                "literal_unseparated_passed": dots_check.get("literal_unseparated_passed"),
                "max_abs_rank_correlation": dots_check["max_abs_rank_correlation"],
                "max_competing_dot_overlap": dots_check.get("max_competing_dot_overlap"),
                "max_dot_overlap_incl_controls": dots_check.get("max_dot_overlap"),
                "calibration_controls": dots_check.get("calibration_control_summary"),
                "max_focus9_dot_overlap": max_focus_overlap,
            },
            "local_lane_dot_overlaps_candidate_within_3px": local_overlaps,
            "crosscheck_file": "evidence/wdp36_crosscheck_20261026.json",
        },
        "raster_sha256": raster_sha,
        "zip_sha256": zip_sha,
        "validator_output": {
            "ok_to_download_research_tif": bool(g4),
            "safe_to_download_and_submit": bool(verdict == "promote"),
            "valid_for_portal": bool(fmt["format_valid"] and strict),
            "template_format_valid": fmt["format_valid"],
            "template_hard_failures": fmt["hard_failures"],
            "repo_validator_passed": rep.passed,
            "repo_validator_errors": list(rep.errors),
            "strict_whole_array_0_1": strict,
            "crs": "EPSG:32611",
            "crs_ok": crs_ok,
            "shape": shape,
            "dtype": "float32",
            "nodata": nodata,
            "nan_inside_footprint": int(np.isnan(arr[footprint]).sum()),
            "values_in_0_1": strict,
            "positive_dots_emitted": n_dots,
            "dots_within_2px_of_catalogue": int((dcat_dots <= 2.0).sum()),
            "median_distance_to_catalogue_px": float(np.median(dcat_dots)),
            "share_dots_within_5px_of_footprint_boundary": float((boundary_dist <= 5.0).mean()),
            "dot_spacing_px_min": float(nn.min()) if nn.size else None,
            "dot_spacing_px_median": float(np.median(nn)) if nn.size else None,
        },
        "gates": {
            "G1_leakage_canary": g1,
            "G2_beats_group_holdout_best_and_A0": g2,
            "G3a_unique_surface": g3_surface,
            "G3b_unique_final_dots_competing": g3_dots,
            "G3_registry_complete_on_disk": bool(not missing),
            "G4_format_and_strict_range": g4,
        },
        "submission_name": f"gemsdoe36-wdp36-{exp_slug}-20261026",
        "submission_file": tif_name,
        "submission_zip": zip_path.name,
        "submission_note": note,
        "submission_note_chars": len(note),
        "organizer_score": None,
        "verdict": verdict,
        "status": "OK_TO_SUBMIT" if verdict == "promote" else "DO_NOT_SUBMIT",
    }
    (ROOT / "evidence/wdp36_holdout_experiments_20261026.json").write_text(
        json.dumps({"canary": canary, "results": results, "paired": paired}, indent=1, default=float) + "\n"
    )
    (ROOT / "evidence/wdp36_crosscheck_20261026.json").write_text(
        json.dumps({"surface": surface_check, "dots": dots_check}, indent=1, default=float) + "\n"
    )
    card_path = ROOT / "evidence/wdp36_run_card_20261026.json"
    card_path.write_text(json.dumps(card, indent=2) + "\n")
    (DOWNLOADS / (tif_path.stem + ".receipt.json")).write_text(json.dumps(card, indent=2) + "\n")
    _log(f"run card -> {card_path} verdict={verdict}", t0)
    print(json.dumps({k: card[k] for k in ("winning_experiment", "verdict", "status",
                     "submission_file", "raster_sha256", "gates")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
