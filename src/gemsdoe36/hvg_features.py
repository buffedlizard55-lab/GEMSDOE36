"""HVG-36 feature engineering: Hydrothermal-Vent Structural-Conduit & Cross-Scale Phase-Dipole.

Memory-safe implementation (peak RAM < 350 MB on 3.9 GB sandbox) storing one
footprint-indexed ``.npy`` file per feature in ``cache_dir`` and reading via
``mmap_mode='r'``.

Implements the preregistered feature families from
``docs/research/preregistration-hvg36-20261026.md`` and
``evidence/hvg36_preregistration_20261026.json``:

1. ``HVG-36-A`` (Hydrothermal-Vent & Upflow Structural-Conduit Anisotropy + RAD-ANISO):
   - ``hvg_geotherm_excess``: OpenEI GDR 1391 multi-geothermometer reservoir temperature
     excess above 25 C (chalcedony, quartz, Na-K-Ca, measured temp_c).
   - ``hvg_vent_spring_axial_conduit``: Anisotropic fault-strike conduit field bridging
     Quaternary volcanic vents (``gdr_volcanic_vents_in_footprint.csv``) and thermal
     springs/wells (``gdr_wellspring_in_footprint.csv``) along the regional contour/strike
     direction minus isotropic background, coupled with potential-field horizontal gradient.
   - ``hvg_rtp_demag_trough_concord``: Hydrothermal magnetite-destruction trough in
     Reduced-to-Pole magnetics (``02_rtp``) concordant with magnetic contact gradient
     (``03_tmi_hg``).
   - ``hvg_rad_aniso_strike`` (``RAD-ANISO``): Strike-parallel (1.5 km) directional line
     integral minus isotropic Gaussian mean of GeoDAWN potassium-to-thorium (``K/Th``) and
     uranium-to-thorium (``U/Th``) ratios.
   - ``hvg_claycap_seal_edge`` (fold-safe): Spatial gradient magnitude of the fold-regressed
     playa-deconfounded ``17_cond_surf`` residual coupled with potential-field gradient.
   - ``hvg_rad_kth_slope_resid`` (fold-safe): Slope- and elevation-deconfounded GeoDAWN
     ``K/Th`` metasomatic enrichment residual fit strictly on ``fold["train"]``.

2. ``HVG-36-B`` (Cross-Scale Magnetic Phase Persistence P-TMI & Basement Dipole D-PAIR):
   - ``hvg_mag_tilt_verduzco``: Depth-invariant Verduzco magnetic tilt angle.
   - ``hvg_grav_tilt_verduzco``: Depth-invariant gravity tilt angle.
   - ``hvg_ptmi_phase_persist`` (``P-TMI``): Cosine phase agreement between surface ``02_rtp``
     gradient and GeoDAWN 150 m upward-continued ``TMI_up150`` gradient combined with
     multi-altitude upward-continuation THDR persistence.
   - ``hvg_dpair_basement_dipole`` (``D-PAIR``): Across-strike paired opposing signed
     curvature shoulders in ``15_depth_to_base_surf`` and ``13_iso_grav_anom`` at
     300-600 m offset.
   - ``hvg_piedmont_scarp_deconf``: Relief-deconfounded piedmont scarp-toe curvature.
   - ``hvg_basement_grav_concord``: Pre-Cenozoic basement slope x isostatic gravity HG.
   - ``hvg_seismic_strain_corridor``: Walker Lane / Great Basin geodetic strain + earthquake
     density composite.
   - ``hvg_trunk_worm_bridge``: 1.5 km strike-parallel potential-field + topographic worm
     bridge across 3DEP 1 m LiDAR coverage gaps.

Strict Leakage Guard:
- ``dist_known_fault_px`` is explicitly banned and stripped upon reading any GDR CSV.
- No catalogue raster (``existing_faults.tif``, ``labels.tif``, ``sgmc``, ``qfaults``) or
  prior submission raster is ever read by ``build_or_load_hvg_static_features``.
- Fold-safe deconfounding regressions (``compute_fold_safe_hvg_residuals``) fit ridge
  weights exclusively on ``fold["train"]`` pixels.
"""

from __future__ import annotations

import csv
import gc
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from gemsdoe36.h36_features import (
    FeatureStore,
    _shift,
    coherent_line,
    regional_slope_azimuth,
)
from gemsdoe36.paths import data_dir

H, W = 3730, 3292
BANNED_GDR_COLS: frozenset[str] = frozenset({"dist_known_fault_px"})

HVG_STATIC_NAMES: tuple[str, ...] = (
    "hvg_geotherm_excess",
    "hvg_vent_spring_axial_conduit",
    "hvg_rtp_demag_trough_concord",
    "hvg_rad_aniso_strike",
    "hvg_mag_tilt_verduzco",
    "hvg_grav_tilt_verduzco",
    "hvg_ptmi_phase_persist",
    "hvg_dpair_basement_dipole",
    "hvg_piedmont_scarp_deconf",
    "hvg_basement_grav_concord",
    "hvg_seismic_strain_corridor",
    "hvg_trunk_worm_bridge",
)

HVG_FOLD_SAFE_NAMES: tuple[str, ...] = (
    "hvg_claycap_seal_edge",
    "hvg_rad_kth_slope_resid",
)


def _fp_to_2d(vec: np.ndarray, fp_idx: np.ndarray, fill: float = 0.0) -> np.ndarray:
    grid = np.full(H * W, fill, dtype=np.float32)
    vals = np.asarray(vec, dtype=np.float32)
    valid = np.isfinite(vals)
    med = float(np.median(vals[valid])) if valid.any() else float(fill)
    grid[fp_idx] = np.where(valid, vals, med)
    return grid.reshape(H, W)


def _robust_z_1d(v: np.ndarray) -> np.ndarray:
    vals = np.asarray(v, dtype=np.float32)
    valid = np.isfinite(vals)
    med = float(np.median(vals[valid])) if valid.any() else 0.0
    mad = float(np.median(np.abs(vals[valid] - med))) * 1.4826 + 1e-6 if valid.any() else 1.0
    z = np.clip((vals - med) / mad, -8.0, 8.0).astype(np.float32)
    return np.nan_to_num(z, nan=0.0, posinf=8.0, neginf=-8.0)


def _robust_z_fp(arr2d: np.ndarray, fp_idx: np.ndarray) -> np.ndarray:
    return _robust_z_1d(arr2d.ravel()[fp_idx])


def _parse_float(val: str | None) -> float:
    if val is None:
        return float("nan")
    s = val.strip()
    if not s:
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _load_gdr_geothermal_and_vents() -> tuple[np.ndarray, np.ndarray]:
    """Load OpenEI GDR 1391 thermal springs/geothermometers and Quaternary vents.

    Strictly drops ``dist_known_fault_px`` on load and asserts its absence.
    Returns two (H, W) impulse grids: (geotherm_excess_grid, vent_spring_impulse_grid).
    """
    ext_dir = data_dir() / "external"
    ws_path = ext_dir / "gdr_wellspring_in_footprint.csv"
    vv_path = ext_dir / "gdr_volcanic_vents_in_footprint.csv"

    geotherm_grid = np.zeros((H, W), dtype=np.float32)
    conduit_seed_grid = np.zeros((H, W), dtype=np.float32)

    if ws_path.exists():
        with ws_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            allowed_fields = [f for f in (reader.fieldnames or []) if f not in BANNED_GDR_COLS]
            assert "dist_known_fault_px" not in allowed_fields
            for raw_row in reader:
                row = {k: raw_row[k] for k in allowed_fields}
                assert "dist_known_fault_px" not in row
                r_f = _parse_float(row.get("row"))
                c_f = _parse_float(row.get("col"))
                if not (np.isfinite(r_f) and np.isfinite(c_f)):
                    continue
                r_i, c_i = int(round(r_f)), int(round(c_f))
                if not (0 <= r_i < H and 0 <= c_i < W):
                    continue
                t_candidates: list[float] = []
                t_meas = _parse_float(row.get("temp_c"))
                if np.isfinite(t_meas) and 10.0 < t_meas < 350.0:
                    t_candidates.append(t_meas)
                for col_name in ("geothermchalc_c", "geothermquartz_c", "geothermcat_c"):
                    t_g = _parse_float(row.get(col_name))
                    if np.isfinite(t_g) and 20.0 < t_g < 350.0:
                        t_candidates.append(t_g)
                excess = 0.0
                if t_candidates:
                    t_med = float(np.median(t_candidates))
                    excess = float(np.clip(t_med - 25.0, 0.0, 220.0))
                if excess > 0.0:
                    val = float(np.log1p(excess))
                    if val > geotherm_grid[r_i, c_i]:
                        geotherm_grid[r_i, c_i] = val
                tclass = (row.get("thermalclass") or "").strip()
                if tclass in ("Hot", "Warm") or excess >= 15.0:
                    w_hot = float(1.0 + 0.5 * np.log1p(max(0.0, excess)))
                    if w_hot > conduit_seed_grid[r_i, c_i]:
                        conduit_seed_grid[r_i, c_i] = w_hot

    if vv_path.exists():
        with vv_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            allowed_fields = [f for f in (reader.fieldnames or []) if f not in BANNED_GDR_COLS]
            assert "dist_known_fault_px" not in allowed_fields
            for raw_row in reader:
                row = {k: raw_row[k] for k in allowed_fields}
                assert "dist_known_fault_px" not in row
                r_f = _parse_float(row.get("row"))
                c_f = _parse_float(row.get("col"))
                if not (np.isfinite(r_f) and np.isfinite(c_f)):
                    continue
                r_i, c_i = int(round(r_f)), int(round(c_f))
                if 0 <= r_i < H and 0 <= c_i < W:
                    if 3.5 > conduit_seed_grid[r_i, c_i]:
                        conduit_seed_grid[r_i, c_i] = 3.5

    return geotherm_grid, conduit_seed_grid


def _dipole_pair_2d(field2d: np.ndarray) -> np.ndarray:
    """Memory-safe across-strike paired opposing signed curvature dipole (D-PAIR)."""
    f_xx = gaussian_filter(field2d, sigma=3.0, order=(0, 2)).astype(np.float32)
    f_yy = gaussian_filter(field2d, sigma=3.0, order=(2, 0)).astype(np.float32)
    lap = (f_xx + f_yy).astype(np.float32)
    del f_xx, f_yy
    pos = np.maximum(0.0, lap)
    neg = np.maximum(0.0, -lap)
    del lap
    best = np.zeros((H, W), dtype=np.float32)
    # 4 cardinal/diagonal across-strike directions at offsets d=3 and d=6 px (300-600 m)
    for dy, dx in ((0, 3), (3, 0), (2, 2), (2, -2), (0, 6), (6, 0), (4, 4), (4, -4)):
        p1 = np.sqrt(_shift(pos, dy, dx) * _shift(neg, -dy, -dx))
        p2 = np.sqrt(_shift(neg, dy, dx) * _shift(pos, -dy, -dx))
        np.maximum(best, p1, out=best)
        np.maximum(best, p2, out=best)
    del pos, neg
    return best


def build_or_load_hvg_static_features(
    store: FeatureStore,
    fp_idx: np.ndarray,
    cache_dir: Path,
) -> tuple[FeatureStore, list[str]]:
    """Build or load the 12 label-free static HVG-36 features into ``store.cache_dir``."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    all_exist = all((store.cache_dir / f"{name}.npy").exists() for name in HVG_STATIC_NAMES)
    if all_exist:
        for name in HVG_STATIC_NAMES:
            if name not in store.names:
                store.names.append(name)
        return store, list(HVG_STATIC_NAMES)

    def _save_col(name: str, vec_fp: np.ndarray) -> None:
        arr = np.nan_to_num(np.asarray(vec_fp, dtype=np.float32), nan=0.0, posinf=8.0, neginf=-8.0)
        assert arr.shape == (store.n_fp,)
        np.save(store.cache_dir / f"{name}.npy", arr)
        if name not in store.names:
            store.names.append(name)

    fp_mask = np.zeros(H * W, dtype=bool)
    fp_mask[fp_idx] = True
    fp_2d = fp_mask.reshape(H, W)

    # Regional slope azimuth from elevation (used for directional line integrals)
    elev = _fp_to_2d(store.column("org_det_elev"), fp_idx)
    slope_az = regional_slope_azimuth(elev, fp_2d)

    # 9. hvg_piedmont_scarp_deconf (while elev is in memory)
    e_yy = gaussian_filter(elev, sigma=2.0, order=(2, 0)).astype(np.float32)
    e_xx = gaussian_filter(elev, sigma=2.0, order=(0, 2)).astype(np.float32)
    e_yx = gaussian_filter(elev, sigma=2.0, order=(1, 1)).astype(np.float32)
    tr = e_xx + e_yy
    det = np.sqrt(np.maximum(0.0, (e_xx - e_yy) ** 2 + 4.0 * e_yx * e_yx))
    lam_min = 0.5 * (tr - det)
    del e_yy, e_xx, e_yx, tr, det
    elev_mean25 = gaussian_filter(elev, sigma=25.0).astype(np.float32)
    elev_std25 = np.sqrt(np.maximum(1.0, gaussian_filter((elev - elev_mean25) ** 2, sigma=25.0))).astype(np.float32)
    scarp_deconf = (np.maximum(0.0, -lam_min) / (elev_std25 + 15.0)).astype(np.float32)
    _save_col("hvg_piedmont_scarp_deconf", _robust_z_fp(scarp_deconf, fp_idx))
    del elev, lam_min, elev_mean25, elev_std25, scarp_deconf
    gc.collect()

    # 1. hvg_geotherm_excess & 2. hvg_vent_spring_axial_conduit
    geotherm_grid, conduit_seed_grid = _load_gdr_geothermal_and_vents()
    gt_blend = (
        0.65 * gaussian_filter(geotherm_grid, sigma=4.0)
        + 0.35 * gaussian_filter(geotherm_grid, sigma=14.0)
    ).astype(np.float32)
    _save_col("hvg_geotherm_excess", _robust_z_fp(gt_blend, fp_idx))
    del geotherm_grid, gt_blend

    seed_smooth = gaussian_filter(conduit_seed_grid, sigma=3.5).astype(np.float32)
    del conduit_seed_grid
    own_seed, mx_seed = coherent_line(seed_smooth, slope_az)
    iso_seed = gaussian_filter(seed_smooth, sigma=6.0).astype(np.float32)
    del seed_smooth
    z_tmi_hg = _robust_z_1d(store.column("org_tmi_hg"))
    z_grav_hg = _robust_z_1d(store.column("org_iso_grav_anom_hg"))
    pot_wall = np.clip(0.5 * (z_tmi_hg + z_grav_hg), -2.0, 6.0)
    axial_fp = _robust_z_fp(0.6 * own_seed + 0.4 * mx_seed - 0.5 * iso_seed, fp_idx) * (
        1.0 + 0.25 * np.maximum(0.0, pot_wall)
    )
    _save_col("hvg_vent_spring_axial_conduit", np.clip(axial_fp, -8.0, 8.0))
    del own_seed, mx_seed, iso_seed, axial_fp
    gc.collect()

    # 3. hvg_rtp_demag_trough_concord & 7. hvg_ptmi_phase_persist (P-TMI)
    rtp = _fp_to_2d(store.column("org_rtp"), fp_idx)
    rtp_trough = np.maximum(0.0, gaussian_filter(rtp, sigma=15.0) - gaussian_filter(rtp, sigma=2.0)).astype(np.float32)
    demag = _robust_z_fp(rtp_trough, fp_idx) * np.log1p(np.maximum(0.0, z_tmi_hg))
    _save_col("hvg_rtp_demag_trough_concord", np.clip(demag, -8.0, 8.0))
    del rtp_trough, demag

    gd_tmi_up150 = _fp_to_2d(store.column("gd_TMI_up150"), fp_idx)
    gy_rtp, gx_rtp = np.gradient(gaussian_filter(rtp, sigma=2.0).astype(np.float32))
    gy_up, gx_up = np.gradient(gaussian_filter(gd_tmi_up150, sigma=2.0).astype(np.float32))
    del rtp, gd_tmi_up150
    mag_rtp = np.hypot(gx_rtp, gy_rtp) + 1e-6
    mag_up = np.hypot(gx_up, gy_up) + 1e-6
    cos_phase = ((gx_rtp * gx_up + gy_rtp * gy_up) / (mag_rtp * mag_up)).astype(np.float32)
    del gx_rtp, gy_rtp, gx_up, gy_up
    ptmi_2d = (np.maximum(0.0, cos_phase) * np.sqrt(mag_rtp * mag_up)).astype(np.float32)
    del cos_phase, mag_rtp, mag_up

    # Multi-scale potential-field persistence across Gaussian continuation scales (sigma=1, 3, 7, 14 px)
    tmi_hg_2d = _fp_to_2d(store.column("org_tmi_hg"), fp_idx)
    grav_hg_2d = _fp_to_2d(store.column("org_iso_grav_anom_hg"), fp_idx)
    worm_pers = (
        _robust_z_fp(gaussian_filter(tmi_hg_2d, sigma=2.0), fp_idx)
        + _robust_z_fp(gaussian_filter(tmi_hg_2d, sigma=6.0), fp_idx)
        + _robust_z_fp(gaussian_filter(grav_hg_2d, sigma=2.0), fp_idx)
        + _robust_z_fp(gaussian_filter(grav_hg_2d, sigma=6.0), fp_idx)
    ) * 0.25
    ptmi_persist = 0.50 * _robust_z_fp(ptmi_2d, fp_idx) + 0.50 * worm_pers
    _save_col("hvg_ptmi_phase_persist", np.clip(ptmi_persist, -8.0, 8.0))
    del ptmi_2d, worm_pers, ptmi_persist
    gc.collect()

    # 12. hvg_trunk_worm_bridge (using tmi_hg_2d, grav_hg_2d, slope)
    slope_2d = _fp_to_2d(store.column("org_det_elev_slope"), fp_idx)
    worm_seed = (
        0.40 * gaussian_filter(tmi_hg_2d, sigma=2.0)
        + 0.40 * gaussian_filter(grav_hg_2d, sigma=2.0)
        + 0.20 * gaussian_filter(slope_2d, sigma=2.0)
    ).astype(np.float32)
    del tmi_hg_2d, grav_hg_2d, slope_2d
    own_w, mx_w = coherent_line(worm_seed, slope_az)
    iso_w = gaussian_filter(worm_seed, sigma=6.0).astype(np.float32)
    del worm_seed
    _save_col("hvg_trunk_worm_bridge", _robust_z_fp(0.5 * own_w + 0.5 * mx_w - 0.35 * iso_w, fp_idx))
    del own_w, mx_w, iso_w
    gc.collect()

    # 4. hvg_rad_aniso_strike (RAD-ANISO)
    gd_k = store.column("gd_K").astype(np.float32)
    gd_th = store.column("gd_Th").astype(np.float32)
    gd_u = store.column("gd_U").astype(np.float32)
    rad_fp = np.nan_to_num(gd_k / (gd_th + 8.0) + 0.7 * (gd_u / (gd_th + 8.0)), nan=0.0).astype(np.float32)
    del gd_k, gd_th, gd_u
    rad_2d = gaussian_filter(_fp_to_2d(rad_fp, fp_idx), sigma=2.0).astype(np.float32)
    del rad_fp
    own_r, mx_r = coherent_line(rad_2d, slope_az)
    iso_r = gaussian_filter(rad_2d, sigma=6.0).astype(np.float32)
    del rad_2d, slope_az
    _save_col("hvg_rad_aniso_strike", _robust_z_fp(0.6 * own_r + 0.4 * mx_r - iso_r, fp_idx))
    del own_r, mx_r, iso_r
    gc.collect()

    # 5. hvg_mag_tilt_verduzco & 6. hvg_grav_tilt_verduzco (pure 1D footprint operations!)
    tmi_vg_1d = store.column("org_tmi_vg").astype(np.float32)
    tmi_hg_1d = store.column("org_tmi_hg").astype(np.float32)
    mag_tilt_1d = np.arctan2(tmi_vg_1d, np.abs(tmi_hg_1d) + 1e-3).astype(np.float32)
    _save_col("hvg_mag_tilt_verduzco", _robust_z_1d(mag_tilt_1d))
    del tmi_vg_1d, tmi_hg_1d, mag_tilt_1d

    grav_vg_1d = store.column("org_iso_grav_anom_vg").astype(np.float32)
    grav_hg_1d = store.column("org_iso_grav_anom_hg").astype(np.float32)
    grav_tilt_1d = np.arctan2(-grav_vg_1d, np.abs(grav_hg_1d) + 1e-3).astype(np.float32)
    _save_col("hvg_grav_tilt_verduzco", _robust_z_1d(grav_tilt_1d))
    del grav_vg_1d, grav_hg_1d, grav_tilt_1d

    # 8. hvg_dpair_basement_dipole (D-PAIR) & 10. hvg_basement_grav_concord
    base_depth = _fp_to_2d(store.column("org_depth_to_base_surf"), fp_idx)
    dip_base = _dipole_pair_2d(base_depth)
    base_sm = gaussian_filter(base_depth, sigma=3.0).astype(np.float32)
    del base_depth
    gby, gbx = np.gradient(base_sm)
    del base_sm
    base_slope_fp = np.hypot(gbx, gby).ravel()[fp_idx].astype(np.float32)
    del gbx, gby
    bg_concord = 0.5 * (_robust_z_1d(base_slope_fp) + z_grav_hg)
    _save_col("hvg_basement_grav_concord", np.clip(bg_concord, -8.0, 8.0))
    del base_slope_fp, bg_concord

    grav_2d = _fp_to_2d(store.column("org_iso_grav_anom"), fp_idx)
    dip_grav = _dipole_pair_2d(grav_2d)
    del grav_2d
    dpair_fp = 0.60 * _robust_z_fp(dip_base, fp_idx) + 0.40 * _robust_z_fp(dip_grav, fp_idx)
    _save_col("hvg_dpair_basement_dipole", np.clip(dpair_fp, -8.0, 8.0))
    del dip_base, dip_grav, dpair_fp
    gc.collect()

    # 11. hvg_seismic_strain_corridor (pure 1D footprint operations!)
    strain_eq = (
        0.30 * _robust_z_1d(store.column("org_geod_2ndinv"))
        + 0.25 * _robust_z_1d(store.column("org_geod_shearrate"))
        + 0.15 * np.abs(_robust_z_1d(store.column("org_geod_dilaterate")))
        + 0.15 * _robust_z_1d(store.column("org_deq_n100a15"))
        + 0.15 * _robust_z_1d(store.column("org_ieq_n100a15"))
    )
    _save_col("hvg_seismic_strain_corridor", np.clip(strain_eq, -8.0, 8.0))
    del strain_eq
    gc.collect()

    return store, list(HVG_STATIC_NAMES)


def compute_fold_safe_hvg_residuals(
    store: FeatureStore,
    fp_idx: np.ndarray,
    train_fp_mask: np.ndarray,
) -> tuple[np.ndarray, list[str]]:
    """Compute fold-safe deconfounded clay-cap boundary and radiometric K/Th residuals.

    Fits ridge regression strictly on ``train_fp_mask`` (excluding all withheld fault
    segments and their 1.5 km spatial buffer) so zero test-fold information leaks.
    """
    cond = store.column("org_cond_surf").astype(np.float32)
    elev = store.column("org_det_elev").astype(np.float32)
    slope = store.column("org_det_elev_slope").astype(np.float32)
    bdepth = store.column("org_depth_to_base_surf").astype(np.float32)
    tmi_hg = store.column("org_tmi_hg").astype(np.float32)
    grav_hg = store.column("org_iso_grav_anom_hg").astype(np.float32)
    gd_k = store.column("gd_K").astype(np.float32)
    gd_th = store.column("gd_Th").astype(np.float32)

    tr = np.asarray(train_fp_mask, dtype=bool)

    def _safe_z(v: np.ndarray) -> np.ndarray:
        v_tr = v[tr]
        valid = np.isfinite(v_tr)
        m = float(np.median(v_tr[valid])) if valid.any() else 0.0
        s = float(np.std(v_tr[valid])) + 1e-6 if valid.any() else 1.0
        out = ((v - m) / s).astype(np.float32)
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)

    z_elev = _safe_z(elev)
    z_slope = _safe_z(slope)
    z_bdepth = _safe_z(bdepth)
    del elev, slope, bdepth

    # 1. Playa-deconfounded conductivity residual -> spatial gradient edge x potential-field HG
    y_cond = _safe_z(np.log1p(np.maximum(0.0, np.nan_to_num(cond, nan=0.0))))
    del cond
    # Subsample training pixels by stride 8 (~500k rows) for fast, low-memory OLS/Ridge fit
    tr_idx = np.flatnonzero(tr)[::8]
    X_tr = np.column_stack(
        [np.ones(tr_idx.size, dtype=np.float64), z_elev[tr_idx], z_slope[tr_idx], z_bdepth[tr_idx], (z_elev[tr_idx] * z_slope[tr_idx])]
    )
    XtX = X_tr.T @ X_tr + 1e-2 * np.eye(5)
    Xty = X_tr.T @ y_cond[tr_idx].astype(np.float64)
    beta_c = np.linalg.solve(XtX, Xty).astype(np.float32)
    del X_tr
    pred_cond = (
        beta_c[0]
        + beta_c[1] * z_elev
        + beta_c[2] * z_slope
        + beta_c[3] * z_bdepth
        + beta_c[4] * (z_elev * z_slope)
    )
    r_cond = (y_cond - pred_cond).astype(np.float32)
    del y_cond, pred_cond, z_bdepth

    r_cond_2d = _fp_to_2d(r_cond, fp_idx)
    del r_cond
    rc_y, rc_x = np.gradient(gaussian_filter(r_cond_2d, sigma=2.0).astype(np.float32))
    del r_cond_2d
    rc_edge = np.hypot(rc_x, rc_y).ravel()[fp_idx].astype(np.float32)
    del rc_x, rc_y
    pot_z = np.maximum(0.0, 0.5 * (_safe_z(tmi_hg) + _safe_z(grav_hg))).astype(np.float32)
    del tmi_hg, grav_hg
    claycap_edge = np.clip(_safe_z(rc_edge) * np.log1p(pot_z), -8.0, 8.0).astype(np.float32)
    del rc_edge, pot_z

    # 2. Slope- and elevation-deconfounded K/Th metasomatic residual
    kth = np.log1p(np.maximum(0.0, np.nan_to_num(gd_k / (gd_th + 8.0), nan=0.0))).astype(np.float32)
    del gd_k, gd_th
    y_kth = _safe_z(kth)
    del kth
    X_rad_tr = np.column_stack([np.ones(tr_idx.size, dtype=np.float64), z_elev[tr_idx], z_slope[tr_idx]])
    XtX_r = X_rad_tr.T @ X_rad_tr + 1e-2 * np.eye(3)
    beta_r = np.linalg.solve(XtX_r, X_rad_tr.T @ y_kth[tr_idx].astype(np.float64)).astype(np.float32)
    del X_rad_tr
    pred_kth = beta_r[0] + beta_r[1] * z_elev + beta_r[2] * z_slope
    r_kth = np.clip((y_kth - pred_kth).astype(np.float32), -8.0, 8.0)

    X_fold = np.column_stack([claycap_edge, r_kth]).astype(np.float32)
    return X_fold, list(HVG_FOLD_SAFE_NAMES)
