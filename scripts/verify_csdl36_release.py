#!/usr/bin/env python3
"""Independent automated verifier for the CSDL-36 lane artifacts and audit remediations."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.submission import check_variants  # noqa: E402
from gemsdoe36.csdl_features import (  # noqa: E402
    BASE_FEATURES,
    CSDL_CONDUIT_FEATURES,
    CSDL_STRUCTURAL_FEATURES,
    EXP1_FEATURES,
    EXP2_FEATURES,
    EXP3_BLIND_FEATURES,
    LIDAR_FEATURE_SET,
)
from gemsdoe36.submission import sha256_file, validate_submission  # noqa: E402


def verify_csdl36() -> dict:
    prereg_path = ROOT / "evidence" / "csdl36_preregistration_20261026.json"
    canary_path = ROOT / "evidence" / "csdl36_canary_20261026.json"
    holdout_path = ROOT / "evidence" / "csdl36_holdout_experiments_20261026.json"
    crosscheck_path = ROOT / "evidence" / "csdl36_crosscheck_20261026.json"
    rc_path = ROOT / "evidence" / "csdl36_run_card_20261026.json"
    dl_rc_path = ROOT / "docs" / "downloads" / "csdl36-run-card.json"
    mono_path = ROOT / "docs" / "research" / "csdl36-20261026.md"

    for p in (prereg_path, canary_path, holdout_path, crosscheck_path, rc_path, dl_rc_path, mono_path):
        if not p.is_file():
            raise RuntimeError(f"Missing required CSDL-36 file: {p}")

    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    canary = json.loads(canary_path.read_text(encoding="utf-8"))
    holdout = json.loads(holdout_path.read_text(encoding="utf-8"))
    crosscheck = json.loads(crosscheck_path.read_text(encoding="utf-8"))
    rc = json.loads(rc_path.read_text(encoding="utf-8"))
    dl_rc = json.loads(dl_rc_path.read_text(encoding="utf-8"))

    if rc != dl_rc:
        raise RuntimeError("evidence/csdl36_run_card_20261026.json != docs/downloads/csdl36-run-card.json")

    # 1. Verify IR-GVSC36-04: exact feature counts
    fc = rc["feature_counts"]
    assert fc["base"] == len(BASE_FEATURES) == 59
    assert fc["csdl_structural"] == len(CSDL_STRUCTURAL_FEATURES) == 16
    assert fc["csdl_conduit"] == len(CSDL_CONDUIT_FEATURES) == 12
    assert fc["exp1_total"] == len(EXP1_FEATURES) == 75
    assert fc["exp2_total"] == len(EXP2_FEATURES) == 87
    assert fc["lidar_features_removed"] == len(LIDAR_FEATURE_SET) == 14
    assert fc["exp3_blind_total"] == len(EXP3_BLIND_FEATURES) == 73

    # 2. Verify preregistration hash & experiment budget
    spec_md = ROOT / prereg["markdown_spec_path"]
    if sha256_file(spec_md) != prereg["markdown_spec_sha256"]:
        raise RuntimeError("CSDL-36 preregistration markdown SHA-256 mismatch")
    if rc["experiment_budget"]["experiments_executed"] != 3:
        raise RuntimeError("CSDL-36 must execute exactly 3 candidate experiments")
    if rc["experiment_budget"]["elapsed_walltime_seconds"] > 7200:
        raise RuntimeError("CSDL-36 exceeded 7200s walltime budget")

    # 3. Verify G1 leakage canary & holdout consistency
    if not canary["passed"] or canary["total_features_tested"] != 87 or canary["max_symmetric_auc"] > 0.90:
        raise RuntimeError("CSDL-36 leakage canary check failed")
    if holdout["lane_id"] != rc["lane_id"] or holdout["withheld_positives"] != rc["holdout"]["withheld_positives"]:
        raise RuntimeError("CSDL-36 holdout summary mismatch vs run card")

    # 4. Verify IR-GVSC36-03: pre-placement surface screening chronology
    chron = crosscheck["chronology_proof"]
    if not chron["surface_checked_strictly_before_dot_placement"]:
        raise RuntimeError("Surface correlation was not checked before dot placement")
    if not (chron["pre_placement_surface_check_utc"] <= chron["dot_emission_started_utc"]):
        raise RuntimeError("Timestamp order violation between surface check and dot emission")

    # 5. Verify GeoTIFF & ZIP
    sub = rc["submission"]
    tif_path = ROOT / "docs" / sub["tif_relpath"]
    zip_path = ROOT / "docs" / sub["zip_relpath"]
    tmpl_path = ROOT / "data" / "raw" / "sample_submission.tif"
    if not tif_path.is_file() or not zip_path.is_file():
        raise RuntimeError("Missing CSDL-36 GeoTIFF or ZIP in docs/downloads")
    if sha256_file(tif_path) != sub["raster_sha256"]:
        raise RuntimeError("CSDL-36 GeoTIFF SHA-256 mismatch")
    if sha256_file(zip_path) != sub["zip_sha256"]:
        raise RuntimeError("CSDL-36 ZIP SHA-256 mismatch")
    if not (1 <= sub["note_length"] <= 140):
        raise RuntimeError(f"Invalid note length: {sub['note_length']}")

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if names != [tif_path.name]:
            raise RuntimeError(f"ZIP must contain only {tif_path.name}, got {names}")

    v1 = validate_submission(tif_path, tmpl_path, require_nonfinite_outside=False)
    v2 = check_variants(tif_path, tmpl_path)
    if not v1.passed or not v2["format_valid"]:
        raise RuntimeError("CSDL-36 GeoTIFF failed format validation")
    if not v2["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]:
        raise RuntimeError("CSDL-36 GeoTIFF failed strict [0, 1] whole-array check")

    if rc["verdict"] != "negative" or rc["safe_to_submit_live_slot"] is not False:
        raise RuntimeError("CSDL-36 verdict must remain fail-closed negative")

    return {
        "lane_id": rc["lane_id"],
        "best_arm": rc["best_arm"],
        "holdout_dti": rc["holdout"][rc["best_arm"]]["dti"],
        "focus9_max_overlap_3px": rc["registry_uniqueness"]["focus_9_sites_max_overlap_3px"],
        "focus9_passed": rc["registry_uniqueness"]["focus_9_sites_passed"],
        "verdict": rc["verdict"],
        "tif": tif_path.name,
        "sha256_12": sub["raster_sha256"][:12],
    }


if __name__ == "__main__":
    summary = verify_csdl36()
    print(f"CSDL-36 release verification PASSED: {json.dumps(summary)}")
