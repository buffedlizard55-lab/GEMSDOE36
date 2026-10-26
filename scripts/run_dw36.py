#!/usr/bin/env python3
"""Preregistered DW36 single experiment; negative results still produce research GeoTIFF."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from run_mto_contact import budgets_for_folds, check_format  # noqa: E402

from gems.holdout import SegmentHoldout  # noqa: E402
from gems.novelty import compare_registry  # noqa: E402
from gems.submission import scored_content_id, write_submission, zip_single  # noqa: E402
from gemsdoe36.h36_emission import emit_dots  # noqa: E402

BANDS = ROOT / ".cache/gems_work/bands"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
SPEC = ROOT / "knowledge/dw36_preregistration_2026-10-26.md"
REGISTRY = ROOT / "registry/uniqueness_registry.json"
OUT = ROOT / "docs/downloads"
CARD = ROOT / "evidence/dw36_run_card_20261026.json"
BUDGET = 37654


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def smoothed_gradient(a, foot, sigma):
    finite = foot & np.isfinite(a) & (a > -1e38)
    weight = gaussian_filter(finite.astype(np.float32), sigma, mode="nearest")
    smooth = gaussian_filter(np.where(finite, a, 0).astype(np.float32), sigma, mode="nearest")
    smooth /= np.maximum(weight, 1e-5)
    gy, gx = np.gradient(smooth)
    return np.hypot(gy, gx).astype(np.float32), weight > .95


def scale(a, support):
    p95 = float(np.percentile(a[support], 95))
    if p95 <= 0 or not np.isfinite(p95):
        raise ValueError("Invalid physical gradient scale")
    return np.clip(a / p95, 0, 2).astype(np.float32), p95


def fields(foot):
    rtp = np.load(BANDS / "02_rtp.npy", mmap_mode="r", allow_pickle=False)
    grav = np.load(BANDS / "13_iso_grav_anom.npy", mmap_mode="r", allow_pickle=False)
    elev = np.load(BANDS / "12_det_elev.npy", mmap_mode="r", allow_pickle=False)
    g2, s2 = smoothed_gradient(rtp, foot, 2)
    g6, s6 = smoothed_gradient(rtp, foot, 6)
    g4, s4 = smoothed_gradient(grav, foot, 4)
    topo, st = smoothed_gradient(elev, foot, 2)
    support = foot & s2 & s6 & s4 & st
    g2, p2 = scale(g2, support)
    g6, p6 = scale(g6, support)
    g4, p4 = scale(g4, support)
    topo, pt = scale(topo, support)
    # Different spatial width from WDP's continuation or MTO's termination.
    broad = np.clip(g6 / (g2 + 0.05), 0, 2).astype(np.float32)
    candidate = broad * np.minimum(g6, 1) * np.minimum(g4, 1) / (1 + topo)
    control = np.minimum(g2, 1) * np.minimum(g4, 1)
    candidate[~support] = 0
    control[~support] = 0
    return {"rtp_gradient_2": g2, "rtp_gradient_6": g6, "gravity_gradient_4": g4,
            "elevation_gradient_2": topo, "magnetic_width_ratio": broad,
            "dw36_field": candidate.astype(np.float32), "control": control.astype(np.float32)}, support, {
                "rtp_g2": p2, "rtp_g6": p6, "grav_g4": p4, "topo_g2": pt,
            }


def registry_entries():
    all_entries = json.loads(REGISTRY.read_text())["entries"]
    present, missing = [], []
    for row in all_entries:
        p = ROOT / row["cache_path"]
        if p.is_file() and sha(p) == row["file_sha256"]:
            present.append(row)
        else:
            missing.append(row["file"])
    return present, missing


def audit(result):
    rows = result["rows"]
    focus = [r for r in rows if r["file"].split("/", 1)[0] in {
        "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
        "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}]
    def worst(rows):
        return max((r for r in rows if r["candidate_dot_overlap_within_3px"] is not None),
                   key=lambda r: r["candidate_dot_overlap_within_3px"], default=None)
    return {"registry_count": len(rows), "max_abs_rank": result["max_abs_rank_correlation"],
            "max_3px_overlap": result["max_dot_overlap"],
            "worst_file": worst(rows)["file"] if worst(rows) else None,
            "focus9_max_3px_overlap": worst(focus)["candidate_dot_overlap_within_3px"] if worst(focus) else None,
            "focus9_worst_file": worst(focus)["file"] if worst(focus) else None,
            "duplicates": [{"file": r["file"], "rho": r["raw_spearman"],
                            "overlap": r["candidate_dot_overlap_within_3px"]}
                           for r in rows if r["duplicate"]], "passed_present_comparators": result["passed"]}


def main():
    t0 = time.monotonic()
    man = json.loads((ROOT / "registry/data_manifest.json").read_text())
    pinned = {r["dest"]: r["sha256"] for r in man["files"]}
    for name in ("training_features.tif", "labels.tif", "sample_submission.tif"):
        if sha(ROOT / "data/raw" / name) != pinned[name]:
            raise RuntimeError("Missing or changed owner-mirror input " + name)
    with rasterio.open(TEMPLATE) as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(LABELS) as ds:
        labels = ds.read(1) == 1
    if int(foot.sum()) != 5167373 or int(labels.sum()) != 60988 or np.any(labels & ~foot):
        raise RuntimeError("Input footprint/catalogue mismatch")
    feature, support, scales = fields(foot)
    entries, missing = registry_entries()
    if not entries:
        raise RuntimeError("No pinned comparators available")
    ho = SegmentHoldout(foot, labels, buffer_px=15)
    canary = ho.canary(feature)
    auc_max = max(max(abs(r["pooled_auc"] - .5) + .5,
                      *(abs(f["auc"] - .5) + .5 for f in r["folds"]))
                  for r in canary["features"].values())
    if not canary["passed"] or auc_max > .90:
        raise RuntimeError("Leakage canary > 0.90; stop")
    budgets = budgets_for_folds(ho)
    candidate, control = [], []
    for f, k in zip(ho.folds, budgets, strict=True):
        eligible = f["valid"] & ~f["visible"] & support
        candidate.append(emit_dots(feature["dw36_field"], eligible, k, support=support))
        control.append(emit_dots(feature["control"], eligible, k, support=support))
    candidate_result = ho.summarize(candidate)
    control_result = ho.summarize(control)
    paired = ho.compare_paired(candidate, control)
    pre = audit(compare_registry(feature["dw36_field"], foot, entries, ROOT))
    card = {
        "schema": "gems-parallel-run-card-v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "branch": "arena/18a2db34-gemsdoe36", "preregistration_sha256": sha(SPEC),
        "lane": "DW36 magnetic damage-zone width", "experiments_run": 1,
        "hypothesis": "Covered fault damage-zone magnetic edge survives 600m smoothing, with coincident gravity edge and muted elevation scarp.",
        "mechanism": "Fixed normalized two-scale RTP-gradient width ratio × broad RTP × gravity gradient / (1 + elevation gradient), unsupervised; binary ridge dots.",
        "named_non_fault_process": "Deep intrusive/plutonic lithologic contacts and sedimentary basin boundaries.",
        "owner_mirror_sha256": {n: pinned[n] for n in ("training_features.tif", "labels.tif", "sample_submission.tif")},
        "feature_scales_unlabelled_p95": scales, "leakage_canary": {"passed": canary["passed"], "max_two_polarity_auc": auc_max, "features": canary["features"]},
        "holdout_dti": {"label": "HOLDOUT-DTI", "evaluator_version": candidate_result["evaluator_version"],
                        "withheld_positives": candidate_result["n_withheld_positive_pixels"],
                        "whole_components": candidate_result["n_unique_withheld_components"],
                        "buffer_m": 1500, "pooled_candidate": candidate_result["dti"],
                        "ci95_candidate": candidate_result["ci95"]["interval"],
                        "pooled_control": control_result["dti"], "ci95_control": control_result["ci95"]["interval"],
                        "paired_delta": paired["paired_delta_dti"], "paired_ci95": paired["paired_delta_ci95"],
                        "fold_wins": paired["fold_wins"], "folds": candidate_result["folds"],
                        "not_an_organizer_score_or_projection": True},
        "registry": {"pinned_count": len(entries) + len(missing), "verified_count": len(entries),
                     "missing": missing, "preplacement": pre, "final": None},
        "raster_sha256": None, "validator_output": None, "submission_name": None,
        "submission_note": None, "verdict": "negative", "submit_ok": False,
    }
    CARD.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    if not pre["passed_present_comparators"]:
        card["duplicate_stop_stage"] = "preplacement"
        CARD.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
        return
    dist = distance_transform_edt(~labels)
    eligible = foot & support & ~labels & (dist > 2)
    dots = emit_dots(feature["dw36_field"], eligible, BUDGET, support=support)
    final = audit(compare_registry(feature["dw36_field"], foot, entries, ROOT, dots=dots))
    card["registry"]["final"] = final
    card["duplicate_stop_stage"] = "final" if final["duplicates"] else None
    if final["duplicates"]:
        card["elapsed_wall_seconds"] = round(time.monotonic() - t0, 1)
        CARD.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
        print("DW36 duplicate final dots: logged and stopped before TIFF export", flush=True)
        return
    # A negative research artifact is never promoted or silently used as a live upload.
    values = dots.astype(np.float32)
    name = f"gemsdoe36-dw36-magnetic-width-20261026-{scored_content_id(values, foot, labels)}-zeros"
    note = f"DW36 broad magnetic edge x gravity | HOLDOUT-DTI {candidate_result['dti']:.4f} | NEGATIVE research only"
    if len(note) > 140:
        raise RuntimeError("Submission note over limit")
    path = OUT / (name + ".tif")
    if path.exists():
        raise RuntimeError("Refusing overwrite of prior artifact")
    write_submission(values, TEMPLATE, path, outside="zero")
    validator = check_format(path, foot, labels)
    if not validator["all_passed"]:
        path.unlink()
        raise RuntimeError("Format validation failed: " + str(validator))
    archive = zip_single(path)
    card.update({"raster_sha256": sha(path), "validator_output": validator,
                 "submission_name": name, "submission_note": note,
                 "download": {"tif": str(path.relative_to(ROOT)), "zip": str(archive.relative_to(ROOT)),
                              "dot_count": int(dots.sum()), "zip_sha256": sha(archive)},
                 "gates": {"canary": bool(canary["passed"]),
                           "beats_current_repo_best_holdout": candidate_result["dti"] > .1357593607032416,
                           "beats_recorded_cross_site_best_holdout": candidate_result["dti"] > .14876,
                           "positive_paired_ci_and_three_fold_wins": paired["paired_delta_ci95"][0] > 0 and paired["fold_wins"] >= 3,
                           "surface_rank": pre["passed_present_comparators"],
                           "full_registry_present": not missing,
                           "final_dot_uniqueness_literal": final["passed_present_comparators"] and not missing,
                           "format": validator["all_passed"]}})
    card["verdict"] = "promote" if all(card["gates"].values()) else "negative"
    card["elapsed_wall_seconds"] = round(time.monotonic() - t0, 1)
    CARD.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(f"DW36 {card['verdict']}: {name}; HOLDOUT-DTI {candidate_result['dti']:.6f}; research download only", flush=True)


if __name__ == "__main__":
    main()
