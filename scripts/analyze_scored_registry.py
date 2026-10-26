#!/usr/bin/env python3
"""Descriptive forensics of every owner-reported scored raster that could be located on GitHub.

Learning/education only: no pixel of any registry raster is copied into a GEMSDOE36 candidate.
Scores are OWNER-REPORTED (from the 2026-10-25 owner brief), not organizer receipts.

Outputs ``evidence/scored_registry_analysis.json`` with, per raster: positive-pixel count, mass,
binary flag, nearest-neighbour dot spacing, LiDAR-coverage fraction, distance-to-catalogue bands,
and the implied credit per emitted pixel under the exact identity
``DTI = T / (0.2 (T + S - M) + 0.8 N)`` with the thin-dot approximation ``T ~= M``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "scored_registry.json"
OUT = ROOT / "evidence" / "scored_registry_analysis.json"
N_GRID = (4000, 8000, 12000)  # assumed public-truth pixel counts for the implied-credit table


def main() -> int:
    rows = json.loads(REG.read_text())["entries"]
    with rasterio.open(ROOT / "data/raw/labels.tif") as s:
        lab = s.read(1)
    fp = lab >= 0
    cat = lab == 1
    dcat = distance_transform_edt(~cat).astype(np.float32)
    with rasterio.open(ROOT / "data/raw/external/lidar_scarp_features_u8.tif") as s:
        lvalid = s.read(12) > 0
    out = []
    for r in rows:
        p = ROOT / r["local"]
        if not p.exists():
            out.append({**r, "error": "missing local file"})
            continue
        with rasterio.open(p) as s:
            a = s.read(1)
            same_grid = s.shape == fp.shape and tuple(s.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        fin = np.isfinite(a)
        inside = a[fp]
        pos = fp & fin & (a > 0)
        n = int(pos.sum())
        mass = float(np.nansum(np.where(fp & fin, a, 0), dtype=np.float64))
        vals = np.unique(inside[np.isfinite(inside)])
        binary = bool(np.isin(vals, [0.0, 1.0]).all())
        pts = np.argwhere(pos)
        if n > 1:
            sub = pts if n <= 200000 else pts[np.random.default_rng(0).choice(n, 200000, replace=False)]
            nn = cKDTree(pts).query(sub, k=2)[0][:, 1]
            nn_med, nn_p10 = float(np.median(nn)), float(np.percentile(nn, 10))
        else:
            nn_med = nn_p10 = None
        d = dcat[pos]
        rec = {
            "site": r["site"], "name": r["name"], "owner_reported_score": r["score"],
            "same_grid": same_grid, "n_pos": n, "mass": round(mass, 2), "binary": binary,
            "n_unique_values": int(len(vals)),
            "min_inside": float(np.nanmin(inside)) if np.isfinite(inside).any() else None,
            "max_inside": float(np.nanmax(inside)) if np.isfinite(inside).any() else None,
            "nan_inside_fp": int((~np.isfinite(inside)).sum()),
            "nonzero_outside_fp": int(((~fp) & fin & (a != 0)).sum()),
            "nn_median_px": nn_med, "nn_p10_px": nn_p10,
            "lidar_valid_frac": float(lvalid[pos].mean()) if n else None,
            "frac_dcat_le2": float((d <= 2).mean()) if n else None,
            "frac_dcat_2to3": float(((d > 2) & (d <= 3)).mean()) if n else None,
            "frac_dcat_3to10": float(((d > 3) & (d <= 10)).mean()) if n else None,
            "frac_dcat_10to30": float(((d > 10) & (d <= 30)).mean()) if n else None,
            "frac_dcat_gt30": float((d > 30).mean()) if n else None,
            "dcat_median_px": float(np.median(d)) if n else None,
        }
        D = r["score"]
        S = mass
        rec["implied_credit_per_unit_mass_T_eq_M"] = {
            str(N): (round(D * (0.2 * S + 0.8 * N) / S, 5) if S > 0 else None) for N in N_GRID
        }
        out.append(rec)
        print(f'{r["score"]:.4f} n={n:7d} bin={binary} nn={nn_med} lidar={rec["lidar_valid_frac"]} dcat_med={rec["dcat_median_px"]} {r["site"]} {r["name"][:60]}', flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "label": "FORENSICS (owner-reported scores; not organizer receipts; no pixels reused)",
        "implied_credit_note": "T ~= D (0.2 S + 0.8 N) under the thin-dot approximation T ~= M; N (public truth pixels) is unknown, so three values are tabulated.",
        "rows": out,
    }, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
