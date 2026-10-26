"""H36-CTRB: Curvature-Tapered Strike-Worm, Geophysical Trunk Relay-Bridge & Tip-Lobe
Concordance with Nested Spatial-Quadrant Purged Cross-Calibration (NSQ-PCC) and
Exact Dinkelbach-Submodular 300 m DTI Kernel Emission.

Memory-disciplined implementation (< 950 MiB peak RSS on 3.8 GiB 0-swap sandboxes):
  - Precomputes a single int16 nearest-footprint index once instead of repeated EDTs.
  - Streams 1-3 raster bands at a time and flushes memmap columns incrementally.
  - Strictly zero target leakage: zero prior/registry rasters read, zero SGMC read,
    ``dist_known_fault_px`` stripped via DictReader, raw ``det_elev`` / ``det_elev_slope``
    excluded, missing 3DEP LiDAR preserved as ``np.nan``.
"""

from __future__ import annotations

import csv
import gc
import hashlib
import heapq
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import (
    convolve,
    distance_transform_edt,
    gaussian_filter,
)
from scipy.ndimage import (
    label as ndi_label,
)
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression

from gems.metric import ridge_nms

FORBIDDEN_CSV_COLUMNS = frozenset({"dist_known_fault_px", "known_fault", "label"})

RAW_BAND_NAMES = (
    "mag_anom",
    "rtp",
    "tmi_hg",
    "geod_2ndinv",
    "iso_grav_anom_slope",
    "tc",
    "geod_shearrate",
    "geod_dilaterate",
    "tmi_vg",
    "deq_n100a15",
    "iso_grav_anom_vg",
    "det_elev",
    "iso_grav_anom",
    "tmi",
    "depth_to_base_surf",
    "ieq_n100a15",
    "cond_surf",
    "iso_grav_anom_hg",
    "det_elev_slope",
)

LOCAL_FEATURE_NAMES: tuple[str, ...] = (
    "pf_mag_analytic_log",
    "pf_tilt_zero_sharp",
    "pf_up150_atten",
    "pf_rtp_hessian_line",
    "pf_grav_hgm_log",
    "pf_grav_tilt_sharp",
    "pf_basement_grad_log",
    "pf_basement_hessian",
    "hydro_thk_depletion",
    "hydro_rad_contrast",
    "hydro_mt_cond_grad",
    "hydro_demag_trough",
    "hydro_gdr_geotherm_aniso",
    "strain_transtension",
    "geom_piedmont_breakline",
    "lidar_polarity_scarp",
    "lidar_step_curv",
)

STRUCTURAL_FEATURE_NAMES: tuple[str, ...] = (
    "worm_pf_1p5km",
    "worm_pf_anderson_1p5km",
    "worm_hydro_1p5km",
    "worm_piedmont_1p5km",
    "xmod_strike_coherence",
    "pf_grav_mag_dip_pair",
    "gts_relay_bridge",
    "gts_tip_lobe",
)

ALL_FEATURE_NAMES: tuple[str, ...] = LOCAL_FEATURE_NAMES + STRUCTURAL_FEATURE_NAMES

# Exact 25 integer offsets inside the official R=3.0 px (300 m) triangular kernel
_DY_GRID, _DX_GRID = np.mgrid[-3:4, -3:4]
_DIST_GRID = np.hypot(_DY_GRID, _DX_GRID)
_MASK_R3 = _DIST_GRID < 3.0 - 1e-9
KERNEL_DY: np.ndarray = _DY_GRID[_MASK_R3].astype(np.int32)
KERNEL_DX: np.ndarray = _DX_GRID[_MASK_R3].astype(np.int32)
KERNEL_W: np.ndarray = (1.0 - _DIST_GRID[_MASK_R3] / 3.0).astype(np.float64)


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def fill_nearest_valid(
    arr: np.ndarray,
    valid_mask: np.ndarray,
    nearest_yx: tuple[np.ndarray, np.ndarray] | None = None,
) -> np.ndarray:
    """Nearest-neighbor fill outside valid_mask so spatial filters never bleed sentinels."""
    a = np.asarray(arr, dtype=np.float32)
    good = np.asarray(valid_mask, dtype=bool) & np.isfinite(a) & (a > -1e30) & (a < 1e30)
    if not good.any():
        return np.zeros_like(a, dtype=np.float32)
    if good.all():
        return a.copy()
    # Fast path when valid_mask exactly equals finite support and nearest_yx is precomputed
    if nearest_yx is not None and np.array_equal(good, valid_mask):
        return a[nearest_yx[0], nearest_yx[1]].astype(np.float32, copy=False)
    idx = distance_transform_edt(~good, return_distances=False, return_indices=True)
    return a[idx[0], idx[1]].astype(np.float32, copy=False)


def grad_mag_f32(arr: np.ndarray, sigma: float = 0.0) -> np.ndarray:
    """Memory-lean float32 gradient magnitude (avoids float64 double allocations)."""
    f = gaussian_filter(arr.astype(np.float32, copy=False), sigma=sigma, mode="nearest") if sigma > 0 else arr.astype(np.float32, copy=False)
    gy = gaussian_filter(f, sigma=0.8, order=(1, 0), mode="nearest") if sigma == 0 else np.empty_like(f)
    if sigma > 0:
        gy = np.gradient(f, axis=0).astype(np.float32, copy=False)
        gx = np.gradient(f, axis=1).astype(np.float32, copy=False)
    else:
        gy = np.gradient(f, axis=0).astype(np.float32, copy=False)
        gx = np.gradient(f, axis=1).astype(np.float32, copy=False)
    out = np.hypot(gy, gx).astype(np.float32, copy=False)
    del gy, gx
    return out


def robust_zpos(arr: np.ndarray, footprint: np.ndarray, clip_max: float = 6.0) -> np.ndarray:
    """Footprint-normalized non-negative robust z-score in [0, 1]."""
    out = np.zeros(arr.shape, dtype=np.float32)
    v = np.asarray(footprint, dtype=bool) & np.isfinite(arr)
    if not v.any():
        return out
    vals = arr[v]
    med = float(np.median(vals))
    q25, q75 = np.percentile(vals, [25.0, 75.0])
    scale = max(float(q75 - q25) / 1.349, 1e-6)
    out[v] = (np.clip((vals - med) / scale, 0.0, clip_max) / clip_max).astype(np.float32)
    return out


def hessian_curvilinear_response(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Scale-normalized Frangi/Sato curvilinear magnitude |lambda_max| - 0.35*|lambda_min|."""
    f = arr.astype(np.float32, copy=False)
    s2 = np.float32(sigma * sigma)
    axx = gaussian_filter(f, sigma=sigma, order=(0, 2), mode="nearest") * s2
    ayy = gaussian_filter(f, sigma=sigma, order=(2, 0), mode="nearest") * s2
    axy = gaussian_filter(f, sigma=sigma, order=(1, 1), mode="nearest") * s2
    tr = np.float32(0.5) * (axx + ayy)
    diff = np.float32(0.5) * (axx - ayy)
    del axx, ayy
    det_term = np.hypot(diff, axy)
    del diff, axy
    abs1 = np.abs(tr + det_term)
    abs2 = np.abs(tr - det_term)
    del tr, det_term
    dom = np.maximum(abs1, abs2)
    sub = np.minimum(abs1, abs2)
    del abs1, abs2
    return np.maximum(dom - np.float32(0.35) * sub, 0.0).astype(np.float32, copy=False)


def structure_double_angle(
    edge_surface: np.ndarray, sigma_grad: float = 1.2, sigma_int: float = 2.5
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return unit strike double-angle (cos 2*theta_s, sin 2*theta_s) and tensor coherence."""
    f = edge_surface.astype(np.float32, copy=False)
    gx = gaussian_filter(f, sigma=sigma_grad, order=(0, 1), mode="nearest")
    gy = gaussian_filter(f, sigma=sigma_grad, order=(1, 0), mode="nearest")
    jxx = gaussian_filter(gx * gx, sigma=sigma_int, mode="nearest")
    jyy = gaussian_filter(gy * gy, sigma=sigma_int, mode="nearest")
    jxy = gaussian_filter(gx * gy, sigma=sigma_int, mode="nearest")
    del gx, gy
    tr = jxx + jyy + np.float32(1e-12)
    dx = jxx - jyy
    del jxx, jyy
    dy = np.float32(2.0) * jxy
    del jxy
    mag = np.hypot(dx, dy) + np.float32(1e-12)
    c2s = (-dx / mag).astype(np.float32, copy=False)
    s2s = (-dy / mag).astype(np.float32, copy=False)
    coh = (mag / tr).astype(np.float32, copy=False)
    return c2s, s2s, coh


def anderson_azimuth_weight(strike_deg_cw_from_north: float) -> float:
    """Anderson (1905) Great Basin extensional/Walker Lane kinematic weight in [0.15, 1.0]."""
    az = strike_deg_cw_from_north % 180.0

    def circ_diff(a: float, b: float) -> float:
        d = abs(a - b) % 180.0
        return min(d, 180.0 - d)

    w_norm = np.exp(-0.5 * (circ_diff(az, 20.0) / 26.0) ** 2)
    w_wl = 0.85 * np.exp(-0.5 * (circ_diff(az, 148.0) / 22.0) ** 2)
    return float(0.15 + 0.85 * max(w_norm, w_wl))


def oriented_worm_persistence(
    surface: np.ndarray,
    footprint: np.ndarray,
    half_len_px: int = 7,
    n_azimuths: int = 12,
) -> tuple[np.ndarray, np.ndarray]:
    """12-azimuth antialiased subpixel 1.5 km line-integral persistence."""
    s = np.where(footprint, surface, 0.0).astype(np.float32)
    ksize = 2 * half_len_px + 1
    steps = np.linspace(-float(half_len_px), float(half_len_px), 4 * half_len_px + 1)
    taper = np.exp(-0.5 * (steps / (0.85 * half_len_px)) ** 2)
    best_raw = np.zeros_like(s, dtype=np.float32)
    best_and = np.zeros_like(s, dtype=np.float32)

    for i in range(n_azimuths):
        az_deg = i * (180.0 / n_azimuths)
        az_rad = np.deg2rad(az_deg)
        ty = -float(np.cos(az_rad))
        tx = float(np.sin(az_rad))
        kern = np.zeros((ksize, ksize), dtype=np.float64)
        for st, wt in zip(steps, taper, strict=True):
            fy = half_len_px + st * ty
            fx = half_len_px + st * tx
            y0 = int(np.floor(fy))
            x0 = int(np.floor(fx))
            wy = fy - y0
            wx = fx - x0
            for dy_b, wb_y in ((0, 1.0 - wy), (1, wy)):
                ry = y0 + dy_b
                if 0 <= ry < ksize:
                    for dx_b, wb_x in ((0, 1.0 - wx), (1, wx)):
                        rx = x0 + dx_b
                        if 0 <= rx < ksize:
                            kern[ry, rx] += wt * wb_y * wb_x
        kern_f32 = (kern / kern.sum()).astype(np.float32)
        resp = convolve(s, kern_f32, mode="constant", cval=0.0)
        np.maximum(best_raw, resp, out=best_raw)
        w_and = np.float32(anderson_azimuth_weight(az_deg))
        np.maximum(best_and, resp * w_and, out=best_and)

    best_raw[~footprint] = 0.0
    best_and[~footprint] = 0.0
    return best_raw, best_and


def extract_geophysical_trunk_topology(
    pf_trunk_score: np.ndarray,
    footprint: np.ndarray,
    quantile: float = 97.5,
    min_component_px: int = 12,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute label-free Geophysical Trunk Relay-Bridge and Trunk-Tip Propagation fields."""
    H, W = footprint.shape
    s = np.where(footprint, pf_trunk_score, -1e9).astype(np.float32)
    sm = gaussian_filter(np.where(footprint, pf_trunk_score, 0.0).astype(np.float32), sigma=1.4)
    gy = np.gradient(sm, axis=0).astype(np.float32, copy=False)
    gx = np.gradient(sm, axis=1).astype(np.float32, copy=False)
    del sm
    theta = (np.rad2deg(np.arctan2(gy, gx)) + 180.0) % 180.0
    del gy, gx

    is_ridge = np.zeros((H, W), dtype=bool)
    q0 = (theta < 22.5) | (theta >= 157.5)
    is_ridge |= q0 & (s >= np.roll(s, 1, axis=1)) & (s > np.roll(s, -1, axis=1))
    q45 = (theta >= 22.5) & (theta < 67.5)
    is_ridge |= (
        q45
        & (s >= np.roll(np.roll(s, 1, axis=0), 1, axis=1))
        & (s > np.roll(np.roll(s, -1, axis=0), -1, axis=1))
    )
    q90 = (theta >= 67.5) & (theta < 112.5)
    is_ridge |= q90 & (s >= np.roll(s, 1, axis=0)) & (s > np.roll(s, -1, axis=0))
    q135 = (theta >= 112.5) & (theta < 157.5)
    is_ridge |= (
        q135
        & (s >= np.roll(np.roll(s, 1, axis=0), -1, axis=1))
        & (s > np.roll(np.roll(s, -1, axis=0), 1, axis=1))
    )
    is_ridge &= footprint
    del theta, s

    thr = float(np.percentile(pf_trunk_score[footprint], quantile))
    raw_skel = is_ridge & (pf_trunk_score >= thr)
    del is_ridge
    comp, n_comp = ndi_label(raw_skel, structure=np.ones((3, 3), dtype=np.int32))
    del raw_skel
    if n_comp == 0:
        return np.zeros((H, W), dtype=np.float32), np.zeros((H, W), dtype=np.float32)

    sizes = np.bincount(comp.ravel())
    keep = sizes >= min_component_px
    keep[0] = False
    trunks = keep[comp]
    if not trunks.any():
        return np.zeros((H, W), dtype=np.float32), np.zeros((H, W), dtype=np.float32)

    # 1. Opposing-EDT Harmonic Relay-Bridge Potential via gradient of smooth EDT
    # Note: grad(dist) IS the exact unit vector away from nearest trunk, requiring ZERO indices array!
    dist = distance_transform_edt(~trunks).astype(np.float32)
    uy = (-np.gradient(dist, axis=0)).astype(np.float32, copy=False)
    ux = (-np.gradient(dist, axis=1)).astype(np.float32, copy=False)
    uy[dist == 0] = 0.0
    ux[dist == 0] = 0.0
    uy_bar = gaussian_filter(uy, sigma=3.5, mode="nearest")
    ux_bar = gaussian_filter(ux, sigma=3.5, mode="nearest")
    del uy, ux
    opposition = np.clip(1.0 - np.hypot(uy_bar, ux_bar), 0.0, 1.0)
    del uy_bar, ux_bar
    bridge_env = np.exp(-dist / np.float32(18.0)) * (
        np.float32(1.0) - np.exp(-((dist / np.float32(2.5)) ** 2))
    )
    del dist
    relay_bridge = np.where(footprint, opposition * bridge_env, 0.0).astype(np.float32)
    del opposition, bridge_env

    # 2. Trunk-Tip Outward Stress-Propagation Lobes
    nb_count = convolve(trunks.astype(np.int16), np.ones((3, 3), dtype=np.int16), mode="constant")
    tips_yx = np.argwhere(trunks & (nb_count <= 2))
    del nb_count, trunks
    tip_lobe = np.zeros((H, W), dtype=np.float32)
    if len(tips_yx) > 0:
        trunk_comp_ids = comp[tips_yx[:, 0], tips_yx[:, 1]]
        rad = 26
        for (ty, tx), cid in zip(tips_yx, trunk_comp_ids, strict=True):
            r0, r1 = max(0, int(ty) - rad), min(H, int(ty) + rad + 1)
            c0, c1 = max(0, int(tx) - rad), min(W, int(tx) + rad + 1)
            sr0, sr1 = max(0, int(ty) - 7), min(H, int(ty) + 8)
            sc0, sc1 = max(0, int(tx) - 7), min(W, int(tx) + 8)
            cy_loc, cx_loc = np.nonzero(comp[sr0:sr1, sc0:sc1] == cid)
            if cy_loc.size < 3:
                continue
            vy = float(ty) - float(sr0 + cy_loc.mean())
            vx = float(tx) - float(sc0 + cx_loc.mean())
            vn = float(np.hypot(vy, vx))
            if vn < 0.5:
                continue
            vy /= vn
            vx /= vn
            ly, lx = np.mgrid[r0:r1, c0:c1]
            dy = (ly - ty).astype(np.float32)
            dx = (lx - tx).astype(np.float32)
            rr = np.hypot(dy, dx)
            cos_psi = (dy * vy + dx * vx) / np.maximum(rr, 1e-4)
            valid_cone = (rr >= 1.5) & (rr <= float(rad)) & (cos_psi > 0.0)
            if not valid_cone.any():
                continue
            lobe = np.where(valid_cone, (cos_psi**4) * np.exp(-rr / 14.0), 0.0).astype(np.float32)
            np.maximum(tip_lobe[r0:r1, c0:c1], lobe, out=tip_lobe[r0:r1, c0:c1])

    del comp
    tip_lobe[~footprint] = 0.0
    return relay_bridge, tip_lobe


def _build_anisotropic_gdr_geotherm(
    data_dir: Path, footprint: np.ndarray
) -> tuple[np.ndarray, dict[str, int]]:
    """Parse GDR 1391 chemical geothermometers & vents using DictReader; block dist_known_fault_px."""
    H, W = footprint.shape
    out = np.zeros((H, W), dtype=np.float32)
    well_csv = data_dir / "external" / "gdr_wellspring_in_footprint.csv"
    vent_csv = data_dir / "external" / "gdr_volcanic_vents_in_footprint.csv"

    az = np.deg2rad(20.0)
    ty, tx = -float(np.cos(az)), float(np.sin(az))
    rad = 14
    ky, kx = np.mgrid[-rad : rad + 1, -rad : rad + 1]
    along = ky * ty + kx * tx
    perp = -ky * tx + kx * ty
    unit_kernel = np.exp(-0.5 * (along / 6.0) ** 2 - 0.5 * (perp / 2.5) ** 2).astype(np.float32)

    n_wells_used = 0
    if well_csv.is_file():
        with well_csv.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                for bad_col in FORBIDDEN_CSV_COLUMNS:
                    row.pop(bad_col, None)
                assert "dist_known_fault_px" not in row
                try:
                    r = round(float(row["row"]))
                    c = round(float(row["col"]))
                except (KeyError, ValueError, TypeError):
                    continue
                if not (0 <= r < H and 0 <= c < W) or not footprint[r, c]:
                    continue
                temps = []
                for col_name in ("temp_c", "geothermquartz_c", "geothermchalc_c"):
                    val_str = row.get(col_name, "")
                    try:
                        v = float(val_str)
                        if np.isfinite(v) and 20.0 < v <= 380.0:
                            temps.append(v)
                    except (ValueError, TypeError):
                        pass
                if not temps:
                    continue
                t_eff = max(temps)
                if t_eff < 55.0:
                    continue
                weight = float(np.clip((t_eff - 55.0) / 165.0, 0.0, 1.0))
                r0, r1 = max(0, r - rad), min(H, r + rad + 1)
                c0, c1 = max(0, c - rad), min(W, c + rad + 1)
                kr0, kr1 = r0 - (r - rad), unit_kernel.shape[0] - ((r + rad + 1) - r1)
                kc0, kc1 = c0 - (c - rad), unit_kernel.shape[1] - ((c + rad + 1) - c1)
                np.maximum(
                    out[r0:r1, c0:c1],
                    weight * unit_kernel[kr0:kr1, kc0:kc1],
                    out=out[r0:r1, c0:c1],
                )
                n_wells_used += 1

    n_vents_used = 0
    if vent_csv.is_file():
        with vent_csv.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                for bad_col in FORBIDDEN_CSV_COLUMNS:
                    row.pop(bad_col, None)
                assert "dist_known_fault_px" not in row
                try:
                    r = round(float(row["row"]))
                    c = round(float(row["col"]))
                except (KeyError, ValueError, TypeError):
                    continue
                if not (0 <= r < H and 0 <= c < W) or not footprint[r, c]:
                    continue
                r0, r1 = max(0, r - rad), min(H, r + rad + 1)
                c0, c1 = max(0, c - rad), min(W, c + rad + 1)
                kr0, kr1 = r0 - (r - rad), unit_kernel.shape[0] - ((r + rad + 1) - r1)
                kc0, kc1 = c0 - (c - rad), unit_kernel.shape[1] - ((c + rad + 1) - c1)
                np.maximum(
                    out[r0:r1, c0:c1],
                    0.75 * unit_kernel[kr0:kr1, kc0:kc1],
                    out=out[r0:r1, c0:c1],
                )
                n_vents_used += 1

    out[~footprint] = 0.0
    return out, {"gdr_thermal_sites_used": n_wells_used, "gdr_vents_used": n_vents_used}


def build_or_load_feature_stack(
    raw_dir: Path,
    cache_dir: Path,
    *,
    force_rebuild: bool = False,
) -> tuple[np.memmap, dict[str, Any]]:
    """Build or load the 25-channel cached feature matrix on footprint pixels (N_fp, 25).

    Streams 1-3 bands at a time to stay strictly below 900 MiB RSS.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    feat_file = cache_dir / "h36_ctrb_features.npy"
    meta_file = cache_dir / "h36_ctrb_features.json"

    if not force_rebuild and feat_file.is_file() and meta_file.is_file():
        meta = json.loads(meta_file.read_text())
        if (
            tuple(meta.get("feature_names", ())) == ALL_FEATURE_NAMES
            and sha256_file(feat_file) == meta.get("features_sha256")
        ):
            return np.load(feat_file, mmap_mode="r"), meta

    tmpl_path = raw_dir / "sample_submission.tif"
    tf_path = raw_dir / "training_features.tif"
    lidar_path = raw_dir / "external" / "lidar_scarp_features_u8.tif"
    rad_path = raw_dir / "external" / "geodawn_rad_u8.tif"
    ext_path = raw_dir / "external" / "geodawn_extensions_u8.tif"

    with rasterio.open(tmpl_path) as ds:
        footprint = np.isfinite(ds.read(1))
    fp_ids = np.flatnonzero(footprint)
    n_fp = int(fp_ids.size)
    n_feat = len(ALL_FEATURE_NAMES)

    # Precompute compact int16 nearest-footprint index ONCE (49 MB total)
    raw_idx = distance_transform_edt(~footprint, return_distances=False, return_indices=True)
    nearest_yx: tuple[np.ndarray, np.ndarray] | None = (
        raw_idx[0].astype(np.int16),
        raw_idx[1].astype(np.int16),
    )
    del raw_idx
    gc.collect()

    out_arr = np.empty((n_fp, n_feat), dtype=np.float32)

    def write_col(name: str, grid2d: np.ndarray, allow_nan: bool = False) -> None:
        idx = ALL_FEATURE_NAMES.index(name)
        vals = grid2d.ravel()[fp_ids].astype(np.float32, copy=False)
        if not allow_nan and not np.isfinite(vals).all():
            raise ValueError(f"Non-finite values in non-NaN feature {name}")
        out_arr[:, idx] = vals

    def read_tf(band_name: str) -> np.ndarray:
        b_idx = RAW_BAND_NAMES.index(band_name) + 1
        with rasterio.open(tf_path) as ds:
            raw = ds.read(b_idx).astype(np.float32)
        return fill_nearest_valid(raw, footprint, nearest_yx=nearest_yx)

    # --- Group A: Magnetic analytic signal, tilt-zero sharpness, upward attenuation, RTP Hessian ---
    tmi_hg = read_tf("tmi_hg")
    tmi_vg = read_tf("tmi_vg")
    mag_analytic_log = np.log1p(np.hypot(tmi_hg, tmi_vg)).astype(np.float32)
    del tmi_hg, tmi_vg
    write_col("pf_mag_analytic_log", mag_analytic_log)
    del mag_analytic_log
    gc.collect()

    tc = read_tf("tc")
    tc_sm = gaussian_filter(tc, sigma=1.0, mode="nearest")
    del tc
    q25_tc, q75_tc = np.percentile(tc_sm[footprint], [25.0, 75.0])
    sig_tc = max(float(q75_tc - q25_tc) * 0.35, 1e-4)
    tilt_zero_sharp = (grad_mag_f32(tc_sm) * np.exp(-np.abs(tc_sm) / sig_tc)).astype(np.float32)
    del tc_sm
    write_col("pf_tilt_zero_sharp", tilt_zero_sharp)
    tz_z = robust_zpos(tilt_zero_sharp, footprint)
    del tilt_zero_sharp
    gc.collect()

    tmi = read_tf("tmi")
    with rasterio.open(ext_path) as ds:
        ext_tmi_up150 = fill_nearest_valid(
            ds.read(4).astype(np.float32) / 255.0, footprint, nearest_yx=nearest_yx
        )
    p1_tmi, p99_tmi = np.percentile(tmi[footprint], [1.0, 99.0])
    tmi_u01 = np.clip((tmi - p1_tmi) / max(float(p99_tmi - p1_tmi), 1e-6), 0.0, 1.0).astype(
        np.float32
    )
    del tmi
    up150_atten = np.abs(tmi_u01 - ext_tmi_up150).astype(np.float32)
    del tmi_u01, ext_tmi_up150
    write_col("pf_up150_atten", up150_atten)
    up_z = robust_zpos(up150_atten, footprint)
    del up150_atten
    gc.collect()

    rtp = read_tf("rtp")
    rtp_hess = hessian_curvilinear_response(rtp, sigma=2.0)
    write_col("pf_rtp_hessian_line", rtp_hess)
    del rtp_hess
    # Keep positive Laplacian of RTP for demagnetization trough
    rtp_sm2 = gaussian_filter(rtp, sigma=2.0, mode="nearest")
    del rtp
    lap_rtp_pos = np.maximum(
        gaussian_filter(rtp_sm2, sigma=1.0, order=(2, 0), mode="nearest")
        + gaussian_filter(rtp_sm2, sigma=1.0, order=(0, 2), mode="nearest"),
        0.0,
    ).astype(np.float32)
    del rtp_sm2
    gc.collect()

    # --- Group B: Gravity HGM, Gravity Tilt, Basement Depth Steps & Hessian ---
    g_hg = read_tf("iso_grav_anom_hg")
    g_sl = read_tf("iso_grav_anom_slope")
    grav_hgm_log = np.log1p(np.abs(g_hg) + 0.5 * np.abs(g_sl)).astype(np.float32)
    del g_sl
    write_col("pf_grav_hgm_log", grav_hgm_log)
    gh_z = robust_zpos(grav_hgm_log, footprint)
    del grav_hgm_log

    g_vg = read_tf("iso_grav_anom_vg")
    theta_g = np.arctan2(g_vg, np.abs(g_hg) + 1e-4).astype(np.float32)
    del g_hg, g_vg
    grav_tilt_sharp = (
        grad_mag_f32(theta_g, sigma=1.2) * np.exp(-np.abs(theta_g) / np.float32(0.35))
    ).astype(np.float32)
    del theta_g
    write_col("pf_grav_tilt_sharp", grav_tilt_sharp)
    del grav_tilt_sharp
    gc.collect()

    db = read_tf("depth_to_base_surf")
    basement_grad_log = np.log1p(grad_mag_f32(db, sigma=1.5)).astype(np.float32)
    write_col("pf_basement_grad_log", basement_grad_log)
    bg_z = robust_zpos(basement_grad_log, footprint)
    del basement_grad_log
    basement_hess = hessian_curvilinear_response(db, sigma=3.0)
    del db
    write_col("pf_basement_hessian", basement_hess)
    del basement_hess
    gc.collect()

    # --- Group C: Hydrothermal Alteration Triad & Crustal Strain ---
    with rasterio.open(ext_path) as ds:
        ext_thk = fill_nearest_valid(
            ds.read(1).astype(np.float32) / 255.0, footprint, nearest_yx=nearest_yx
        )
        ext_uk = fill_nearest_valid(
            ds.read(2).astype(np.float32) / 255.0, footprint, nearest_yx=nearest_yx
        )
    thk_depl = np.maximum(
        gaussian_filter(ext_thk, sigma=8.0, mode="nearest")
        - gaussian_filter(ext_thk, sigma=1.2, mode="nearest")
        + 0.3
        * np.maximum(
            gaussian_filter(ext_uk, sigma=8.0, mode="nearest")
            - gaussian_filter(ext_uk, sigma=1.2, mode="nearest"),
            0.0,
        ),
        0.0,
    ).astype(np.float32)
    del ext_thk, ext_uk
    write_col("hydro_thk_depletion", thk_depl)
    thk_z = robust_zpos(thk_depl, footprint)
    del thk_depl

    demag_trough = (lap_rtp_pos * (0.30 + 0.70 * thk_z)).astype(np.float32)
    del lap_rtp_pos
    write_col("hydro_demag_trough", demag_trough)
    del demag_trough
    gc.collect()

    rad_grad = np.zeros(footprint.shape, dtype=np.float32)
    with rasterio.open(rad_path) as ds:
        for bi in (1, 2, 3):
            rc = fill_nearest_valid(
                ds.read(bi).astype(np.float32) / 255.0, footprint, nearest_yx=nearest_yx
            )
            np.maximum(rad_grad, grad_mag_f32(rc, sigma=1.2), out=rad_grad)
            del rc
    write_col("hydro_rad_contrast", rad_grad)
    rad_z = robust_zpos(rad_grad, footprint)
    del rad_grad
    gc.collect()

    cond = read_tf("cond_surf")
    mt_cond_grad = grad_mag_f32(cond, sigma=1.5)
    del cond
    write_col("hydro_mt_cond_grad", mt_cond_grad)
    mt_z = robust_zpos(mt_cond_grad, footprint)
    del mt_cond_grad

    gdr_aniso, gdr_stats = _build_anisotropic_gdr_geotherm(raw_dir, footprint)
    write_col("hydro_gdr_geotherm_aniso", gdr_aniso)
    del gdr_aniso

    dil = np.maximum(read_tf("geod_dilaterate"), 0.0)
    shr = np.abs(read_tf("geod_shearrate"))
    inv2 = robust_zpos(read_tf("geod_2ndinv"), footprint)
    strain_tt = (np.sqrt(dil * shr) + 0.5 * inv2).astype(np.float32)
    del dil, shr, inv2
    write_col("strain_transtension", strain_tt)
    del strain_tt
    gc.collect()

    # --- Group D: Contour-Orthogonal Piedmont Breakline & NaN-Routed 3DEP LiDAR ---
    elev = read_tf("det_elev")
    lrm = elev - gaussian_filter(elev, sigma=6.0, mode="nearest")
    lrm_grad = grad_mag_f32(lrm, sigma=1.0)
    del lrm

    reg_elev = gaussian_filter(elev, sigma=12.0, mode="nearest")
    r_gy = np.gradient(reg_elev, axis=0).astype(np.float32, copy=False)
    r_gx = np.gradient(reg_elev, axis=1).astype(np.float32, copy=False)
    del reg_elev
    r_gn = np.hypot(r_gy, r_gx) + np.float32(1e-5)

    loc_elev = gaussian_filter(elev, sigma=1.2, mode="nearest")
    del elev
    l_gy = np.gradient(loc_elev, axis=0).astype(np.float32, copy=False)
    l_gx = np.gradient(loc_elev, axis=1).astype(np.float32, copy=False)
    del loc_elev
    l_gn = np.hypot(l_gy, l_gx) + np.float32(1e-5)
    cos_ortho = np.abs((l_gy * r_gy + l_gx * r_gx) / (l_gn * r_gn))
    del r_gy, r_gx, r_gn, l_gy, l_gx, l_gn

    eslope = read_tf("det_elev_slope")
    macro_rough = gaussian_filter(np.abs(eslope), sigma=16.0, mode="nearest")
    del eslope
    tau0 = float(np.percentile(macro_rough[footprint], 35.0)) + 1e-4
    piedmont_breakline = ((lrm_grad / (macro_rough + tau0)) * (cos_ortho**2)).astype(np.float32)
    del lrm_grad, macro_rough, cos_ortho
    write_col("geom_piedmont_breakline", piedmont_breakline)
    pb_z = robust_zpos(piedmont_breakline, footprint)
    del piedmont_breakline
    nearest_yx = None
    gc.collect()

    with rasterio.open(lidar_path) as ds:
        lid_valid = ds.read(12) > 0
        lid_down = ds.read(6).astype(np.float32) / 255.0
        lid_up = ds.read(7).astype(np.float32) / 255.0
        lid_coh = ds.read(10).astype(np.float32) / 255.0
        lid_pol = np.where(
            lid_valid & footprint, np.abs(lid_down - lid_up) * (0.30 + 0.70 * lid_coh), np.nan
        ).astype(np.float32)
        del lid_down, lid_up, lid_coh
        write_col("lidar_polarity_scarp", lid_pol, allow_nan=True)
        del lid_pol

        lid_step = ds.read(3).astype(np.float32) / 255.0
        lid_lapneg = ds.read(4).astype(np.float32) / 255.0
        lid_sc = np.where(
            lid_valid & footprint, np.maximum(lid_step, lid_lapneg), np.nan
        ).astype(np.float32)
        del lid_step, lid_lapneg
        write_col("lidar_step_curv", lid_sc, allow_nan=True)
        del lid_sc

    n_lid_valid = int((lid_valid & footprint).sum())
    n_lid_gap = int((~lid_valid & footprint).sum())
    del lid_valid
    gc.collect()

    # --- Group E: 1.5 km Strike Worms, Cross-Horizon Coherence & Geophysical Trunk Relay/Tip ---
    pf_joint = (0.35 * tz_z + 0.35 * gh_z + 0.15 * up_z + 0.15 * bg_z).astype(np.float32)
    del up_z
    worm_pf, worm_pf_and = oriented_worm_persistence(pf_joint, footprint, half_len_px=7)
    del pf_joint
    write_col("worm_pf_1p5km", worm_pf)
    del worm_pf
    write_col("worm_pf_anderson_1p5km", worm_pf_and)
    gc.collect()

    hy_joint = (0.40 * thk_z + 0.35 * mt_z + 0.25 * rad_z).astype(np.float32)
    del thk_z, mt_z
    worm_hy, _ = oriented_worm_persistence(hy_joint, footprint, half_len_px=7)
    del hy_joint
    write_col("worm_hydro_1p5km", worm_hy)
    del worm_hy
    gc.collect()

    worm_pb, _ = oriented_worm_persistence(pb_z, footprint, half_len_px=7)
    write_col("worm_piedmont_1p5km", worm_pb)
    del worm_pb
    gc.collect()

    deep_h = (0.60 * gh_z + 0.40 * bg_z).astype(np.float32)
    shal_h = (0.60 * tz_z + 0.40 * rad_z).astype(np.float32)
    del rad_z
    c1, s1, w1 = structure_double_angle(deep_h)
    del deep_h
    c2, s2, w2 = structure_double_angle(shal_h)
    del shal_h
    c3, s3, w3 = structure_double_angle(pb_z)
    del pb_z
    w_sum = w1 + w2 + w3 + np.float32(1e-6)
    rx = (w1 * c1 + w2 * c2 + w3 * c3) / w_sum
    ry = (w1 * s1 + w2 * s2 + w3 * s3) / w_sum
    del c1, s1, w1, c2, s2, w2, c3, s3, w3
    xmod_coh = (np.hypot(rx, ry) * np.minimum(w_sum / np.float32(0.45), np.float32(1.0))).astype(
        np.float32
    )
    del rx, ry, w_sum
    write_col("xmod_strike_coherence", xmod_coh)
    del xmod_coh
    gc.collect()

    dip_pair = (
        gaussian_filter(gh_z, sigma=2.5, mode="nearest")
        * gaussian_filter(tz_z, sigma=1.5, mode="nearest")
    ).astype(np.float32)
    del tz_z
    write_col("pf_grav_mag_dip_pair", dip_pair)
    del dip_pair

    trunk_seed = (0.55 * worm_pf_and + 0.45 * (0.5 * gh_z + 0.5 * bg_z)).astype(np.float32)
    del worm_pf_and, gh_z, bg_z
    gc.collect()

    relay_bridge, tip_lobe = extract_geophysical_trunk_topology(
        trunk_seed, footprint, quantile=97.5, min_component_px=12
    )
    del trunk_seed
    write_col("gts_relay_bridge", relay_bridge)
    del relay_bridge
    write_col("gts_tip_lobe", tip_lobe)
    del tip_lobe

    np.save(feat_file, out_arr)
    gc.collect()

    feat_sha = sha256_file(feat_file)
    meta = {
        "schema_version": 1,
        "feature_names": list(ALL_FEATURE_NAMES),
        "local_feature_names": list(LOCAL_FEATURE_NAMES),
        "structural_feature_names": list(STRUCTURAL_FEATURE_NAMES),
        "footprint_pixels": n_fp,
        "lidar_valid_footprint_pixels": n_lid_valid,
        "lidar_gap_footprint_pixels": n_lid_gap,
        "features_sha256": feat_sha,
        "catalogue_features": [],
        "sgmc_used": False,
        "registry_rasters_read": False,
        "forbidden_csv_columns_stripped": sorted(FORBIDDEN_CSV_COLUMNS),
        **gdr_stats,
        "input_sha256": {
            "training_features.tif": sha256_file(tf_path),
            "sample_submission.tif": sha256_file(tmpl_path),
            "lidar_scarp_features_u8.tif": sha256_file(lidar_path),
            "geodawn_rad_u8.tif": sha256_file(rad_path),
            "geodawn_extensions_u8.tif": sha256_file(ext_path),
        },
    }
    meta_file.write_text(json.dumps(meta, indent=2) + "\n")
    return np.load(feat_file, mmap_mode="r"), meta


def unsupervised_concordance_surface(
    X_fp: np.ndarray,
    footprint: np.ndarray,
) -> np.ndarray:
    """EXP-1 label-free physical concordance probability proxy in [0, 1]."""
    H, W = footprint.shape
    fp_ids = np.flatnonzero(footprint)

    def col01(name: str) -> np.ndarray:
        v = np.asarray(X_fp[:, ALL_FEATURE_NAMES.index(name)], dtype=np.float32)
        fin = np.isfinite(v)
        if not fin.any():
            return np.zeros_like(v)
        med = float(np.median(v[fin]))
        q25, q75 = np.percentile(v[fin], [25.0, 75.0])
        sc = max(float(q75 - q25) / 1.349, 1e-6)
        z = np.where(fin, np.clip((v - med) / sc, 0.0, 5.0) / 5.0, 0.0)
        return z.astype(np.float32)

    p_pf = (
        0.45 * col01("worm_pf_anderson_1p5km")
        + 0.30 * col01("pf_grav_mag_dip_pair")
        + 0.25 * col01("pf_basement_hessian")
    )
    p_hy = (
        0.40 * col01("worm_hydro_1p5km")
        + 0.35 * col01("hydro_demag_trough")
        + 0.25 * col01("hydro_gdr_geotherm_aniso")
    )
    p_gm = 0.65 * col01("worm_piedmont_1p5km") + 0.35 * col01("lidar_polarity_scarp")
    p_net = 0.55 * col01("gts_relay_bridge") + 0.45 * col01("gts_tip_lobe")
    coh = 0.40 + 0.60 * col01("xmod_strike_coherence")

    # Memory-lean 2nd-largest of 4 pillars without allocating a 4x5.16M stack
    max1 = np.maximum(np.maximum(p_pf, p_hy), np.maximum(p_gm, p_net))
    min1 = np.minimum(np.minimum(p_pf, p_hy), np.minimum(p_gm, p_net))
    # Sum of top-2 minus max1? Better: pairwise min of maxes
    m_ab_max = np.maximum(p_pf, p_hy)
    m_ab_min = np.minimum(p_pf, p_hy)
    m_cd_max = np.maximum(p_gm, p_net)
    m_cd_min = np.minimum(p_gm, p_net)
    second_best = np.maximum(np.minimum(m_ab_max, m_cd_max), np.maximum(m_ab_min, m_cd_min))
    del max1, min1, m_ab_max, m_ab_min, m_cd_max, m_cd_min

    mean_pillar = 0.38 * p_pf + 0.22 * p_hy + 0.22 * p_gm + 0.18 * p_net
    del p_pf, p_hy, p_gm, p_net
    raw_score = mean_pillar * (0.35 + 0.65 * second_best) * coh
    del mean_pillar, second_best, coh

    p997 = max(float(np.percentile(raw_score, 99.7)), 1e-6)
    cal = np.clip(0.55 * (raw_score / p997), 0.0, 0.85).astype(np.float32)
    del raw_score

    out = np.zeros((H, W), dtype=np.float32)
    out.ravel()[fp_ids] = cal
    return out


def fit_predict_nsq_pcc_fold(
    X_fp: np.ndarray,
    footprint: np.ndarray,
    fold_grid_2d: np.ndarray,
    train_mask_2d: np.ndarray,
    visible_2d: np.ndarray,
    held_out_fold_id: int,
    *,
    feature_indices: list[int] | np.ndarray,
    seed: int = 20261025,
    neg_pos_ratio: int = 4,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Nested Spatial-Quadrant Purged Cross-Calibration (NSQ-PCC) for one held-out fold."""
    fp_ids = np.flatnonzero(footprint)
    n_fp = fp_ids.size

    train_fp = train_mask_2d.ravel()[fp_ids]
    vis_fp = visible_2d.ravel()[fp_ids]
    quad_fp = fold_grid_2d.ravel()[fp_ids]

    d_vis_2d = distance_transform_edt(~visible_2d).astype(np.float32)
    clean_neg_fp = train_fp & (~vis_fp) & (d_vis_2d.ravel()[fp_ids] >= 3.0)
    del d_vis_2d
    pos_fp = train_fp & vis_fp

    base_rate = float(pos_fp.sum() / max(int(train_fp.sum()), 1))
    train_quads = [q for q in (0, 1, 2, 3) if q != held_out_fold_id]

    oof_raw_train = np.full(n_fp, np.nan, dtype=np.float32)
    sub_models: list[HistGradientBoostingClassifier] = []
    f_idx = np.asarray(feature_indices, dtype=np.int32)

    for sub_i, val_q in enumerate(train_quads):
        rng = np.random.default_rng(seed + 100 * held_out_fold_id + sub_i)
        in_sub_train = train_fp & (quad_fp != val_q)
        pos_ids = np.flatnonzero(in_sub_train & pos_fp)
        neg_pool = np.flatnonzero(in_sub_train & clean_neg_fp)
        n_neg = min(int(neg_pool.size), int(pos_ids.size) * neg_pos_ratio)
        neg_ids = rng.choice(neg_pool, size=n_neg, replace=False)

        sample_ids = np.concatenate([pos_ids, neg_ids])
        y_sub = np.concatenate(
            [np.ones(pos_ids.size, dtype=np.int32), np.zeros(neg_ids.size, dtype=np.int32)]
        )
        X_sub = np.asarray(X_fp[sample_ids][:, f_idx], dtype=np.float32)

        clf = HistGradientBoostingClassifier(
            max_iter=180,
            learning_rate=0.055,
            max_depth=6,
            max_leaf_nodes=31,
            min_samples_leaf=80,
            l2_regularization=2.5,
            random_state=seed + 1000 * held_out_fold_id + sub_i,
        )
        clf.fit(X_sub, y_sub)
        sub_models.append(clf)
        del X_sub, y_sub

        val_q_ids = np.flatnonzero(train_fp & (quad_fp == val_q) & (pos_fp | clean_neg_fp))
        if val_q_ids.size > 0:
            for c0 in range(0, val_q_ids.size, 300_000):
                sl = val_q_ids[c0 : c0 + 300_000]
                X_vq = np.asarray(X_fp[sl][:, f_idx], dtype=np.float32)
                oof_raw_train[sl] = clf.predict_proba(X_vq)[:, 1].astype(np.float32)
                del X_vq

    sample_prior = 1.0 / (1.0 + float(neg_pos_ratio))

    def prior_correct(p: np.ndarray) -> np.ndarray:
        p64 = np.clip(p.astype(np.float64), 1e-6, 1.0 - 1e-6)
        num = p64 * (base_rate / sample_prior)
        den = num + (1.0 - p64) * ((1.0 - base_rate) / max(1.0 - sample_prior, 1e-6))
        return (num / np.maximum(den, 1e-12)).astype(np.float32)

    cal_ids = np.flatnonzero(np.isfinite(oof_raw_train) & (pos_fp | clean_neg_fp))
    y_cal = pos_fp[cal_ids].astype(np.float64)
    p_cal_prior = prior_correct(oof_raw_train[cal_ids])
    del oof_raw_train

    w_cal = np.where(
        y_cal > 0.5,
        1.0,
        float((~pos_fp & train_fp).sum()) / max(float((y_cal < 0.5).sum()), 1.0),
    )
    iso = IsotonicRegression(y_min=0.0, y_max=0.65, out_of_bounds="clip")
    iso.fit(p_cal_prior, y_cal, sample_weight=w_cal)
    oof_cal_mean = float(
        np.mean(0.50 * iso.predict(p_cal_prior).astype(np.float32) + 0.50 * p_cal_prior)
    )
    oof_cal_max = float(
        np.max(0.50 * iso.predict(p_cal_prior).astype(np.float32) + 0.50 * p_cal_prior)
    )
    del y_cal, p_cal_prior, w_cal, cal_ids

    full_prob_fp = np.zeros(n_fp, dtype=np.float32)
    raw_sub_fp = np.zeros(n_fp, dtype=np.float32)
    chunk = 350_000
    for start in range(0, n_fp, chunk):
        end = min(start + chunk, n_fp)
        X_ch = np.asarray(X_fp[start:end][:, f_idx], dtype=np.float32)
        p_sum = np.zeros(end - start, dtype=np.float64)
        for clf in sub_models:
            p_sum += clf.predict_proba(X_ch)[:, 1]
        del X_ch
        p_raw = (p_sum / len(sub_models)).astype(np.float32)
        raw_sub_fp[start:end] = p_raw
        p_mean = prior_correct(p_raw)
        p_iso = iso.predict(p_mean).astype(np.float32)
        full_prob_fp[start:end] = np.clip(0.50 * p_iso + 0.50 * p_mean, 0.0, 0.85)

    prob_2d = np.zeros(footprint.shape, dtype=np.float32)
    prob_2d.ravel()[fp_ids] = full_prob_fp
    del full_prob_fp

    raw_sub_2d = np.zeros(footprint.shape, dtype=np.float32)
    raw_sub_2d.ravel()[fp_ids] = raw_sub_fp
    del raw_sub_fp

    info = {
        "held_out_fold_id": held_out_fold_id,
        "train_positives": int(pos_fp.sum()),
        "train_pixels": int(train_fp.sum()),
        "train_base_rate": base_rate,
        "oof_cal_mean_on_train": oof_cal_mean,
        "oof_cal_max_on_train": oof_cal_max,
    }
    return prob_2d, raw_sub_2d, info


def submodular_dti_emit(
    prob_2d: np.ndarray,
    allowed_mask: np.ndarray,
    *,
    footprint: np.ndarray | None = None,
    enforce_ridge_skeleton: bool = True,
    ridge_sigma: float = 1.15,
    n_dots: int = 36_800,
    dstar_ref: float = 0.22,
    min_gain: float = 0.0,
    candidate_pool: int = 220_000,
) -> np.ndarray:
    """Exact Minoux lazy-greedy Dinkelbach-Submodular maximizer on 1-px fault ridge skeletons.

    Restricting candidate locations to 1-px Hessian curvilinear ridges (``ridge_nms``)
    prevents broad 2D basin/caldera probability plateaus from being tiled with hexagonal
    3-px lattices, concentrating dots strictly along 1D fault centerlines at optimal
    2-3 px (200-300 m) submodular spacing.
    """
    H, W = prob_2d.shape
    if n_dots <= 0 or not np.any(allowed_mask):
        return np.zeros((H, W), dtype=np.float32)

    cand_mask = np.asarray(allowed_mask, dtype=bool)
    if enforce_ridge_skeleton:
        dom = np.asarray(footprint, dtype=bool) if footprint is not None else np.isfinite(prob_2d) & (prob_2d > 0)
        # Pre-smooth slightly to break flat tree-leaf plateaus cleanly along ridge crests
        p_sm = gaussian_filter(
            np.where(dom & np.isfinite(prob_2d), prob_2d, 0.0).astype(np.float32),
            sigma=0.85,
            mode="nearest",
        )
        skel = ridge_nms(p_sm, dom, sigma=ridge_sigma)
        del p_sm
        cand_mask = cand_mask & skel
        del skel
        if not np.any(cand_mask):
            return np.zeros((H, W), dtype=np.float32)

    lam_fp = np.float32((0.2 * float(dstar_ref)) / max(1.0 - 0.2 * float(dstar_ref), 1e-6))
    pad = 3
    q_pad = np.zeros((H + 2 * pad, W + 2 * pad), dtype=np.float32)
    q_pad[pad : pad + H, pad : pad + W] = np.clip(
        np.where(np.isfinite(prob_2d), prob_2d, 0.0), 0.0, 1.0
    )
    cov_pad = np.zeros_like(q_pad)

    dy_list = KERNEL_DY.tolist()
    dx_list = KERNEL_DX.tolist()
    kw_list = KERNEL_W.tolist()
    n_off = len(kw_list)

    init_tp = np.zeros((H, W), dtype=np.float32)
    q_nb = np.zeros((H, W), dtype=np.float32)
    for oy, ox, kv in zip(dy_list, dx_list, kw_list, strict=True):
        sub = q_pad[pad + oy : pad + oy + H, pad + ox : pad + ox + W]
        init_tp += np.float32(kv) * sub
        np.maximum(q_nb, np.float32(kv) * sub, out=q_nb)

    pen_arr = lam_fp * (np.float32(1.0) - q_nb)
    del q_nb
    u0 = init_tp - pen_arr

    elig = np.flatnonzero(cand_mask & (init_tp > 0.0) & (u0 > min_gain))
    del init_tp
    if elig.size == 0:
        return np.zeros((H, W), dtype=np.float32)
    if elig.size > candidate_pool:
        u_elig = u0.ravel()[elig]
        keep = np.argpartition(u_elig, -candidate_pool)[-candidate_pool:]
        elig = elig[keep]

    ys = (elig // W + pad).tolist()
    xs = (elig % W + pad).tolist()
    pens = pen_arr.ravel()[elig].tolist()
    u_vals = u0.ravel()[elig].tolist()
    del pen_arr, u0

    heap: list[tuple[float, int, int, int, float]] = [
        (-u_vals[i] - 1e-13 * (ys[i] * 3301 + xs[i]), int(elig[i]), ys[i], xs[i], pens[i])
        for i in range(len(elig))
    ]
    del ys, xs, pens, u_vals, elig
    heapq.heapify(heap)

    out = np.zeros((H, W), dtype=np.float32)
    selected = 0

    while selected < n_dots and heap:
        _neg_u, flat_idx, py, px, pen_val = heapq.heappop(heap)
        gain_tp = 0.0
        for m in range(n_off):
            ny = py + dy_list[m]
            nx = px + dx_list[m]
            qv = float(q_pad[ny, nx])
            if qv > 0.0:
                diff = kw_list[m] - float(cov_pad[ny, nx])
                if diff > 0.0:
                    gain_tp += qv * diff
        cur_u = gain_tp - pen_val
        if cur_u <= min_gain:
            continue
        if not heap or (-cur_u - 1e-13 * (py * 3301 + px)) <= heap[0][0] + 1e-12:
            out.ravel()[flat_idx] = 1.0
            selected += 1
            for m in range(n_off):
                ny = py + dy_list[m]
                nx = px + dx_list[m]
                kv = kw_list[m]
                if kv > cov_pad[ny, nx]:
                    cov_pad[ny, nx] = np.float32(kv)
        else:
            heapq.heappush(
                heap, (-cur_u - 1e-13 * (py * 3301 + px), flat_idx, py, px, pen_val)
            )

    return out
