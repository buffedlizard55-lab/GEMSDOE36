#!/usr/bin/env python3
"""Parallel-run protocol leakage canary (rule 4).

Tests each prepared feature band ALONE on the spatially-blocked holdout:
for each band and each fold, compute the ROC AUC of band values against the
off-catalogue SGMC truth pixels inside that fold's evaluation domain
(background = footprint pixels outside the 300 m truth support).

AUC above 0.90 for a single feature means leakage until proven otherwise --
that feature is (near-)perfectly predicting the holdout truth by itself and
cannot be trusted.

Outputs a JSON canary report and prints a summary. Requires the prepared
bands from scripts/prepare_data.py (.cache/gems_work/bands) and the restored
competition data under data/raw.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

REPO_ROOT = Path(__file__).resolve().parents[1]

LEAKAGE_AUC = 0.90
BACKGROUND_CAP = 60_000  # background pixels sampled per fold (keep it fast)


def auc_from_ranks(pos_vals: np.ndarray, neg_vals: np.ndarray) -> float:
    """Mann-Whitney U AUC; robust to ties via average ranks."""
    if pos_vals.size == 0 or neg_vals.size == 0:
        return float("nan")
    all_vals = np.concatenate([pos_vals, neg_vals])
    ranks = rankdata(all_vals, method="average")
    n_pos = pos_vals.size
    n_neg = neg_vals.size
    rank_sum_pos = ranks[:n_pos].sum()
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return float(u / (n_pos * n_neg))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--bands-dir",
        type=Path,
        default=REPO_ROOT / ".cache" / "gems_work" / "bands",
        help="directory with per-band .npy arrays from prepare_data.py",
    )
    ap.add_argument(
        "--data-dir",
        type=Path,
        default=REPO_ROOT / "data" / "raw",
        help="restored competition data directory",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "evidence" / "leakage_canary.json",
        help="canary report output path",
    )
    args = ap.parse_args()

    bands_dir = Path(args.bands_dir)
    data_dir = Path(args.data_dir)
    footprint_path = bands_dir / "_footprint.npy"
    if not footprint_path.is_file():
        raise FileNotFoundError(
            f"prepared bands not found at {bands_dir}; run scripts/prepare_data.py first"
        )

    footprint = np.load(footprint_path)

    with rasterio.open(data_dir / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0

    # Off-catalogue SGMC truth proxy: SGMC faults >300 m from the provided
    # catalogue labels (same definition as scripts/run_holdout.py).
    with rasterio.open(data_dir / "labels.tif") as ds:
        lab = (ds.read(1) == 1) & footprint
    cat_dil = distance_transform_edt(~lab) <= 3.0
    sgmc_off = sgmc & footprint & ~cat_dil

    # Folds: reuse the live-mirror quadrant blocking for a spatial holdout.
    sys_path = REPO_ROOT / "src"
    import sys

    sys.path.insert(0, str(sys_path))
    from gemsdoe36.live_mirror import quadrant_ids

    quad = quadrant_ids(footprint)
    folds = [(f, quad == f) for f in range(4)]

    band_files = sorted(bands_dir.glob("[0-9][0-9]_*.npy"))
    if not band_files:
        raise FileNotFoundError(f"no band .npy files in {bands_dir}")

    results: list[dict] = []
    leak_found = False
    for bf in band_files:
        arr = np.load(bf)
        band_entry = {
            "band": bf.stem,
            "per_fold_auc": {},
            "max_auc": None,
            "mean_auc": None,
            "leakage_flag": False,
        }
        fold_aucs = []
        for fold_name, qmask in folds:
            domain = qmask
            truth = sgmc_off & domain
            n_pos = int(truth.sum())
            if n_pos == 0:
                band_entry["per_fold_auc"][fold_name] = None
                continue
            pos_vals = arr[truth]
            pos_vals = pos_vals[np.isfinite(pos_vals)]
            neg_cells = domain & footprint & (~sgmc_off) & (~cat_dil)
            neg_idx = np.argwhere(neg_cells)
            if neg_idx.size == 0:
                band_entry["per_fold_auc"][fold_name] = None
                continue
            if neg_idx.shape[0] > BACKGROUND_CAP:
                rng = np.random.default_rng(7)
                sel = rng.choice(neg_idx.shape[0], size=BACKGROUND_CAP, replace=False)
                neg_idx = neg_idx[sel]
            neg_vals = arr[neg_idx[:, 0], neg_idx[:, 1]]
            neg_vals = neg_vals[np.isfinite(neg_vals)]
            auc = auc_from_ranks(pos_vals.astype(np.float64), neg_vals.astype(np.float64))
            band_entry["per_fold_auc"][fold_name] = round(auc, 6)
            fold_aucs.append(auc)
        valid_aucs = [a for a in fold_aucs if not math.isnan(a)]
        if valid_aucs:
            band_entry["max_auc"] = round(max(valid_aucs), 6)
            band_entry["mean_auc"] = round(float(np.mean(valid_aucs)), 6)
            if max(valid_aucs) > LEAKAGE_AUC:
                band_entry["leakage_flag"] = True
                leak_found = True
        results.append(band_entry)

    report = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protocol": {
            "leakage_auc_threshold": LEAKAGE_AUC,
            "background_cap_per_fold": BACKGROUND_CAP,
            "holdout": "4-quadrant spatial blocks (live_mirror.quadrant_ids)",
            "truth": "sgmc_off_catalogue (>300 m from provided catalogue labels)",
        },
        "leakage_found": bool(leak_found),
        "bands": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"LEAKAGE CANARY: {'LEAKAGE DETECTED' if leak_found else 'NO LEAKAGE'}")
    for b in results:
        print(
            f"  {b['band']:18s} max_auc={b['max_auc']} mean_auc={b['mean_auc']} "
            f"flag={b['leakage_flag']}"
        )
    print(f"wrote {args.out}")
    return 1 if leak_found else 0


if __name__ == "__main__":
    raise SystemExit(main())
