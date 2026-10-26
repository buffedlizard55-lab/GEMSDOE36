#!/usr/bin/env python3
"""Parallel-run protocol lane check (rule 1).

Compares a candidate submission raster against every raster in the project
registry (prior candidate TIFs under docs/downloads/ and scored study rasters
under data/raw/scored/ that are kept as learning references only).

Duplicate-lane triggers (either one => log DUPLICATE and stop):
  * Spearman rank correlation of the two rasters over their common finite
    footprint exceeds 0.90, OR
  * more than 70% of the candidate's dots fall within 3 px (300 m) of one
    registry raster's dots.

Same-content rebuilds (identical SHA-256) are reported but NOT flagged as a
lane drift: regenerating your own submission is not copying another lane.

Outputs a machine-readable JSON lane log to --out and prints a summary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = REPO_ROOT / "docs" / "downloads"
SCORED = REPO_ROOT / "data" / "raw" / "scored"

DOT_THRESH = 0.5
CORR_DUPLICATE = 0.90
DOT_OVERLAP_DUPLICATE = 0.70
DOT_NEAR_PX = 3  # 300 m on the 100 m grid


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_raster(path: Path):
    with rasterio.open(path) as ds:
        arr = ds.read(1, masked=False)
        profile = {
            "crs": ds.crs.to_string() if ds.crs else None,
            "transform": ds.transform,
            "shape": (ds.height, ds.width),
        }
    return arr, profile


def raster_pair_overlap(a: np.ndarray, b: np.ndarray):
    """Common finite cells of two rasters (must share grid)."""
    return np.isfinite(a) & np.isfinite(b)


def spearman_overlap(a: np.ndarray, b: np.ndarray) -> float | None:
    m = raster_pair_overlap(a, b)
    if int(m.sum()) < 10:
        return None
    x = a[m].astype(np.float64).ravel()
    y = b[m].astype(np.float64).ravel()
    res = spearmanr(x, y)
    return float(res.statistic)


def dots(arr: np.ndarray) -> np.ndarray:
    return np.argwhere(np.isfinite(arr) & (arr > DOT_THRESH))


def fraction_dots_near(cand_arr: np.ndarray, reg_arr: np.ndarray) -> float:
    """Fraction of candidate dots within DOT_NEAR_PX of any registry dot."""
    cand = dots(cand_arr)
    reg = dots(reg_arr)
    if len(cand) == 0 or len(reg) == 0:
        return 0.0
    reg_mask = np.zeros(reg_arr.shape, dtype=bool)
    reg_mask[reg[:, 0], reg[:, 1]] = True
    dist_to_reg = distance_transform_edt(~reg_mask)
    if len(cand) == 0:
        return 0.0
    near = dist_to_reg[cand[:, 0], cand[:, 1]] <= DOT_NEAR_PX
    return float(near.mean())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path, help="candidate GeoTIFF to lane-check")
    ap.add_argument(
        "--registry",
        type=Path,
        default=DOWNLOADS,
        help="directory holding prior candidate TIFs (registry rasters)",
    )
    ap.add_argument(
        "--include-scored",
        action="store_true",
        help="also compare against scored study rasters under data/raw/scored",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "evidence" / "lane_check.json",
        help="lane log output path",
    )
    args = ap.parse_args()

    cand_arr, cand_prof = read_raster(args.candidate)
    cand_sha = sha256_file(args.candidate)
    cand_dots_count = int(dots(cand_arr).shape[0])

    registry_paths: list[Path] = []
    if args.registry.is_dir():
        registry_paths.extend(
            sorted(
                p
                for p in args.registry.glob("*.tif")
                if p.name != "GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif"
            )
        )
    if args.include_scored and SCORED.is_dir():
        registry_paths.extend(sorted(SCORED.glob("*.tif")))

    checks: list[dict] = []
    duplicate = False
    for reg_path in registry_paths:
        reg_arr, reg_prof = read_raster(reg_path)
        reg_sha = sha256_file(reg_path)
        entry: dict = {
            "registry_raster": str(reg_path),
            "sha256": reg_sha,
            "same_content_as_candidate": reg_sha == cand_sha,
        }
        if reg_sha == cand_sha:
            entry["spearman_rho"] = None
            entry["common_finite_px"] = 0
            entry["dots_within_3px_fraction"] = None
            entry["verdict"] = "same-content rebuild (own lane; not a drift)"
            checks.append(entry)
            continue

        same_grid = (
            cand_prof["shape"] == reg_prof["shape"]
            and cand_prof["crs"] == reg_prof["crs"]
            and cand_prof["transform"] == reg_prof["transform"]
        )
        entry["same_grid"] = bool(same_grid)

        rho = None
        overlap_px = 0
        if same_grid:
            rho = spearman_overlap(cand_arr, reg_arr)
            m = raster_pair_overlap(cand_arr, reg_arr)
            overlap_px = int(m.sum())
            entry["spearman_rho"] = None if rho is None else round(rho, 6)
            entry["common_finite_px"] = overlap_px
            # A rho of magnitude 1.0 over the shared footprint means the two
            # rasters carry the same prediction (e.g. the -zeros/-nan companion
            # pair of one build). That is a format variant of the *same*
            # submission, not a drift into another lane.
            if rho is not None and abs(rho) == 1.0:
                entry["companion_same_prediction"] = True
        else:
            entry["spearman_rho"] = None
            entry["common_finite_px"] = 0
            entry["companion_same_prediction"] = False

        near = (
            fraction_dots_near(cand_arr, reg_arr) if same_grid else None
        )  # dot proximity needs a shared grid
        entry["dots_within_3px_fraction"] = (
            None if near is None else round(near, 6)
        )
        entry["candidate_dots"] = cand_dots_count
        entry["registry_dots"] = int(dots(reg_arr).shape[0])

        triggered = []
        if rho is not None and rho > CORR_DUPLICATE:
            triggered.append(f"spearman rho {rho:.3f} > {CORR_DUPLICATE}")
        if near is not None and near > DOT_OVERLAP_DUPLICATE:
            triggered.append(f"{near*100:.1f}% of dots within {DOT_NEAR_PX} px")
        entry["duplicate_trigger"] = triggered
        if entry.get("companion_same_prediction"):
            entry["verdict"] = (
                "companion variant (identical footprint prediction); not a lane drift"
            )
            triggered = []
        else:
            entry["verdict"] = "DUPLICATE-LANE" if triggered else "distinct lane"
            if triggered:
                duplicate = True
        checks.append(entry)

    log = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidate": str(args.candidate),
        "candidate_sha256": cand_sha,
        "candidate_dots": cand_dots_count,
        "protocol": {
            "corr_duplicate_threshold": CORR_DUPLICATE,
            "dot_overlap_duplicate_threshold": DOT_OVERLAP_DUPLICATE,
            "dot_near_px": DOT_NEAR_PX,
        },
        "duplicate_found": bool(duplicate),
        "checks": checks,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(log, indent=2) + "\n")
    print(f"LANE CHECK: {'DUPLICATE FOUND' if duplicate else 'ALL DISTINCT'}")
    for c in checks:
        print(
            f"  {Path(c['registry_raster']).name:55s} "
            f"same_content={c['same_content_as_candidate']} "
            f"rho={c['spearman_rho']} near3px={c['dots_within_3px_fraction']} "
            f"=> {c['verdict']}"
        )
    print(f"wrote {args.out}")
    return 1 if duplicate else 0


if __name__ == "__main__":
    raise SystemExit(main())
