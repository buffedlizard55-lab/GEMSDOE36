"""KPL-36: long-range (3-5 km) oriented line-coherence features (expert-traceability lane).

Preregistered in ``evidence/kpl36_preregistration_20261026.json`` (H-KPL-A). Every feature is
LABEL-FREE: inputs are physical raster bands already in the GVSC-36 footprint store
(``lid_step_max``, ``org_det_elev_slope``, ``org_tmi_hg``, ``org_iso_grav_anom_hg``,
``lid_valid``). No catalogue pixel is read, so all features are fold-safe by construction.

Physical idea: the hidden truth was drawn by experts tracing continuous kilometre-scale
fault lines. Existing repo worms integrate 1.5 km (half-length 7 px). KPL integrates
3-5 km: structure-tensor coherence at integration sigma 15 px, directional line-integral
anisotropy at half-lengths 15/25 px, and cross-channel tensor-orientation agreement
between topography and magnetics. Named non-fault mimic: long straight roads/railways,
Lahontan shoreline benches, range-front erosional facets.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.signal import fftconvolve

KPL_FEATURES: tuple[str, ...] = (
    "kpl_lid_coh3km",
    "kpl_lid_energy3km",
    "kpl_lid_line15",
    "kpl_lid_line25",
    "kpl_slope_coh3km",
    "kpl_slope_line15",
    "kpl_mag_coh3km",
    "kpl_mag_line15",
    "kpl_grav_coh3km",
    "kpl_xorient_agree",
    "kpl_xcoh_product",
    "kpl_persist_ratio",
)

# LiDAR-derived KPL columns (excluded from the LiDAR-blind bridge expert, together with
# the cross-channel columns that consume the LiDAR tensor through kpl_xcoh_product's
# slope/magnetic pair only -- xorient uses slope+mag tensors, so it stays blind-safe;
# xcoh uses lidar+mag coherence, so it is NOT blind-safe).
KPL_LIDAR_FEATURES: frozenset[str] = frozenset(
    n for n in KPL_FEATURES if n.startswith("kpl_lid") or n == "kpl_xcoh_product" or n == "kpl_persist_ratio"
)

N_ORIENT = 8
SIGMA_INT = 15.0  # 3 km structure-tensor integration scale (px at 100 m)


def _fill(a: np.ndarray, fp: np.ndarray) -> np.ndarray:
    med = float(np.nanmedian(a[fp])) if np.isfinite(a[fp]).any() else 0.0
    return np.where(np.isfinite(a), a, med).astype(np.float32)


def _robust_unit(a: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Map a non-negative field to ~[0,1] by its footprint 99.5th percentile (label-free)."""
    v = a[fp]
    scale = float(np.nanpercentile(v[np.isfinite(v)], 99.5)) if np.isfinite(v).any() else 1.0
    scale = scale if scale > 1e-12 else 1.0
    return np.clip(np.nan_to_num(a, nan=0.0) / scale, 0.0, 1.0).astype(np.float32)


def structure_tensor(a: np.ndarray, fp: np.ndarray, sigma_int: float = SIGMA_INT):
    """Return (coherence, log-energy, theta) of the gradient structure tensor.

    theta is the axial orientation (radians, image coords) of the dominant gradient
    direction; the line (strike) direction is theta + pi/2, identical for cos(2*dtheta)
    agreement between two tensors.
    """
    z = gaussian_filter(_fill(a, fp), 1.0)
    gy, gx = np.gradient(z)
    del z
    jxx = gaussian_filter((gx * gx).astype(np.float32), sigma_int)
    jyy = gaussian_filter((gy * gy).astype(np.float32), sigma_int)
    jxy = gaussian_filter((gx * gy).astype(np.float32), sigma_int)
    del gx, gy
    trace = jxx + jyy
    disc = np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy**2, 0.0))
    coh = np.where(trace > 1e-12, disc / (trace + 1e-12), 0.0).astype(np.float32)
    theta = (0.5 * np.arctan2(2.0 * jxy, jxx - jyy)).astype(np.float32)
    energy = np.log1p(np.maximum(trace, 0.0)).astype(np.float32)
    del jxx, jyy, jxy, trace, disc
    return coh, energy, theta


def _line_kernel(theta_deg: float, half: int) -> np.ndarray:
    size = 2 * half + 1
    k = np.zeros((size, size), np.float32)
    th = np.deg2rad(theta_deg)
    dy, dx = -np.cos(th), np.sin(th)
    for t in np.linspace(-half, half, 8 * size):
        r, c = int(round(half + t * dy)), int(round(half + t * dx))
        if 0 <= r < size and 0 <= c < size:
            k[r, c] = 1.0
    return (k / k.sum()).astype(np.float32)


def line_anisotropy(unit_field: np.ndarray, half: int) -> np.ndarray:
    """Max-over-8-orientations line integral minus orientation mean (anisotropy excess)."""
    acc = np.zeros(unit_field.shape, np.float32)
    mx = np.zeros(unit_field.shape, np.float32)
    for k in range(N_ORIENT):
        resp = fftconvolve(unit_field, _line_kernel(k * 180.0 / N_ORIENT, half), mode="same").astype(np.float32)
        acc += resp
        np.maximum(mx, resp, out=mx)
        del resp
    return (mx - acc / N_ORIENT).astype(np.float32)


def build_kpl_features(cols2d: dict[str, np.ndarray], fp: np.ndarray) -> dict[str, np.ndarray]:
    """Compute the 12 KPL 2-D feature fields from unfolded store columns."""
    step = cols2d["lid_step_max"]
    slope = cols2d["org_det_elev_slope"]
    mag = cols2d["org_tmi_hg"]
    grav = cols2d["org_iso_grav_anom_hg"]
    lid_ok = np.isfinite(cols2d["lid_valid"]) & (cols2d["lid_valid"] > 0.5) & np.isfinite(step)

    out: dict[str, np.ndarray] = {}

    coh_l, en_l, _th_l = structure_tensor(np.where(lid_ok, step, 0.0).astype(np.float32), fp)
    out["kpl_lid_coh3km"] = np.where(lid_ok, coh_l, np.nan).astype(np.float32)
    out["kpl_lid_energy3km"] = np.where(lid_ok, en_l, np.nan).astype(np.float32)
    unit_step = _robust_unit(np.where(lid_ok, step, 0.0), fp)
    line15_l = line_anisotropy(unit_step, 15)
    line25_l = line_anisotropy(unit_step, 25)
    out["kpl_lid_line15"] = np.where(lid_ok, line15_l, np.nan).astype(np.float32)
    out["kpl_lid_line25"] = np.where(lid_ok, line25_l, np.nan).astype(np.float32)
    persist = np.where(lid_ok, line25_l / (line15_l + 0.05), np.nan).astype(np.float32)
    del unit_step, line15_l, line25_l, en_l, _th_l

    coh_s, _en_s, th_s = structure_tensor(slope, fp)
    out["kpl_slope_coh3km"] = coh_s
    out["kpl_slope_line15"] = line_anisotropy(_robust_unit(slope, fp), 15)

    coh_m, _en_m, th_m = structure_tensor(mag, fp)
    out["kpl_mag_coh3km"] = coh_m
    out["kpl_mag_line15"] = line_anisotropy(_robust_unit(mag, fp), 15)

    coh_g, _en_g, _th_g = structure_tensor(grav, fp)
    out["kpl_grav_coh3km"] = coh_g
    del _en_s, _en_m, _en_g, _th_g, coh_g

    agree = np.cos(2.0 * (th_s - th_m)).astype(np.float32)
    out["kpl_xorient_agree"] = (agree * np.minimum(coh_s, coh_m)).astype(np.float32)
    out["kpl_xcoh_product"] = np.where(
        lid_ok, np.sqrt(np.maximum(coh_l, 0.0) * np.maximum(coh_m, 0.0)), np.nan
    ).astype(np.float32)
    out["kpl_persist_ratio"] = persist

    assert tuple(out.keys()) == KPL_FEATURES, f"KPL feature order mismatch: {tuple(out.keys())}"
    return out
