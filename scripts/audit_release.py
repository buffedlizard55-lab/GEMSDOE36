#!/usr/bin/env python3
"""Audit all GeoTIFFs in docs/downloads/ against the pinned sample_submission template."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe36.paths import data_dir
from gemsdoe36.submission import sha256_file, validate_submission


def validate_archive_raster(path: Path, template: Path) -> dict:
    """Use strict outside-footprint handling regardless of historical filename."""
    return validate_submission(path, template, require_nonfinite_outside=True).to_dict()


def archive_review_row(path: Path, digest: str, report: dict, atvr_card: dict) -> dict:
    """A historical format audit never grants a slot, even for a forged card."""
    is_atvr36 = path.name == "gemsdoe36-atvr36-20261026.tif"
    return {
        "sha256": digest,
        "validator": report,
        "submit_ready": False,
        "historical_card_verdict": atvr_card.get("verdict") if is_atvr36 else None,
        "reason": (
            "Historical research artifact only: format checks do not establish literal "
            "registry uniqueness or a separate slot-selection decision; DO NOT SUBMIT."
        ),
    }


def main() -> int:
    template = data_dir() / "sample_submission.tif"
    if not template.exists():
        template = ROOT / "data" / "sample_submission.tif"
    if not template.exists():
        raise SystemExit("Missing pinned mirror template; restore sample_submission first")
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text(encoding="utf-8"))
    entry = next(x for x in manifest["files"] if x["id"] == "sample_submission")
    if sha256_file(template) != entry["sha256"]:
        raise SystemExit("Template hash mismatch")

    atvr_card = json.loads(
        (ROOT / "evidence/atvr36_run_card_20261026.json").read_text(encoding="utf-8")
    )

    rows = []
    for path in sorted((ROOT / "docs/downloads").glob("*.tif")):
        # Historical suffixes are metadata, not format authorization.
        report = validate_archive_raster(path, template)
        report["path"] = str(path.relative_to(ROOT))
        rows.append(archive_review_row(path, sha256_file(path), report, atvr_card))

    output = {
        "template_sha256": entry["sha256"],
        "audited_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "Historical format audit only; no literal registry or selector authorization",
        "artifacts": rows,
        "promoted_count": sum(1 for r in rows if r["submit_ready"]),
    }
    # Do not overwrite the dated historical audit with new results.
    dest = ROOT / "evidence" / "downloads_validation_latest.json"
    dest.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(
        f"Audited {len(rows)} files ({output['promoted_count']} promoted). "
        f"{dest.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
