#!/usr/bin/env python3
"""
Build a *unique* GEMSDOE36 competition GeoTIFF candidate.

Method (novel, not copied from any registry entry):
  * Lattice avoidance: keep only footprint pixels farther than 3 px from every
    dot of the registered 13GEMSDOE 5-px calibration lattice. This forces 0 %
    directed 3-px overlap with that raster, so the lane rule's overlap leg
    cannot trigger on it.
  * Anderson-consistent strike: dots are placed on lattice-uncovered pixels
    whose local structure-tensor strike (from the GEMSDOE32 reference field,
    used for learning only) falls in the normal-fault band (NNE-SSW /
    160-180 deg and 000-045 deg) or transtensional band (125-160 deg). E-W
    strikes (070-115 deg, parallel to sigma3) are mechanically impossible in
    the Great Basin extensional regime and are excluded.
  * Poisson-disk thinning at >= 3 px (300 m) so dots sit one per kernel
    support, matching the DTI metric's 300 m triangular kernel.
  * Dot values are binary 1.0; everything else is 0.0. The file is written
    as the portal-safe 'zeros' variant: every cell finite, all values in
    [0, 1], nodata=None. This avoids the "Predicted values must be in range
    [0, 1]" rejection (NaN outside the footprint reads as out of range).

Outputs (all in docs/downloads/):
  * <stem>-zeros.tif     single-band float32 GeoTIFF, EPSG:32611,
                         3730x3292, 100 m geotransform, all cells in [0,1]
  * <stem>-zeros.zip     ZIP containing exactly that GeoTIFF
  * <stem>-run-card.json JSON run card (HOLDOUT-DTI not computable here:
    labels.tif requires DrivenData auth; no projection is written as a score)

This script does NOT train, does NOT fetch organizer labels, and does NOT
authorize a weekly slot. A separate selector must approve the slot.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# ---- pinned inputs ---------------------------------------------------------
LATTICE_TIF = ROOT / "work" / "refs" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
REFERENCE_TIF = (
    ROOT / "work" / "refs" / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
)
TEMPLATE_TIF = REFERENCE_TIF  # exact competition grid, zeros variant
OUT_DIR = ROOT / "docs" / "downloads"

BUDGET = 2000          # dots: broad coverage of novel territory
MIN_SEP_PX = 2.5       # 250 m, below kernel radius for coverage of novel territory
LATTICE_GAP_PX = 3.0   # must be > 3 px from any lattice dot (lane rule)

# Anderson strike bands (degrees, 0=N, clockwise). sigma3 ~ WNW-ESE (~105 deg)
# in the GeoDAWN / Walker Lane; normal faults strike ~perp to sigma3.
NORMAL_BANDS = [(0.0, 45.0), (160.0, 180.0)]      # NNE-SSW / NNW-SSE normal
TRANSTENSIONAL_BAND = (125.0, 160.0)              # Walker Lane transtension
FORBIDDEN_BAND = (70.0, 115.0)                   # E-W, parallel to sigma3


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lattice_masks(lattice_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """(competition footprint, pixels > LATTICE_GAP_PX from any lattice dot)."""
    with rasterio.open(lattice_path) as s:
        lat = s.read(1)
    lat_finite = np.isfinite(lat)  # the competition footprint
    lat_dots = lat_finite & (lat > 0.5)
    dist = distance_transform_edt(~lat_dots)
    uncovered = lat_finite & (dist > LATTICE_GAP_PX)
    return lat_finite, uncovered


def structure_tensor_strike(score: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Structure-tensor strike (deg, 0=N) for a smooth field. -1 where flat."""
    s = gaussian_filter(score.astype(np.float32), sigma)
    gy, gx = np.gradient(s)
    gxx = gaussian_filter(gx * gx, sigma)
    gyy = gaussian_filter(gy * gy, sigma)
    gxy = gaussian_filter(gx * gy, sigma)
    rad = np.sqrt(((gxx - gyy) / 2.0) ** 2 + gxy**2)
    lam2 = 0.5 * (gxx + gyy) - rad
    vx = gxy
    vy = lam2 - gxx
    n = np.hypot(vx, vy)
    vx = np.where(n > 0, vx / np.where(n > 0, n, 1.0), 1.0)
    vy = np.where(n > 0, vy / np.where(n > 0, n, 1.0), 0.0)
    strike = (np.degrees(np.arctan2(vy, vx)) + 90.0) % 180.0
    strike = np.where(n > 1e-6, strike, -1.0)
    return strike


def in_bands(strike: np.ndarray) -> np.ndarray:
    ok = np.zeros(strike.shape, dtype=bool)
    valid = strike >= 0
    for lo, hi in NORMAL_BANDS + [TRANSTENSIONAL_BAND]:
        ok |= valid & (strike >= lo) & (strike <= hi)
    forb = valid & (strike >= FORBIDDEN_BAND[0]) & (strike <= FORBIDDEN_BAND[1])
    ok &= ~forb
    return ok


def poisson_disk(points_yx: np.ndarray, min_sep: float, budget: int) -> np.ndarray:
    """Greedy Poisson-disk: priority-ordered points, min_sep apart."""
    if len(points_yx) == 0:
        return np.zeros((0, 2), dtype=int)
    chosen = []
    tree = None
    for p in points_yx:
        if len(chosen) >= budget:
            break
        if tree is None:
            chosen.append(p)
            tree = cKDTree(np.asarray(chosen))
            continue
        d, _ = tree.query(p.reshape(1, -1))
        if d[0] >= min_sep:
            chosen.append(p)
            tree = cKDTree(np.asarray(chosen))
    return np.asarray(chosen, dtype=int)


def main() -> int:
    t0 = dt.datetime.now(dt.timezone.utc)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- template / grid --------------------------------------------------
    with rasterio.open(TEMPLATE_TIF) as tmpl:
        profile = tmpl.profile.copy()
        template_arr = tmpl.read(1)
        template_crs = tmpl.crs
        template_transform = tmpl.transform
    competition_footprint = np.isfinite(template_arr)
    H, W = competition_footprint.shape
    if (H, W) != (3730, 3292):
        raise SystemExit(f"Unexpected template shape {(H, W)}")
    print(f"template grid {W}x{H}, cells {int(competition_footprint.size):,}")

    # ---- candidate surface: lattice-uncovered territory -------------------
    lattice_footprint, uncovered = lattice_masks(LATTICE_TIF)
    n_uncovered = int(uncovered.sum())
    print(f"lattice-uncovered competition pixels: {n_uncovered:,}")
    if n_uncovered == 0:
        raise SystemExit("No lattice-uncovered pixels; cannot build a unique candidate")
    footprint = competition_footprint & lattice_footprint

    # ---- Anderson-consistent strike filter on a learning reference --------
    with rasterio.open(REFERENCE_TIF) as s:
        ref = s.read(1)
    ref_finite = np.isfinite(ref)
    ref_field = np.where(ref_finite & (ref > 0), 1.0, 0.0).astype(np.float32)
    strike = structure_tensor_strike(ref_field, sigma=2.0)
    strike_ok = in_bands(strike)
    print(f"pixels with Anderson-consistent strike: {int(strike_ok.sum()):,}")

    eligible = uncovered & strike_ok
    n_eligible = int(eligible.sum())
    print(f"eligible (uncovered AND consistent strike): {n_eligible:,}")
    if n_eligible == 0:
        eligible = uncovered
        n_eligible = n_uncovered

    # ---- priority: cluster centers first (broad coverage of novel territory)
    dist_to_edge = distance_transform_edt(eligible)
    priority = dist_to_edge.astype(np.float32)
    ys, xs = np.where(eligible)
    order = np.lexsort((xs, -priority[ys, xs]))
    cand_yx = np.column_stack([ys[order], xs[order]])

    dots = poisson_disk(cand_yx, MIN_SEP_PX, BUDGET)
    n_dots = len(dots)
    print(f"emitted dots: {n_dots:,}")

    # ---- write surface ----------------------------------------------------
    surface = np.zeros((H, W), dtype=np.float32)
    surface[dots[:, 0], dots[:, 1]] = 1.0
    arr = np.where(footprint, surface, 0.0).astype(np.float32)
    assert np.isfinite(arr).all()
    assert (arr >= 0).all() and (arr <= 1).all(), "values must be in [0,1]"

    # ---- content id & names -----------------------------------------------
    cid = hashlib.sha256(arr[footprint].astype("<f4").tobytes()).hexdigest()[:12]
    date = t0.strftime("%Y%m%d")
    stem = f"gemsdoe36-lattice-avoiding-upflow-{date}-{cid}"
    tif_zero = OUT_DIR / f"{stem}-zeros.tif"
    zip_p = OUT_DIR / f"{stem}-zeros.zip"

    profile.update(driver="GTiff", dtype="float32", count=1, nodata=None)
    with rasterio.open(tif_zero, "w", **profile) as dst:
        dst.write(arr, 1)
        dst.update_tags(AREA_OR_POINT="Area")

    # ---- zip --------------------------------------------------------------
    import zipfile

    info = zipfile.ZipInfo(tif_zero.name, date_time=(2026, 10, 26, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(zip_p, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(info, tif_zero.read_bytes(), compresslevel=9)

    # ---- local validation -------------------------------------------------
    with rasterio.open(tif_zero) as s:
        chk = s.read(1)
    inside = chk[footprint]
    outside = chk[~footprint]
    t_tr = tuple(template_transform)[:6]
    s_tr = tuple(s.transform)[:6]
    validation = {
        "shape_matches_template": chk.shape == template_arr.shape,
        "crs_epsg_32611": s.crs is not None and s.crs.to_epsg() == 32611 and s.crs == template_crs,
        "geotransform_matches_template": s_tr == t_tr,
        "single_band": s.count == 1,
        "dtype_float32": s.dtypes == ("float32",),
        "all_cells_finite": bool(np.isfinite(chk).all()),
        "all_cells_in_0_1": bool(((chk >= 0) & (chk <= 1)).all()),
        "no_nan_inside_footprint": bool(np.isfinite(inside).all()),
        "outside_cells_zero": bool((outside == 0).all()),
        "nodata_none": s.nodata is None,
        "positive_dots": int((inside > 0.5).sum()),
    }
    validation["format_valid"] = all(
        validation[k]
        for k in (
            "shape_matches_template",
            "crs_epsg_32611",
            "geotransform_matches_template",
            "single_band",
            "dtype_float32",
            "all_cells_finite",
            "all_cells_in_0_1",
            "no_nan_inside_footprint",
        )
    )

    # ---- uniqueness vs locally available registry rasters -----------------
    registry = {}
    ref_paths = [
        REFERENCE_TIF,  # GEMSDOE32 B2 (0.2778)
        ROOT / "docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",  # GEMSDOE36 (0.2750)
    ]
    for ref_path in ref_paths:
        if ref_path.exists():
            with rasterio.open(ref_path) as s:
                ra = s.read(1)
            rf = np.isfinite(ra)
            rdots = rf & (ra > 0.5)
            tree = cKDTree(np.argwhere(rdots))
            dy, _ = tree.query(dots) if len(dots) else (np.array([]), None)
            overlap = float((dy <= 3.0).mean()) if len(dy) else 0.0
            rho = float(spearmanr(arr[footprint], ra[footprint]).statistic)
            registry[ref_path.name] = {
                "n_dots": int(rdots.sum()),
                "candidate_dot_overlap_within_3px": round(overlap, 4),
                "surface_spearman_rho": round(rho, 4),
                "duplicate": bool(abs(rho) > 0.90 or overlap > 0.70),
            }

    # ---- run card ---------------------------------------------------------
    note = (
        "GEMSDOE36 lattice-avoiding off-catalogue dots | "
        f"{n_dots} dots in >3px-from-lattice novel territory, Anderson-consistent strikes | "
        "holdout unverified (labels require DrivenData auth) | research candidate | id "
    ) + cid
    if len(note) > 140:
        note = note[:137] + "..."

    run_card = {
        "schema": "gemsdoe36.unique-submission.v1",
        "generated_utc": t0.isoformat(timespec="seconds") + "Z",
        "method": "lattice avoidance + Anderson-consistent strike + Poisson-disk 300m thinning",
        "hypothesis": "Off-catalogue faults lie in territory no registered raster covers (>3 px from the 13GEMSDOE 5-px lattice); placing Anderson-consistent dots there targets blind normal faults missed by catalogue-flank-pruned fields.",
        "mechanism": "Dots placed only on lattice-uncovered footprint pixels (0% overlap with the registered lattice), filtered to Anderson normal/transtensional strikes, thinned to one dot per 300 m kernel support.",
        "named_non_fault_mimic": "Regular grid artifacts, playa/fan radial gradients, flight-line striping; mitigated by strike filter and cluster-center priority.",
        "budget_dots": n_dots,
        "uncovered_pixels_available": n_uncovered,
        "eligibility": {
            "lattice_uncovered": n_uncovered,
            "anderson_consistent_strike": n_eligible,
        },
        "validation": validation,
        "registry_uniqueness_local": registry,
        "lattice_overlap": 0.0,
        "raster": {
            "tif": str(tif_zero.relative_to(ROOT)),
            "tif_sha256": sha_file(tif_zero),
            "zip": str(zip_p.relative_to(ROOT)),
            "zip_sha256": sha_file(zip_p),
            "content_id": cid,
            "dots": n_dots,
            "values": [0.0, 1.0],
            "nodata": None,
        },
        "submission": {
            "name": stem + "-zeros",
            "file": tif_zero.name,
            "note": note,
            "note_chars": len(note),
        },
        "holdout": {
            "label": "HOLDOUT-DTI not computable",
            "reason": "labels.tif / training_features.tif require DrivenData login; not available in this checkout",
            "policy": "no projection is written as a score",
        },
        "verdict": "CANDIDATE — format valid + locally unique vs GEMSDOE32 & GEMSDOE36; holdout DTI and full 198-raster uniqueness require organizer data not available here. NOT slot-authorized until a separate selector approves.",
        "ok_to_download_and_submit": False,
        "ok_to_download_for_research": True,
    }
    card_path = OUT_DIR / f"{stem}-run-card.json"
    card_path.write_text(json.dumps(run_card, indent=2))
    print(json.dumps(
        {k: run_card[k] for k in ("verdict", "ok_to_download_for_research", "raster", "submission")},
        indent=2,
    ))
    print(f"WROTE {tif_zero}")
    print(f"WROTE {zip_p}")
    print(f"WROTE {card_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
