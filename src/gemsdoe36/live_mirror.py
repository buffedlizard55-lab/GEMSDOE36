"""Live-mirror holdout instrument (LM) -- spatially blocked DTI against off-catalogue truth.

Evaluates candidates on four spatially blocked quadrants against the USGS State Geologic Map
Compilation (SGMC) fault traces lying strictly >300 m from the published catalogue.
Reproduces known live leaderboard orderings (e.g. 0.2708 > 0.2600 > 0.2477) and guards
against catalogue-leakage artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, binary_erosion, distance_transform_edt

FOLD_NAMES = ("NW", "NE", "SW", "SE")
FOLDS = (0, 1, 2, 3)
DOMAIN_ERODE = 12  # 1.2 km boundary erosion
CAT_FLANK_PX = 3  # 300 m metric radius


@dataclass
class LiveMirrorCell:
    key: str
    fold: int
    bbox: tuple[slice, slice]
    domain: np.ndarray
    truth: np.ndarray
    truth_coords: tuple[np.ndarray, np.ndarray]
    n_truth: int


@dataclass
class LiveMirrorContext:
    foot: np.ndarray
    labels: np.ndarray
    sgmc_off: np.ndarray
    quad: np.ndarray
    cells: list[LiveMirrorCell]


def quadrant_ids(footprint: np.ndarray) -> np.ndarray:
    footprint = np.asarray(footprint, bool)
    yy, xx = np.nonzero(footprint)
    ym, xm = int(np.median(yy)), int(np.median(xx))
    H, W = footprint.shape
    gy, gx = np.ogrid[:H, :W]
    q = np.full((H, W), -1, np.int8)
    q[(gy < ym) & (gx < xm) & footprint] = 0
    q[(gy < ym) & (gx >= xm) & footprint] = 1
    q[(gy >= ym) & (gx < xm) & footprint] = 2
    q[(gy >= ym) & (gx >= xm) & footprint] = 3
    return q


def load_live_mirror_context(
    ddir: Path, foot: np.ndarray, labels: np.ndarray
) -> LiveMirrorContext:
    """Build the four spatially blocked off-catalogue truth cells."""
    sgmc_path = ddir / "external" / "derived_sgmc_faults_100m_u8.tif"
    if not sgmc_path.exists():
        sgmc_path = ddir / "derived_sgmc_faults_100m_u8.tif"
    with rasterio.open(sgmc_path) as ds:
        sgmc = ds.read(1) > 0

    sgmc_off = sgmc & foot & ~labels & ~binary_dilation(labels, iterations=CAT_FLANK_PX)
    quad = quadrant_ids(foot)
    cells: list[LiveMirrorCell] = []
    for fold in FOLDS:
        q = quad == fold
        rows = np.flatnonzero(q.any(axis=1))
        cols = np.flatnonzero(q.any(axis=0))
        r0 = max(0, int(rows[0]) - 6)
        r1 = min(foot.shape[0], int(rows[-1]) + 7)
        c0 = max(0, int(cols[0]) - 6)
        c1 = min(foot.shape[1], int(cols[-1]) + 7)
        sl = (slice(r0, r1), slice(c0, c1))
        domain = binary_erosion(q, iterations=DOMAIN_ERODE)
        truth = (sgmc_off & domain)[sl]
        tc = np.nonzero(truth)
        cells.append(
            LiveMirrorCell(
                key=f"fold{FOLD_NAMES[fold]}",
                fold=fold,
                bbox=sl,
                domain=domain[sl],
                truth=truth,
                truth_coords=tc,
                n_truth=int(tc[0].size),
            )
        )
    return LiveMirrorContext(
        foot=foot, labels=labels, sgmc_off=sgmc_off, quad=quad, cells=cells
    )


def kernel_triangle(dist: np.ndarray, radius: float = 3.0) -> np.ndarray:
    return np.maximum(1.0 - dist / radius, 0.0)


def official_dti(P: np.ndarray, G: np.ndarray) -> dict:
    """Official distance-weighted Tversky index between prediction and truth."""
    P = np.asarray(P, bool)
    G = np.asarray(G, bool)
    n_p = int(P.sum())
    n_g = int(G.sum())
    if n_p == 0 or n_g == 0:
        return {"dti": 0.0, "tp_w": 0.0, "tp_p": 0.0, "tp_g": 0.0, "n_p": n_p, "n_g": n_g}
    dp = distance_transform_edt(~P)
    dg = distance_transform_edt(~G)
    tp_p = float(kernel_triangle(dp[G]).sum())
    tp_g = float(kernel_triangle(dg[P]).sum())
    tp_w = 0.5 * (tp_p + tp_g)
    denom = 0.2 * n_p + 0.8 * n_g + 0.8 * (tp_g - tp_p) + 1e-8
    return {
        "dti": float(tp_w / denom),
        "tp_w": tp_w,
        "tp_p": tp_p,
        "tp_g": tp_g,
        "n_p": n_p,
        "n_g": n_g,
    }


def evaluate_live_mirror(
    mask: np.ndarray,
    ctx: LiveMirrorContext,
    name: str = "candidate",
    calibrate_prevalence: bool = True,
    g_lb_total: float = 12691.0,
) -> dict:
    """Score candidate under the spatially blocked live mirror."""
    mask = np.asarray(mask, bool) & ctx.foot
    n_emit = int(mask.sum())
    foot_px = float(ctx.foot.sum())
    per_fold_cal: dict[str, float] = {}
    details: dict[str, dict] = {}

    for cell in ctx.cells:
        sl = cell.bbox
        p = mask[sl] & cell.domain
        g = cell.truth
        r = official_dti(p, g)
        details[cell.key] = r
        if calibrate_prevalence and r["n_g"] > 0:
            g_cal = g_lb_total * (float(cell.domain.sum()) / foot_px)
            denom_cal = 0.2 * r["n_p"] + 0.8 * g_cal + 0.8 * (r["tp_g"] - r["tp_p"]) + 1e-8
            per_fold_cal[cell.key] = float(r["tp_w"] / denom_cal)
        else:
            per_fold_cal[cell.key] = r["dti"]

    vals = np.array(list(per_fold_cal.values()), dtype=np.float64)
    return {
        "candidate_id": name,
        "lm_calibrated_mean": float(vals.mean()),
        "lm_calibrated_std": float(vals.std()),
        "lm_calibrated_per_fold": per_fold_cal,
        "emitted_pixels": n_emit,
        "on_catalogue_pixels": int((mask & ctx.labels).sum()),
        "fold_detail": details,
    }
