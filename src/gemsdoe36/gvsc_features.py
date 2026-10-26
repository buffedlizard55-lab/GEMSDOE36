"""GVSC-36: Geothermal Vent-Conduit Strike-Projected & Structural Feature Builder.

Implements the preregistered label-free physical feature stack for lane ``GVSC-36``
(``docs/research/preregistration-gvsc36-20261026.md``):

1. ``BASE_FEATURES`` (59 columns): exact reuse of ``gemsdoe36.h36_features`` multi-sensor
   stack (19 GeoDAWN/INGENIOUS bands + 18 isotropic context/anomaly bands + 14 dequantized
   USGS 3DEP 1 m LiDAR scarp bands + 8 GeoDAWN radiometric/upward-continued bands).
2. ``SA_FEATURES`` (16 columns): Verduzco depth-invariant magnetic tilt, magnetite-destruction
   RTP trough, 150 m upward-continuation attenuation, true 2-D horizontal gravity gradient
   magnitude (fixing ``IR-36-ATVR-03``), relative basement-step gradient, MT smectite clay-cap
   lateral edge, relief-deconfounded 10 m piedmont breakline, 8-azimuth 1.5 km directional
   strike-anisotropy worms, surface-to-basement strike concordance, K/Th alteration excess,
   and brittle strain-to-seismicity localization.
3. ``GVSC_FEATURES`` (14 columns): Official DOE OpenEI GDR 1391 INGENIOUS geothermal vent
   & shallow thermal-plume features (``paleo_geothermal_regional.zip``: 281 footprint sinter,
   explosion-crater, silicified-breccia, travertine, silica-cemented-sand, and Lahontan-
   deweighted tufa deposits; ``2m_temperature_probe_INGENIOUS_regional_data.zip``: 2,782
   footprint ``F2mDAB`` shallow probes across 34 survey areas; ``gdr_volcanic_vents``: 21
   Quaternary vents; ``gdr_wellspring``: chalcedony/quartz/Na-K-Ca geothermometers) mapped
   onto candidate fault conduits via Up-Hydraulic-Gradient Plume Back-Projection and
   multiplicative structural-worm corroboration.

Strict anti-leakage contract:
- Never opens ``labels.tif``, ``existing_faults.tif``, ``derived_sgmc_faults_100m_u8.tif``,
  ``gdr_qfaults_traces.csv``, or any registry/scored submission raster.
- Explicitly strips ``dist_known_fault_px`` before parsing ``gdr_wellspring_in_footprint.csv``
  and ``gdr_volcanic_vents_in_footprint.csv``.
"""

from __future__ import annotations

import csv
import gc
import io
import json
import math
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform as warp_transform
from scipy.ndimage import gaussian_filter, map_coordinates

from gemsdoe36.h36_features import (
    LIDAR_BANDS,
    LIDAR_QUANT,
    NODATA_CUT,
    FeatureStore,
    dequantize,
)
from gemsdoe36.paths import repo_root

N_AZIMUTHS = 8
WORM_HALF_PX = 7  # 2 * 7 + 1 = 15 px = 1.5 km lineament integration window

BASE_FEATURES: tuple[str, ...] = (
    "org_mag_anom",
    "org_rtp",
    "org_tmi_hg",
    "org_geod_2ndinv",
    "org_iso_grav_anom_slope",
    "org_tc",
    "org_geod_shearrate",
    "org_geod_dilaterate",
    "org_tmi_vg",
    "org_deq_n100a15",
    "org_iso_grav_anom_vg",
    "org_det_elev",
    "org_iso_grav_anom",
    "org_tmi",
    "org_depth_to_base_surf",
    "org_ieq_n100a15",
    "org_cond_surf",
    "org_iso_grav_anom_hg",
    "org_det_elev_slope",
    "ctx_rtp_g3",
    "ctx_rtp_anom3",
    "ctx_rtp_g10",
    "ctx_tmi_hg_g3",
    "ctx_tmi_hg_anom3",
    "ctx_tmi_hg_g10",
    "ctx_det_elev_g3",
    "ctx_det_elev_anom3",
    "ctx_det_elev_g10",
    "ctx_iso_grav_anom_g3",
    "ctx_iso_grav_anom_anom3",
    "ctx_iso_grav_anom_g10",
    "ctx_iso_grav_anom_hg_g3",
    "ctx_iso_grav_anom_hg_anom3",
    "ctx_iso_grav_anom_hg_g10",
    "ctx_det_elev_slope_g3",
    "ctx_det_elev_slope_anom3",
    "ctx_det_elev_slope_g10",
    "lid_ex_max",
    "lid_ex_mean",
    "lid_step_max",
    "lid_lapneg_max",
    "lid_lappos_max",
    "lid_downface_max",
    "lid_upface_max",
    "lid_cross_max",
    "lid_relief",
    "lid_coh100",
    "lid_strike_cos2",
    "lid_strike_sin2",
    "lid_valid",
    "ctx_lid_step_g3",
    "gd_K",
    "gd_Th",
    "gd_U",
    "gd_TC",
    "gd_ThK",
    "gd_UK",
    "gd_UTh",
    "gd_TMI_up150",
)


@dataclass(frozen=True)
class FootprintGrid:
    footprint: np.ndarray
    crs: str
    transform: rasterio.Affine
    shape: tuple[int, int]

    @property
    def n_fp(self) -> int:
        return int(self.footprint.sum())


def load_footprint_grid(data_dir: Path | None = None) -> FootprintGrid:
    """Load competition grid and active footprint strictly from ``sample_submission.tif``."""
    d = data_dir or (repo_root() / "data" / "raw")
    with rasterio.open(d / "sample_submission.tif") as src:
        fp = np.isfinite(src.read(1))
        crs = str(src.crs)
        tr = src.transform
        shape = (int(src.height), int(src.width))
    return FootprintGrid(footprint=fp, crs=crs, transform=tr, shape=shape)

SA_FEATURES: tuple[str, ...] = (
    "sa_mag_tilt",
    "sa_mag_thdr_log",
    "sa_rtp_trough_dog",
    "sa_mag_atten_150m",
    "sa_grav_thdr",
    "sa_grav_tilt_ridge",
    "sa_base_step_rel",
    "sa_mt_cond_edge",
    "sa_worm_mag",
    "sa_worm_grav_base",
    "sa_piedmont_break",
    "sa_worm_piedmont",
    "sa_worm_lidar",
    "sa_strike_concordance",
    "sa_rad_k_th_anom",
    "sa_strain_seis_ratio",
)

GVSC_FEATURES: tuple[str, ...] = (
    "gvsc_vent_throat_local",
    "gvsc_vent_strike_corridor",
    "gvsc_apron_backproj",
    "gvsc_f2mdab_local",
    "gvsc_f2mdab_grad",
    "gvsc_f2mdab_backproj",
    "gvsc_geotherm_backproj",
    "gvsc_total_upflow_potential",
    "gvsc_conduit_x_piedmont",
    "gvsc_conduit_x_mag_demag",
    "gvsc_conduit_x_grav_base",
    "gvsc_conduit_x_mt_rad",
    "gvsc_volcanic_dike_worm",
    "gvsc_hydro_alteration_composite",
)

EXP1_FEATURES: tuple[str, ...] = BASE_FEATURES + SA_FEATURES
EXP2_FEATURES: tuple[str, ...] = BASE_FEATURES + SA_FEATURES + GVSC_FEATURES
LIDAR_FEATURE_SET: frozenset[str] = frozenset(
    n for n in EXP2_FEATURES if n.startswith("lid_") or "lid_" in n or n == "sa_worm_lidar"
)
EXP3_BLIND_FEATURES: tuple[str, ...] = tuple(
    n for n in EXP2_FEATURES if n not in LIDAR_FEATURE_SET
)

BANNED_COLUMN_NAMES: frozenset[str] = frozenset(
    {"dist_known_fault_px", "fault_dist", "dist_fault", "label", "labels", "existing_faults"}
)

IN_SITU_VENT_TYPES: frozenset[str] = frozenset(
    {
        "Sinter",
        "Explosion craters",
        "Silicified fault breccia",
        "Alteration",
        "Sulfur",
        "Calcite-qtz veins",
        "Silica vein",
        "Quartzite",
    }
)
OUTFLOW_APRON_TYPES: frozenset[str] = frozenset(
    {"Travertine", "Silica-cemented sand", "Tufa"}
)


@dataclass(frozen=True)
class GeothermalInventoryStats:
    paleo_in_situ_count: int
    paleo_apron_count: int
    paleo_lahontan_tufa_deweighted: int
    probe_2m_count: int
    probe_2m_hot_gt2c_count: int
    volcanic_vent_count: int
    wellspring_count: int


def _fill_median(arr: np.ndarray, fp: np.ndarray) -> np.ndarray:
    valid = fp & np.isfinite(arr)
    med = float(np.median(arr[valid])) if valid.any() else 0.0
    return np.where(np.isfinite(arr), arr, med).astype(np.float32)


def _robust_pos_z(arr: np.ndarray, fp: np.ndarray, clip_max: float = 8.0) -> np.ndarray:
    vals = arr[fp & np.isfinite(arr)]
    if vals.size == 0:
        return np.zeros_like(arr, dtype=np.float32)
    med = float(np.median(vals))
    iqr = float(np.percentile(vals, 75.0) - np.percentile(vals, 25.0))
    scale = max(iqr / 1.349, 1e-5)
    z = (np.nan_to_num(arr, nan=med) - med) / scale
    return np.clip(z, 0.0, clip_max).astype(np.float32)


def _grad_mag(arr: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    s = gaussian_filter(arr.astype(np.float32), sigma) if sigma > 0 else arr.astype(np.float32)
    gy, gx = np.gradient(s)
    return np.hypot(gy, gx).astype(np.float32)


def build_sparse_line_taps(
    theta_deg: float, half_len: int = WORM_HALF_PX
) -> list[tuple[int, int, float]]:
    """Build bilinearly splatted unit-sum sparse taps for a line of azimuth ``theta_deg``.

    ``theta_deg`` is measured clockwise from North (``0`` = N-S along rows,
    ``90`` = E-W along cols), matching geological strike convention.
    """
    rad = math.radians(theta_deg)
    dr = -math.cos(rad)
    dc = math.sin(rad)
    weights: dict[tuple[int, int], float] = {}
    for t in range(-half_len, half_len + 1):
        ry = t * dr
        cx = t * dc
        r0 = math.floor(ry)
        c0 = math.floor(cx)
        wy = ry - r0
        wx = cx - c0
        for ir, wr in ((r0, 1.0 - wy), (r0 + 1, wy)):
            for ic, wc in ((c0, 1.0 - wx), (c0 + 1, wx)):
                w = wr * wc
                if w > 1e-6:
                    ir_c = max(-half_len, min(half_len, ir))
                    ic_c = max(-half_len, min(half_len, ic))
                    weights[(ir_c, ic_c)] = weights.get((ir_c, ic_c), 0.0) + w
    total = sum(weights.values())
    return [(r, c, float(w / total)) for (r, c), w in sorted(weights.items())]


_LINE_TAPS_8: tuple[list[tuple[int, int, float]], ...] = tuple(
    build_sparse_line_taps(k * (180.0 / N_AZIMUTHS), WORM_HALF_PX)
    for k in range(N_AZIMUTHS)
)


def directional_worm_anisotropy(
    field: np.ndarray,
    *,
    ortho_penalty: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute 8-azimuth 1.5 km strike-lineament anisotropy and dominant strike azimuth.

    Returns ``(anisotropy, strike_deg)`` as ``float32`` arrays of ``field.shape``.
    For each azimuth ``theta_k``, scores ``L(theta_k) - ortho_penalty * L(theta_k + 90 deg)``,
    suppressing isotropic blobs, plutons, and circular playas while preserving planar faults.
    """
    h, w = field.shape
    pad = WORM_HALF_PX
    padded = np.pad(np.nan_to_num(field, nan=0.0).astype(np.float32), pad, mode="edge")
    responses = np.empty((N_AZIMUTHS, h, w), dtype=np.float32)
    for k, taps in enumerate(_LINE_TAPS_8):
        acc = np.zeros((h, w), dtype=np.float32)
        for dy, dx, wt in taps:
            acc += wt * padded[pad + dy : pad + dy + h, pad + dx : pad + dx + w]
        responses[k] = acc
    del padded

    best_aniso = np.full((h, w), -1e30, dtype=np.float32)
    best_k = np.zeros((h, w), dtype=np.int16)
    half_az = N_AZIMUTHS // 2
    for k in range(N_AZIMUTHS):
        k_ortho = (k + half_az) % N_AZIMUTHS
        aniso = responses[k] - np.float32(ortho_penalty) * responses[k_ortho]
        better = aniso > best_aniso
        best_aniso = np.where(better, aniso, best_aniso)
        best_k = np.where(better, k, best_k)
    del responses
    strike_deg = (best_k.astype(np.float32) * np.float32(180.0 / N_AZIMUTHS))
    return np.maximum(best_aniso, 0.0).astype(np.float32), strike_deg


def strike_guided_projection(
    impulse: np.ndarray,
    strike_deg: np.ndarray,
) -> np.ndarray:
    """Project point impulses along the local dominant geophysical/geomorphic strike."""
    h, w = impulse.shape
    pad = WORM_HALF_PX
    base = gaussian_filter(impulse.astype(np.float32), 2.0)
    padded = np.pad(base, pad, mode="constant", constant_values=0.0)
    out = np.zeros((h, w), dtype=np.float32)
    step_deg = 180.0 / N_AZIMUTHS
    k_idx = (np.rint(strike_deg / step_deg).astype(np.int32)) % N_AZIMUTHS
    for k, taps in enumerate(_LINE_TAPS_8):
        mask = k_idx == k
        if not mask.any():
            continue
        acc = np.zeros((h, w), dtype=np.float32)
        for dy, dx, wt in taps:
            acc += wt * padded[pad + dy : pad + dy + h, pad + dx : pad + dx + w]
        out = np.where(mask, acc, out)
    return out


def upgradient_backproject(
    plume_field: np.ndarray,
    u_up_r: np.ndarray,
    u_up_c: np.ndarray,
    *,
    shifts_px: tuple[float, ...] = (4.0, 8.0, 14.0, 20.0),
    sigmas_px: tuple[float, ...] = (2.5, 4.0, 6.0, 8.5),
    weights: tuple[float, ...] = (0.35, 0.30, 0.20, 0.15),
    chunk_rows: int = 512,
) -> np.ndarray:
    """Advectively back-project downslope geothermal outflow plumes onto upslope faults.

    At candidate fault cell ``x = (r, c)``, downslope fluid outflow sits in direction
    ``-u_up(x)``, i.e. at ``(r - s * u_up_r[r, c], c - s * u_up_c[r, c])``. Evaluating the
    multi-scale smoothed plume at ``x - s * u_up(x)`` places peak conduit potential
    0.4--2.0 km upslope of shallow thermal anomalies and outflow springs.
    """
    h, w = plume_field.shape
    out = np.zeros((h, w), dtype=np.float32)
    cols = np.arange(w, dtype=np.float32)[None, :]
    for s_px, sig, wt in zip(shifts_px, sigmas_px, weights, strict=True):
        smoothed = gaussian_filter(plume_field.astype(np.float32), sig)
        for r0 in range(0, h, chunk_rows):
            r1 = min(h, r0 + chunk_rows)
            rows = np.arange(r0, r1, dtype=np.float32)[:, None]
            sample_r = rows - np.float32(s_px) * u_up_r[r0:r1]
            sample_c = cols - np.float32(s_px) * u_up_c[r0:r1]
            coords = np.stack([sample_r, np.broadcast_to(sample_c, sample_r.shape)], axis=0)
            sampled = map_coordinates(smoothed, coords, order=1, mode="nearest")
            out[r0:r1] += np.float32(wt) * sampled.astype(np.float32)
        del smoothed
    return out


def _read_dbf_records(raw_dbf: bytes) -> list[dict[str, str]]:
    num_rec, hdr_len, rec_len = struct.unpack("<IHH", raw_dbf[4:12])
    fields: list[tuple[str, int]] = []
    pos = 32
    while raw_dbf[pos] != 0x0D:
        fname = raw_dbf[pos : pos + 11].split(b"\x00", 1)[0].decode("ascii", "replace")
        if fname.lower() in BANNED_COLUMN_NAMES:
            raise ValueError(f"Banned label/fault column {fname!r} encountered in DBF")
        flen = raw_dbf[pos + 16]
        fields.append((fname, flen))
        pos += 32

    records: list[dict[str, str]] = []
    for i in range(num_rec):
        rec = raw_dbf[hdr_len + i * rec_len : hdr_len + (i + 1) * rec_len]
        if len(rec) < rec_len or rec[0:1] == b"*":
            continue
        off = 1
        row_dict: dict[str, str] = {}
        for fname, flen in fields:
            row_dict[fname] = rec[off : off + flen].decode("cp1252", "replace").strip()
            off += flen
        records.append(row_dict)
    return records


def rasterize_ingenious_geothermal_layers(
    data_dir: Path,
    grid: FootprintGrid,
    det_elev_filled: np.ndarray,
) -> tuple[dict[str, np.ndarray], GeothermalInventoryStats]:
    """Load and rasterize label-free INGENIOUS geothermal vent & 2 m probe layers."""
    ext = data_dir / "external"
    fp = grid.footprint
    h, w = grid.shape
    tr = grid.transform

    vent_throat = np.zeros((h, w), dtype=np.float32)
    outflow_apron = np.zeros((h, w), dtype=np.float32)
    f2m_pos = np.zeros((h, w), dtype=np.float32)
    f2m_signed_sum = np.zeros((h, w), dtype=np.float32)
    f2m_count = np.zeros((h, w), dtype=np.float32)
    volc_vent = np.zeros((h, w), dtype=np.float32)
    geotherm_imp = np.zeros((h, w), dtype=np.float32)

    # 1. Paleo-geothermal deposits (DOE GDR 1391, NAD83 -> EPSG:32611)
    paleo_zip = ext / "paleo_geothermal_regional.zip"
    in_situ_n = 0
    apron_n = 0
    lahontan_tufa_n = 0
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
            in_situ_n += 1
        elif dt in OUTFLOW_APRON_TYPES:
            wt = 1.0
            if dt == "Tufa" and float(det_elev_filled[r, c]) <= -60.0:
                # Suppress basin-floor Pleistocene Lake Lahontan shoreline/playa tufa mimicry
                # (12_det_elev is detrended local relief in metres; basin lakebeds sit <= -60 m)
                wt = 0.35
                lahontan_tufa_n += 1
            outflow_apron[r, c] += np.float32(wt)
            apron_n += 1

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
    volc_n = 0
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
                volc_n += 1

    # 4. Well/spring geothermometry (explicitly strip dist_known_fault_px)
    ws_n = 0
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
            ws_n += 1
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

    stats = GeothermalInventoryStats(
        paleo_in_situ_count=in_situ_n,
        paleo_apron_count=apron_n,
        paleo_lahontan_tufa_deweighted=lahontan_tufa_n,
        probe_2m_count=probe_n,
        probe_2m_hot_gt2c_count=probe_hot_n,
        volcanic_vent_count=volc_n,
        wellspring_count=ws_n,
    )
    rasters = {
        "vent_throat": vent_throat,
        "outflow_apron": outflow_apron,
        "f2m_pos": f2m_pos,
        "f2m_signed_sum": f2m_signed_sum,
        "f2m_count": f2m_count,
        "volc_vent": volc_vent,
        "geotherm_imp": geotherm_imp,
    }
    return rasters, stats


def _ensure_base_59_columns(
    cache_dir: Path, d: Path, fp: np.ndarray, *, force: bool = False
) -> None:
    if not force and all((cache_dir / f"{n}.npy").exists() for n in BASE_FEATURES):
        return

    def add(name: str, full: np.ndarray) -> None:
        np.save(cache_dir / f"{name}.npy", np.asarray(full[fp], dtype=np.float32))

    ctx_targets = (
        "det_elev",
        "det_elev_slope",
        "iso_grav_anom",
        "iso_grav_anom_hg",
        "tmi_hg",
        "rtp",
    )
    ctx_bands: dict[str, np.ndarray] = {}
    with rasterio.open(d / "training_features.tif") as src:
        band_names = [
            desc.split(" - ")[0] if desc else f"b{i + 1}"
            for i, desc in enumerate(src.descriptions)
        ]
        for i, name in enumerate(band_names, start=1):
            a = src.read(i).astype(np.float32)
            a[a < NODATA_CUT] = np.nan
            add(f"org_{name}", a)
            if name in ctx_targets:
                ctx_bands[name] = a

    for name, a in ctx_bands.items():
        filled = np.where(np.isfinite(a), a, np.nanmedian(a[fp])).astype(np.float32)
        for sig in (3.0, 10.0):
            g = gaussian_filter(filled, sig)
            add(f"ctx_{name}_g{int(sig)}", g)
            if sig == 3.0:
                add(f"ctx_{name}_anom3", filled - g)
    del ctx_bands
    gc.collect()

    step_max = None
    with rasterio.open(d / "external" / "lidar_scarp_features_u8.tif") as s_lid:
        for i, name in enumerate(LIDAR_BANDS, start=1):
            q = s_lid.read(i)
            xmax, t = LIDAR_QUANT[name]
            x = dequantize(q, xmax, t)
            if name == "strike":
                th = np.deg2rad(x)
                add("lid_strike_cos2", np.cos(2.0 * th))
                add("lid_strike_sin2", np.sin(2.0 * th))
            else:
                if name == "step_max":
                    step_max = x
                add(f"lid_{name}", x)
    assert step_max is not None
    add("ctx_lid_step_g3", gaussian_filter(np.nan_to_num(step_max, nan=0.0), 3.0))
    del step_max

    for fname, bnames in (
        ("geodawn_rad_u8.tif", ("K", "Th", "U", "TC")),
        ("geodawn_extensions_u8.tif", ("ThK", "UK", "UTh", "TMI_up150")),
    ):
        with rasterio.open(d / "external" / fname) as s_gd:
            for i, name in enumerate(bnames, start=1):
                q = s_gd.read(i).astype(np.float32)
                add(f"gd_{name}", np.where(q > 0, q, np.nan))
    gc.collect()


def build_gvsc_feature_store(
    cache_dir: Path,
    *,
    data_dir: Path | None = None,
    force: bool = False,
) -> tuple[FeatureStore, FootprintGrid, GeothermalInventoryStats]:
    """Build or reopen the 89-feature GVSC-36 footprint store in ``cache_dir``."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    d = data_dir or (repo_root() / "data" / "raw")
    meta_path = cache_dir / "gvsc36_features.json"

    grid = load_footprint_grid(d)
    fp = grid.footprint

    all_names = list(EXP2_FEATURES)
    if meta_path.exists() and not force:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("names") == all_names and all(
            (cache_dir / f"{n}.npy").exists() for n in all_names
        ):
            inv = GeothermalInventoryStats(**meta["geothermal_inventory"])
            return FeatureStore(cache_dir, all_names, grid.n_fp), grid, inv

    _ensure_base_59_columns(cache_dir, d, fp, force=force)

    def save_col(name: str, full2d: np.ndarray) -> None:
        np.save(cache_dir / f"{name}.npy", np.asarray(full2d[fp], dtype=np.float32))

    # Load required raw 2D rasters (never labels or existing_faults!)
    wanted_bands = {
        "rtp",
        "tmi_hg",
        "geod_2ndinv",
        "geod_shearrate",
        "tmi_vg",
        "iso_grav_anom_vg",
        "det_elev",
        "iso_grav_anom",
        "depth_to_base_surf",
        "ieq_n100a15",
        "cond_surf",
        "iso_grav_anom_hg",
        "det_elev_slope",
    }
    raw_bands: dict[str, np.ndarray] = {}
    with rasterio.open(d / "training_features.tif") as src:
        for i, desc in enumerate(src.descriptions, start=1):
            bname = desc.split(" - ")[0] if desc else f"b{i}"
            if bname in wanted_bands:
                arr = src.read(i).astype(np.float32)
                arr[arr < NODATA_CUT] = np.nan
                raw_bands[bname] = arr

    det_elev = _fill_median(raw_bands["det_elev"], fp)
    det_slope = _fill_median(raw_bands["det_elev_slope"], fp)
    rtp = _fill_median(raw_bands["rtp"], fp)
    tmi_hg = _fill_median(raw_bands["tmi_hg"], fp)
    tmi_vg = _fill_median(raw_bands["tmi_vg"], fp)
    grav = _fill_median(raw_bands["iso_grav_anom"], fp)
    grav_hg = _fill_median(raw_bands["iso_grav_anom_hg"], fp)
    grav_vg = _fill_median(raw_bands["iso_grav_anom_vg"], fp)
    depth_base = np.maximum(_fill_median(raw_bands["depth_to_base_surf"], fp), 0.0)
    cond_surf = np.maximum(_fill_median(raw_bands["cond_surf"], fp), 1e-4)
    geod_2nd = _fill_median(raw_bands["geod_2ndinv"], fp)
    geod_shear = _fill_median(raw_bands["geod_shearrate"], fp)
    ieq = _fill_median(raw_bands["ieq_n100a15"], fp)
    del raw_bands
    gc.collect()

    # ---- Block 2: SA_FEATURES (16 structural anisotropy & subsurface physics features) ----
    mag_tilt = np.arctan2(tmi_vg, np.abs(tmi_hg) + 1e-3).astype(np.float32)
    save_col("sa_mag_tilt", mag_tilt)
    del tmi_hg, tmi_vg

    rtp_grad = _grad_mag(rtp, sigma=1.2)
    mag_thdr_log = np.log10(rtp_grad + 1e-3).astype(np.float32)
    save_col("sa_mag_thdr_log", mag_thdr_log)

    rtp_trough_dog = np.maximum(
        0.0, gaussian_filter(rtp, 8.0) - gaussian_filter(rtp, 1.5)
    ).astype(np.float32)
    save_col("sa_rtp_trough_dog", rtp_trough_dog)
    del rtp

    with rasterio.open(d / "external" / "geodawn_extensions_u8.tif") as s_ext:
        tmi_up150_q = s_ext.read(4).astype(np.float32)
    tmi_up150 = _fill_median(np.where(tmi_up150_q > 0, tmi_up150_q, np.nan), fp)
    del tmi_up150_q
    mag_atten = (_grad_mag(tmi_up150, sigma=1.2) / (rtp_grad + 1e-2)).astype(np.float32)
    save_col("sa_mag_atten_150m", np.clip(mag_atten, 0.0, 5.0))
    del tmi_up150, rtp_grad, mag_atten

    # True 2D horizontal gravity gradient magnitude (correcting IR-36-ATVR-03)
    grav_thdr = np.hypot(grav_hg, grav_vg).astype(np.float32)
    save_col("sa_grav_thdr", grav_thdr)
    del grav_hg, grav_vg

    grav_g15 = _grad_mag(grav, sigma=1.5)
    grav_tilt_ridge = (grav_g15 / (gaussian_filter(grav_g15, 10.0) + 1e-3)).astype(np.float32)
    save_col("sa_grav_tilt_ridge", grav_tilt_ridge)
    del grav, grav_g15, grav_tilt_ridge

    base_step_rel = (_grad_mag(depth_base, sigma=1.2) / (depth_base + 200.0)).astype(np.float32)
    save_col("sa_base_step_rel", base_step_rel)
    del depth_base

    mt_cond_edge = _grad_mag(np.log10(cond_surf), sigma=1.5)
    save_col("sa_mt_cond_edge", mt_cond_edge)
    del cond_surf

    worm_mag, _ = directional_worm_anisotropy(_robust_pos_z(mag_thdr_log, fp))
    save_col("sa_worm_mag", worm_mag)
    del mag_thdr_log, mag_tilt

    grav_base_comb = 0.5 * _robust_pos_z(grav_thdr, fp) + 0.5 * _robust_pos_z(base_step_rel, fp)
    worm_grav_base, strike_grav = directional_worm_anisotropy(grav_base_comb)
    save_col("sa_worm_grav_base", worm_grav_base)
    del grav_thdr, grav_base_comb

    slope_break_raw = _grad_mag(det_slope, sigma=1.0)
    piedmont_break = (slope_break_raw / (gaussian_filter(det_slope, 15.0) + 1.0)).astype(np.float32)
    save_col("sa_piedmont_break", piedmont_break)
    del slope_break_raw, det_slope

    worm_piedmont, strike_pied = directional_worm_anisotropy(_robust_pos_z(piedmont_break, fp))
    save_col("sa_worm_piedmont", worm_piedmont)
    del piedmont_break

    strike_concord = np.abs(np.cos(np.deg2rad(2.0 * (strike_pied - strike_grav)))).astype(
        np.float32
    )
    save_col("sa_strike_concordance", strike_concord)
    del strike_grav

    # 1 m LiDAR directional worm (NaN preserved inside 24.63% NE/basin LiDAR gaps!)
    with rasterio.open(d / "external" / "lidar_scarp_features_u8.tif") as s_lid:
        step_idx = LIDAR_BANDS.index("step_max") + 1
        coh_idx = LIDAR_BANDS.index("coh100") + 1
        val_idx = LIDAR_BANDS.index("valid") + 1
        lid_step = dequantize(s_lid.read(step_idx), *LIDAR_QUANT["step_max"])
        lid_coh = dequantize(s_lid.read(coh_idx), *LIDAR_QUANT["coh100"])
        lid_valid = dequantize(s_lid.read(val_idx), *LIDAR_QUANT["valid"])
    lid_strength = np.nan_to_num(lid_step, nan=0.0) * np.nan_to_num(lid_coh, nan=0.0)
    worm_lid_raw, _ = directional_worm_anisotropy(lid_strength)
    has_lid = np.isfinite(lid_valid) & (lid_valid > 0.5) & np.isfinite(lid_step)
    save_col("sa_worm_lidar", np.where(has_lid, worm_lid_raw, np.nan).astype(np.float32))
    del lid_step, lid_coh, lid_valid, lid_strength, worm_lid_raw, has_lid

    with rasterio.open(d / "external" / "geodawn_rad_u8.tif") as s_rad:
        k_q = s_rad.read(1).astype(np.float32)
        th_q = s_rad.read(2).astype(np.float32)
    k_f = _fill_median(np.where(k_q > 0, k_q, np.nan), fp)
    th_f = _fill_median(np.where(th_q > 0, th_q, np.nan), fp)
    k_th_ratio = k_f / (th_f + 4.0)
    rad_k_th_anom = (
        gaussian_filter(k_th_ratio, 1.5) - gaussian_filter(k_th_ratio, 12.0)
    ).astype(np.float32)
    save_col("sa_rad_k_th_anom", rad_k_th_anom)
    del k_q, th_q, k_f, th_f, k_th_ratio

    strain_seis = (
        np.log1p(_robust_pos_z(geod_2nd, fp) * _robust_pos_z(base_step_rel, fp))
        - 0.5 * np.log1p(_robust_pos_z(ieq, fp))
    ).astype(np.float32)
    save_col("sa_strain_seis_ratio", strain_seis)
    del geod_2nd, ieq, base_step_rel, strain_seis
    gc.collect()

    # ---- Block 3: GVSC_FEATURES (14 geothermal vent-conduit & back-projection features) ----
    gt_rasters, inv_stats = rasterize_ingenious_geothermal_layers(d, grid, det_elev)

    # Regional hydraulic head upslope unit-bounded gradient u_up = grad(G_12(det_elev))
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
    save_col("gvsc_vent_throat_local", vent_local)
    del vent_local

    vent_strike = strike_guided_projection(vent_throat, strike_pied)
    vent_strike_local = np.maximum(
        0.0, vent_strike - 0.65 * gaussian_filter(vent_throat, 18.0)
    ).astype(np.float32)
    save_col("gvsc_vent_strike_corridor", vent_strike_local)
    del vent_throat, vent_strike, strike_pied

    apron_bp = upgradient_backproject(gt_rasters["outflow_apron"], u_up_r, u_up_c)
    apron_bp_local = np.maximum(
        0.0, apron_bp - 0.65 * gaussian_filter(gt_rasters["outflow_apron"], 22.0)
    ).astype(np.float32)
    save_col("gvsc_apron_backproj", apron_bp_local)
    del apron_bp

    f2m_pos = gt_rasters["f2m_pos"]
    f2m_local = (
        gaussian_filter(f2m_pos, 3.0) - 0.70 * gaussian_filter(f2m_pos, 18.0)
    ).astype(np.float32)
    save_col("gvsc_f2mdab_local", f2m_local)
    del f2m_local

    # Intra-array 2 m temperature lateral gradient strictly inside surveyed probe corridors
    cnt_smooth = gaussian_filter(gt_rasters["f2m_count"], 4.0)
    sum_smooth = gaussian_filter(gt_rasters["f2m_signed_sum"], 4.0)
    in_survey = cnt_smooth > 0.015
    local_mean_dab = np.where(in_survey, sum_smooth / (cnt_smooth + 0.02), 0.0).astype(np.float32)
    f2m_grad = np.where(
        cnt_smooth > 0.03, _grad_mag(local_mean_dab, sigma=1.5), 0.0
    ).astype(np.float32)
    save_col("gvsc_f2mdab_grad", f2m_grad)
    del cnt_smooth, sum_smooth, in_survey, local_mean_dab, f2m_grad

    f2m_bp = upgradient_backproject(f2m_pos, u_up_r, u_up_c)
    f2m_bp_local = np.maximum(
        0.0, f2m_bp - 0.65 * gaussian_filter(f2m_pos, 22.0)
    ).astype(np.float32)
    save_col("gvsc_f2mdab_backproj", f2m_bp_local)
    del f2m_pos, f2m_bp

    geotherm_imp = gt_rasters["geotherm_imp"]
    gt_bp = upgradient_backproject(geotherm_imp, u_up_r, u_up_c)
    gt_bp_local = np.maximum(
        0.0, gt_bp - 0.65 * gaussian_filter(geotherm_imp, 22.0)
    ).astype(np.float32)
    save_col("gvsc_geotherm_backproj", gt_bp_local)
    del geotherm_imp, gt_bp, u_up_r, u_up_c

    upflow_pot = (
        0.30 * _robust_pos_z(vent_strike_local, fp)
        + 0.20 * _robust_pos_z(apron_bp_local, fp)
        + 0.30 * _robust_pos_z(f2m_bp_local, fp)
        + 0.20 * _robust_pos_z(gt_bp_local, fp)
    ).astype(np.float32)
    save_col("gvsc_total_upflow_potential", upflow_pot)
    del vent_strike_local, apron_bp_local, f2m_bp_local, gt_bp_local

    z_pied = _robust_pos_z(worm_piedmont, fp)
    z_magw = _robust_pos_z(worm_mag, fp)
    z_gravw = _robust_pos_z(worm_grav_base, fp)
    z_demag = _robust_pos_z(rtp_trough_dog, fp)
    z_mt = _robust_pos_z(mt_cond_edge, fp)
    z_kth = _robust_pos_z(rad_k_th_anom, fp)

    save_col("gvsc_conduit_x_piedmont", (upflow_pot * z_pied).astype(np.float32))
    save_col("gvsc_conduit_x_mag_demag", (upflow_pot * z_demag * (0.5 + 0.5 * z_magw)).astype(np.float32))
    save_col("gvsc_conduit_x_grav_base", (upflow_pot * z_gravw).astype(np.float32))
    save_col("gvsc_conduit_x_mt_rad", (upflow_pot * 0.5 * (z_mt + z_kth)).astype(np.float32))

    volc_corridor = np.maximum(
        0.0,
        gaussian_filter(gt_rasters["volc_vent"], 6.0)
        - gaussian_filter(gt_rasters["volc_vent"], 25.0),
    )
    volc_dike_worm = (
        _robust_pos_z(volc_corridor, fp)
        * (0.6 * z_magw + 0.4 * _robust_pos_z(geod_shear, fp))
    ).astype(np.float32)
    save_col("gvsc_volcanic_dike_worm", volc_dike_worm)

    hydro_alt_comp = np.cbrt(z_demag * z_kth * z_mt).astype(np.float32)
    save_col("gvsc_hydro_alteration_composite", hydro_alt_comp)

    del (
        gt_rasters,
        worm_piedmont,
        worm_mag,
        worm_grav_base,
        rtp_trough_dog,
        mt_cond_edge,
        rad_k_th_anom,
        geod_shear,
        upflow_pot,
        z_pied,
        z_magw,
        z_gravw,
        z_demag,
        z_mt,
        z_kth,
        volc_corridor,
        volc_dike_worm,
        hydro_alt_comp,
    )
    gc.collect()

    meta = {
        "lane_id": "GVSC-36",
        "names": all_names,
        "n_fp": int(grid.n_fp),
        "counts": {
            "base": len(BASE_FEATURES),
            "sa": len(SA_FEATURES),
            "gvsc": len(GVSC_FEATURES),
            "exp1_total": len(EXP1_FEATURES),
            "exp2_total": len(EXP2_FEATURES),
            "exp3_blind_total": len(EXP3_BLIND_FEATURES),
        },
        "geothermal_inventory": inv_stats.__dict__,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return FeatureStore(cache_dir, all_names, grid.n_fp), grid, inv_stats
