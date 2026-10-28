#!/usr/bin/env python3
"""Read-only content checks on the pinned nine-site rasters (28 Oct 2026 session).

Verifies three claims from the owner/executive pages against the pinned bytes:
  1. GEMSDOE32 B2 is a strict subset of the 44,090-dot GEMSDOE25 raster, with exactly
     6,436 dots removed, none added, and every removed dot 1-2 px from the catalogue.
  2. Which of the nine pinned rasters have identical content (in-footprint values and
     positive pixels), ignoring the outside-footprint encoding.
  3. Whether GEMSDOE25 and GEMSDOE30 differ only in outside-footprint encoding.

Requires restored inputs: data/raw/sample_submission.tif, data/raw/labels.tif and the
focus rasters in data/registry/scored/ (copied from .cache/focus_registry by
scripts/fetch_pinned_focus_rasters.py). Writes evidence/focus9_content_checks_20261028.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "data" / "registry" / "scored"
TEMPLATE = ROOT / "data" / "raw" / "sample_submission.tif"
LABELS = ROOT / "data" / "raw" / "labels.tif"
OUT = ROOT / "evidence" / "focus9_content_checks_20261028.json"

B2 = "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
D28_SITE = "GEMSDOE25__gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
D30 = "GEMSDOE30__gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as ds:
        return ds.read(1), {
            "transform": tuple(ds.transform)[:6],
            "epsg": ds.crs.to_epsg() if ds.crs else None,
            "shape": [ds.height, ds.width],
            "nodata": None if ds.nodata is None else str(ds.nodata),
        }


def main() -> int:
    required = [TEMPLATE, LABELS, REG / B2, REG / D28_SITE, REG / D30]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    if missing:
        print("Missing inputs (restore first):", *missing, sep="\n  ")
        return 2

    footprint_arr, grid = read(TEMPLATE)
    footprint = np.isfinite(footprint_arr)
    labels, lgrid = read(LABELS)
    catalogue = np.isfinite(labels) & (labels > 0)
    dist_to_catalogue = distance_transform_edt(~catalogue)

    # 1. B2 lineage against the 44,090-dot GEMSDOE25 raster.
    b2, b2grid = read(REG / B2)
    d28, d28grid = read(REG / D28_SITE)
    if b2grid["epsg"] != 32611 or d28grid["epsg"] != 32611 or b2grid["shape"] != grid["shape"]:
        raise SystemExit("Grid mismatch in B2 / D2.8 inputs")
    b2_pos = np.isfinite(b2) & (b2 > 0)
    d28_pos = np.isfinite(d28) & (d28 > 0)
    removed = d28_pos & ~b2_pos
    added = b2_pos & ~d28_pos
    lineage = {
        "d28_dots": int(d28_pos.sum()),
        "b2_dots": int(b2_pos.sum()),
        "removed_from_d28": int(removed.sum()),
        "added_to_d28": int(added.sum()),
        "removed_distance_to_catalogue_px_min": float(dist_to_catalogue[removed].min()) if removed.any() else None,
        "removed_distance_to_catalogue_px_max": float(dist_to_catalogue[removed].max()) if removed.any() else None,
        "kept_b2_dots_within_2px_of_catalogue": int((b2_pos & (dist_to_catalogue <= 2)).sum()),
    }
    lineage["verdict"] = bool(
        lineage["added_to_d28"] == 0
        and lineage["d28_dots"] - lineage["removed_from_d28"] == lineage["b2_dots"]
        and lineage["kept_b2_dots_within_2px_of_catalogue"] == 0
        and (lineage["removed_distance_to_catalogue_px_max"] or 0) <= 2.0
    )

    # 2. Content duplicates among all pinned focus rasters present on disk.
    files = sorted(REG.glob("GEMSDOE*__*.tif"))
    records = []
    for path in files:
        arr, meta = read(path)
        inside = np.where(footprint, np.nan_to_num(arr, nan=0.0), 0.0)
        pos = footprint & np.isfinite(arr) & (arr > 0)
        outside = arr[~footprint]
        if np.all(np.isnan(outside)):
            encoding = "nan"
        elif np.all(outside == 0):
            encoding = "zeros"
        else:
            encoding = "other"
        records.append({"name": path.name, "sha256": sha256(path), "inside": inside, "pos": pos,
                        "encoding": encoding, "dots": int(pos.sum())})

    groups: list[list[int]] = []
    assigned: set[int] = set()
    for i, rec in enumerate(records):
        if i in assigned:
            continue
        group = [i]
        assigned.add(i)
        for j in range(i + 1, len(records)):
            if j not in assigned and np.array_equal(rec["pos"], records[j]["pos"]) \
                    and np.array_equal(rec["inside"], records[j]["inside"]):
                group.append(j)
                assigned.add(j)
        groups.append(group)
    duplicates = [
        [{"file": records[k]["name"].split("__", 1)[0], "sha256_12": records[k]["sha256"][:12],
          "outside_encoding": records[k]["encoding"], "dots": records[k]["dots"]} for k in g]
        for g in groups if len(g) > 1
    ]

    # 3. GEMSDOE25 vs GEMSDOE30 (same dots?) - explicit pair for the record.
    d30, _ = read(REG / D30)
    d30_pos = np.isfinite(d30) & (d30 > 0)
    pair = {
        "gemsdoe25_sha256": sha256(REG / D28_SITE),
        "gemsdoe30_sha256": sha256(REG / D30),
        "bytes_identical": (REG / D28_SITE).read_bytes() == (REG / D30).read_bytes(),
        "positive_pixel_sets_identical": bool(np.array_equal(d28_pos, d30_pos)),
        "inside_footprint_values_identical": bool(
            np.array_equal(np.where(footprint, d28, 0.0), np.where(footprint, d30, 0.0))
        ),
    }

    result = {
        "schema": "gemsdoe36.focus9-content-checks.v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs_note": "Hash-pinned owner-mirror or GitHub-commit bytes; not organizer-authenticated.",
        "b2_lineage": lineage,
        "nine_site_distinct_contents": len(groups),
        "nine_site_content_duplicate_groups": duplicates,
        "gemsdoe25_vs_gemsdoe30": pair,
    }
    OUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if lineage["verdict"] else 1


if __name__ == "__main__":
    sys.exit(main())
