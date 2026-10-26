#!/usr/bin/env python3
"""Fail-closed verification of the NEW negative MTO-36 research release.

A locally valid GeoTIFF is necessary for a research download. It NEVER
supersedes a failed strict all-registry duplicate/holdout gate or authorizes an
organizer upload. The separate CTRB/ATVR legacy gates remain independent.
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.submission import check_variants  # noqa: E402
from gemsdoe36.submission import validate_submission  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_all(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    card_path = root / "evidence/mto36_run_card_20261026.json"
    card = json.loads(card_path.read_text())
    d = card["download"]
    tif, archive = root / d["tif"], root / d["zip"]
    docs = root / "docs"

    for candidate, expected in (
        (tif, card["raster_sha256"]), (archive, d["zip_sha256"]),
    ):
        if not candidate.is_file() or digest(candidate) != expected:
            errors.append(f"Missing or mismatched release file: {candidate}")
    for copy in (
        docs / "downloads/mto36-run-card.json",
        tif.with_suffix(".receipt.json"),
    ):
        if not copy.is_file() or copy.read_bytes() != card_path.read_bytes():
            errors.append(f"Run-card mirror does not match evidence: {copy}")
    if tif.is_file() and archive.is_file():
        with zipfile.ZipFile(archive) as zf:
            if zf.namelist() != [tif.name]:
                errors.append("ZIP must contain exactly one TIFF with the expected filename")
            elif hashlib.sha256(zf.read(tif.name)).hexdigest() != card["raster_sha256"]:
                errors.append("ZIP TIFF contents differ from original bytes")

    h, r, gates = card["holdout_dti"], card["registry"], card["gates"]
    if card["verdict"] != "negative" or card["submit_ok"] or not card["download_ok_for_research"]:
        errors.append("A negative duplicate must be research-only, never submit-authorized")
    if card["organizer_receipt_for_this_file"] is not None:
        errors.append("A negative research file must not claim an organizer receipt")
    if card["budget"]["experiments_run"] > 3 or card["elapsed_wall_seconds"] > 7200:
        errors.append("Experiment or time budget exceeded")
    if len(card["submission_note"]) > 140 or len(card["submission_note"]) != card["submission_note_length"]:
        errors.append("Note length mismatch / exceeds 140")
    if h["evaluator_version"] != "gems-segment-pooled-v1" or h["withheld_positives"] != 60_988:
        errors.append("Shared pooled evaluator/provenance mismatch")
    if h["paired_ci95"][0] > 0 or h["paired_ci95"][1] < 0 or h["pooled_candidate"] >= h["recorded_group_best_not_recomputed"]:
        errors.append("Holdout failed; do not rewrite as positive or a leaderboard projection")
    if not card["leakage_canary"]["passed"] or card["leakage_canary"]["n_features"] != 9 or card["leakage_canary"]["max_two_polarity_auc"] > 0.90:
        errors.append("Individual feature leakage canary failed")
    before, after = r["surface_before_placement"], r["final_dots"]
    if not before["all_entries_passed_literal"] or before["max_abs_rank_correlation"] > 0.90:
        errors.append("Surface passed claim inconsistent")
    if after["all_entries_passed_literal"] or not (after["max_dot_overlap_3px_all"] > 0.70):
        errors.append("Final duplicate gate MUST remain failed")
    if not (after["n_registry_rasters_verified"] >= 198 and after["overlap_vs_champion_B2"] < 0.70):
        errors.append("Comparator population or descriptive focus overlap invalid")
    if not any("lattice-s5" in row["file"] and row["overlap_3px"] > 0.70 for row in after["literal_duplicates"]):
        errors.append("Detected calibration-lattice duplicate is missing")
    if all(gates.values()):
        errors.append("Every gate cannot pass on a negative card")
    if card["duplicate_stop_stage"] != "final_dots":
        errors.append("Duplicate stop must be recorded at final dots")

    tmp = root / "data/raw/sample_submission.tif"
    known = root / "data/raw/existing_faults.tif"
    if not tmp.is_file() or not known.is_file():
        errors.append("Pinned template/catalogue missing: restore core owner mirrors first")
    elif tif.is_file():
        check = check_variants(tif, tmp)
        independent = validate_submission(tif, tmp, require_nonfinite_outside=False)
        if not (check["format_valid"] and check["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"] and independent.passed):
            errors.append("Local dual TIFF validators failed")
        with rasterio.open(tif) as ds, rasterio.open(tmp) as template, rasterio.open(known) as faults:
            arr = ds.read(1)
            foot = np.isfinite(template.read(1))
            cat = faults.read(1) == 1
            if (ds.count, ds.dtypes, ds.shape, ds.crs, ds.transform) != (
                1, ("float32",), template.shape, template.crs, template.transform
            ):
                errors.append("TIFF grid, band count or dtype mismatch")
            if not np.isfinite(arr).all() or np.any((arr < 0) | (arr > 1)):
                errors.append("Any invalid value on entire 2D grid is a release failure")
            if np.any((arr > 0) & (cat | ~foot)) or int(((arr > 0) & foot).sum()) != d["dot_count"]:
                errors.append("Nonzero pixel on known fault/outside footprint or wrong dot count")

    cur = json.loads((docs / "current-run.json").read_text())
    if cur.get("lane_id") != "MTO-36" or cur.get("verdict") != "negative" or cur.get("slot_approved") or cur.get("ok_to_download_and_submit") or cur.get("tif_sha256") != card["raster_sha256"]:
        errors.append("Current Pages manifest contradicts negative MTO card")
    for page in ("index.html", "executive-summary.html"):
        text = (docs / page).read_text()
        if not all(term in text for term in (tif.name, card["raster_sha256"], card["submission_note"], "DO NOT SUBMIT")):
            errors.append(f"Current HTML missing MTO-36 SHA/name/note or negative verdict: {page}")
    focus = json.loads((root / "evidence/focus_sites_9repo_summary_20261026.json").read_text())["focus_sites"]
    if len(focus) != 9 or any("ORGANIZER-CONFIRMED" in row["highest_historical_submission"]["score_label"] for row in focus):
        errors.append("Nine-site ledger still mislabels score provenance")
    for original, copy in (
        (card_path, docs / "downloads/mto36-run-card.json"),
        (root / "evidence/focus_sites_9repo_summary_20261026.json", docs / "downloads/focus9-verified-source-ledger.json"),
        (root / "evidence/mto36_ninesite_forensics.json", docs / "downloads/focus9-source-integrity.json"),
    ):
        if not copy.is_file() or digest(original) != digest(copy):
            errors.append(f"Pages JSON mirror out of sync: {copy}")

    return {
        "passed": not errors, "verdict": card["verdict"],
        "download_research": card["download_ok_for_research"],
        "download_and_submit": card["submit_ok"],
        "tif_sha256": card["raster_sha256"], "errors": errors,
    }


def main() -> int:
    result = verify_all()
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
