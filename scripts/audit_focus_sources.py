#!/usr/bin/env python3
"""Recheck all nine historical TIFF bytes, names, dots and B2 lineage.

Only verified file identity and geometry are proven; historical leaderboard
numbers remain owner-reported unless an organizer submission receipt is archived.
All reference rasters are comparison-only and never used by the detector.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.validator import sha256_file  # noqa: E402


def main() -> int:
    ledger = json.loads((ROOT / "evidence/focus_sites_9repo_summary_20261026.json").read_text())
    scored = json.loads((ROOT / "registry/scored_registry.json").read_text())["entries"]
    with rasterio.open(ROOT / "data/raw/sample_submission.tif") as template, rasterio.open(
        ROOT / "data/raw/existing_faults.tif"
    ) as faults:
        foot = np.isfinite(template.read(1))
        cat = faults.read(1) == 1
        grid = (template.shape, template.crs, template.transform)
    if len(ledger["focus_sites"]) != 9 or foot.sum() != 5_167_373 or cat.sum() != 60_988:
        raise RuntimeError("Site count/footprint mismatch")

    masks: dict[str, np.ndarray] = {}
    rows = []
    for site in ledger["focus_sites"]:
        name = site["site"]
        row = site["highest_historical_submission"]
        matching = [r for r in scored if r["repo"] == name and r["sha256"] == row["sha256_full"]]
        if len(matching) != 1 or "ORGANIZER-CONFIRMED" in row["score_label"]:
            raise RuntimeError(f"No unique raster or unsupported score provenance for {name}")
        source = matching[0]
        path = ROOT / source["local"]
        digest = sha256_file(path)
        if digest != row["sha256_full"] or source["path"].split("/")[-1] != row["name"]:
            raise RuntimeError(f"Hash/name mismatch for {name}")
        with rasterio.open(path) as ds:
            if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
                raise RuntimeError(f"Grid mismatch: {path}")
            arr = ds.read(1)
        if not np.isfinite(arr[foot]).all() or np.any((arr[foot] < 0) | (arr[foot] > 1)):
            raise RuntimeError(f"Invalid prediction inside footprint: {path}")
        masks[name] = foot & (arr > 0)
        dots = int(masks[name].sum())
        if dots != row["dots"]:
            raise RuntimeError(f"Dot count mismatch for {name}: {dots} != {row['dots']}")
        rows.append({
            "site": name, "name": row["name"], "sha256": digest,
            "dots_in_footprint": dots, "reported_score_not_organizer_authenticated": row["score"],
            "score_provenance": row["score_label"], "pinned_source_url": row["pinned_raster_source_url"],
        })

    # Compare the exact scored rasters used in the inherited forensic claims.
    def matched(site: str, term: str) -> np.ndarray:
        entries = [e for e in scored if e["repo"] == site and term in e["path"]]
        if len(entries) != 1:
            raise RuntimeError(f"Ambiguous matched raster {site}/{term}")
        entry = entries[0]
        p = ROOT / entry["local"]
        if sha256_file(p) != entry["sha256"]:
            raise RuntimeError(f"Cached reference hash mismatch: {p}")
        with rasterio.open(p) as f:
            arr = f.read(1)
            return foot & np.isfinite(arr) & (arr > 0)

    d28 = masks["GEMSDOE25"]
    d30 = masks["GEMSDOE30"]
    solo = masks["GEMSDOE31"]
    solo28 = matched("GEMSDOE28", "h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif")
    b2 = masks["GEMSDOE32"]
    old36 = masks["GEMSDOE36"]
    dist = distance_transform_edt(~cat)
    claims = {
        "d28_25_vs_30_xor": int(np.count_nonzero(d28 ^ d30)),
        "solo_31_vs_28_xor": int(np.count_nonzero(solo ^ solo28)),
        "solo_31_vs_d28_gt_1px_xor": int(np.count_nonzero(solo ^ (d28 & (dist > 1)))),
        "b2_vs_d28_gt_2px_xor": int(np.count_nonzero(b2 ^ (d28 & (dist > 2)))),
        "d28_removed_to_b2": int(np.count_nonzero(d28 & ~b2)),
        "solo_removed_to_b2": int(np.count_nonzero(solo & ~b2)),
        "legacy36_added_over_b2": int(np.count_nonzero(old36 & ~b2)),
        "legacy36_missing_b2": int(np.count_nonzero(b2 & ~old36)),
    }
    expected = {
        "d28_25_vs_30_xor": 0, "solo_31_vs_28_xor": 0,
        "solo_31_vs_d28_gt_1px_xor": 0, "b2_vs_d28_gt_2px_xor": 0,
        "d28_removed_to_b2": 6436, "solo_removed_to_b2": 2545,
        "legacy36_added_over_b2": 1200, "legacy36_missing_b2": 0,
    }
    if claims != expected:
        raise RuntimeError(f"Inherited byte-forensics disagrees with pinned rasters: {claims}")
    receipt = {
        "schema": "focus9-source-integrity-v2", "checked_date_utc": "2026-10-26",
        "score_provenance": "OWNER-REPORTED only; none of these nine scores has an authenticated submission-page receipt in this repo",
        "source": "registry/scored_registry.json + evidence/focus_sites_9repo_summary_20261026.json",
        "sites": rows,
        "nested_family_crosschecks": claims,
        "limit": "Exact raster identity proves neither which bytes were uploaded nor why the blind organizer score changed; extra off-catalogue truth is unavailable.",
    }
    dest = ROOT / "evidence/mto36_ninesite_forensics.json"
    dest.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(f"Validated {len(rows)} sites, all eight inherited family checks; {dest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
