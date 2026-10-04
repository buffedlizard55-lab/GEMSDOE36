#!/usr/bin/env python3
"""Validate a candidate GeoTIFF against the organizer's local sample template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemsdoe36.submission import validate_submission


def main() -> int:
    default_template = Path(__file__).resolve().parents[1] / "data" / "raw" / "sample_submission.tif"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument(
        "--template",
        type=Path,
        default=default_template if default_template.is_file() else None,
        required=not default_template.is_file(),
        help="Path to sample_submission.tif template",
    )
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument(
        "--zeros-mode",
        action="store_true",
        help="permit 0.0 outside bounds (portal-safe mode)",
    )
    args = parser.parse_args()

    # Automatically enable zeros mode if the filename ends with -zeros.tif
    zeros_mode = args.zeros_mode or args.submission.name.endswith("-zeros.tif")
    require_nonfinite = not zeros_mode

    report = validate_submission(
        args.submission,
        args.template,
        require_nonfinite_outside=require_nonfinite,
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, allow_nan=True))
    else:
        status = "PASS" if report.passed else "FAIL"
        print(f"{status}: {report.path}")
        if not report.passed:
            for error in report.errors:
                print(f"  - {error}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
