"""ATVR-36 Memory-Bounded Physical Feature Stack & Fold-Safe Deconfounding.

Constructs and caches 1D footprint-indexed float32 memmaps (<400 MB peak RAM on
3.8 GiB / 0 Swap) strictly from physical observables:
  - RAW19 (all 19 official competition bands from ``.cache/gems_work/bands/``,
    sentinel-sanitized: ``01_mag_anom`` .. ``19_det_elev_slope``)
  - H36-A (Verduzco magnetic tilt/THDR + gravity directional grid-gradient obliquity
    angle/THDR, multi-scale Hessian scarp/toe curvatures of ``12_det_elev``, 2.5 km
    relief-deconfounded slope & radiometric total-count ``06_tc`` contrasts,
    missingness-aware USGS 3DEP 1 m LiDAR scarp ratios, plus fold-only
    visible-catalogue Anderson alignment)
  - H36-B (Hydrothermal magnetite-destruction band-pass trough on ``02_rtp``,
    USGS GeoDAWN K/Th & TMI_up150, DOE GDR 1391 physical well/spring
    geothermometers strictly excluding ``dist_known_fault_px``, plus fold-regressed
    playa-deconfounded ``17_cond_surf`` clay-cap residual)
  - H36-C (``15_depth_to_base_surf`` flexural hinge curvature x gravity THDR
    concordance, declustered/instrumental seismic + geodetic strain-rate corridor,
    and continuous 3-regime Mountain / Piedmont / Basin weights)

Hard integrity guardrails:
  - NEVER reads ``derived_sgmc_faults_100m_u8.tif`` or ``gdr_qfaults_traces.csv``
  - NEVER reads ``dist_known_fault_px`` from ``gdr_wellspring_in_footprint.csv``
  - NEVER reads any prior scored or registry submission raster
"""

from __future__ import annotations

import csv
import gc
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
from sklearn.linear_model import Ridge

from .anderson_dip import local_extension_field
from .paths import data_dir, work_dir
from .variational_anderson import anderson_alignment_field, structure_tensor_orientation

RAW19_NAMES: tuple[str, ...] = (
    "01_mag_anom",
    "02_rtp",
    "03_tmi_hg",
    "04_geod_2ndinv",
    "05_iso_grav_anom_slope",
    "06_tc",
    "07_geod_shearrate",
    "08_geod_dilaterate",
    "09_tmi_vg",
    "10_deq_n100a15",
    "11_iso_grav_anom_vg",
    "12_det_elev",
    "13_iso_grav_anom",
    "14_tmi",
    "15_depth_to_base_surf",
    "16_ieq_n100a15",
    "17_cond_surf",
    "18_iso_grav_anom_hg",
    "19_det_elev_slope",
)

H36A_STATIC_NAMES: tuple[str, ...] = (
    "h36a_grav_tilt",
    "h36a_grav_thdr",
    "h36a_mag_tilt",
    "h36a_mag_thdr",
    "h36a_joint_potential_concord",
    "h36a_elev_hessian_ridge_s2",
    "h36a_elev_hessian_trough_s2",
    "h36a_elev_dog_2_8",
    "h36a_slope_rel_relief25",
    "h36a_tc_rel_relief25",
    "h36a_piedmont_zone_score",
    "h36a_lidar_valid",
    "h36a_lidar_scarp_break",
    "h36a_lidar_toe_crest_sym",
    "h36a_lidar_coh100",
    "h36a_grav_hessian_ridge_s3",
)

H36B_STATIC_NAMES: tuple[str, ...] = (
    "h36b_rtp_trough_2_15",
    "h36b_rtp_trough_x_tilt",
    "h36b_cond_surf_local_anom",
    "h36b_geodawn_k_th_ratio",
    "h36b_geodawn_tmi_trough",
    "h36b_gdr_geotherm_chalc_idw",
    "h36b_gdr_thermal_spring_idw",
)

H36C_STATIC_NAMES: tuple[str, ...] = (
    "h36c_basement_grad",
    "h36c_basement_flexure",
    "h36c_basement_grav_concord",
    "h36c_seismic_strain_corridor",
    "h36c_regime_piedmont_prob",
    "h36c_regime_basin_prob",
)

ALL_STATIC_NAMES: tuple[str, ...] = (
    RAW19_NAMES + H36A_STATIC_NAMES + H36B_STATIC_NAMES + H36C_STATIC_NAMES
)

BANNED_PATH_TOKENS: tuple[str, ...] = (
    "sgmc",
    "qfaults",
    "scored/",
    "focus_registry",
    "downloads/",
)


def _assert_safe_source(path: Path) -> None:
    s = str(path).lower()
    for tok in BANNED_PATH_TOKENS:
        if tok in s:
            raise RuntimeError(f"ATVR-36 integrity violation: banned input path {path}")


def _hessian_eigs_2d(field: np.ndarray, sigma_px: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (ridge_pos_curv, trough_pos_curv) of Gaussian-smoothed 2D field."""
    sm = gaussian_filter(field.astype(np.float32, copy=False), sigma=sigma_px)
    gy, gx = np.gradient(sm)
    hyy, hyx = np.gradient(gy)
    hxy, hxx = np.gradient(gx)
    hxy = 0.5 * (hxy + hyx)
    del sm, gx, gy, hyx
    tr = hxx + hyy
    disc = np.hypot(hxx - hyy, 2.0 * hxy)
    ridge = np.maximum(0.0, 0.5 * (disc - tr)).astype(np.float32)
    trough = np.maximum(0.0, 0.5 * (tr + disc)).astype(np.float32)
    return ridge, trough


def _grad_mag_2d(field: np.ndarray, sigma_px: float = 1.0) -> np.ndarray:
    sm = (
        gaussian_filter(field.astype(np.float32, copy=False), sigma=sigma_px)
        if sigma_px > 0
        else field.astype(np.float32, copy=False)
    )
    gy, gx = np.gradient(sm)
    return np.hypot(gx, gy).astype(np.float32)


def _robust_z_on_foot(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    vals = arr[foot]
    finite = vals[np.isfinite(vals)]
    if finite.size == 0:
        return np.zeros_like(arr, dtype=np.float32)
    med = float(np.median(finite))
    iqr = float(np.percentile(finite, 75) - np.percentile(finite, 25))
    scale = max(iqr / 1.349, 1e-6)
    out = np.zeros_like(arr, dtype=np.float32)
    out[foot] = ((arr[foot] - med) / scale).astype(np.float32)
    return out


def _rasterize_gdr_geothermometers(
    csv_path: Path,
    shape: tuple[int, int],
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Build smooth physical geothermometer & thermal-spring density fields from GDR 1391.

    Explicitly ignores ``dist_known_fault_px`` so zero catalogue distance can leak.
    """
    _assert_safe_source(csv_path)
    h, w = shape
    chalc_num = np.zeros((h, w), dtype=np.float32)
    chalc_den = np.zeros((h, w), dtype=np.float32)
    therm_imp = np.zeros((h, w), dtype=np.float32)

    allowed_cols = {"row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"}
    with csv_path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, TypeError, ValueError):
                continue
            if not (0 <= r < h and 0 <= c < w):
                continue

            vals_t: list[float] = []
            for k in ("geothermchalc_c", "geothermquartz_c", "geothermcat_c"):
                assert k in allowed_cols
                raw_v = (row.get(k) or "").strip()
                if raw_v and raw_v.upper() != "NULL":
                    try:
                        v = float(raw_v)
                        if 20.0 <= v <= 380.0:
                            vals_t.append(v)
                    except ValueError:
                        pass
            if vals_t:
                t_est = float(np.median(vals_t))
                chalc_num[r, c] += max(0.0, t_est - 40.0)
                chalc_den[r, c] += 1.0

            raw_temp = (row.get("temp_c") or "").strip()
            if raw_temp and raw_temp.upper() != "NULL":
                try:
                    tc = float(raw_temp)
                    if 25.0 <= tc <= 250.0:
                        therm_imp[r, c] += max(0.0, tc - 20.0)
                except ValueError:
                    pass

    num_sm = 0.65 * gaussian_filter(chalc_num, sigma=15.0) + 0.35 * gaussian_filter(chalc_num, sigma=40.0)
    den_sm = 0.65 * gaussian_filter(chalc_den, sigma=15.0) + 0.35 * gaussian_filter(chalc_den, sigma=40.0)
    chalc_field = (num_sm / (den_sm + 1e-4)).astype(np.float32)

    therm_field = (
        0.7 * gaussian_filter(np.log1p(therm_imp), sigma=12.0)
        + 0.3 * gaussian_filter(np.log1p(therm_imp), sigma=30.0)
    ).astype(np.float32)
    chalc_field[~foot] = 0.0
    therm_field[~foot] = 0.0
    return chalc_field, therm_field


@dataclass(frozen=True)
class StaticFeatureCache:
    cache_dir: Path
    footprint: np.ndarray
    labels: np.ndarray
    foot_rows: np.ndarray
    foot_cols: np.ndarray
    feature_names: tuple[str, ...]
    memmap_path: Path
    potential_normal_path: Path
    potential_coherence_path: Path

    def open_matrix(self) -> np.memmap:
        return np.memmap(
            self.memmap_path,
            dtype=np.float32,
            mode="r",
            shape=(len(self.foot_rows), len(self.feature_names)),
        )


def build_or_load_static_feature_cache(
    *,
    bands_dir: Path | None = None,
    ext_root: Path | None = None,
    cache_dir: Path | None = None,
    force_rebuild: bool = False,
) -> StaticFeatureCache:
    """Build or reopen the footprint-indexed ATVR-36 static physical feature memmap."""
    b_dir = bands_dir or (work_dir() / "bands")
    d_root = ext_root or data_dir()
    c_dir = cache_dir or (work_dir() / "atvr_features_v1")
    c_dir.mkdir(parents=True, exist_ok=True)

    foot = np.load(b_dir / "_footprint.npy").astype(bool)
    labels = np.load(b_dir / "_labels.npy").astype(np.float32)
    foot_rc = np.argwhere(foot)
    foot_rows = np.ascontiguousarray(foot_rc[:, 0], dtype=np.int32)
    foot_cols = np.ascontiguousarray(foot_rc[:, 1], dtype=np.int32)
    n_foot = len(foot_rows)
    n_feat = len(ALL_STATIC_NAMES)

    mm_path = c_dir / "static_features_f32.mmap"
    meta_path = c_dir / "metadata.json"
    pot_norm_path = c_dir / "potential_normal_f32.npy"
    pot_coh_path = c_dir / "potential_coherence_f32.npy"

    if (
        not force_rebuild
        and mm_path.exists()
        and meta_path.exists()
        and pot_norm_path.exists()
        and pot_coh_path.exists()
    ):
        meta = json.loads(meta_path.read_text())
        if (
            meta.get("feature_names") == list(ALL_STATIC_NAMES)
            and meta.get("n_foot") == n_foot
            and mm_path.stat().st_size == n_foot * n_feat * 4
        ):
            return StaticFeatureCache(
                cache_dir=c_dir,
                footprint=foot,
                labels=labels,
                foot_rows=foot_rows,
                foot_cols=foot_cols,
                feature_names=ALL_STATIC_NAMES,
                memmap_path=mm_path,
                potential_normal_path=pot_norm_path,
                potential_coherence_path=pot_coh_path,
            )

    mm = np.memmap(mm_path, dtype=np.float32, mode="w+", shape=(n_foot, n_feat))
    name_to_col = {name: i for i, name in enumerate(ALL_STATIC_NAMES)}

    def _load_band(name: str) -> np.ndarray:
        p = b_dir / f"{name}.npy"
        _assert_safe_source(p)
        arr = np.load(p).astype(np.float32)
        arr[~foot] = 0.0
        return np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

    def _write_col(name: str, grid2d: np.ndarray) -> None:
        mm[:, name_to_col[name]] = grid2d[foot_rows, foot_cols].astype(np.float32, copy=False)

    # 1. RAW19 bands
    for bname in RAW19_NAMES:
        arr = _load_band(bname)
        _write_col(bname, arr)
        del arr
    mm.flush()

    # 2. H36-A Verduzco gravity/magnetic tilt & THDR + topographic scarp/piedmont features
    grav_hg = np.abs(_load_band("18_iso_grav_anom_hg"))
    grav_vg = _load_band("11_iso_grav_anom_vg")
    grav_tilt = np.arctan2(grav_vg, grav_hg + 1e-5).astype(np.float32)
    grav_tilt[~foot] = 0.0
    grav_thdr = _grad_mag_2d(grav_tilt, sigma_px=1.2)
    grav_thdr[~foot] = 0.0
    grav_ridge_s3, _ = _hessian_eigs_2d(grav_hg, sigma_px=3.0)
    grav_ridge_s3[~foot] = 0.0
    _write_col("h36a_grav_tilt", grav_tilt)
    _write_col("h36a_grav_thdr", grav_thdr)
    _write_col("h36a_grav_hessian_ridge_s3", grav_ridge_s3)
    del grav_hg, grav_vg, grav_tilt, grav_ridge_s3

    tmi_hg = np.abs(_load_band("03_tmi_hg"))
    tmi_vg = _load_band("09_tmi_vg")
    mag_tilt = np.arctan2(tmi_vg, tmi_hg + 1e-5).astype(np.float32)
    mag_tilt[~foot] = 0.0
    mag_thdr = _grad_mag_2d(mag_tilt, sigma_px=1.2)
    mag_thdr[~foot] = 0.0
    joint_pot = np.sqrt(np.maximum(0.0, grav_thdr * mag_thdr)).astype(np.float32)
    _write_col("h36a_mag_tilt", mag_tilt)
    _write_col("h36a_mag_thdr", mag_thdr)
    _write_col("h36a_joint_potential_concord", joint_pot)
    del tmi_hg, tmi_vg, mag_tilt

    det_elev = _load_band("12_det_elev")
    det_slope = np.abs(_load_band("19_det_elev_slope"))
    tc = np.abs(_load_band("06_tc"))

    elev_ridge_s2, elev_trough_s2 = _hessian_eigs_2d(det_elev, sigma_px=2.0)
    elev_dog = (
        gaussian_filter(det_elev, sigma=2.0) - gaussian_filter(det_elev, sigma=8.0)
    ).astype(np.float32)

    slope_bg25 = gaussian_filter(det_slope, sigma=25.0).astype(np.float32)
    tc_bg25 = gaussian_filter(tc, sigma=25.0).astype(np.float32)
    slope_pad = max(float(np.median(det_slope[foot])) * 0.25, 1e-4)
    tc_pad = max(float(np.median(tc[foot])) * 0.25, 1e-4)
    slope_rel = (det_slope / (slope_bg25 + slope_pad)).astype(np.float32)
    tc_rel = (tc / (tc_bg25 + tc_pad)).astype(np.float32)

    # Regional 2.5 km relief dispersion for Mountain / Piedmont / Basin partitioning
    elev_m25 = gaussian_filter(det_elev, sigma=25.0)
    elev_sq25 = gaussian_filter(det_elev * det_elev, sigma=25.0)
    elev_std25 = np.sqrt(np.maximum(0.0, elev_sq25 - elev_m25 * elev_m25)).astype(np.float32)
    del elev_m25, elev_sq25

    std_p50 = float(np.percentile(elev_std25[foot], 50))
    std_iqr = max(float(np.percentile(elev_std25[foot], 75) - np.percentile(elev_std25[foot], 25)), 1e-4)
    slp_p60 = float(np.percentile(det_slope[foot], 60))
    slp_iqr = max(float(np.percentile(det_slope[foot], 75) - np.percentile(det_slope[foot], 25)), 1e-4)

    near_range = 1.0 / (1.0 + np.exp(-((elev_std25 - std_p50) / (0.5 * std_iqr))))
    apron_slope = 1.0 / (1.0 + np.exp((det_slope - slp_p60) / (0.4 * slp_iqr)))
    piedmont_prob = np.clip(near_range * apron_slope, 0.0, 1.0).astype(np.float32)
    basin_prob = np.clip((1.0 - near_range) * apron_slope, 0.0, 1.0).astype(np.float32)

    _write_col("h36a_elev_hessian_ridge_s2", elev_ridge_s2)
    _write_col("h36a_elev_hessian_trough_s2", elev_trough_s2)
    _write_col("h36a_elev_dog_2_8", elev_dog)
    _write_col("h36a_slope_rel_relief25", slope_rel)
    _write_col("h36a_tc_rel_relief25", tc_rel)
    _write_col("h36a_piedmont_zone_score", piedmont_prob)
    _write_col("h36c_regime_piedmont_prob", piedmont_prob)
    _write_col("h36c_regime_basin_prob", basin_prob)

    comp_struct = (
        0.45 * _robust_z_on_foot(joint_pot, foot)
        + 0.35 * _robust_z_on_foot(grav_thdr, foot)
        + 0.20 * _robust_z_on_foot(elev_trough_s2, foot)
    ).astype(np.float32)
    pot_norm, pot_coh, _, _ = structure_tensor_orientation(
        comp_struct, foot, grad_sigma_px=1.0, tensor_sigma_px=2.5
    )
    np.save(pot_norm_path, pot_norm[foot_rows, foot_cols].astype(np.float32))
    np.save(pot_coh_path, pot_coh[foot_rows, foot_cols].astype(np.float32))
    del (
        det_elev,
        det_slope,
        tc,
        elev_ridge_s2,
        elev_trough_s2,
        elev_dog,
        slope_bg25,
        tc_bg25,
        slope_rel,
        tc_rel,
        elev_std25,
        near_range,
        apron_slope,
        piedmont_prob,
        basin_prob,
        comp_struct,
        pot_norm,
        pot_coh,
        joint_pot,
    )
    gc.collect()

    # 3. USGS 3DEP 1 m LiDAR missingness-aware features
    lidar_path = d_root / "external" / "lidar_scarp_features_u8.tif"
    _assert_safe_source(lidar_path)
    with rasterio.open(lidar_path) as src:
        lidar_valid = (src.read(12) > 0) & foot
        step_max = src.read(3).astype(np.float32)
        lapneg = src.read(4).astype(np.float32)
        lappos = src.read(5).astype(np.float32)
        relief_l = src.read(9).astype(np.float32)
        coh100 = src.read(10).astype(np.float32)

    valid_f = lidar_valid.astype(np.float32)
    scarp_break = np.full(foot.shape, np.nan, dtype=np.float32)
    scarp_break[lidar_valid] = step_max[lidar_valid] / (relief_l[lidar_valid] + 12.0)
    toe_crest = np.full(foot.shape, np.nan, dtype=np.float32)
    toe_crest[lidar_valid] = np.sqrt(lapneg[lidar_valid] * lappos[lidar_valid]) / (relief_l[lidar_valid] + 12.0)
    coh_f = np.full(foot.shape, np.nan, dtype=np.float32)
    coh_f[lidar_valid] = coh100[lidar_valid] / 255.0

    _write_col("h36a_lidar_valid", valid_f)
    _write_col("h36a_lidar_scarp_break", scarp_break)
    _write_col("h36a_lidar_toe_crest_sym", toe_crest)
    _write_col("h36a_lidar_coh100", coh_f)
    del lidar_valid, step_max, lapneg, lappos, relief_l, coh100, valid_f, scarp_break, toe_crest, coh_f
    gc.collect()

    # 4. H36-B Hydrothermal Magnetite-Destruction RTP Trough + GeoDAWN + GDR 1391
    rtp = _load_band("02_rtp")
    rtp_trough = np.maximum(0.0, gaussian_filter(rtp, sigma=15.0) - gaussian_filter(rtp, sigma=2.0)).astype(
        np.float32
    )
    rtp_trough[~foot] = 0.0
    rtp_trough_x_tilt = (rtp_trough * mag_thdr).astype(np.float32)
    _write_col("h36b_rtp_trough_2_15", rtp_trough)
    _write_col("h36b_rtp_trough_x_tilt", rtp_trough_x_tilt)
    del rtp, rtp_trough, rtp_trough_x_tilt, mag_thdr

    cond_surf = _load_band("17_cond_surf")
    cond_local = (cond_surf - gaussian_filter(cond_surf, sigma=20.0)).astype(np.float32)
    cond_local[~foot] = 0.0
    _write_col("h36b_cond_surf_local_anom", cond_local)
    del cond_surf, cond_local

    gd_rad_path = d_root / "external" / "geodawn_rad_u8.tif"
    gd_ext_path = d_root / "external" / "geodawn_extensions_u8.tif"
    _assert_safe_source(gd_rad_path)
    _assert_safe_source(gd_ext_path)
    with rasterio.open(gd_rad_path) as src:
        k_band = src.read(1).astype(np.float32)
        th_band = src.read(2).astype(np.float32)
        gd_valid = ((k_band > 0) | (th_band > 0)) & foot
    k_th = np.full(foot.shape, np.nan, dtype=np.float32)
    k_th[gd_valid] = (k_band[gd_valid] + 1.0) / (th_band[gd_valid] + 8.0)
    _write_col("h36b_geodawn_k_th_ratio", k_th)
    del k_band, th_band, gd_valid, k_th

    with rasterio.open(gd_ext_path) as src:
        tmi_u8 = src.read(4).astype(np.float32)
        tmi_valid = (tmi_u8 > 0) & foot
    tmi_fill = np.where(
        tmi_valid, tmi_u8, float(np.median(tmi_u8[tmi_valid])) if tmi_valid.any() else 0.0
    ).astype(np.float32)
    tmi_trough_raw = gaussian_filter(tmi_fill, sigma=10.0) - gaussian_filter(tmi_fill, sigma=1.2)
    tmi_trough = np.full(foot.shape, np.nan, dtype=np.float32)
    tmi_trough[tmi_valid] = tmi_trough_raw[tmi_valid].astype(np.float32)
    _write_col("h36b_geodawn_tmi_trough", tmi_trough)
    del tmi_u8, tmi_valid, tmi_fill, tmi_trough_raw, tmi_trough

    gdr_csv = d_root / "external" / "gdr_wellspring_in_footprint.csv"
    chalc_f, therm_f = _rasterize_gdr_geothermometers(gdr_csv, foot.shape, foot)
    _write_col("h36b_gdr_geotherm_chalc_idw", chalc_f)
    _write_col("h36b_gdr_thermal_spring_idw", therm_f)
    del chalc_f, therm_f
    gc.collect()

    # 5. H36-C Basement Flexural Hinge & Seismic/Geodetic Strain Corridor
    basement = _load_band("15_depth_to_base_surf")
    base_grad = _grad_mag_2d(basement, sigma_px=2.0)
    base_grad[~foot] = 0.0
    base_flex, _ = _hessian_eigs_2d(basement, sigma_px=4.0)
    base_flex[~foot] = 0.0
    base_grav_concord = (
        np.maximum(0.0, _robust_z_on_foot(base_grad, foot))
        * np.maximum(0.0, _robust_z_on_foot(grav_thdr, foot))
    ).astype(np.float32)
    _write_col("h36c_basement_grad", base_grad)
    _write_col("h36c_basement_flexure", base_flex)
    _write_col("h36c_basement_grav_concord", base_grav_concord)
    del basement, base_grad, base_flex, base_grav_concord, grav_thdr

    deq = _load_band("10_deq_n100a15")
    ieq = _load_band("16_ieq_n100a15")
    shear = np.abs(_load_band("07_geod_shearrate"))
    dilate = _load_band("08_geod_dilaterate")
    seis_strain = (
        0.40 * _robust_z_on_foot(deq, foot)
        + 0.30 * _robust_z_on_foot(ieq, foot)
        + 0.15 * _robust_z_on_foot(shear, foot)
        + 0.15 * _robust_z_on_foot(dilate, foot)
    ).astype(np.float32)
    seis_strain[~foot] = 0.0
    _write_col("h36c_seismic_strain_corridor", seis_strain)
    del deq, ieq, shear, dilate, seis_strain

    mm.flush()
    mm = None
    gc.collect()

    meta_path.write_text(
        json.dumps(
            {
                "schema": "gems36.atvr_features.v1",
                "n_foot": n_foot,
                "feature_names": list(ALL_STATIC_NAMES),
                "banned_tokens_enforced": list(BANNED_PATH_TOKENS),
            },
            indent=2,
        )
    )
    return StaticFeatureCache(
        cache_dir=c_dir,
        footprint=foot,
        labels=labels,
        foot_rows=foot_rows,
        foot_cols=foot_cols,
        feature_names=ALL_STATIC_NAMES,
        memmap_path=mm_path,
        potential_normal_path=pot_norm_path,
        potential_coherence_path=pot_coh_path,
    )


def compute_fold_anderson_feature(
    cache: StaticFeatureCache,
    visible_fault_mask: np.ndarray,
) -> tuple[np.ndarray, object]:
    """Compute fold-safe Anderson alignment feature & ExtensionField strictly from visible_k."""
    ext = local_extension_field(visible_fault_mask)
    pot_norm = np.load(cache.potential_normal_path)
    pot_coh = np.load(cache.potential_coherence_path)

    full_norm = np.zeros(cache.footprint.shape, dtype=np.float32)
    full_norm[cache.foot_rows, cache.foot_cols] = pot_norm
    align2d = anderson_alignment_field(full_norm, ext)
    feat_foot = (
        align2d[cache.foot_rows, cache.foot_cols]
        * pot_coh
        * ext.confidence[cache.foot_rows, cache.foot_cols]
    ).astype(np.float32)
    return feat_foot, ext


def compute_fold_playa_cond_residual(
    cache: StaticFeatureCache,
    train_foot_mask: np.ndarray,
) -> np.ndarray:
    """Fit playa/depth surface-conductivity baseline strictly on train_foot_mask and return residual.

    Regresses ``17_cond_surf`` on ``[15_depth_to_base_surf, 19_det_elev_slope, 12_det_elev,
    h36c_regime_basin_prob]`` using training-fold pixels only, deconfounding closed-basin
    evaporite playas from fault-hosted smectite/illite hydrothermal clay caps.
    """
    mm = cache.open_matrix()
    name_to_idx = {n: i for i, n in enumerate(cache.feature_names)}
    raw_cond = mm[:, name_to_idx["17_cond_surf"]].astype(np.float32)
    X_reg = np.column_stack(
        [
            mm[:, name_to_idx["15_depth_to_base_surf"]],
            mm[:, name_to_idx["19_det_elev_slope"]],
            mm[:, name_to_idx["12_det_elev"]],
            mm[:, name_to_idx["h36c_regime_basin_prob"]],
        ]
    ).astype(np.float32)
    X_reg = np.nan_to_num(X_reg, nan=0.0, posinf=0.0, neginf=0.0)
    y_all = np.nan_to_num(raw_cond, nan=0.0, posinf=0.0, neginf=0.0)

    tr_idx = np.flatnonzero(train_foot_mask)
    if len(tr_idx) > 200_000:
        rng = np.random.default_rng(3601)
        tr_idx = rng.choice(tr_idx, size=200_000, replace=False)

    mu = X_reg[tr_idx].mean(axis=0, dtype=np.float64).astype(np.float32)
    sd = np.maximum(X_reg[tr_idx].std(axis=0, dtype=np.float64).astype(np.float32), 1e-5)
    X_std = ((X_reg - mu) / sd).astype(np.float32)

    reg = Ridge(alpha=10.0, random_state=36)
    reg.fit(X_std[tr_idx], y_all[tr_idx])
    pred = reg.predict(X_std).astype(np.float32)
    return (y_all - pred).astype(np.float32)
