#!/usr/bin/env python3
"""Fail-closed artifact-only verification for the GVSC-36 negative research release.

This verifier does not rerun experiments, update any gate, or authorize a portal submission.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.submission import check_variants  # noqa: E402
from gemsdoe36.submission import validate_submission  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path = ROOT) -> dict[str, object]:
    errors: list[str] = []
    card_path = root / "evidence/gvsc36_run_card_20261026.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    sub = card["submission"]
    tif = root / "docs/downloads" / sub["zeros_filename"]
    archive = root / "docs/downloads" / sub["zip_archive_name"]
    template = root / "data/raw/sample_submission.tif"

    if card.get("verdict") != "negative" or card.get("safe_to_submit_live_slot"):
        errors.append("GVSC-36 must remain a negative, non-submit-authorized artifact")
    if card.get("gates", {}).get("G4c_competing_methods_3px_overlap_le_0p70") is not False:
        errors.append("Competing-method uniqueness failure must remain recorded")
    if card.get("gates", {}).get("G4d_literal_all_registry_3px_overlap_le_0p70") is not False:
        errors.append("Literal all-entry uniqueness failure must remain recorded")
    if card.get("experiment_budget", {}).get("experiments_executed") != 3:
        errors.append("Candidate experiment count must remain exactly three")
    budget = card.get("experiment_budget", {})
    if float(budget.get("elapsed_walltime_seconds", 0)) > float(budget.get("max_walltime_seconds", 7200)):
        errors.append("Recorded end-to-end walltime exceeds the registered 2-hour cap")
    if len(sub.get("note", "")) > 140 or len(sub.get("note", "")) != sub.get("note_length"):
        errors.append("Submission note length is invalid")
    for item in card.get("protocol_audit_flags", []):
        if item.get("severity") == "protocol_blocking" and "pre-placement screening order" in item.get("finding", "").lower():
            break
    else:
        errors.append("Required screening-order protocol caveat is missing")

    for path, expected in ((tif, sub["raster_sha256"]), (archive, sub["zip_sha256"])):
        if not path.is_file() or sha(path) != expected:
            errors.append(f"Missing or SHA-mismatched GVSC-36 artifact: {path.name}")
    if tif.is_file() and archive.is_file():
        with zipfile.ZipFile(archive) as zf:
            if zf.namelist() != [tif.name]:
                errors.append("ZIP must contain exactly the candidate TIFF")
            elif hashlib.sha256(zf.read(tif.name)).hexdigest() != sub["raster_sha256"]:
                errors.append("ZIP member bytes differ from the candidate TIFF")
    if tif.is_file() and template.is_file():
        a = validate_submission(tif, template, require_nonfinite_outside=False)
        b = check_variants(tif, template)
        if not a.passed or not b["format_valid"]:
            errors.append("Local template validator failure")
        if not b["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]:
            errors.append("Strict whole-array [0,1] validator failed")
        with rasterio.open(tif) as ds:
            arr = ds.read(1)
            if not np.isfinite(arr).all() or np.any((arr < 0) | (arr > 1)):
                errors.append("Raster is not whole-array finite and in [0,1]")
            if ds.count != 1 or ds.dtypes != ("float32",):
                errors.append("Raster must be single-band float32")
            if ds.crs.to_epsg() != 32611 or ds.shape != (3730, 3292):
                errors.append("Raster CRS/shape mismatch")

    mirror = root / "docs/downloads/gvsc36-run-card.json"
    if not mirror.is_file() or mirror.read_bytes() != card_path.read_bytes():
        errors.append("Public GVSC run-card mirror mismatch")
    for page in (root / "docs/index.html", root / "docs/executive-summary.html"):
        text = page.read_text(encoding="utf-8")
        for required in (tif.name, "DO NOT SUBMIT", "HOLDOUT-DTI", sub["raster_sha256"]):
            if required not in text:
                errors.append(f"{page.name} is missing GVSC-36 release text: {required}")
    return {
        "passed": not errors,
        "verdict": card["verdict"],
        "safe_to_download_for_research": card["safe_to_download_for_research"],
        "safe_to_submit": card["safe_to_submit_live_slot"],
        "tif_sha256": sub["raster_sha256"],
        "errors": errors,
    }


def main() -> int:
    report = verify()
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
