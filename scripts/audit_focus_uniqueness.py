#!/usr/bin/env python3
"""Compute pairwise three-pixel overlap and binary-surface Spearman for nine historical TIFFs.

Comparison only: these rasters never enter model features or candidate construction.
Requires the ignored competition template and pinned scored raster cache to be restored.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(root: Path = ROOT) -> dict[str, Any]:
    ledger = json.loads((root / "evidence/focus_sites_9repo_summary_20261026.json").read_text())
    registry = json.loads((root / "registry/scored_registry.json").read_text())["entries"]
    with rasterio.open(root / "data/raw/sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
        grid = (ds.shape, ds.crs, ds.transform)

    masks: dict[str, np.ndarray] = {}
    hashes: dict[str, str] = {}
    for site_row in ledger["focus_sites"]:
        site = site_row["site"]
        hist = site_row["highest_historical_submission"]
        candidates = [
            entry for entry in registry
            if entry["repo"] == site and entry["sha256"] == hist["sha256_full"]
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one pinned raster for {site}; found {len(candidates)}")
        entry = candidates[0]
        path = root / entry["local"]
        digest = sha256_file(path)
        if digest != hist["sha256_full"]:
            raise RuntimeError(f"Pinned raster SHA-256 mismatch: {path}")
        with rasterio.open(path) as ds:
            if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
                raise RuntimeError(f"Raster geometry mismatch: {path}")
            arr = ds.read(1)
        values = np.unique(arr[footprint])
        if not np.isfinite(arr[footprint]).all() or not np.isin(values, [0.0, 1.0]).all():
            raise RuntimeError(f"Expected finite binary predictions inside footprint: {path}")
        masks[site] = footprint & (arr == 1.0)
        hashes[site] = digest

    distance_to_positive = {
        site: distance_transform_edt(~mask) for site, mask in masks.items()
    }
    pair_rows = []
    site_summary = {}
    for candidate_site, candidate in masks.items():
        overlaps = []
        rhos = []
        for reference_site, reference in masks.items():
            if candidate_site == reference_site:
                continue
            overlap = float(
                np.count_nonzero(candidate & (distance_to_positive[reference_site] <= 3.0))
                / np.count_nonzero(candidate)
            )
            rho = float(
                np.corrcoef(
                    candidate[footprint].astype(np.float64),
                    reference[footprint].astype(np.float64),
                )[0, 1]
            )
            overlaps.append(overlap)
            rhos.append(rho)
            pair_rows.append({
                "candidate": candidate_site,
                "reference": reference_site,
                "candidate_dots": int(candidate.sum()),
                "reference_dots": int(reference.sum()),
                "candidate_dots_within_3px_of_reference_fraction": overlap,
                "binary_surface_spearman_rho": rho,
                "fails_overlap_ceiling_gt_0p70": overlap > 0.70,
                "fails_abs_spearman_ceiling_gt_0p90": abs(rho) > 0.90,
            })
        site_summary[candidate_site] = {
            "sha256": hashes[candidate_site],
            "dots": int(candidate.sum()),
            "min_overlap_vs_other_eight": min(overlaps),
            "max_overlap_vs_other_eight": max(overlaps),
            "n_other_sites_overlap_gt_0p70": sum(x > 0.70 for x in overlaps),
            "max_abs_binary_surface_spearman": max(abs(x) for x in rhos),
            "n_other_sites_abs_spearman_gt_0p90": sum(abs(x) > 0.90 for x in rhos),
            "unique_under_parallel_protocol_vs_all_eight": all(x <= 0.70 for x in overlaps)
            and all(abs(x) <= 0.90 for x in rhos),
        }

    return {
        "schema": "gemsdoe36.focus9_pairwise_uniqueness.v1",
        "date_utc": "2026-10-26",
        "method": {
            "footprint_pixels": int(footprint.sum()),
            "mask_values": [0, 1],
            "spearman_note": "For binary 0/1 surfaces, Spearman rank correlation equals Pearson correlation of the binary masks.",
            "dot_overlap": "Directed fraction of candidate positive pixels at Euclidean distance <= 3 pixels from the reference positives.",
            "protocol_limits": {"abs_spearman_max_exclusive": 0.90, "dot_overlap_max_exclusive": 0.70},
        },
        "all_nine_sites_pass_unique_vs_each_other": all(
            row["unique_under_parallel_protocol_vs_all_eight"] for row in site_summary.values()
        ),
        "site_summary": site_summary,
        "directed_pairwise_checks": pair_rows,
        "limitations": [
            "Historical scores remain OWNER-REPORTED; this measures only raster uniqueness.",
            "This pairwise nine-site check does not replace comparison against the expanded registry.",
        ],
    }


def main() -> int:
    result = audit()
    dest = ROOT / "evidence/focus_sites_pairwise_uniqueness_20261026.json"
    dest.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        f"Audited {len(result['site_summary'])} sites / "
        f"{len(result['directed_pairwise_checks'])} directed pairs; "
        f"all-nine-unique={result['all_nine_sites_pass_unique_vs_each_other']}; wrote {dest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
