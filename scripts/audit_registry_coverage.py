#!/usr/bin/env python3
"""Audit how sensitive the literal 3-px registry overlap gate is, per registry raster.

For every restored registry raster in data/raw/scored/ this computes the share of
footprint cells lying within 3 px (Euclidean) of that raster's dots. A random
placement of dots would reach that share by chance, so when it approaches 1.0 the
literal "more than 70% of your dots within 3 px" test cannot discriminate
anything. It also reports the dot count above which a candidate is forced over the
70% gate against the reference, using the same bound as scripts/registry_feasibility.py.

Read-only: writes only the evidence JSON given by --out. Requires the restored
competition template at data/raw/sample_submission.tif (scripts/restore_data.py).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RADIUS_PX = 3
THRESHOLD = 0.70


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def coverage_within_radius(dots: np.ndarray, footprint: np.ndarray, radius: int) -> int:
    """Count footprint cells whose Euclidean distance to the nearest dot is <= radius."""
    from scipy import ndimage

    if not dots.any():
        return 0
    dist = ndimage.distance_transform_edt(~dots)
    return int(((dist <= radius) & footprint).sum())


def forced_overlap_bound(footprint_cells: int, covered_cells: int, n_dots: int) -> float:
    """Minimum share of n_dots that must lie within the radius of the reference.

    Dots can only avoid the covered cells by sitting in the uncovered cells, so at
    most (footprint - covered) dots can be unmatched.
    """
    uncovered = footprint_cells - covered_cells
    return max(0.0, (n_dots - uncovered) / n_dots)


def first_forced_count(footprint_cells: int, covered_cells: int) -> int:
    """Smallest dot count whose minimum overlap share exceeds THRESHOLD."""
    uncovered = footprint_cells - covered_cells
    # need (n - uncovered) / n > THRESHOLD  <=>  n > uncovered / (1 - THRESHOLD)
    return math.floor(uncovered / (1 - THRESHOLD)) + 1


def audit(template: Path, scored_dir: Path) -> dict:
    import rasterio

    with rasterio.open(template) as t:
        tmpl = t.read(1).astype("float64")
        crs, shape, transform = str(t.crs), t.shape, tuple(t.transform)[:6]
    footprint = np.isfinite(tmpl)
    footprint_cells = int(footprint.sum())

    rows = []
    for path in sorted(scored_dir.glob("*.tif")):
        with rasterio.open(path) as r:
            if r.shape != shape or str(r.crs) != crs or tuple(r.transform)[:6] != transform:
                rows.append({"file": path.name, "status": "grid-mismatch-skipped"})
                continue
            a = r.read(1).astype("float64")
        dots = np.isfinite(a) & (a > 0)
        n_dots = int(dots.sum())
        covered = coverage_within_radius(dots, footprint, RADIUS_PX)
        row = {
            "file": path.name,
            "sha256": sha256_file(path),
            "dot_pixels": n_dots,
            "footprint_cells_within_3px": covered,
            "coverage_share": round(covered / footprint_cells, 6),
            "first_dot_count_forced_over_70pct": first_forced_count(footprint_cells, covered),
            "gate_degenerate": covered / footprint_cells > 0.95,
        }
        rows.append(row)

    return {
        "schema_version": "gemsdoe36.registry-coverage-audit.v1",
        "template": str(template.relative_to(ROOT)),
        "template_sha256": sha256_file(template),
        "crs": crs,
        "shape": list(shape),
        "footprint_cells": footprint_cells,
        "radius_px": RADIUS_PX,
        "threshold": THRESHOLD,
        "provenance": "SHA-pinned owner mirrors via scripts/restore_data.py; not organizer-authenticated",
        "rasters": rows,
        "degenerate_references": [r["file"] for r in rows if r.get("gate_degenerate")],
        "interpretation": (
            "A reference whose 3-px coverage is near 1.0 makes the literal 70% gate fail for "
            "almost any candidate placed inside the footprint, so the gate cannot tell a "
            "duplicate from a non-duplicate against that reference. This is a finding for "
            "owner review, not a verdict on any candidate."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--template", type=Path, default=ROOT / "data/raw/sample_submission.tif")
    ap.add_argument("--scored", type=Path, default=ROOT / "data/raw/scored")
    ap.add_argument(
        "--out", type=Path, default=ROOT / "evidence/registry_coverage_audit_20261028.json"
    )
    args = ap.parse_args()
    if not args.template.exists():
        print(
            f"missing template {args.template}; run scripts/restore_data.py first", file=sys.stderr
        )
        return 1
    result = audit(args.template, args.scored)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for r in result["rasters"]:
        if "coverage_share" in r:
            print(f"{r['coverage_share']:.4f}  dots={r['dot_pixels']:>7}  {r['file']}")
    print(f"degenerate references: {result['degenerate_references']}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
