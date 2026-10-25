#!/usr/bin/env python3
"""Re-read legacy downloads; format checks never imply scientific promotion."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe36.submission import sha256_file, validate_submission


def main():
    template = ROOT / "data/sample_submission.tif"
    if not template.exists():
        raise SystemExit("Missing pinned mirror template; restore sample_submission first")
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text())
    entry = next(x for x in manifest["files"] if x["id"] == "sample_submission")
    if sha256_file(template) != entry["sha256"]:
        raise SystemExit("Template hash mismatch")
    rows = []
    for path in sorted((ROOT / "docs/downloads").glob("*.tif")):
        report = validate_submission(
            path, template, require_nonfinite_outside=not path.name.endswith("-zeros.tif")
        ).to_dict()
        report["path"] = str(path.relative_to(ROOT))
        rows.append({"sha256": sha256_file(path), "validator": report,
                     "submit_ready": False,
                     "reason": "Legacy artifact: no valid hide-and-recover promotion receipt"})
    output = {"template_sha256": entry["sha256"],
              "provenance": "Pinned owner mirror; not organizer authenticated",
              "artifacts": rows, "submit_ready": False}
    dest = ROOT / "evidence/review-20261025/legacy-validation.json"
    dest.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(f"Audited {len(rows)} legacy files. No artifact promoted. {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
