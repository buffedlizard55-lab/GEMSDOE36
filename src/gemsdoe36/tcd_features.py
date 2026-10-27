"""TCD-36: Tri-Domain 10m-3DEP Morphometry, Fluvial Chi, Deconfounding & Stage-2 Ridge Features.

Implements the frozen preregistration ``docs/research/tcd36-preregistration-20261027.md``
(``evidence/tcd36_preregistration_20261027.json``):

- 22 label-free, 100%-footprint Stage-1 physical features (``TCD_STAGE1_FEATURES``) derived
  solely from public-domain USGS 3DEP 10 m seamless DEM morphometry
  (``topo_10m_derived_100m_u8.tif``), Perron-Royden (2013) fluvial chi/ksn/knickpoint rasters
  (``dem10_chi_100m_i16.tif``, ``dem10_chi_100m_u8.tif``), and US Census TIGER/Line road/railroad
  distance (``tiger_road_distance_m.tif``). Zero fault-catalogue or submission inputs are read.
- Orthogonal 3-domain feature partition (``MORPHO_FEATURES``, ``GEOPHYS_FEATURES``,
  ``HYDRO_FLUV_SEIS_FEATURES``) across the 123-column combined Stage-1 feature store.
- 18 strictly mask-confined Stage-2 spatial-context ridge consolidation features
  (``TCD_STAGE2_FEATURES``) capturing multi-domain corroboration (``s2_second_best_domain``),
  Difference-of-Gaussians axial crest sharpening, Hessian principal ridge curvature,
  800 m / 1,800 m steerable probability worms, and connected ridge strand length.
"""

from __future__ import annotations

import gc
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
from scipy.ndimage import label as ndi_label
from scipy.signal import fftconvolve

from gemsdoe36.gvsc_features import (
    EXP2_FEATURES,
    GVSC_FEATURES,
    LIDAR_FEATURE_SET,
)
from gemsdoe36.kpl_features import KPL_FEATURES, KPL_LIDAR_FEATURES, structure_tensor

N_ORIENT = 8

TCD_STAGE1_FEATURES: tuple[str, ...] = (
    # USGS 3DEP 10 m seamless sub-cell morphometry (11 features, 100% footprint coverage)
    "tcd_t10_slope_p90",
    "tcd_t10_slope_max",
    "tcd_t10_curv_absmax",
    "tcd_t10_aspect_coh",
    "tcd_t10_hs_lineament",
    "tcd_t10_piedmont_step",
    "tcd_t10_scarp_localization",
    "tcd_t10_dem_lap_toe",
    "tcd_t10_scarp_w600",
    "tcd_t10_scarp_w1500",
    "tcd_t10_scarp_aniso1500",
    # Perron-Royden (2013) 10 m fluvial chi, ksn & knickpoint disequilibrium (5 features)
    "tcd_chi_step_smooth",
    "tcd_chi_ksn_smooth",
    "tcd_chi_knick_density",
    "tcd_chi_knick_worm1400",
    "tcd_playa_fill_frac",
    # True ASL Pleistocene Lake Lahontan & US Census TIGER cultural deconfounding (6 features)
    "tcd_zmean_asl_km",
    "tcd_lahontan_band",
    "tcd_lahontan_contour_mimic",
    "tcd_tect_contour_obliquity",
    "tcd_tiger_road_logdist",
    "tcd_tiger_road_line_mimic",
)

TCD123_FEATURES: tuple[str, ...] = tuple(EXP2_FEATURES) + tuple(KPL_FEATURES) + TCD_STAGE1_FEATURES

TCD_BLIND_FEATURES: tuple[str, ...] = tuple(
    n
    for n in TCD123_FEATURES
    if n not in LIDAR_FEATURE_SET and n not in KPL_LIDAR_FEATURES
)

# Orthogonal physical-domain partition for Stage-2 multi-domain corroboration
MORPHO_FEATURES: tuple[str, ...] = tuple(
    n
    for n in TCD123_FEATURES
    if (
        n in LIDAR_FEATURE_SET
        or n in KPL_LIDAR_FEATURES
        or n.startswith(("tcd_t10_", "tcd_zmean_", "tcd_lahontan_", "tcd_tect_", "tcd_tiger_"))
        or n
        in {
            "org_det_elev",
            "org_det_elev_slope",
            "ctx_det_elev_g3",
            "ctx_det_elev_anom3",
            "ctx_det_elev_g10",
            "ctx_det_elev_slope_g3",
            "ctx_det_elev_slope_anom3",
            "ctx_det_elev_slope_g10",
            "sa_piedmont_break",
            "sa_worm_piedmont",
            "kpl_slope_coh3km",
            "kpl_slope_line15",
        }
    )
)

GEOPHYS_FEATURES: tuple[str, ...] = tuple(
    n
    for n in TCD123_FEATURES
    if (
        n
        in {
            "org_mag_anom",
            "org_rtp",
            "org_tmi_hg",
            "org_tmi_vg",
            "org_tmi",
            "org_iso_grav_anom_slope",
            "org_iso_grav_anom_vg",
            "org_iso_grav_anom",
            "org_iso_grav_anom_hg",
            "org_depth_to_base_surf",
            "ctx_rtp_g3",
            "ctx_rtp_anom3",
            "ctx_rtp_g10",
            "ctx_tmi_hg_g3",
            "ctx_tmi_hg_anom3",
            "ctx_tmi_hg_g10",
            "ctx_iso_grav_anom_g3",
            "ctx_iso_grav_anom_anom3",
            "ctx_iso_grav_anom_g10",
            "ctx_iso_grav_anom_hg_g3",
            "ctx_iso_grav_anom_hg_anom3",
            "ctx_iso_grav_anom_hg_g10",
            "gd_TMI_up150",
            "sa_mag_tilt",
            "sa_mag_thdr_log",
            "sa_rtp_trough_dog",
            "sa_mag_atten_150m",
            "sa_grav_thdr",
            "sa_grav_tilt_ridge",
            "sa_base_step_rel",
            "sa_worm_mag",
            "sa_worm_grav_base",
            "sa_strike_concordance",
            "kpl_mag_coh3km",
            "kpl_mag_line15",
            "kpl_grav_coh3km",
            "kpl_xorient_agree",
        }
    )
)

HYDRO_FLUV_SEIS_FEATURES: tuple[str, ...] = tuple(
    n
    for n in TCD123_FEATURES
    if (
        n in GVSC_FEATURES
        or n.startswith(("tcd_chi_", "tcd_playa_"))
        or n
        in {
            "org_geod_2ndinv",
            "org_tc",
            "org_geod_shearrate",
            "org_geod_dilaterate",
            "org_deq_n100a15",
            "org_ieq_n100a15",
            "org_cond_surf",
            "gd_K",
            "gd_Th",
            "gd_U",
            "gd_TC",
            "gd_ThK",
            "gd_UK",
            "gd_UTh",
            "sa_mt_cond_edge",
            "sa_rad_k_th_anom",
            "sa_strain_seis_ratio",
        }
    )
)

assert len(set(MORPHO_FEATURES) & set(GEOPHYS_FEATURES)) == 0
assert len(set(MORPHO_FEATURES) & set(HYDRO_FLUV_SEIS_FEATURES)) == 0
assert len(set(GEOPHYS_FEATURES) & set(HYDRO_FLUV_SEIS_FEATURES)) == 0
assert (
    set(MORPHO_FEATURES) | set(GEOPHYS_FEATURES) | set(HYDRO_FLUV_SEIS_FEATURES)
) == set(TCD123_FEATURES)

TCD_STAGE2_FEATURES: tuple[str, ...] = (
    "s2_p_fused",
    "s2_p_morpho",
    "s2_p_geophys",
    "s2_p_hydro",
    "s2_second_best_domain",
    "s2_domain_geomean",
    "s2_domain_min",
    "s2_p_g1",
    "s2_p_g2_5",
    "s2_p_g6",
    "s2_p_g14",
    "s2_dog_crest_sharp",
    "s2_dog_crest_broad",
    "s2_hessian_ridge",
    "s2_prob_worm_800m",
    "s2_prob_worm_1800m",
    "s2_prob_worm_aniso1800m",
    "s2_ridge_strand_len_log",
)


def norm_gauss(
    arr: np.ndarray,
    mask: np.ndarray,
    sigma: float,
    weight_cache: dict[float, np.ndarray] | None = None,
) -> np.ndarray:
    """Mask-normalized 2-D Gaussian convolution with zero cross-boundary bleed."""
    m = mask.astype(np.float32, copy=False)
    num = gaussian_filter(np.where(mask, np.nan_to_num(arr, nan=0.0), 0.0).astype(np.float32), sigma)
    if weight_cache is not None and sigma in weight_cache:
        den = weight_cache[sigma]
    else:
        den = gaussian_filter(m, sigma)
        if weight_cache is not None:
            weight_cache[sigma] = den
    out = np.where((den > 1e-6) & mask, num / np.maximum(den, 1e-6), 0.0)
    return out.astype(np.float32)


def _line_kernel(theta_deg: float, half_px: int) -> np.ndarray:
    size = 2 * half_px + 1
    k = np.zeros((size, size), dtype=np.float32)
    th = np.deg2rad(theta_deg)
    dy, dx = -np.cos(th), np.sin(th)
    for t in np.linspace(-half_px, half_px, 8 * size):
        r = int(round(half_px + t * dy))
        c = int(round(half_px + t * dx))
        if 0 <= r < size and 0 <= c < size:
            k[r, c] = 1.0
    return (k / max(float(k.sum()), 1e-6)).astype(np.float32)


def steerable_worm(
    arr: np.ndarray,
    mask: np.ndarray,
    half_px: int,
    n_orient: int = N_ORIENT,
) -> tuple[np.ndarray, np.ndarray]:
    """Mask-normalized 8-azimuth line integral returning (max_response, max_minus_mean)."""
    x = np.where(mask, np.nan_to_num(arr, nan=0.0), 0.0).astype(np.float32)
    m = mask.astype(np.float32)
    mx = np.zeros(arr.shape, dtype=np.float32)
    acc = np.zeros(arr.shape, dtype=np.float32)
    for idx in range(n_orient):
        kern = _line_kernel(idx * 180.0 / n_orient, half_px)
        num = fftconvolve(x, kern, mode="same").astype(np.float32)
        den = fftconvolve(m, kern, mode="same").astype(np.float32)
        resp = np.where((den > 1e-4) & mask, num / np.maximum(den, 1e-4), 0.0).astype(np.float32)
        acc += resp
        np.maximum(mx, resp, out=mx)
        del num, den, resp
    mean = acc / float(n_orient)
    aniso = np.where(mask, mx - mean, 0.0).astype(np.float32)
    return np.where(mask, mx, 0.0).astype(np.float32), aniso


def build_tcd_stage1_features(data_dir: Path, fp: np.ndarray) -> dict[str, np.ndarray]:
    """Compute all 22 label-free 2-D TCD Stage-1 features across the active footprint."""
    ext = data_dir / "external"
    wcache: dict[float, np.ndarray] = {}
    out: dict[str, np.ndarray] = {}

    # 1. USGS 3DEP 10 m seamless DEM morphometry (9 uint8 bands)
    with rasterio.open(ext / "topo_10m_derived_100m_u8.tif") as tsrc:
        if tsrc.shape != fp.shape:
            raise ValueError(f"topo_10m shape {tsrc.shape} != {fp.shape}")
        t10 = tsrc.read().astype(np.float32) / np.float32(255.0)

    slope_p90 = np.where(fp, t10[0], 0.0).astype(np.float32)
    slope_max = np.where(fp, t10[1], 0.0).astype(np.float32)
    slope_std = np.where(fp, t10[3], 0.0).astype(np.float32)
    relief_loc = np.where(fp, t10[4], 0.0).astype(np.float32)
    curv_abs = np.where(fp, t10[5], 0.0).astype(np.float32)
    aspect_coh = np.where(fp, t10[6], 0.0).astype(np.float32)
    hs_lin = np.where(fp, t10[7], 0.0).astype(np.float32)
    dem_u8 = np.where(fp, t10[8], 0.0).astype(np.float32)
    del t10

    pstep = np.where(fp, slope_max / np.sqrt(relief_loc + np.float32(0.05)), 0.0).astype(np.float32)
    scarp_loc = np.where(
        fp,
        (slope_max - np.float32(0.65) * slope_p90 + np.float32(0.50) * slope_std)
        / np.sqrt(slope_p90 + np.float32(0.04)),
        0.0,
    ).astype(np.float32)
    dem_lap_toe = (norm_gauss(dem_u8, fp, 6.0, wcache) - norm_gauss(dem_u8, fp, 1.5, wcache)).astype(
        np.float32
    )
    s10 = np.where(
        fp,
        np.float32(0.45) * pstep + np.float32(0.30) * hs_lin + np.float32(0.25) * curv_abs * aspect_coh,
        0.0,
    ).astype(np.float32)

    w600, _ = steerable_worm(s10, fp, half_px=3, n_orient=N_ORIENT)
    w1500, aniso1500 = steerable_worm(s10, fp, half_px=7, n_orient=N_ORIENT)

    out["tcd_t10_slope_p90"] = slope_p90
    out["tcd_t10_slope_max"] = slope_max
    out["tcd_t10_curv_absmax"] = curv_abs
    out["tcd_t10_aspect_coh"] = aspect_coh
    out["tcd_t10_hs_lineament"] = hs_lin
    out["tcd_t10_piedmont_step"] = pstep
    out["tcd_t10_scarp_localization"] = scarp_loc
    out["tcd_t10_dem_lap_toe"] = dem_lap_toe
    out["tcd_t10_scarp_w600"] = w600
    out["tcd_t10_scarp_w1500"] = w1500
    out["tcd_t10_scarp_aniso1500"] = aniso1500
    del slope_p90, slope_max, slope_std, relief_loc, curv_abs, aspect_coh, hs_lin, dem_u8, pstep, scarp_loc, dem_lap_toe, w600, w1500, aniso1500
    gc.collect()

    # 2. Perron-Royden (2013) 10 m fluvial chi, ksn, knickpoints & zmean_m ASL
    with rasterio.open(ext / "dem10_chi_100m_i16.tif") as ci16, rasterio.open(
        ext / "dem10_chi_100m_u8.tif"
    ) as cu8:
        if ci16.shape != fp.shape or cu8.shape != fp.shape:
            raise ValueError("dem10_chi grid mismatch")
        chi_step_raw = ci16.read(1).astype(np.float32)
        chi_ksn_raw = ci16.read(3).astype(np.float32)
        zmean_raw = ci16.read(5).astype(np.float32)
        knick_n = cu8.read(2).astype(np.float32)
        raised_n = cu8.read(3).astype(np.float32)
        valid_n = cu8.read(4)

    chi_valid = (valid_n > 0) & (chi_step_raw > -32000.0) & fp
    step_pos = np.where(chi_valid, np.maximum(chi_step_raw, 0.0) / np.float32(1000.0), 0.0).astype(
        np.float32
    )
    ksn_pos = np.where(chi_valid, np.maximum(chi_ksn_raw, 0.0), 0.0).astype(np.float32)
    chi_step_s = norm_gauss(step_pos, fp, 2.5, wcache)
    chi_ksn_s = norm_gauss(ksn_pos, fp, 2.5, wcache)
    chi_knick_d = norm_gauss(np.where(fp, knick_n, 0.0), fp, 3.0, wcache)
    chi_worm, _ = steerable_worm(
        chi_knick_d * np.log1p(np.float32(5.0) * chi_step_s), fp, half_px=7, n_orient=N_ORIENT
    )
    playa_fill = norm_gauss(np.where(fp, raised_n / np.float32(100.0), 0.0), fp, 2.0, wcache)

    out["tcd_chi_step_smooth"] = chi_step_s
    out["tcd_chi_ksn_smooth"] = chi_ksn_s
    out["tcd_chi_knick_density"] = chi_knick_d
    out["tcd_chi_knick_worm1400"] = chi_worm
    out["tcd_playa_fill_frac"] = playa_fill
    del chi_step_raw, chi_ksn_raw, knick_n, raised_n, valid_n, chi_valid, step_pos, ksn_pos, chi_step_s, chi_ksn_s, chi_knick_d, chi_worm, playa_fill
    gc.collect()

    # 3. True elevation ASL, Pleistocene Lake Lahontan strandline mimic & contour obliquity
    z_ok = (zmean_raw > -1000.0) & fp
    z_inpaint = norm_gauss(np.where(z_ok, zmean_raw, 0.0), z_ok, 4.0)
    z_m = np.where(z_ok, zmean_raw, np.where(fp, z_inpaint, 1500.0)).astype(np.float32)
    del zmean_raw, z_ok, z_inpaint

    z_smooth = norm_gauss(z_m, fp, 3.0, wcache)
    gz_y, gz_x = np.gradient(z_smooth)
    theta_z_grad = np.arctan2(gz_y, gz_x).astype(np.float32)
    del z_smooth, gz_y, gz_x

    # Structure-tensor gradient orientation of 10 m scarp composite s10
    _coh_s, _en_s, theta_s_grad = structure_tensor(s10, fp, sigma_int=4.0)
    del _coh_s, _en_s

    # Parallelism between scarp strike and elevation contour <=> alignment of gradient axes:
    # cos^2(dtheta): 1 when scarp parallels contour (shoreline bench), 0 when orthogonal!
    cos2_parallel = (np.cos(theta_s_grad - theta_z_grad) ** 2).astype(np.float32)
    sin_oblique = np.abs(np.sin(theta_s_grad - theta_z_grad)).astype(np.float32)
    del theta_s_grad, theta_z_grad

    lahontan_sehoo = np.exp(-0.5 * np.clip(((z_m - 1330.0) / 45.0) ** 2, 0.0, 40.0))
    lahontan_recess = 0.70 * np.exp(-0.5 * np.clip(((z_m - 1235.0) / 40.0) ** 2, 0.0, 40.0))
    lahontan_band = np.where(fp, lahontan_sehoo + lahontan_recess, 0.0).astype(np.float32)
    del lahontan_sehoo, lahontan_recess

    out["tcd_zmean_asl_km"] = np.where(fp, z_m / np.float32(1000.0), 0.0).astype(np.float32)
    out["tcd_lahontan_band"] = lahontan_band
    out["tcd_lahontan_contour_mimic"] = np.where(fp, lahontan_band * cos2_parallel * s10, 0.0).astype(
        np.float32
    )
    out["tcd_tect_contour_obliquity"] = np.where(fp, s10 * sin_oblique, 0.0).astype(np.float32)
    del z_m, lahontan_band, cos2_parallel, sin_oblique

    # 4. US Census TIGER/Line road/highway/railroad cultural embankment deconfounding
    with rasterio.open(ext / "tiger_road_distance_m.tif") as rsrc:
        if rsrc.shape != fp.shape:
            raise ValueError("tiger_road_distance_m grid mismatch")
        d_road = np.maximum(np.nan_to_num(rsrc.read(1).astype(np.float32), nan=5000.0), 0.0)

    out["tcd_tiger_road_logdist"] = np.where(
        fp, np.log1p(d_road / np.float32(100.0)), 0.0
    ).astype(np.float32)
    out["tcd_tiger_road_line_mimic"] = np.where(
        fp, np.exp(-np.clip(d_road / np.float32(150.0), 0.0, 30.0)) * s10, 0.0
    ).astype(np.float32)
    del d_road, s10, wcache
    gc.collect()

    assert tuple(out.keys()) == TCD_STAGE1_FEATURES
    return out


def build_stage2_context_matrix(
    p_fused: np.ndarray,
    p_morpho: np.ndarray,
    p_geophys: np.ndarray,
    p_hydro: np.ndarray,
    domain_mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute 18 strictly mask-confined Stage-2 spatial-context features on ``domain_mask``.

    All spatial convolutions zero out ``~domain_mask`` and normalize by smoothed mask weights
    so zero signal crosses between training and validation folds.

    Returns ``(X_domain, flat_indices)`` where ``X_domain`` has shape ``(n_domain, 18)``.
    """
    m = np.asarray(domain_mask, dtype=bool)
    flat_idx = np.flatnonzero(m.ravel())
    n_dom = int(flat_idx.size)
    X = np.empty((n_dom, len(TCD_STAGE2_FEATURES)), dtype=np.float32)

    pf = np.where(m, np.clip(p_fused, 0.0, 1.0), 0.0).astype(np.float32)
    pm = np.where(m, np.clip(p_morpho, 0.0, 1.0), 0.0).astype(np.float32)
    pg = np.where(m, np.clip(p_geophys, 0.0, 1.0), 0.0).astype(np.float32)
    ph = np.where(m, np.clip(p_hydro, 0.0, 1.0), 0.0).astype(np.float32)

    X[:, 0] = pf.ravel()[flat_idx]
    X[:, 1] = pm.ravel()[flat_idx]
    X[:, 2] = pg.ravel()[flat_idx]
    X[:, 3] = ph.ravel()[flat_idx]

    # Multi-domain corroboration: second_best = sum - max - min across 3 physical domains
    mx3 = np.maximum(np.maximum(pm, pg), ph)
    mn3 = np.minimum(np.minimum(pm, pg), ph)
    sec3 = pm + pg + ph - mx3 - mn3
    geomean3 = np.cbrt(np.maximum(pm * pg * ph, 0.0)).astype(np.float32)
    X[:, 4] = sec3.ravel()[flat_idx]
    X[:, 5] = geomean3.ravel()[flat_idx]
    X[:, 6] = mn3.ravel()[flat_idx]
    del pm, pg, ph, mx3, mn3, sec3, geomean3

    wcache: dict[float, np.ndarray] = {}
    g08 = norm_gauss(pf, m, 0.8, wcache)
    g10 = norm_gauss(pf, m, 1.0, wcache)
    g15 = norm_gauss(pf, m, 1.5, wcache)
    g25 = norm_gauss(pf, m, 2.5, wcache)
    g40 = norm_gauss(pf, m, 4.0, wcache)
    g60 = norm_gauss(pf, m, 6.0, wcache)
    g80 = norm_gauss(pf, m, 8.0, wcache)
    g140 = norm_gauss(pf, m, 14.0, wcache)

    X[:, 7] = g10.ravel()[flat_idx]
    X[:, 8] = g25.ravel()[flat_idx]
    X[:, 9] = g60.ravel()[flat_idx]
    X[:, 10] = g140.ravel()[flat_idx]
    X[:, 11] = (g08 - g40).ravel()[flat_idx]
    X[:, 12] = (g15 - g80).ravel()[flat_idx]
    del g10, g15, g25, g40, g60, g80, g140, wcache

    # Principal 1-D ridge curvature: -lambda_min of 2-D Hessian of g08
    gy, gx = np.gradient(g08)
    hyy, hyx = np.gradient(gy)
    hxy, hxx = np.gradient(gx)
    del gy, gx
    hxy = 0.5 * (hyx + hxy)
    tr = hxx + hyy
    disc = np.sqrt(np.maximum((hxx - hyy) ** 2 + 4.0 * (hxy**2), 0.0))
    lam_min = 0.5 * (tr - disc)
    hess_ridge = np.where(m, np.maximum(-lam_min, 0.0), 0.0).astype(np.float32)
    X[:, 13] = hess_ridge.ravel()[flat_idx]
    del hyy, hyx, hxy, hxx, tr, disc, lam_min, hess_ridge

    # 800 m & 1,800 m steerable probability worms
    pw800, _ = steerable_worm(pf, m, half_px=4, n_orient=N_ORIENT)
    pw1800, pwaniso1800 = steerable_worm(pf, m, half_px=9, n_orient=N_ORIENT)
    X[:, 14] = pw800.ravel()[flat_idx]
    X[:, 15] = pw1800.ravel()[flat_idx]
    X[:, 16] = pwaniso1800.ravel()[flat_idx]
    del pw800, pw1800, pwaniso1800

    # Connected high-probability ridge strand length (suppresses isolated speckles)
    vals_g08 = g08.ravel()[flat_idx]
    q94 = float(np.quantile(vals_g08, 0.94)) if vals_g08.size else 1.0
    hi_mask = m & (g08 >= max(q94, 1e-6))
    comp, n_comp = ndi_label(hi_mask, structure=np.ones((3, 3), dtype=np.int32))
    if n_comp > 0:
        sizes = np.bincount(comp.ravel())
        sizes[0] = 0
        strand_len = np.log1p(sizes[comp].astype(np.float32))
    else:
        strand_len = np.zeros(pf.shape, dtype=np.float32)
    X[:, 17] = strand_len.ravel()[flat_idx]
    del g08, hi_mask, comp, strand_len, pf
    gc.collect()
    return X, flat_idx
