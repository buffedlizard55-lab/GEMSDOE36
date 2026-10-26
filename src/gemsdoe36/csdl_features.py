"""CSDL-36 feature engineering: Cross-Strike Displaced-Lag Shear/Offset Coherence,
Co-Signed Basement-Gravity Throw Covariance, 3-D Euler Sheet Structural Index, and
Lahontan-Deconfounded Hydrothermal Conduit Synthesis.

Addresses all four GVSC-36 audit flags (IR-GVSC36-01..04):
1. IR-GVSC36-01 (Clean ablation lineage):
   - EXP-1 (75 features = 59 BASE + 16 CSDL_STRUCTURAL_FEATURES) strictly isolates the
     Cross-Strike Displaced-Lag, Co-Signed Basement-Gravity Throw Covariance, and 3-D
     Euler Sheet Structural Index block with zero hydrothermal conduit features.
   - EXP-2 (87 features = 75 EXP-1 + 12 CSDL_CONDUIT_FEATURES) strictly isolates the
     marginal contribution of the 12 deconfounded INGENIOUS hydrothermal conduit features.
   - EXP-3 (87 features M_full + 74 features LiDAR-blind M_blind) strictly isolates the
     Relief-Conditioned LiDAR-Gap Bridge + Two-Regime Submodular 300 m Cover.
2. IR-GVSC36-02 (No detrended-elevation shoreline threshold):
   - Paleo-geothermal deposits (OpenEI GDR 1391 Paleo_Geothermal_Deposits_20230519.csv)
     are partitioned purely by mineralogical/structural deposit class (silica sinter /
     silicified fault breccia / hydrothermal explosion crater vs carbonate travertine /
     tufa outflow apron) without thresholding detrended local elevation (12_det_elev).
3. IR-GVSC36-03 (Pre-placement surface rank-correlation screening chronology):
   - Enforced in scripts/run_csdl36.py where compare_registry(..., dots=None) is executed
     and timestamped strictly prior to emit_two_regime_submodular_cover.
4. IR-GVSC36-04 (Exact programmatic feature counts):
   - BASE_FEATURES = 59, CSDL_STRUCTURAL_FEATURES = 16, CSDL_CONDUIT_FEATURES = 12,
     EXP1_FEATURES = 75, EXP2_FEATURES = 87, EXP3_BLIND_FEATURES = 73 (14 LiDAR columns
     removed: 13 lid_* base columns + csdl_lidar_polarity_worm).
"""

from __future__ import annotations

import csv
import gc
import io
import json
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy.ndimage import convolve, gaussian_filter

from gemsdoe36.gvsc_features import (
    BANNED_COLUMN_NAMES,
    BASE_FEATURES,
    IN_SITU_VENT_TYPES,
    LIDAR_BANDS,
    LIDAR_QUANT,
    NODATA_CUT,
    OUTFLOW_APRON_TYPES,
    FeatureStore,
    FootprintGrid,
    _ensure_base_59_columns,
    _fill_median,
    _grad_mag,
    _read_dbf_records,
    _robust_pos_z,
    dequantize,
    directional_worm_anisotropy,
    load_footprint_grid,
    strike_guided_projection,
    upgradient_backproject,
)

CSDL_STRUCTURAL_FEATURES: tuple[str, ...] = (
    "csdl_rtp_lag2_step",
    "csdl_rtp_lag5_step",
    "csdl_rtp_lag_persistence",
    "csdl_rtp_shear_offset_match",
    "csdl_mag_tilt_worm",
    "csdl_rtp_demag_trough",
    "csdl_euler_sheet_index",
    "csdl_up150_depth_persistence",
    "csdl_grav_thdr_2d",
    "csdl_grav_lag4_step",
    "csdl_base_lag4_step",
    "csdl_basement_grav_throw_cov",
    "csdl_mt_rad_fault_fluid",
    "csdl_piedmont_relief_deconf",
    "csdl_lidar_polarity_worm",
    "csdl_strike_tri_concordance",
)

CSDL_CONDUIT_FEATURES: tuple[str, ...] = (
    "csdl_vent_throat_local",
    "csdl_vent_strike_corridor",
    "csdl_apron_upgrad_backproj",
    "csdl_f2mdab_local",
    "csdl_f2mdab_survey_grad",
    "csdl_f2mdab_upgrad_backproj",
    "csdl_geotherm_upgrad_backproj",
    "csdl_total_upflow_potential",
    "csdl_conduit_x_lag_step",
    "csdl_conduit_x_throw_cov",
    "csdl_conduit_x_piedmont",
    "csdl_walker_transtensional_index",
)

EXP1_FEATURES: tuple[str, ...] = BASE_FEATURES + CSDL_STRUCTURAL_FEATURES
EXP2_FEATURES: tuple[str, ...] = BASE_FEATURES + CSDL_STRUCTURAL_FEATURES + CSDL_CONDUIT_FEATURES

LIDAR_FEATURE_SET: frozenset[str] = frozenset(
    n for n in EXP2_FEATURES if n.startswith("lid_") or n == "csdl_lidar_polarity_worm"
)
EXP3_BLIND_FEATURES: tuple[str, ...] = tuple(
    n for n in EXP2_FEATURES if n not in LIDAR_FEATURE_SET
)

assert len(BASE_FEATURES) == 59, f"Expected 59 BASE_FEATURES, got {len(BASE_FEATURES)}"
assert len(CSDL_STRUCTURAL_FEATURES) == 16, (
    f"Expected 16 CSDL_STRUCTURAL_FEATURES, got {len(CSDL_STRUCTURAL_FEATURES)}"
)
assert len(CSDL_CONDUIT_FEATURES) == 12, (
    f"Expected 12 CSDL_CONDUIT_FEATURES, got {len(CSDL_CONDUIT_FEATURES)}"
)
assert len(EXP1_FEATURES) == 75, f"Expected 75 EXP1_FEATURES, got {len(EXP1_FEATURES)}"
assert len(EXP2_FEATURES) == 87, f"Expected 87 EXP2_FEATURES, got {len(EXP2_FEATURES)}"
assert len(LIDAR_FEATURE_SET) == 14, f"Expected 14 LiDAR features, got {len(LIDAR_FEATURE_SET)}"
assert len(EXP3_BLIND_FEATURES) == 73, (
    f"Expected 73 EXP3_BLIND_FEATURES, got {len(EXP3_BLIND_FEATURES)}"
)

# Channels used by Regime-B concealed subsurface-conduit gate in EXP-3
CSDL_SUBSURFACE_GATE_NAMES: tuple[str, ...] = (
    "csdl_rtp_lag_persistence",
    "csdl_rtp_shear_offset_match",
    "csdl_basement_grav_throw_cov",
    "csdl_euler_sheet_index",
    "csdl_grav_lag4_step",
    "csdl_walker_transtensional_index",
)

CSDL_UPFLOW_GATE_NAMES: tuple[str, ...] = (
    "csdl_total_upflow_potential",
    "csdl_conduit_x_lag_step",
    "csdl_conduit_x_throw_cov",
    "csdl_mt_rad_fault_fluid",
    "csdl_f2mdab_upgrad_backproj",
)


@dataclass(frozen=True)
class DeconfoundedGeothermalInventory:
    """Summary of INGENIOUS geothermal records rasterized without det_elev shoreline bias."""

    paleo_throat_in_footprint: int
    paleo_apron_in_footprint: int
    temp2m_stations_in_footprint: int
    temp2m_positive_dab_in_footprint: int
    geochem_excess_in_footprint: int
    volcanic_vents_in_footprint: int


def _shift_2d(arr: np.ndarray, dr: int, dc: int) -> np.ndarray:
    """Fast edge-padded 2-D integer pixel translation."""
    h, w = arr.shape
    pad = max(abs(dr), abs(dc))
    if pad == 0:
        return arr.copy()
    p = np.pad(arr, pad, mode="edge")
    return p[pad + dr : pad + dr + h, pad + dc : pad + dc + w]


def _along_strike_kernel(theta_deg: float, half_len: int = 5) -> np.ndarray:
    """Oriented 1-D line integration kernel of length (2*half_len + 1) pixels."""
    size = 2 * half_len + 1
    k = np.zeros((size, size), dtype=np.float32)
    rad = np.deg2rad(theta_deg)
    dr = -np.sin(rad)
    dc = np.cos(rad)
    for t in np.linspace(-half_len, half_len, 2 * size + 1):
        r = int(round(half_len + t * dr))
        c = int(round(half_len + t * dc))
        if 0 <= r < size and 0 <= c < size:
            k[r, c] = 1.0
    s = float(k.sum())
    return k / max(s, 1.0)


def compute_cross_strike_lag_step(
    field: np.ndarray,
    lag_px: int,
    angles_deg: tuple[float, ...] = (0.0, 30.0, 60.0, 90.0, 120.0, 150.0),
    half_len: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Oriented cross-strike displaced-lag step coherence and dominant strike azimuth.

    For each strike orientation theta, evaluates |F(x + L*n_perp) - F(x - L*n_perp)|
    integrated along strike (theta) minus its orthogonal cross-strike average (theta+90).
    """
    f = np.nan_to_num(field, nan=0.0).astype(np.float32)
    best_step = np.zeros_like(f, dtype=np.float32)
    best_theta = np.zeros_like(f, dtype=np.float32)

    for theta in angles_deg:
        rad = np.deg2rad(theta)
        # Fault-normal unit vector n_perp = (-cos(theta), -sin(theta)) in (row, col)
        nr = int(round(-lag_px * np.cos(rad)))
        nc = int(round(-lag_px * np.sin(rad)))
        if nr == 0 and nc == 0:
            nr = 1
        step_abs = np.abs(_shift_2d(f, nr, nc) - _shift_2d(f, -nr, -nc))
        k_along = _along_strike_kernel(theta, half_len=half_len)
        k_cross = _along_strike_kernel((theta + 90.0) % 180.0, half_len=half_len)
        resp = np.maximum(
            0.0,
            convolve(step_abs, k_along, mode="nearest")
            - 0.75 * convolve(step_abs, k_cross, mode="nearest"),
        )
        better = resp > best_step
        best_step = np.where(better, resp, best_step)
        best_theta = np.where(better, np.float32(theta), best_theta)
    return best_step.astype(np.float32), best_theta.astype(np.float32)


def compute_shear_displaced_lag_match(
    field: np.ndarray,
    fp: np.ndarray,
    normal_lag_px: int = 2,
    shear_lag_px: int = 3,
    angles_deg: tuple[float, ...] = (0.0, 30.0, 60.0, 90.0, 120.0, 150.0),
) -> np.ndarray:
    """Along-strike displaced-lag shear offset coherence for oblique/strike-slip faults.

    Compares cross-strike gradient anomalies on opposite sides of the fault plane
    (+L*n_perp vs -L*n_perp) shifted laterally along strike by +/- shear_lag_px.
    """
    f = np.nan_to_num(field, nan=0.0).astype(np.float32)
    best_shear = np.zeros_like(f, dtype=np.float32)

    for theta in angles_deg:
        rad = np.deg2rad(theta)
        # Along-strike unit vector s_par = (-sin(theta), cos(theta))
        sr = int(round(-shear_lag_px * np.sin(rad)))
        sc = int(round(shear_lag_px * np.cos(rad)))
        # Cross-strike unit vector n_perp = (-cos(theta), -sin(theta))
        nr = int(round(-normal_lag_px * np.cos(rad)))
        nc = int(round(-normal_lag_px * np.sin(rad)))

        g_perp = _shift_2d(f, nr, nc) - _shift_2d(f, -nr, -nc)
        g_z = _robust_pos_z(np.abs(g_perp), fp)

        # Dextral (+s on +n side, -s on -n side) and Sinistral (-s on +n side, +s on -n side)
        pos_dext = _shift_2d(g_z, nr + sr, nc + sc) * _shift_2d(g_z, -nr - sr, -nc - sc)
        pos_sini = _shift_2d(g_z, nr - sr, nc - sc) * _shift_2d(g_z, -nr + sr, -nc + sc)
        raw_match = np.sqrt(np.maximum(0.0, np.maximum(pos_dext, pos_sini)))

        k_along = _along_strike_kernel(theta, half_len=5)
        coh = convolve(raw_match, k_along, mode="nearest")
        best_shear = np.maximum(best_shear, coh)
    return best_shear.astype(np.float32)


def compute_cosigned_basement_grav_throw_cov(
    depth_base: np.ndarray,
    grav_iso: np.ndarray,
    fp: np.ndarray,
    lag_px: int = 4,
    angles_deg: tuple[float, ...] = (0.0, 30.0, 60.0, 90.0, 120.0, 150.0),
) -> np.ndarray:
    """Co-signed basement depth vs isostatic gravity cross-strike throw covariance.

    A normal fault dropping denser pre-Tertiary basement downward on one side
    (Delta_perp D_base > 0) must produce a negative isostatic gravity step on that
    same hanging-wall side (Delta_perp g_iso < 0) due to low-density Cenozoic basin
    fill, so ReLU(-Delta_perp D_base * Delta_perp g_iso) > 0.
    """
    d_norm = np.nan_to_num(depth_base / (depth_base + 250.0), nan=0.0).astype(np.float32)
    g_med = float(np.median(grav_iso[fp]))
    g_mad = float(np.median(np.abs(grav_iso[fp] - g_med))) * 1.4826 + 1e-5
    g_norm = np.nan_to_num((grav_iso - g_med) / g_mad, nan=0.0).astype(np.float32)

    best_cov = np.zeros_like(d_norm, dtype=np.float32)
    for theta in angles_deg:
        rad = np.deg2rad(theta)
        nr = int(round(-lag_px * np.cos(rad)))
        nc = int(round(-lag_px * np.sin(rad)))
        if nr == 0 and nc == 0:
            nr = 1
        d_diff = _shift_2d(d_norm, nr, nc) - _shift_2d(d_norm, -nr, -nc)
        g_diff = _shift_2d(g_norm, nr, nc) - _shift_2d(g_norm, -nr, -nc)
        # Opposite-sign physical requirement: -d_diff * g_diff > 0
        cosigned = np.sqrt(np.maximum(0.0, -d_diff * g_diff))
        k_along = _along_strike_kernel(theta, half_len=5)
        coh = convolve(cosigned, k_along, mode="nearest")
        best_cov = np.maximum(best_cov, coh)
    return best_cov.astype(np.float32)


def compute_euler_sheet_index(
    tmi: np.ndarray,
    tmi_hg: np.ndarray,
    tmi_vg: np.ndarray,
    worm_mag: np.ndarray,
    fp: np.ndarray,
) -> np.ndarray:
    """3-D Euler homogeneity structural index filter selecting dipping sheets/contacts (N ~ 0.85).

    Suppresses equidimensional volcanic plugs/pipes and point dipoles (N >= 2.0).
    """
    local_anom = np.abs(tmi - gaussian_filter(tmi, 14.0)) + 2.5
    grad_total = np.abs(tmi_vg) + 0.5 * np.abs(tmi_hg)
    # Characteristic upper-crustal fault depth scale z0 ~ 3.0 grid cells (300 m)
    n_eff = (3.0 * grad_total) / local_anom
    sheet_selectivity = np.exp(-0.5 * ((n_eff - 0.85) / 0.55) ** 2).astype(np.float32)
    z_worm = _robust_pos_z(worm_mag, fp)
    return (sheet_selectivity * z_worm).astype(np.float32)


def rasterize_deconfounded_geothermal_layers(
    raw_dir: Path,
    grid: FootprintGrid,
) -> tuple[dict[str, np.ndarray], DeconfoundedGeothermalInventory]:
    """Rasterize OpenEI GDR 1391 INGENIOUS geothermal layers without det_elev shoreline thresholds."""
    ext = raw_dir / "external"
    h, w = grid.shape
    fp = grid.footprint
    tr = grid.transform

    vent_throat = np.zeros((h, w), dtype=np.float32)
    outflow_apron = np.zeros((h, w), dtype=np.float32)
    f2m_pos = np.zeros((h, w), dtype=np.float32)
    f2m_signed_sum = np.zeros((h, w), dtype=np.float32)
    f2m_count = np.zeros((h, w), dtype=np.float32)
    geotherm_imp = np.zeros((h, w), dtype=np.float32)
    volc_vent = np.zeros((h, w), dtype=np.float32)

    # 1. Paleo-geothermal deposits (DOE GDR 1391, NAD83 -> EPSG:32611)
    # Pure mineralogical/structural classification (fixing IR-GVSC36-02: zero det_elev threshold)
    paleo_zip = ext / "paleo_geothermal_regional.zip"
    n_throat = 0
    n_apron = 0
    with zipfile.ZipFile(paleo_zip) as zf:
        with zf.open("Paleo_geothermal_final.csv") as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="cp1252", errors="replace"))
            if reader.fieldnames and (set(reader.fieldnames) & BANNED_COLUMN_NAMES):
                raise ValueError("Banned column in Paleo_geothermal_final.csv")
            lons, lats, dtypes = [], [], []
            for row in reader:
                try:
                    lons.append(float(row["Long_deg_NAD83"]))
                    lats.append(float(row["Lat_deg_NAD83"]))
                    dtypes.append(row["Deposit_type"].strip())
                except (KeyError, TypeError, ValueError):
                    continue
    xs, ys = warp_transform("EPSG:4269", grid.crs, lons, lats)
    for x, y, dt in zip(xs, ys, dtypes, strict=True):
        c = int((x - tr.c) // tr.a)
        r = int((y - tr.f) // tr.e)
        if not (0 <= r < h and 0 <= c < w and fp[r, c]):
            continue
        if dt in IN_SITU_VENT_TYPES:
            wt = 1.25 if dt in ("Sinter", "Explosion craters", "Silicified fault breccia") else 1.0
            vent_throat[r, c] += np.float32(wt)
            n_throat += 1
        elif dt in OUTFLOW_APRON_TYPES:
            # Mineralogical differentiation only: Travertine (1.0) vs Tufa (0.65)
            wt = 0.65 if dt == "Tufa" else 1.0
            outflow_apron[r, c] += np.float32(wt)
            n_apron += 1

    # 2. 2-meter shallow temperature probes (DOE GDR 1391, NAD83 -> EPSG:32611)
    probe_zip = ext / "2m_temperature_probe_INGENIOUS_regional_data.zip"
    dbf_member = (
        "2m_temperature_probe_INGENIOUS_regional_data/"
        "2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf"
    )
    with zipfile.ZipFile(probe_zip) as zf:
        dbf_rows = _read_dbf_records(zf.read(dbf_member))
    p_lons, p_lats, p_dab = [], [], []
    for row in dbf_rows:
        try:
            lon = float(row["LongDegree"])
            lat = float(row["LatDegreeN"])
            dab = float(row["F2mDAB"])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(lon) and math.isfinite(lat) and math.isfinite(dab):
            p_lons.append(lon)
            p_lats.append(lat)
            p_dab.append(dab)
    pxs, pys = warp_transform("EPSG:4269", grid.crs, p_lons, p_lats)
    probe_n = 0
    probe_hot_n = 0
    for x, y, dab in zip(pxs, pys, p_dab, strict=True):
        c = int((x - tr.c) // tr.a)
        r = int((y - tr.f) // tr.e)
        if not (0 <= r < h and 0 <= c < w and fp[r, c]):
            continue
        probe_n += 1
        if dab >= 2.0:
            probe_hot_n += 1
        pos_anom = max(0.0, min(dab, 25.0))
        if pos_anom > f2m_pos[r, c]:
            f2m_pos[r, c] = np.float32(pos_anom)
        f2m_signed_sum[r, c] += np.float32(max(-8.0, min(dab, 25.0)))
        f2m_count[r, c] += 1.0

    # 3. Quaternary volcanic vents (explicitly strip dist_known_fault_px)
    n_volc_fp = 0
    with (ext / "gdr_volcanic_vents_in_footprint.csv").open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            row.pop("dist_known_fault_px", None)
            if set(row.keys()) & BANNED_COLUMN_NAMES:
                raise ValueError("Banned column remained in volcanic vents row")
            r = int(row["row"])
            c = int(row["col"])
            if 0 <= r < h and 0 <= c < w and fp[r, c]:
                volc_vent[r, c] += 1.0
                vent_throat[r, c] += 0.9
                n_volc_fp += 1

    # 4. Well/spring geothermometry (explicitly strip dist_known_fault_px)
    n_geochem_fp = 0
    with (ext / "gdr_wellspring_in_footprint.csv").open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            row.pop("dist_known_fault_px", None)
            if set(row.keys()) & BANNED_COLUMN_NAMES:
                raise ValueError("Banned column remained in wellspring row")
            r = int(row["row"])
            c = int(row["col"])
            if not (0 <= r < h and 0 <= c < w and fp[r, c]):
                continue
            n_geochem_fp += 1
            vals = []
            for k in ("geothermchalc_c", "geothermquartz_c", "geothermcat_c"):
                try:
                    v = float(row[k])
                    if math.isfinite(v) and 0.0 < v < 400.0:
                        vals.append(v)
                except (KeyError, TypeError, ValueError):
                    pass
            gt_ex = max(0.0, min((max(vals) - 60.0) if vals else 0.0, 180.0)) / 60.0
            try:
                tc = float(row["temp_c"])
                t_ex = max(0.0, min(tc - 16.0, 85.0)) / 30.0 if math.isfinite(tc) else 0.0
            except (KeyError, TypeError, ValueError):
                t_ex = 0.0
            score = np.float32(gt_ex + 0.6 * t_ex)
            if score > geotherm_imp[r, c]:
                geotherm_imp[r, c] = score

    inv = DeconfoundedGeothermalInventory(
        paleo_throat_in_footprint=n_throat,
        paleo_apron_in_footprint=n_apron,
        temp2m_stations_in_footprint=probe_n,
        temp2m_positive_dab_in_footprint=probe_hot_n,
        geochem_excess_in_footprint=n_geochem_fp,
        volcanic_vents_in_footprint=n_volc_fp,
    )
    return {
        "vent_throat": vent_throat,
        "outflow_apron": outflow_apron,
        "f2m_pos": f2m_pos,
        "f2m_signed_sum": f2m_signed_sum,
        "f2m_count": f2m_count,
        "geotherm_imp": geotherm_imp,
        "volc_vent": volc_vent,
    }, inv


def build_csdl_feature_store(
    cache_dir: Path | str = ".cache/csdl36_features",
    raw_dir: Path | str = "data/raw",
) -> tuple[FeatureStore, FootprintGrid, DeconfoundedGeothermalInventory]:
    """Build or load the 87-feature CSDL-36 feature store (59 Base + 16 Structural + 12 Conduit)."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    d = Path(raw_dir)
    grid = load_footprint_grid(d)
    fp = grid.footprint

    all_names = list(EXP2_FEATURES)
    meta_path = cache_dir / "meta.json"
    if meta_path.is_file() and all((cache_dir / f"{n}.npy").is_file() for n in all_names):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        inv = DeconfoundedGeothermalInventory(**meta["geothermal_inventory"])
        return FeatureStore(cache_dir, all_names, grid.n_fp), grid, inv

    def save_col(name: str, arr2d: np.ndarray) -> None:
        p = cache_dir / f"{name}.npy"
        np.save(p, np.asarray(arr2d[fp], dtype=np.float32))

    def _read_clean(src: rasterio.DatasetReader, idx: int) -> np.ndarray:
        a = src.read(idx).astype(np.float32)
        a[(a < NODATA_CUT) | (~fp)] = np.nan
        return _fill_median(a, fp)

    # 1. Ensure 59 BASE_FEATURES are present in cache_dir
    _ensure_base_59_columns(cache_dir, d, fp)

    # 2. Load raw organizer channels needed for CSDL_STRUCTURAL_FEATURES & CSDL_CONDUIT_FEATURES
    with rasterio.open(d / "training_features.tif") as src:
        rtp = _read_clean(src, 2)
        tmi_hg = _read_clean(src, 3)
        ieq = _read_clean(src, 4)
        geod_2nd = _read_clean(src, 6)
        geod_shear = _read_clean(src, 7)
        tmi_vg = _read_clean(src, 9)
        grav_vg = _read_clean(src, 11)
        det_elev = _read_clean(src, 12)
        grav_iso = _read_clean(src, 13)
        tmi = _read_clean(src, 14)
        depth_base = np.maximum(0.0, _read_clean(src, 15))
        cond_surf = np.maximum(1e-5, _read_clean(src, 17))
        grav_hg = _read_clean(src, 18)
        det_slope = np.maximum(0.0, _read_clean(src, 19))

    # ---- Block 2: CSDL_STRUCTURAL_FEATURES (16 features) ----
    # (1-3) Cross-strike displaced-lag RTP steps at lag=2 px (200 m) and lag=5 px (500 m)
    rtp_lag2, strike_rtp = compute_cross_strike_lag_step(rtp, lag_px=2)
    save_col("csdl_rtp_lag2_step", rtp_lag2)

    rtp_lag5, _ = compute_cross_strike_lag_step(rtp, lag_px=5)
    save_col("csdl_rtp_lag5_step", rtp_lag5)

    rtp_lag_pers = np.sqrt(
        _robust_pos_z(rtp_lag2, fp) * _robust_pos_z(rtp_lag5, fp)
    ).astype(np.float32)
    save_col("csdl_rtp_lag_persistence", rtp_lag_pers)
    del rtp_lag2, rtp_lag5

    # (4) Along-strike displaced-lag shear offset match (dextral/sinistral +/- 300 m)
    rtp_shear_match = compute_shear_displaced_lag_match(rtp, fp, normal_lag_px=2, shear_lag_px=3)
    save_col("csdl_rtp_shear_offset_match", rtp_shear_match)

    # (5) Magnetic tilt directional worm
    mag_tilt = np.arctan2(tmi_vg, np.abs(tmi_hg) + 1e-3).astype(np.float32)
    rtp_grad = _grad_mag(rtp, sigma=1.2)
    mag_thdr_log = np.log10(rtp_grad + 1e-3).astype(np.float32)
    worm_mag, _ = directional_worm_anisotropy(
        0.6 * _robust_pos_z(mag_thdr_log, fp) + 0.4 * _robust_pos_z( np.abs(mag_tilt), fp )
    )
    save_col("csdl_mag_tilt_worm", worm_mag)
    del mag_tilt, mag_thdr_log

    # (6) RTP hydrothermal demagnetization trough DoG
    rtp_demag = np.maximum(
        0.0, gaussian_filter(rtp, 8.0) - gaussian_filter(rtp, 1.5)
    ).astype(np.float32)
    save_col("csdl_rtp_demag_trough", rtp_demag)

    # (7) 3-D Euler homogeneity sheet structural index (N ~ 0.85 sheet vs N >= 2 pipe)
    euler_sheet = compute_euler_sheet_index(tmi, tmi_hg, tmi_vg, worm_mag, fp)
    save_col("csdl_euler_sheet_index", euler_sheet)
    del tmi, tmi_hg, tmi_vg, euler_sheet

    # (8) Upward-continued 150 m TMI cross-strike depth persistence
    with rasterio.open(d / "external" / "geodawn_extensions_u8.tif") as s_ext:
        tmi_up150_q = s_ext.read(4).astype(np.float32)
    tmi_up150 = _fill_median(np.where(tmi_up150_q > 0, tmi_up150_q, np.nan), fp)
    del tmi_up150_q
    up150_pers = np.clip(
        _grad_mag(tmi_up150, sigma=1.2) / (rtp_grad + 1e-2), 0.0, 5.0
    ).astype(np.float32)
    save_col("csdl_up150_depth_persistence", up150_pers)
    del tmi_up150, rtp_grad, up150_pers, rtp

    # (9) True 2-D horizontal/total gravity gradient (fixing 1-D gradient bias)
    grav_thdr = np.hypot(grav_hg, grav_vg).astype(np.float32)
    save_col("csdl_grav_thdr_2d", grav_thdr)
    del grav_hg, grav_vg

    # (10) Cross-strike gravity lag-4 step (400 m half-lag)
    grav_lag4, strike_grav = compute_cross_strike_lag_step(grav_iso, lag_px=4)
    save_col("csdl_grav_lag4_step", grav_lag4)

    # (11) Cross-strike relative basement-depth lag-4 step
    base_rel = (depth_base / (depth_base + 250.0)).astype(np.float32)
    base_lag4, _ = compute_cross_strike_lag_step(base_rel, lag_px=4)
    save_col("csdl_base_lag4_step", base_lag4)
    del base_rel, base_lag4

    # (12) Co-signed basement-depth vs isostatic gravity throw covariance
    throw_cov = compute_cosigned_basement_grav_throw_cov(depth_base, grav_iso, fp, lag_px=4)
    save_col("csdl_basement_grav_throw_cov", throw_cov)
    del depth_base, grav_iso, grav_thdr

    # (13) MT conductivity edge co-aligned with radiometric K/Th alteration
    mt_edge = _grad_mag(np.log10(cond_surf), sigma=1.5)
    del cond_surf
    with rasterio.open(d / "external" / "geodawn_rad_u8.tif") as s_rad:
        k_q = s_rad.read(1).astype(np.float32)
        th_q = s_rad.read(2).astype(np.float32)
    k_f = _fill_median(np.where(k_q > 0, k_q, np.nan), fp)
    th_f = _fill_median(np.where(th_q > 0, th_q, np.nan), fp)
    k_th = k_f / (th_f + 4.0)
    rad_kth_anom = (gaussian_filter(k_th, 1.5) - gaussian_filter(k_th, 12.0)).astype(np.float32)
    del k_q, th_q, k_f, th_f, k_th
    mt_rad_fluid = (
        0.5 * _robust_pos_z(mt_edge, fp) + 0.5 * _robust_pos_z(rad_kth_anom, fp)
    ).astype(np.float32)
    save_col("csdl_mt_rad_fault_fluid", mt_rad_fluid)
    del mt_edge, rad_kth_anom

    # (14) Relief-deconfounded piedmont break directional worm
    slope_break = _grad_mag(det_slope, sigma=1.0)
    relief_scale = gaussian_filter(np.abs(det_elev), 20.0) + 12.0
    piedmont_deconf = (
        slope_break / ((gaussian_filter(det_slope, 14.0) + 1.0) * np.sqrt(relief_scale))
    ).astype(np.float32)
    worm_piedmont, strike_pied = directional_worm_anisotropy(_robust_pos_z(piedmont_deconf, fp))
    save_col("csdl_piedmont_relief_deconf", worm_piedmont)
    del slope_break, relief_scale, piedmont_deconf, det_slope

    # (15) 1 m LiDAR scarp polarity-consistent directional worm (NaN preserved inside 24.63% gaps)
    with rasterio.open(d / "external" / "lidar_scarp_features_u8.tif") as s_lid:
        step_idx = LIDAR_BANDS.index("step_max") + 1
        coh_idx = LIDAR_BANDS.index("coh100") + 1
        down_idx = LIDAR_BANDS.index("downface_max") + 1
        up_idx = LIDAR_BANDS.index("upface_max") + 1
        val_idx = LIDAR_BANDS.index("valid") + 1
        lid_step = dequantize(s_lid.read(step_idx), *LIDAR_QUANT["step_max"])
        lid_coh = dequantize(s_lid.read(coh_idx), *LIDAR_QUANT["coh100"])
        lid_down = dequantize(s_lid.read(down_idx), *LIDAR_QUANT["downface_max"])
        lid_up = dequantize(s_lid.read(up_idx), *LIDAR_QUANT["upface_max"])
        lid_valid = dequantize(s_lid.read(val_idx), *LIDAR_QUANT["valid"])
    pol_asym = np.abs(np.nan_to_num(lid_down, nan=0.0) - np.nan_to_num(lid_up, nan=0.0)) / (
        np.nan_to_num(lid_down, nan=0.0) + np.nan_to_num(lid_up, nan=0.0) + 0.05
    )
    lid_strength = (
        np.nan_to_num(lid_step, nan=0.0)
        * np.nan_to_num(lid_coh, nan=0.0)
        * (0.5 + 0.5 * pol_asym)
    )
    worm_lid_raw, _ = directional_worm_anisotropy(lid_strength)
    has_lid = np.isfinite(lid_valid) & (lid_valid > 0.5) & np.isfinite(lid_step)
    save_col("csdl_lidar_polarity_worm", np.where(has_lid, worm_lid_raw, np.nan).astype(np.float32))
    del lid_step, lid_coh, lid_down, lid_up, lid_valid, pol_asym, lid_strength, worm_lid_raw, has_lid

    # (16) Three-layer strike concordance (RTP lag strike, Gravity lag strike, Piedmont strike)
    c_rg = np.abs(np.cos(np.deg2rad(2.0 * (strike_rtp - strike_grav))))
    c_pg = np.abs(np.cos(np.deg2rad(2.0 * (strike_pied - strike_grav))))
    c_rp = np.abs(np.cos(np.deg2rad(2.0 * (strike_rtp - strike_pied))))
    tri_concord = ((c_rg + c_pg + c_rp) / 3.0).astype(np.float32)
    save_col("csdl_strike_tri_concordance", tri_concord)
    del strike_rtp, strike_grav, c_rg, c_pg, c_rp, tri_concord
    gc.collect()

    # ---- Block 3: CSDL_CONDUIT_FEATURES (12 Lahontan-deconfounded conduit & regime features) ----
    gt_rasters, inv_stats = rasterize_deconfounded_geothermal_layers(d, grid)

    z_reg = gaussian_filter(det_elev, 12.0)
    gz_r, gz_c = np.gradient(z_reg)
    gnorm = np.hypot(gz_r, gz_c) + np.float32(2.0)
    u_up_r = (gz_r / gnorm).astype(np.float32)
    u_up_c = (gz_c / gnorm).astype(np.float32)
    del det_elev, z_reg, gz_r, gz_c, gnorm

    vent_throat = gt_rasters["vent_throat"]
    vent_local = (
        gaussian_filter(vent_throat, 3.0) - gaussian_filter(vent_throat, 18.0)
    ).astype(np.float32)
    save_col("csdl_vent_throat_local", vent_local)
    del vent_local

    vent_strike = strike_guided_projection(vent_throat, strike_pied)
    vent_strike_local = np.maximum(
        0.0, vent_strike - 0.65 * gaussian_filter(vent_throat, 18.0)
    ).astype(np.float32)
    save_col("csdl_vent_strike_corridor", vent_strike_local)
    del vent_throat, vent_strike, strike_pied

    apron_bp = upgradient_backproject(gt_rasters["outflow_apron"], u_up_r, u_up_c)
    apron_bp_local = np.maximum(
        0.0, apron_bp - 0.65 * gaussian_filter(gt_rasters["outflow_apron"], 22.0)
    ).astype(np.float32)
    save_col("csdl_apron_upgrad_backproj", apron_bp_local)
    del apron_bp

    f2m_pos = gt_rasters["f2m_pos"]
    f2m_local = (
        gaussian_filter(f2m_pos, 3.0) - 0.70 * gaussian_filter(f2m_pos, 18.0)
    ).astype(np.float32)
    save_col("csdl_f2mdab_local", f2m_local)
    del f2m_local

    cnt_smooth = gaussian_filter(gt_rasters["f2m_count"], 4.0)
    sum_smooth = gaussian_filter(gt_rasters["f2m_signed_sum"], 4.0)
    in_survey = cnt_smooth > 0.015
    local_mean_dab = np.where(in_survey, sum_smooth / (cnt_smooth + 0.02), 0.0).astype(np.float32)
    f2m_grad = np.where(
        cnt_smooth > 0.03, _grad_mag(local_mean_dab, sigma=1.5), 0.0
    ).astype(np.float32)
    save_col("csdl_f2mdab_survey_grad", f2m_grad)
    del cnt_smooth, sum_smooth, in_survey, local_mean_dab, f2m_grad

    f2m_bp = upgradient_backproject(f2m_pos, u_up_r, u_up_c)
    f2m_bp_local = np.maximum(
        0.0, f2m_bp - 0.65 * gaussian_filter(f2m_pos, 22.0)
    ).astype(np.float32)
    save_col("csdl_f2mdab_upgrad_backproj", f2m_bp_local)
    del f2m_pos, f2m_bp

    geotherm_imp = gt_rasters["geotherm_imp"]
    gt_bp = upgradient_backproject(geotherm_imp, u_up_r, u_up_c)
    gt_bp_local = np.maximum(
        0.0, gt_bp - 0.65 * gaussian_filter(geotherm_imp, 22.0)
    ).astype(np.float32)
    save_col("csdl_geotherm_upgrad_backproj", gt_bp_local)
    del geotherm_imp, gt_bp, u_up_r, u_up_c

    upflow_pot = (
        0.30 * _robust_pos_z(vent_strike_local, fp)
        + 0.20 * _robust_pos_z(apron_bp_local, fp)
        + 0.30 * _robust_pos_z(f2m_bp_local, fp)
        + 0.20 * _robust_pos_z(gt_bp_local, fp)
    ).astype(np.float32)
    save_col("csdl_total_upflow_potential", upflow_pot)
    del vent_strike_local, apron_bp_local, f2m_bp_local, gt_bp_local

    z_lag = 0.5 * _robust_pos_z(rtp_lag_pers, fp) + 0.5 * _robust_pos_z(grav_lag4, fp)
    z_throw = _robust_pos_z(throw_cov, fp)
    z_pied = _robust_pos_z(worm_piedmont, fp)
    z_demag = _robust_pos_z(rtp_demag, fp)

    save_col(
        "csdl_conduit_x_lag_step",
        (upflow_pot * z_lag * (0.5 + 0.5 * z_demag)).astype(np.float32),
    )
    save_col("csdl_conduit_x_throw_cov", (upflow_pot * z_throw).astype(np.float32))
    save_col("csdl_conduit_x_piedmont", (upflow_pot * z_pied).astype(np.float32))

    # Walker Lane / oblique transtensional coupling index:
    # combines GPS shear strain, 2nd invariant, displaced-lag shear match, and volcanic vent corridors
    volc_corridor = np.maximum(
        0.0,
        gaussian_filter(gt_rasters["volc_vent"], 6.0)
        - gaussian_filter(gt_rasters["volc_vent"], 25.0),
    )
    z_shear = 0.5 * _robust_pos_z(geod_shear, fp) + 0.5 * _robust_pos_z(geod_2nd, fp)
    z_offset = 0.6 * _robust_pos_z(rtp_shear_match, fp) + 0.4 * _robust_pos_z(worm_mag, fp)
    walker_idx = (
        np.log1p(z_shear * (z_offset + 0.35 * _robust_pos_z(volc_corridor, fp)))
        - 0.35 * np.log1p(_robust_pos_z(ieq, fp))
    ).astype(np.float32)
    save_col("csdl_walker_transtensional_index", walker_idx)

    del (
        gt_rasters,
        rtp_lag_pers,
        rtp_shear_match,
        worm_mag,
        rtp_demag,
        grav_lag4,
        throw_cov,
        mt_rad_fluid,
        worm_piedmont,
        upflow_pot,
        z_lag,
        z_throw,
        z_pied,
        z_demag,
        volc_corridor,
        geod_shear,
        geod_2nd,
        ieq,
        walker_idx,
    )
    gc.collect()

    meta = {
        "lane_id": "CSDL-36",
        "names": all_names,
        "n_fp": int(grid.n_fp),
        "counts": {
            "base": len(BASE_FEATURES),
            "csdl_structural": len(CSDL_STRUCTURAL_FEATURES),
            "csdl_conduit": len(CSDL_CONDUIT_FEATURES),
            "exp1_total": len(EXP1_FEATURES),
            "exp2_total": len(EXP2_FEATURES),
            "exp3_blind_total": len(EXP3_BLIND_FEATURES),
            "lidar_features_removed_in_blind": len(LIDAR_FEATURE_SET),
        },
        "geothermal_inventory": inv_stats.__dict__,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return FeatureStore(cache_dir, all_names, grid.n_fp), grid, inv_stats
