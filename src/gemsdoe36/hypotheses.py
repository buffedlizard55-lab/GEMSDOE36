"""Candidate Geological Hypotheses & Physics-Informed Transforms for GEMSDOE36.

Four distinct, label-free geological hypotheses targeting uncatalogued faults:
- H36-1: Anderson Kinematic Consistency & Step-Over Dilatational Pumping (Rank #1)
- H36-2: Multi-Scale Dip-Projected Basement Step Asymmetry (Rank #2)
- H36-3: GDR Measured Geothermometer Hydrothermal Upflow Conduits (Rank #3)
- H36-4: 3DEP LiDAR Scarp Residual Curvature (Rank #4)
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter


def robust_zpos(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Robust non-negative z-score inside footprint using median and IQR, clipped to [0, 6]."""
    out = np.zeros(arr.shape, dtype=np.float32)
    valid = foot & np.isfinite(arr)
    if not valid.any():
        return out
    vals = arr[valid]
    med = float(np.median(vals))
    q25, q75 = np.percentile(vals, [25.0, 75.0])
    iqr = max(float(q75 - q25), 1e-6)
    z = (arr - med) / (iqr / 1.349)
    out[valid] = np.clip(z[valid], 0.0, 6.0)
    return out


def fill_smooth(arr: np.ndarray, foot: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Fill non-finite values with footprint median and smooth."""
    valid = foot & np.isfinite(arr)
    med = float(np.median(arr[valid])) if valid.any() else 0.0
    filled = np.where(valid, arr, med).astype(np.float32)
    if sigma > 0:
        return gaussian_filter(filled, sigma=sigma)
    return filled


def ridge_nms_2d(score: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """1-pixel oriented ridge crest extraction via 4-direction non-maximum suppression."""
    s = np.where(foot, score, -1e9).astype(np.float32)
    gy, gx = np.gradient(s)
    theta = (np.rad2deg(np.arctan2(gy, gx)) + 180.0) % 180.0
    p0 = np.roll(s, 1, axis=1)
    n0 = np.roll(s, -1, axis=1)
    p90 = np.roll(s, 1, axis=0)
    n90 = np.roll(s, -1, axis=0)
    p45 = np.roll(np.roll(s, 1, axis=0), 1, axis=1)
    n45 = np.roll(np.roll(s, -1, axis=0), -1, axis=1)
    p135 = np.roll(np.roll(s, 1, axis=0), -1, axis=1)
    n135 = np.roll(np.roll(s, -1, axis=0), 1, axis=1)

    b0 = (theta < 22.5) | (theta >= 157.5)
    b45 = (theta >= 22.5) & (theta < 67.5)
    b90 = (theta >= 67.5) & (theta < 112.5)
    b135 = (theta >= 112.5) & (theta < 157.5)
    is_max = (
        (b0 & (s >= p0) & (s > n0))
        | (b45 & (s >= p45) & (s > n45))
        | (b90 & (s >= p90) & (s > n90))
        | (b135 & (s >= p135) & (s > n135))
    )
    return is_max & foot


def sample_bilinear(field: np.ndarray, yy: np.ndarray, xx: np.ndarray) -> np.ndarray:
    """Vectorized bilinear interpolation on 2D grid."""
    H, W = field.shape
    y = np.clip(yy, 0.0, H - 1.001)
    x = np.clip(xx, 0.0, W - 1.001)
    y0, x0 = y.astype(np.int32), x.astype(np.int32)
    y1, x1 = y0 + 1, x0 + 1
    wy, wx = y - y0, x - x0
    return (
        (1.0 - wy) * (1.0 - wx) * field[y0, x0]
        + (1.0 - wy) * wx * field[y0, x1]
        + wy * (1.0 - wx) * field[y1, x0]
        + wy * wx * field[y1, x1]
    ).astype(np.float32)


def poisson_disk_thin_priority(
    candidates_mask: np.ndarray,
    priority: np.ndarray,
    min_dist_px: float = 2.35,
    existing_dots: np.ndarray | None = None,
    max_add: int | None = None,
) -> np.ndarray:
    """Greedy priority-ordered Poisson-disk selector enforcing Euclidean distance >= min_dist_px."""
    H, W = candidates_mask.shape
    selected = np.zeros((H, W), dtype=bool)
    blocked = np.zeros((H, W), dtype=bool)

    r_int = int(np.ceil(min_dist_px))
    dy_grid, dx_grid = np.mgrid[-r_int : r_int + 1, -r_int : r_int + 1]
    disk_offs = (
        np.argwhere((dy_grid * dy_grid + dx_grid * dx_grid) < (min_dist_px * min_dist_px - 1e-6))
        - r_int
    )

    if existing_dots is not None and existing_dots.any():
        dist_ex = distance_transform_edt(~existing_dots)
        blocked |= dist_ex < (min_dist_px - 1e-6)

    elig = candidates_mask & ~blocked
    yy, xx = np.nonzero(elig)
    if yy.size == 0:
        return selected

    scores = priority[yy, xx]
    order = np.argsort(-scores, kind="mergesort")
    yy = yy[order]
    xx = xx[order]

    added = 0
    dy_off = disk_offs[:, 0]
    dx_off = disk_offs[:, 1]
    for r, c in zip(yy, xx):
        if blocked[r, c]:
            continue
        selected[r, c] = True
        added += 1
        if max_add is not None and added >= max_add:
            break
        nr = r + dy_off
        nc = c + dx_off
        ok = (nr >= 0) & (nr < H) & (nc >= 0) & (nc < W)
        blocked[nr[ok], nc[ok]] = True

    return selected
