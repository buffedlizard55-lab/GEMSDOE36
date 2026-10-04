#!/usr/bin/env python3
"""Write a competition-grid GeoTIFF from this project's selected 2-D NumPy score array.

This formatter does not train a model, establish spatial-holdout superiority, or fetch
competition data. Run it only after the release gate passes. The official sample template
must be obtained through an authorized DrivenData session.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from gemsdoe36.submission import unique_submission_name, write_submission


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scores", type=Path, help="2-D .npy array of this project's predictions")
    parser.add_argument(
        "--template", type=Path, required=True, help="official sample_submission.tif"
    )
    parser.add_argument(
        "--submission-name",
        required=True,
        help="unique, human-readable name to use in the competition form",
    )
    parser.add_argument(
        "--note",
        required=True,
        help="short, truthful method and spatial-holdout note for the submission form",
    )
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/submissions"))
    args = parser.parse_args()

    if not args.submission_name.strip():
        parser.error("--submission-name must not be empty")
    if not args.note.strip():
        parser.error("--note must not be empty")

    scores = np.load(args.scores, allow_pickle=False)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    output = args.out_dir / unique_submission_name(scores, prefix=args.submission_name)
    manifest = output.with_suffix(".json")
    report = write_submission(
        scores,
        args.template,
        output,
        note=args.note.strip(),
        submission_name=args.submission_name.strip(),
        manifest_path=manifest,
    )
    print(f"PASS: {output}")
    print(f"Competition submission name: {args.submission_name.strip()}")
    print(f"Submission note: {args.note.strip()}")
    print(f"Manifest: {manifest}")
    print(f"Range: [{report.minimum}, {report.maximum}]")
    print("Local format validation is not platform acceptance or a performance result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
