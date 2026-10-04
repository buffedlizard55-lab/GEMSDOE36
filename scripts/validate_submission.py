#!/usr/bin/env python3
"""Validate a candidate GeoTIFF against the organizer's local sample template."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gemsdoe36.submission import validate_submission


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args()

    report = validate_submission(args.submission, args.template)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, allow_nan=True))
    else:
        status = "PASS" if report.passed else "FAIL"
        print(f"{status}: {report.path}")
        print(
            f"grid={report.width}x{report.height} bands={report.count} dtype={report.dtype} "
            f"crs={report.crs} resolution={report.resolution_m} range="
            f"[{report.minimum}, {report.maximum}] outside_finite="
            f"{report.finite_outside_bounds} outside_infinite={report.infinite_outside_bounds}"
        )
        for error in report.errors:
            print(f"- {error}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
