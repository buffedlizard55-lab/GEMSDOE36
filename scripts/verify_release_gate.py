#!/usr/bin/env python3
"""Historical H36 evidence audit; not an authorization to upload a submission.

Fails if the pinned raster inputs needed for fresh validation are unavailable.
A selector and current full-registry audit are separate prerequisites.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.submission import check_variants as gems_check_variants
from gemsdoe36.submission import sha256_file, validate_submission


def verify_all(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []

    ev_rc = root / "evidence" / "h36_ctrb_run_card_20261025.json"
    dl_rc = root / "docs" / "downloads" / "run_card.json"
    if not ev_rc.is_file() or not dl_rc.is_file():
        raise FileNotFoundError("Missing Run Card JSON in evidence/ or docs/downloads/")
    if ev_rc.read_bytes() != dl_rc.read_bytes():
        errors.append("evidence Run Card and docs/downloads/run_card.json differ")

    rc = json.loads(ev_rc.read_text())

    # 1. Experiment budget & note length
    if rc["experiment_budget"]["experiments_executed"] > 3:
        errors.append("Exceeded 3-experiment Parallel-Run Protocol budget")
    if rc["experiment_budget"]["elapsed_walltime_seconds"] > 7200:
        errors.append("Exceeded 2-hour Parallel-Run Protocol walltime budget")
    note = rc["submission"]["note"]
    if len(note) > 140:
        errors.append(f"Submission note exceeds 140 chars ({len(note)})")

    # 2. Canary gate
    if not rc["leakage_canary"]["passed"] or rc["leakage_canary"]["max_symmetric_auc"] > 0.90:
        errors.append("Single-feature leakage canary failed (> 0.90 AUC)")

    # 3. Uniqueness checks (both 107 owner-scored rasters and 198 expanded registry)
    surf_u = rc["registry_uniqueness"]["surface_before_placement"]
    dots_u = rc["registry_uniqueness"]["final_dots"]
    if not surf_u["passed"] or float(surf_u["max_abs_rank_correlation"]) > 0.90:
        errors.append("Surface pre-placement Spearman rank correlation exceeded 0.90")
    if (
        not dots_u["competing_method_passed"]
        or float(dots_u["max_abs_rank_correlation"]) > 0.90
        or float(dots_u["max_competing_dot_overlap"]) > 0.70
    ):
        errors.append("107-raster scored registry novelty check unexpectedly failed")

    gates = rc.get("gates", {})
    all_gates_pass = bool(gates) and all(bool(v) for v in gates.values())
    expected_verdict = "promote" if all_gates_pass else "negative"
    if rc["verdict"] != expected_verdict:
        errors.append(
            f"Fail-closed verdict mismatch: gates={gates} implies '{expected_verdict}', got '{rc['verdict']}'"
        )
    if rc["validator_output"]["safe_to_download_and_submit"] != (expected_verdict == "promote"):
        errors.append("validator_output.safe_to_download_and_submit out of sync with gate verdict")

    # 4. GeoTIFF & ZIP integrity + Dual Validators
    dl_dir = root / "docs" / "downloads"
    zeros_fname = rc["submission"].get("zeros_filename") or rc["submission"]["submission_name"]
    zeros_p = dl_dir / zeros_fname
    nan_p = dl_dir / rc["submission"]["companion_nan_name"]
    zip_p = dl_dir / rc["submission"]["zip_archive_name"]

    for p, expected_sha in (
        (zeros_p, rc["submission"]["raster_sha256"]),
        (nan_p, rc["submission"]["companion_nan_sha256"]),
        (zip_p, rc["submission"]["zip_sha256"]),
    ):
        if not p.is_file():
            errors.append(f"Missing submission artifact: {p}")
        elif sha256_file(p) != expected_sha:
            errors.append(f"SHA-256 mismatch on {p.name}")

    with zipfile.ZipFile(zip_p) as zf:
        if zf.namelist() != [zeros_p.name]:
            errors.append(f"ZIP archive members {zf.namelist()} != [{zeros_p.name}]")

    tmpl_p = root / "data" / "raw" / "sample_submission.tif"
    lbl_p = root / "data" / "raw" / "labels.tif"
    raster_validation_performed = False
    if not tmpl_p.is_file() or not lbl_p.is_file():
        errors.append("Fresh raster validation unavailable: missing sample_submission.tif or labels.tif")
    else:
        manifest = json.loads((root / "registry" / "data_manifest.json").read_text())
        pins = {item["id"]: item["sha256"] for item in manifest["files"]}
        mismatched = [name for name, path in (("sample_submission", tmpl_p), ("labels", lbl_p))
                      if pins.get(name) != sha256_file(path)]
        if mismatched:
            errors.append("Raster input hash mismatch: " + ", ".join(mismatched))
        else:
            raster_validation_performed = True
    if raster_validation_performed:
        rep_z = validate_submission(zeros_p, tmpl_p, require_nonfinite_outside=False)
        rep_n = validate_submission(nan_p, tmpl_p, require_nonfinite_outside=True)
        chk_z = gems_check_variants(zeros_p, tmpl_p)
        chk_n = gems_check_variants(nan_p, tmpl_p)
        if not (rep_z.passed and rep_n.passed):
            errors.append("Repo submission validator failed")
        if not (
            chk_z["format_valid"]
            and chk_z["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]
            and chk_n["official_format_compliant"]
        ):
            errors.append("Shared gems.submission.check_variants failed")

        with rasterio.open(tmpl_p) as t, rasterio.open(lbl_p) as l_ds, rasterio.open(zeros_p) as s:
            fp = np.isfinite(t.read(1))
            cat = fp & np.isfinite(l_ds.read(1)) & (l_ds.read(1) > 0.5)
            arr = s.read(1)
            if not np.isfinite(arr).all() or float(arr.min()) < 0.0 or float(arr.max()) > 1.0:
                errors.append("Primary -zeros.tif failed full-grid finite [0, 1] check")
            d_cat = distance_transform_edt(~cat)
            if int(((arr > 0.5) & (d_cat <= 2.0)).sum()) != 0:
                errors.append("Primary -zeros.tif has dots within 200 m of catalogue")

    # 5. HTML & Markdown link, banner visibility, and anti-projection checks
    banned_phrases = ("projected live score", "live projection:", "projected 0.2798")
    for doc_rel in ("README.md", "docs/index.html", "docs/executive-summary.html"):
        doc_p = root / doc_rel
        if not doc_p.is_file():
            errors.append(f"Missing required doc: {doc_rel}")
            continue
        txt = doc_p.read_text(encoding="utf-8")
        low = txt.lower()
        for bp in banned_phrases:
            if bp in low:
                errors.append(f"Banned unverified score projection phrase '{bp}' in {doc_rel}")
        if doc_p.suffix == ".html":
            if expected_verdict == "negative" and "DO NOT SUBMIT" not in txt:
                errors.append(f"Fail-closed HTML missing 'DO NOT SUBMIT' in {doc_rel}")
            if "DOWNLOAD: YES" not in txt:
                errors.append(f"HTML missing explicit 'DOWNLOAD: YES' status in {doc_rel}")
            for m in re.finditer(r'(?:href|src)="([^"]+)"', txt):
                ref = m.group(1)
                if ref.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                clean_ref = ref.split("#", 1)[0].split("?", 1)[0]
                if not clean_ref:
                    continue
                target = (doc_p.parent / clean_ref).resolve()
                if not target.exists():
                    errors.append(f"Broken relative link '{ref}' in {doc_rel}")

    return {
        "passed": len(errors) == 0,
        "verdict": rc["verdict"],
        "ok_to_download_research_tif": rc["validator_output"]["ok_to_download_research_tif"],
        "safe_to_download_and_submit": False,
        "raster_validation_performed": raster_validation_performed,
        "scope": "Historical H36 audit only; never a selector or current registry authorization",
        "submission_name": rc["submission"]["submission_name"],
        "zeros_filename": zeros_fname,
        "raster_sha256": rc["submission"]["raster_sha256"],
        "errors": errors,
    }


def main() -> None:
    res = verify_all(ROOT)
    print(json.dumps(res, indent=2))
    if not res["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
