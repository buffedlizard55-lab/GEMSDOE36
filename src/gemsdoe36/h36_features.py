"""H36-GPS feature stack: competition bands + LiDAR scarp product + radiometrics, plus the lane's
new physics features (scarp polarity, graben-pair conjugacy, strike-coherent scarp integral).

Everything here is LABEL-FREE: no catalogue pixel is read, so every feature is fold-safe by
construction (the hide-and-recover protocol only constrains catalogue-derived features).

Layers (all on the organizer 100 m EPSG:32611 grid, 3730 x 3292):
* ``data/raw/training_features.tif`` - 19 organizer bands (float32, nodata -3.4028e38).
* ``data/raw/external/lidar_scarp_features_u8.tif`` - 12 bands aggregated from USGS 3DEP 1 m DEM
  tiles (706/716) by the owner's CI; quantisation q = 1 + round(254 * t(clip(x/xmax,0,1))), 0 = no
  lidar; see ``data/external/lidar_scarp_features.json`` in GEMSDOE24 (copied to
  ``registry/lidar_scarp_features.json``).
* ``data/raw/external/geodawn_rad_u8.tif`` (K, Th, U, TC) and ``geodawn_extensions_u8.tif``
  (ThK, UK, UTh, TMI_up150) - GeoDAWN radiometric / magnetic derivatives, 0 = no data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import convolve, gaussian_filter

from .paths import repo_root

NODATA_CUT = -1e30

LIDAR_BANDS = (
    "ex_max",
    "ex_mean",
    "step_max",
    "lapneg_max",
    "lappos_max",
    "downface_max",
    "upface_max",
    "cross_max",
    "relief",
    "coh100",
    "strike",
    "valid",
)
# (xmax, transform) from the product's own quantisation receipt.
LIDAR_QUANT = {
    "ex_max": (1.5, "sqrt"),
    "ex_mean": (0.3, "sqrt"),
    "step_max": (1.0, "sqrt"),
    "lapneg_max": (0.05, "sqrt"),
    "lappos_max": (0.05, "sqrt"),
    "downface_max": (1.0, "sqrt"),
    "upface_max": (1.0, "sqrt"),
    "cross_max": (1.0, "sqrt"),
    "relief": (300.0, "sqrt"),
    "coh100": (1.0, "linear"),
    "strike": (180.0, "linear"),
    "valid": (1.0, "linear"),
}

# Lane-specific (candidate-only) features; the paired baseline omits exactly these.
LANE_FEATURES = (
    "gps_up_share",
    "gps_polarity",
    "gps_graben_pair",
    "gps_graben_pair_wide",
    "gps_coherent_scarp_line",
    "gps_coherent_scarp_line_max",
    "gps_conjugate_line",
)

N_ORIENT = 8
GP_SHIFTS = tuple(range(2, 11))  # 200 m - 1 km conjugate-scarp separation
GP_WIDE_SHIFTS = tuple(range(10, 21))  # 1 - 2 km (wider grabens / horst margins)
LINE_HALF = 7  # 15-px (1.5 km) strike-parallel line integral


def dequantize(q: np.ndarray, xmax: float, transform: str) -> np.ndarray:
    """Invert the product quantisation; 0 (no lidar) -> NaN."""
    q = q.astype(np.float32)
    t = (q - 1.0) / 254.0
    x = xmax * (t * t if transform == "sqrt" else t)
    return np.where(q > 0, x, np.nan).astype(np.float32)


@dataclass
class Grid:
    footprint: np.ndarray
    labels: np.ndarray
    transform: tuple
    shape: tuple

    @property
    def n_fp(self) -> int:
        return int(self.footprint.sum())


def load_grid(data_dir: Path | None = None) -> Grid:
    d = data_dir or (repo_root() / "data" / "raw")
    with rasterio.open(d / "labels.tif") as s:
        lab = s.read(1)
        tr = tuple(s.transform)[:6]
        shape = s.shape
    return Grid(footprint=lab >= 0, labels=lab == 1, transform=tr, shape=shape)


def _line_kernel(theta_deg: float, half: int = LINE_HALF) -> np.ndarray:
    """Normalised strike-parallel line kernel (raster row/col axes, strike measured from north
    clockwise, i.e. azimuth; row axis points south)."""
    size = 2 * half + 1
    k = np.zeros((size, size), np.float32)
    th = np.deg2rad(theta_deg)
    dy, dx = -np.cos(th), np.sin(th)  # azimuth -> (row, col) step
    for t in np.linspace(-half, half, 4 * size):
        r, c = int(round(half + t * dy)), int(round(half + t * dx))
        if 0 <= r < size and 0 <= c < size:
            k[r, c] = 1.0
    return k / k.sum()


def _shift(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """out[y, x] = a[y + dy, x + dx] with zero fill (no wrap-around)."""
    out = np.zeros_like(a)
    h, w = a.shape
    ys, ye = max(0, -dy), min(h, h - dy)
    xs, xe = max(0, -dx), min(w, w - dx)
    if ys < ye and xs < xe:
        out[ys:ye, xs:xe] = a[ys + dy : ye + dy, xs + dx : xe + dx]
    return out


def regional_slope_azimuth(det_elev: np.ndarray, footprint: np.ndarray, sigma: float = 5.0) -> np.ndarray:
    """Azimuth (deg, from north clockwise, axial in [0, 180)) of the regional DOWNSLOPE direction of
    the organizer's detrended elevation smoothed at ``sigma`` px (500 m). NaN where flat/undefined.

    The LiDAR product's own ``strike`` band was checked against catalogue line orientation and is
    statistically unrelated to it (uniform axial differences; see evidence/h36_strike_check.json),
    so the lane derives geometry from the regional slope instead.
    """
    z = np.where(np.isfinite(det_elev), det_elev, np.nanmedian(det_elev[footprint])).astype(np.float32)
    zs = gaussian_filter(z, sigma)
    gy, gx = np.gradient(zs)  # gy: d/d(row) (southward), gx: d/d(col) (eastward)
    # downslope vector = -grad; north component = +gy (row axis points south), east = -gx
    az = np.degrees(np.arctan2(-gx, gy)) % 180.0
    mag = np.hypot(gx, gy)
    return np.where(mag > 1e-3, az, np.nan).astype(np.float32)


def _in_bin(az: np.ndarray, theta: float, width: float) -> np.ndarray:
    a = np.where(np.isfinite(az), az, -1000.0)
    return (a > -1) & (np.abs(((a - theta + 90.0) % 180.0) - 90.0) <= width / 2.0)


def graben_pair(
    down: np.ndarray,
    up: np.ndarray,
    slope_az: np.ndarray,
    coh: np.ndarray,
    shifts: tuple[int, ...] = GP_SHIFTS,
) -> np.ndarray:
    """Conjugate-scarp (graben / horst margin) pairing score.

    ``downface`` = synthetic, downslope-facing step; ``upface`` = antithetic, uphill-facing step
    (both measured against the 100 m regional slope by the LiDAR product). In an extensional
    graben on a piedmont, the synthetic and antithetic scarps are offset ALONG the regional slope
    direction. For every pixel we search 200 m - 1 km (default) up- and down-slope for the strongest
    opposite-polarity scarp: score = sqrt(own * partner) * coherence. Wave-cut shoreline risers,
    terrace risers and fan-head trenches are single-facing; channel banks face each other ACROSS
    the slope (``cross_max``), not along it.
    """
    down = np.nan_to_num(down, nan=0.0).astype(np.float32)
    up = np.nan_to_num(up, nan=0.0).astype(np.float32)
    coh = np.nan_to_num(coh, nan=0.0).astype(np.float32)
    width = 180.0 / N_ORIENT
    out = np.zeros(down.shape, np.float32)
    for k in range(N_ORIENT):
        theta = k * width
        in_bin = _in_bin(slope_az, theta, width)
        if not in_bin.any():
            continue
        th = np.deg2rad(theta)
        ny, nx = -np.cos(th), np.sin(th)  # azimuth -> (row, col) unit step
        best_u = np.zeros_like(down)
        best_d = np.zeros_like(down)
        for s_ in shifts:
            for sign in (1, -1):
                dy, dx = int(round(sign * s_ * ny)), int(round(sign * s_ * nx))
                np.maximum(best_u, _shift(up, dy, dx), out=best_u)
                np.maximum(best_d, _shift(down, dy, dx), out=best_d)
        pair = np.maximum(np.sqrt(down * best_u), np.sqrt(up * best_d))
        out = np.where(in_bin, pair, out)
    return (out * coh).astype(np.float32)


def coherent_line(strength: np.ndarray, slope_az: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """1.5 km line integral of scarp strength along the regional CONTOUR direction (perpendicular to
    the regional slope, i.e. the expected strike of piedmont scarps), and the maximum over eight
    orientations. Long straight scarps integrate coherently; sinuous channel banks do not."""
    s_ = np.nan_to_num(strength, nan=0.0).astype(np.float32)
    width = 180.0 / N_ORIENT
    own = np.zeros_like(s_)
    mx = np.zeros_like(s_)
    for k in range(N_ORIENT):
        theta = k * width
        resp = convolve(s_, _line_kernel(theta), mode="constant", cval=0.0)
        np.maximum(mx, resp, out=mx)
        contour_bin = _in_bin(slope_az, (theta + 90.0) % 180.0, width)
        own = np.where(contour_bin, resp, own)
    return own, mx


class FeatureStore:
    """Footprint-only float32 feature columns stored as one ``.npy`` per feature (memory-safe)."""

    def __init__(self, cache_dir: Path, names: list[str], n_fp: int):
        self.cache_dir = cache_dir
        self.names = list(names)
        self.n_fp = n_fp

    def column(self, name: str) -> np.ndarray:
        return np.load(self.cache_dir / f"{name}.npy", mmap_mode="r")

    def rows(self, idx: np.ndarray, names: list[str] | None = None) -> np.ndarray:
        names = self.names if names is None else names
        out = np.empty((len(idx), len(names)), np.float32)
        for j, n in enumerate(names):
            out[:, j] = self.column(n)[idx]
        return out


def build_feature_stack(
    cache_dir: Path, *, data_dir: Path | None = None, force: bool = False
) -> tuple[FeatureStore, Grid]:
    """Build (or reopen) the footprint-only feature columns."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    d = data_dir or (repo_root() / "data" / "raw")
    grid = load_grid(d)
    fp = grid.footprint
    meta_p = cache_dir / "h36_features.json"
    if meta_p.exists() and not force:
        meta = json.loads(meta_p.read_text())
        if all((cache_dir / f"{n}.npy").exists() for n in meta["names"]):
            return FeatureStore(cache_dir, meta["names"], grid.n_fp), grid

    names: list[str] = []

    def add(name: str, full: np.ndarray) -> None:
        np.save(cache_dir / f"{name}.npy", np.asarray(full[fp], dtype=np.float32))
        names.append(name)

    with rasterio.open(d / "training_features.tif") as s:
        band_names = [desc.split(" - ")[0] if desc else f"b{i + 1}" for i, desc in enumerate(s.descriptions)]
        bands = {}
        for i, name in enumerate(band_names, start=1):
            a = s.read(i).astype(np.float32)
            a[a < NODATA_CUT] = np.nan
            add(f"org_{name}", a)
            if name in ("det_elev", "det_elev_slope", "iso_grav_anom", "iso_grav_anom_hg", "tmi_hg", "rtp"):
                bands[name] = a
    slope_az = regional_slope_azimuth(bands["det_elev"], fp)
    # Multi-scale context (common to baseline AND candidate): smoothed level and local anomaly.
    for name, a in bands.items():
        filled = np.where(np.isfinite(a), a, np.nanmedian(a[fp])).astype(np.float32)
        for sig in (3.0, 10.0):
            g = gaussian_filter(filled, sig)
            add(f"ctx_{name}_g{int(sig)}", g)
            if sig == 3.0:
                add(f"ctx_{name}_anom3", filled - g)
    del bands

    lid = {}
    with rasterio.open(d / "external" / "lidar_scarp_features_u8.tif") as s:
        for i, name in enumerate(LIDAR_BANDS, start=1):
            q = s.read(i)
            xmax, t = LIDAR_QUANT[name]
            x = dequantize(q, xmax, t)
            if name == "strike":
                lid[name] = x
                th = np.deg2rad(x)
                add("lid_strike_cos2", np.cos(2 * th))
                add("lid_strike_sin2", np.sin(2 * th))
            else:
                lid[name] = x
                add(f"lid_{name}", x)
    step_s = np.nan_to_num(lid["step_max"], nan=0.0)
    add("ctx_lid_step_g3", gaussian_filter(step_s, 3.0))

    for fname, bnames in (
        ("geodawn_rad_u8.tif", ("K", "Th", "U", "TC")),
        ("geodawn_extensions_u8.tif", ("ThK", "UK", "UTh", "TMI_up150")),
    ):
        with rasterio.open(d / "external" / fname) as s:
            for i, name in enumerate(bnames, start=1):
                q = s.read(i).astype(np.float32)
                add(f"gd_{name}", np.where(q > 0, q, np.nan))

    # ---- lane-specific physics (candidate only) ----
    down, up = lid["downface_max"], lid["upface_max"]
    dn, un = np.nan_to_num(down, nan=0.0), np.nan_to_num(up, nan=0.0)
    has = np.isfinite(down) & np.isfinite(up)
    add("gps_up_share", np.where(has, un / (un + dn + 1e-3), np.nan))
    add("gps_polarity", np.where(has, dn - un, np.nan))
    gp = graben_pair(down, up, slope_az, lid["coh100"], GP_SHIFTS)
    add("gps_graben_pair", np.where(np.isfinite(down), gp, np.nan))
    gpw = graben_pair(down, up, slope_az, lid["coh100"], GP_WIDE_SHIFTS)
    add("gps_graben_pair_wide", np.where(np.isfinite(down), gpw, np.nan))
    strength = np.nan_to_num(lid["step_max"], nan=0.0) * np.nan_to_num(lid["coh100"], nan=0.0)
    own, mx = coherent_line(strength, slope_az)
    add("gps_coherent_scarp_line", np.where(np.isfinite(down), own, np.nan))
    add("gps_coherent_scarp_line_max", np.where(np.isfinite(down), mx, np.nan))
    own_gp, _ = coherent_line(gp, slope_az)
    add("gps_conjugate_line", np.where(np.isfinite(down), own_gp, np.nan))
    del lid, down, up, gp, gpw, own, mx, own_gp, slope_az

    meta_p.write_text(
        json.dumps({"names": names, "n_fp": grid.n_fp, "lane_features": list(LANE_FEATURES)}, indent=1)
    )
    return FeatureStore(cache_dir, names, grid.n_fp), grid
