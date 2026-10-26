#!/usr/bin/env python3
"""Shared CLI for the existing strict writer; never authorizes a weekly slot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.submission import check_variants, write_submission  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("prediction", type=Path, help="2D .npy or aligned single-band .tif")
    ap.add_argument("output", type=Path)
    ap.add_argument("--template", type=Path, default=ROOT / "data/bridge/sample_submission.tif")
    ap.add_argument("--outside", choices=("nan", "zero"), default="nan")
    args = ap.parse_args()
    if args.prediction.suffix == ".npy":
        a = np.load(args.prediction, allow_pickle=False)
    else:
        with rasterio.open(args.prediction) as s, rasterio.open(args.template) as t:
            if (s.shape, s.crs, s.transform, s.count) != (t.shape, t.crs, t.transform, 1):
                raise SystemExit("Prediction must match the template grid and be single-band")
            a = s.read(1)
    p = write_submission(a, args.template, args.output, outside=args.outside)
    checks = check_variants(p, args.template)
    print(json.dumps(checks, indent=2))
    if not checks["format_valid"]:
        raise SystemExit("Written file failed pinned-grid format validation")


if __name__ == "__main__":
    main()
