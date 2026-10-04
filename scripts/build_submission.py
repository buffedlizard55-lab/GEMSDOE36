#!/usr/bin/env python3
"""Write a competition-grid GeoTIFF from an already-validated 2-D NumPy score array.

This script intentionally does not download competition data or fetch leaderboard data.
The sample template must be obtained through an authorized DrivenData session.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from gemsdoe36.submission import unique_submission_name, write_submission


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scores", type=Path, help="2-D .npy array of predictions")
    parser.add_argument(
        "--template", type=Path, required=True, help="official sample_submission.tif"
    )
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/submissions"))
    parser.add_argument("--note", type=Path, help="plain-text submission narrative note")
    args = parser.parse_args()

    scores = np.load(args.scores, allow_pickle=False)
    note = args.note.read_text(encoding="utf-8").strip() if args.note else ""
    args.out_dir.mkdir(parents=True, exist_ok=True)
    output = args.out_dir / unique_submission_name(scores)
    manifest = output.with_suffix(".json")
    report = write_submission(scores, args.template, output, note=note, manifest_path=manifest)
    print(f"PASS: {output}")
    print(f"Manifest: {manifest}")
    print(f"Range: [{report.minimum}, {report.maximum}]")
    print("Local format validation is not platform acceptance or a performance result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
