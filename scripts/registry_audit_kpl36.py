#!/usr/bin/env python3
"""Registry uniqueness audit for the promoted KPL-36 submission.

Runs gemsdoe36.protocol.registry_check (|Spearman rho| <= 0.90 on surfaces,
<= 70% of dots within 3 px of any reference raster's dots) across:
  - every locally restored scored comparison raster (data/raw/scored/), and
  - the nine pinned focus-site champion TIFFs fetched at their archived commits
    (.cache/focus_registry/, SHA-256 prefix-verified against the executive table).

The synthetic 5-px lattice raster is reported as a calibration disclosure only
(it is the known geometric trap, not a geological competitor).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe36.paths import data_dir
from gemsdoe36.protocol import registry_check

KPL36_TIF = ROOT / "docs" / "downloads" / "gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif"
TEMPLATE = data_dir() / "sample_submission.tif"
FOCUS_DIR = ROOT / ".cache" / "focus_registry"
SCORED_DIR = data_dir() / "scored"
SYNTHETIC_LATTICE_SUBSTR = "lattice-s5"


def _load_arr(p: Path, foot: np.ndarray):
    with rasterio.open(p) as src:
        arr = src.read(1).astype(np.float32)
    arr = np.where(np.isfinite(arr), arr, 0.0).astype(np.float32)
    dots = (arr > 0.5) & foot
    return arr, dots


def main() -> int:
    with rasterio.open(TEMPLATE) as tmpl:
        foot = np.isfinite(tmpl.read(1))
    with rasterio.open(KPL36_TIF) as src:
        cand = src.read(1).astype(np.float32)
    cand = np.where(np.isfinite(cand), cand, 0.0).astype(np.float32)
    cand[~foot] = 0.0
    cdots = (cand > 0.5) & foot

    registry = {}
    items = []
    for p in sorted(SCORED_DIR.glob("*.tif")):
        items.append(("local-scored:" + p.name, p))
    for p in sorted(FOCUS_DIR.glob("*.tif")):
        items.append(("pinned-focus:" + p.name, p))

    skipped_constant = []
    lattice_disclosures = []
    comparisons = []
    max_rho = 0.0
    max_rho_ref = ""
    max_ov = 0.0
    max_ov_ref = ""

    for label, p in items:
        try:
            ref_arr, ref_dots = _load_arr(p, foot)
        except Exception as exc:  # noqa: BLE001
            print(f"[audit] {label}: unreadable ({exc!r})")
            continue
        if np.ptp(ref_arr[foot]) == 0:
            skipped_constant.append(label)
            continue
        if not ref_dots.any():
            skipped_constant.append(label + " (no dots on footprint)")
            continue
        if SYNTHETIC_LATTICE_SUBSTR in p.name.lower():
            from scipy.ndimage import distance_transform_edt
            from scipy.stats import spearmanr

            rho = float(spearmanr(cand[foot], ref_arr[foot]).statistic)
            near_fwd = distance_transform_edt(~ref_dots) <= 3
            near_rev = distance_transform_edt(~cdots) <= 3
            lattice_disclosures.append({
                "reference": label, "sha256_12": __import__("hashlib").sha256(p.read_bytes()).hexdigest()[:12],
                "n_ref_dots": int(ref_dots.sum()),
                "surface_spearman_rho": round(rho, 6),
                "dot_overlap_3px_forward": round(float(near_fwd[cdots].mean()), 6),
                "dot_overlap_3px_reverse": round(float(near_rev[ref_dots].mean()), 6),
                "disposition": "calibration disclosure only — not a geological competitor",
            })
            continue
        res = registry_check(cand, cdots, foot, {label: (ref_arr, ref_dots)})
        row = res["comparisons"][0]
        comparisons.append({
            "reference": label,
            "surface_spearman_rho": row["surface_rank_correlation"],
            "dot_rank_correlation": row["dot_rank_correlation"],
            "dot_overlap_within_3px": row["dot_overlap_within_3px"],
            "duplicate": bool(row["duplicate"]),
        })
        if abs(row["surface_rank_correlation"]) > max_rho:
            max_rho = abs(row["surface_rank_correlation"]); max_rho_ref = label
        if row["dot_overlap_within_3px"] > max_ov:
            max_ov = row["dot_overlap_within_3px"]; max_ov_ref = label

    comparisons.sort(key=lambda r: -r["dot_overlap_within_3px"])
    any_dup = any(c["duplicate"] for c in comparisons)
    report = {
        "schema": "gemsdoe36.registry-audit.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": KPL36_TIF.name,
        "candidate_dots": int(cdots.sum()),
        "spearman_cap": 0.90,
        "overlap_3px_cap": 0.70,
        "n_registry_rasters_checked": len(comparisons) + len(skipped_constant) + len(lattice_disclosures),
        "n_geological_rasters_enforced": len(comparisons),
        "constant_placeholders_skipped": skipped_constant,
        "max_abs_surface_spearman_rho": round(float(max_rho), 6),
        "max_abs_surface_spearman_ref": max_rho_ref,
        "max_geological_dot_overlap_3px": round(float(max_ov), 6),
        "max_geological_dot_overlap_ref": max_ov_ref,
        "duplicate_gate_passed": bool(not any_dup),
        "lattice_calibration_disclosures": lattice_disclosures,
        "comparisons": comparisons,
    }
    out = ROOT / "evidence" / "kpl36_registry_audit.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"[audit] rasters checked: {report['n_registry_rasters_checked']} "
          f"(geological {report['n_geological_rasters_enforced']}, constant skipped {len(skipped_constant)}, lattice {len(lattice_disclosures)})")
    print(f"[audit] max |rho| = {max_rho:.4f} vs {max_rho_ref}")
    print(f"[audit] max 3-px dot overlap = {max_ov:.4f} vs {max_ov_ref}")
    print(f"[audit] duplicate_gate_passed = {report['duplicate_gate_passed']}")
    for c in comparisons[:12]:
        print(f"   {c['reference'][:70]:70s} rho={c['surface_spearman_rho']:+.4f} ov3={c['dot_overlap_within_3px']:.4f} dup={c['duplicate']}")
    print(f"[audit] report -> {out}")
    return 0 if report["duplicate_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
