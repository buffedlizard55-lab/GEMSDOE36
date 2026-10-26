#!/usr/bin/env python3
"""Independent fail-closed cross-check of ANY candidate GeoTIFF with the shared template tools.

Checks (no human step): template ``check_variants`` format validation, strict whole-array [0, 1],
dot geometry (spacing, distance to the catalogue), and final-dot uniqueness against every raster in
``registry/uniqueness_registry.json`` via ``gems.novelty.compare_registry`` (the binary file itself
is the only surface available for a third-party file, so the surface-stage check is not possible).
It never changes another lane's verdict; it reports agreement or conflict.

Usage: python3 scripts/crosscheck_candidate.py docs/downloads/<file>.tif --out evidence/<name>.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.novelty import compare_registry  # noqa: E402
from gems.submission import check_variants  # noqa: E402

TEMPLATE = ROOT / "data/raw/sample_submission.tif"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tif", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    tif = args.tif if args.tif.is_absolute() else ROOT / args.tif
    fmt = check_variants(tif, TEMPLATE)
    with rasterio.open(tif) as s:
        a = s.read(1)
    with rasterio.open(ROOT / "data/raw/labels.tif") as s:
        lab = s.read(1)
    fp, cat = lab >= 0, lab == 1
    strict = bool(np.isfinite(a).all() and ((a >= 0) & (a <= 1)).all())
    dots = fp & np.isfinite(a) & (a > 0)
    pts = np.argwhere(dots)
    nn = cKDTree(pts).query(pts, k=2)[0][:, 1]
    dcat = distance_transform_edt(~cat)[dots]
    reg = json.loads((ROOT / "registry/uniqueness_registry.json").read_text())["entries"]
    own_sha = hashlib.sha256(tif.read_bytes()).hexdigest()
    reg = [r for r in reg if r.get("file_sha256") != own_sha]  # never compare a file with itself
    surface = np.where(fp, np.nan_to_num(a, nan=0.0), 0.0).astype(np.float32)
    chk = compare_registry(surface, fp, reg, ROOT, dots=dots, separate_calibration_controls=True)
    rows = sorted(chk["rows"], key=lambda r: -(r.get("candidate_dot_overlap_within_3px") or 0))
    over = [r for r in rows if r.get("comparator_class") == "competing_method" and (r["candidate_dot_overlap_within_3px"] or 0) > 0.70]
    out = {
        "file": str(tif.relative_to(ROOT)),
        "sha256": own_sha,
        "template_format_valid": fmt["format_valid"],
        "template_hard_failures": fmt["hard_failures"],
        "strict_whole_array_0_1": strict,
        "dots": int(dots.sum()),
        "unique_values_in_footprint": sorted({float(v) for v in np.unique(a[fp])})[:10],
        "dot_spacing_px": {"min": float(nn.min()), "median": float(np.median(nn))},
        "distance_to_catalogue_px": {"min": float(dcat.min()), "share_le_2px": float((dcat <= 2).mean()), "share_le_3px": float((dcat <= 3).mean())},
        "registry_rasters_compared": chk["registry_unique_rasters"],
        "max_abs_rank_correlation": chk["max_abs_rank_correlation"],
        "max_competing_dot_overlap": chk.get("max_competing_dot_overlap"),
        "final_dot_uniqueness_passed": bool(chk["passed"]),
        "competing_rasters_over_0.70": [
            {"file": r["file"], "overlap": r["candidate_dot_overlap_within_3px"], "footprint_3px_coverage": r.get("footprint_3px_coverage")}
            for r in over
        ],
        "scope": "Format + final-dot uniqueness only; holdout claims of the candidate's own lane are not re-run (a final full-catalogue model cannot be scored on a hide-and-recover holdout without leakage).",
    }
    args.out.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps({k: out[k] for k in ("file", "template_format_valid", "strict_whole_array_0_1", "dots", "max_abs_rank_correlation", "max_competing_dot_overlap", "final_dot_uniqueness_passed")}, indent=1))
    for r in out["competing_rasters_over_0.70"][:10]:
        print(f"  {r['overlap']:.4f} {r['file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
