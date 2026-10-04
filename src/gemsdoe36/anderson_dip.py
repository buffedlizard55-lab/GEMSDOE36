"""Anderson (1905) fault-mechanics model for the Great Basin extensional regime.

References (see docs/research/sources.md for access status and links):

* Anderson, E.M. (1905), "The dynamics of faulting," Trans. Edinburgh Geol. Soc. 8(3),
  387-402. https://doi.org/10.1144/transed.8.3.387 — in a normal-faulting regime
  (sigma-1 vertical, sigma-3 horizontal) the fault plane bisects the angle between
  sigma-1 and sigma-3: it dips at ~60 degrees from horizontal, strikes perpendicular
  to sigma-3 (extension), and its horizontal normal (dip direction) is parallel to
  sigma-3.
* World Stress Map Database Release 2025 (Heidbach et al.),
  https://doi.org/10.5880/WSM.2025.001 — global present-day stress compilation;
  the Great Basin region is classified normal-faulting with WNW-ESE sigma-3.
  (Publisher record verified; the CSV itself was not downloadable from this
  sandbox, so the regional azimuth below is anchored to the literature values
  recorded in docs/research/sources.md instead of a per-record WSM query.)
* Nevada Geodetic Laboratory, "Strain in the Great Basin,"
  https://geodesy.unr.edu/greatbasinstrain.php — "most of the Great Basin is under
  extension" (retrieved 2026-10-04).
* Wright (1999), late-Cenozoic Great Basin fault patterns: "The major normal
  faults, which strike north-northeast in most parts of the Great Basin, suggest a
  pervasive horizontal minimum compressive (maximum tensional) stress that is
  oriented west-northwest." (recorded in docs/research/sources.md)

Angle conventions (must match orientation.py):
* raster angles are radians measured from +column (east) toward +row (south);
* axial (line) directions are modulo pi;
* geographic azimuth (0 = north, clockwise toward east) converts with
  ``azimuth_to_raster``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter

# Regional prior for the competition AOI (GeoDAWN: northwestern Great Basin,
# roughly 37.5-42.5 N). sigma-3 (extension) azimuth in degrees from north, with
# an uncertainty sigma. Anchored to the WNW-ESE / E-W sigma-3 directions recorded
# for the northern and central Great Basin in the sources above; the southern
# Basin and Range trend toward ESE (~110 deg) is outside the AOI.
REGIONAL_EXTENSION_AZIMUTH_DEG = 275.0
REGIONAL_EXTENSION_SIGMA_DEG = 20.0

# Anderson normal-fault dip (degrees from horizontal) and the dip bank used for
# dip projection (weights sum to 1). Anderson's ~60 deg is the centre.
DEFAULT_DIP_DEG = 60.0
DIP_BANK_DEG = (50.0, 55.0, 60.0, 65.0, 70.0)
DIP_BANK_WEIGHTS = (0.10, 0.20, 0.40, 0.20, 0.10)

# Effective sampling depth bank (metres) for the *deep* potential-field channels
# (magnetics, gravity, MT). A fault dipping delta in the extension direction puts
# its depth-z expression at z*cot(delta) down-dip of the surface trace, so the
# observed edge must be pulled back up-dip by that amount to estimate the trace.
DEEP_DEPTH_BANK_M = (200.0, 400.0, 600.0, 800.0)
DEEP_DEPTH_WEIGHTS = (0.20, 0.35, 0.30, 0.15)


def azimuth_to_raster(azimuth_deg: np.ndarray | float) -> np.ndarray | float:
    """Geographic azimuth (deg from north, clockwise) -> raster angle (rad from east)."""
    az = np.asarray(azimuth_deg, dtype=np.float64) * (np.pi / 180.0)
    return np.arctan2(-np.cos(az), np.sin(az))


def axial_distance(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Shortest angular distance between two axial (mod pi) directions, in [0, pi/2]."""
    d = np.abs(np.sin(a - b))  # |sin(delta)| for axial angles: period pi/2 in cos(2d)
    return np.arcsin(np.clip(d, 0.0, 1.0))


def circular_mean_axial(angles: np.ndarray, weights: np.ndarray | None = None) -> tuple[float, float]:
    """Weighted circular mean and Rayleigh resultant length (R-hat) of axial angles.

    Axial (mod pi) angles are mapped to the double-angle circle before averaging,
    which is the standard construction for line orientations.
    """
    a = np.asarray(angles, dtype=np.float64)
    w = np.ones_like(a) if weights is None else np.asarray(weights, dtype=np.float64)
    m = np.isfinite(a) & (w > 0)
    if not m.any():
        return 0.0, 0.0
    a, w = a[m], w[m]
    z = np.sum(w * np.exp(2j * a))
    mean = 0.5 * np.angle(z) % np.pi
    r_hat = min(1.0, np.abs(z) / np.sum(w))
    return float(mean), float(r_hat)


@dataclass(frozen=True)
class ExtensionField:
    """Spatially varying Anderson extension direction and confidence.

    ``angle_raster``: extension (sigma-3) direction in raster convention (radians,
    axial).  ``confidence``: in [0, 1]; combines catalogue strike concentration,
    catalogue coverage, and agreement with the regional prior.
    """

    angle_raster: np.ndarray
    confidence: np.ndarray
    tile_extension_azimuth: dict[tuple[int, int], float] | None = None


def catalogue_strikes(
    catalogue: np.ndarray,
    *,
    tile_px: int = 120,
    smoothing_px: float = 1.5,
    min_pixels: int = 40,
) -> dict[tuple[int, int], tuple[float, float, int]]:
    """Dominant fault strike per tile from the catalogue's structure tensor.

    Returns {(tile_row, tile_col): (strike_raster, concentration, n_pixels)}.
    The structure tensor's dominant eigenvector is normal to the ridge (the fault
    line), so strike = normal + pi/2. Concentration is the eigenvalue separation,
    in [0, 1]; near-isotropic tiles (joints, scattered pixels) get low values.
    """
    h, w = catalogue.shape
    mask = catalogue.astype(np.float32)
    if not mask.any():
        return {}
    sm = gaussian_filter(mask, sigma=smoothing_px).astype(np.float32)
    gy, gx = np.gradient(sm)
    r = max(1, int(np.ceil(3.0 * smoothing_px)))
    jxx = gaussian_filter(gx * gx, sigma=r).astype(np.float32)
    jxy = gaussian_filter(gx * gy, sigma=r).astype(np.float32)
    jyy = gaussian_filter(gy * gy, sigma=r).astype(np.float32)
    del sm, gx, gy

    n_rows, n_cols = h // tile_px, w // tile_px
    out: dict[tuple[int, int], tuple[float, float, int]] = {}
    for tr in range(n_rows):
        for tc in range(n_cols):
            y0, x0 = tr * tile_px, tc * tile_px
            y1, x1 = y0 + tile_px, x0 + tile_px
            a = mask[y0:y1, x0:x1]
            n_px = int(a.sum())
            if n_px < min_pixels:
                continue
            sel = a > 0.5
            tile_jxx = float(jxx[y0:y1, x0:x1][sel].mean())
            tile_jxy = float(jxy[y0:y1, x0:x1][sel].mean())
            tile_jyy = float(jyy[y0:y1, x0:x1][sel].mean())
            diff = tile_jxx - tile_jyy
            norm = float(np.hypot(diff, 2.0 * tile_jxy))
            if norm <= 0:
                continue
            # Dominant eigenvector (normal to the line) of [[Jxx, Jxy], [Jxy, Jyy]].
            normal = 0.5 * np.arctan2(2.0 * tile_jxy, diff)
            strike = (normal + np.pi / 2.0) % np.pi
            concentration = float(np.clip(norm / (tile_jxx + tile_jyy + 1e-12), 0.0, 1.0))
            out[(tr, tc)] = (float(strike), concentration, n_px)
    del jxx, jxy, jyy
    return out


def local_extension_field(
    catalogue: np.ndarray,
    *,
    tile_px: int = 120,
    regional_azimuth_deg: float = REGIONAL_EXTENSION_AZIMUTH_DEG,
    regional_sigma_deg: float = REGIONAL_EXTENSION_SIGMA_DEG,
    min_pixels: int = 40,
    conflict_limit_deg: float = 45.0,
) -> ExtensionField:
    """Build the spatially varying extension direction and confidence.

    Method (documented, deterministic):
      1. Per-tile dominant catalogue strike (structure tensor) -> tile extension
         direction = strike + pi/2 (normal faults: strike is perpendicular to the
         extension axis).
      2. Tile confidence = strike concentration x min(1, n_px / 4x min_pixels) x
         agreement with the regional prior (Gaussian in the axial distance with
         sigma = regional_sigma_deg). Tiles whose strike-derived extension
         conflicts with the regional prior by more than ``conflict_limit_deg`` are
         treated as unreliable (pre-Basin-and-Range structures, strike-slip
         segments) and fall back to the regional value with halved confidence.
      3. Tiles without sufficient catalogue use the regional prior with
         confidence scaled by the regional sigma only.
      4. The tile field is interpolated to pixel resolution on the double-angle
         circle (complex exponential), so no wrap-around artifacts appear.
    """
    h, w = catalogue.shape
    regional_angle = azimuth_to_raster(regional_azimuth_deg) % np.pi
    conflict_limit = np.deg2rad(conflict_limit_deg)

    strikes = catalogue_strikes(catalogue, tile_px=tile_px, min_pixels=min_pixels)
    n_rows, n_cols = h // tile_px, w // tile_px

    tile_angles = np.full((n_rows, n_cols), regional_angle, dtype=np.float64)
    tile_conf = np.zeros((n_rows, n_cols), dtype=np.float64)
    tile_ext_az: dict[tuple[int, int], float] = {}

    # Regional-prior confidence baseline: the regime is well established, but the
    # exact azimuth varies at the scale of the prior sigma.
    base_conf = float(np.cos(np.deg2rad(10.0)))  # ~0.98 * coverage factor below
    for tr in range(n_rows):
        for tc in range(n_cols):
            y0, x0 = tr * tile_px, tc * tile_px
            y1, x1 = min(h, y0 + tile_px), min(w, x0 + tile_px)
            coverage = float(catalogue[y0:y1, x0:x1].mean())
            if (tr, tc) in strikes:
                strike, conc, n_px = strikes[(tr, tc)]
                ext = (strike + np.pi / 2.0) % np.pi
                delta = axial_distance(np.array([ext]), np.array([regional_angle]))[0]
                coverage_factor = min(1.0, n_px / (4.0 * min_pixels))
                if delta > conflict_limit:
                    # Unreliable local direction (old/transcurrent structures).
                    tile_angles[tr, tc] = regional_angle
                    tile_conf[tr, tc] = 0.5 * base_conf * coverage_factor
                else:
                    agreement = float(np.exp(-(delta / np.deg2rad(regional_sigma_deg)) ** 2))
                    tile_angles[tr, tc] = ext
                    tile_conf[tr, tc] = base_conf * max(conc, 0.3) * coverage_factor * (
                        0.5 + 0.5 * agreement
                    )
            else:
                tile_angles[tr, tc] = regional_angle
                tile_conf[tr, tc] = base_conf * min(1.0, coverage * 20.0) * 0.5
            # Axial azimuth: raster_deg + 90, reduced mod 180 (line directions).
            tile_ext_az[(tr, tc)] = float(
                (np.rad2deg(tile_angles[tr, tc] % np.pi) + 90.0) % 180.0
            )

    # Bilinear interpolation of the double-angle field to pixel resolution.
    # Interpolating cos(2a), sin(2a) separately (real fields, float32) avoids the
    # complex (h, w) temporaries and any wrap-around artifacts.
    c2 = (np.cos(2.0 * tile_angles) * np.clip(tile_conf, 0.0, 1.0)).astype(np.float32)
    s2 = (np.sin(2.0 * tile_angles) * np.clip(tile_conf, 0.0, 1.0)).astype(np.float32)

    def _bilinear(field: np.ndarray) -> np.ndarray:
        # Image row y -> tile row y * n_rows / h (tile grid spans the whole image).
        rows = (np.arange(h) + 0.5) * (n_rows / h) - 0.5
        cols = (np.arange(w) + 0.5) * (n_cols / w) - 0.5
        r0 = np.clip(np.floor(rows).astype(int), 0, n_rows - 1)
        c0 = np.clip(np.floor(cols).astype(int), 0, n_cols - 1)
        r1 = np.clip(r0 + 1, 0, n_rows - 1)
        c1 = np.clip(c0 + 1, 0, n_cols - 1)
        fr = (rows - r0)[:, None]
        fc = (cols - c0)[None, :]
        return (
            (1 - fr) * (1 - fc) * field[r0[:, None], c0[None, :]]
            + fr * (1 - fc) * field[r1[:, None], c0[None, :]]
            + (1 - fr) * fc * field[r0[:, None], c1[None, :]]
            + fr * fc * field[r1[:, None], c1[None, :]]
        ).astype(np.float32)

    c2_pix = _bilinear(c2)
    s2_pix = _bilinear(s2)
    angle = (0.5 * np.arctan2(s2_pix, c2_pix)) % np.pi
    confidence = np.clip(np.hypot(c2_pix, s2_pix), 0.0, 1.0)
    return ExtensionField(
        angle_raster=angle.astype(np.float32),
        confidence=confidence.astype(np.float32),
        tile_extension_azimuth=tile_ext_az,
    )


def strike_consistency_weight(
    evidence: np.ndarray,
    extension_field: ExtensionField,
    *,
    tolerance_deg: float = 25.0,
    floor: float = 0.6,
    smoothing_px: float = 2.0,
) -> np.ndarray:
    """Soft weight for lineaments consistent with Anderson's predicted strike range.

    This is the *soft* orientation-consistency term required by the project brief:
    a candidate whose local strike (from the structure tensor of ``evidence``) is
    inconsistent with the Anderson range (perpendicular to local extension, within
    ``tolerance_deg``) is down-weighted, never zeroed (``floor``). Where the
    extension confidence is low the weight tends to 1 (no penalty). The weight is
    multiplicative on the belief field / additive in the network loss — it is not a
    hard post-hoc filter: inconsistent lineaments still contribute, they just carry
    a weaker claim.
    """
    if not 0.0 <= floor <= 1.0:
        raise ValueError("floor must be in [0, 1]")
    sm = gaussian_filter(evidence.astype(np.float32), sigma=1.0)
    gy, gx = np.gradient(sm)
    del sm
    r = max(1, int(np.ceil(3.0 * smoothing_px)))
    jxx = gaussian_filter(gx * gx, sigma=r).astype(np.float32)
    jxy = gaussian_filter(gx * gy, sigma=r).astype(np.float32)
    jyy = gaussian_filter(gy * gy, sigma=r).astype(np.float32)
    del gx, gy
    diff = jxx - jyy
    norm = np.hypot(diff, 2.0 * jxy)
    # Normal to the line; axial distance to the extension axis.
    normal = 0.5 * np.arctan2(2.0 * jxy, diff)
    delta = axial_distance(normal, extension_field.angle_raster.astype(np.float32))
    anisotropy = np.clip(norm / (jxx + jyy + 1e-12), 0.0, 1.0)
    del jxx, jxy, jyy, norm, normal
    tol = np.deg2rad(tolerance_deg)
    gauss = np.exp(-((delta / tol) ** 2))
    del delta
    weight = floor + (1.0 - floor) * gauss
    # Modulate by anisotropy (flat areas have no line orientation to judge) and by
    # the extension confidence (low confidence -> no penalty).
    weight = 1.0 - (1.0 - weight) * anisotropy * extension_field.confidence
    return weight.astype(np.float32)


def dip_pullback_offsets(
    extension_field: ExtensionField,
    tile_px: int,
    *,
    depth_bank_m: tuple[float, ...] = DEEP_DEPTH_BANK_M,
    depth_weights: tuple[float, ...] = DEEP_DEPTH_WEIGHTS,
    dip_deg: float = DEFAULT_DIP_DEG,
) -> dict[tuple[int, int], list[tuple[int, int, float]]]:
    """Per-tile up-dip pullback offsets for projecting deep-channel evidence to traces.

    For each tile and each bank depth z, the offset (in pixels) is
    ``-z * cot(dip) / 100 m`` along the local extension direction (up-dip, i.e.
    against extension): a fault dipping ``dip`` in the extension direction puts its
    depth-z expression ``z*cot(dip)`` down-dip of the surface trace. Offsets are
    rounded to integer pixels; weights combine the depth and dip banks.
    """
    h, w = extension_field.angle_raster.shape
    n_rows, n_cols = h // tile_px, w // tile_px
    cot = 1.0 / np.tan(np.deg2rad(dip_deg))
    out: dict[tuple[int, int], list[tuple[int, int, float]]] = {}
    for tr in range(n_rows):
        for tc in range(n_cols):
            cy, cx = tr * tile_px + tile_px // 2, tc * tile_px + tile_px // 2
            if cy >= h or cx >= w:
                continue
            ang = extension_field.angle_raster[cy, cx]
            # Extension direction unit vector in (row, col) axes.
            d_row, d_col = np.sin(ang), np.cos(ang)
            offsets: list[tuple[int, int, float]] = []
            for z, wz in zip(depth_bank_m, depth_weights, strict=True):
                dist_px = z * cot / 100.0
                dy = int(round(-d_row * dist_px))
                dx = int(round(-d_col * dist_px))
                if (dy, dx) == (0, 0):
                    dy, dx = int(np.sign(-d_row)), int(np.sign(-d_col))
                offsets.append((dy, dx, float(wz)))
            out[(tr, tc)] = offsets
    return out


def dip_project(
    evidence: np.ndarray,
    extension_field: ExtensionField,
    tile_px: int = 120,
    *,
    depth_bank_m: tuple[float, ...] = DEEP_DEPTH_BANK_M,
    depth_weights: tuple[float, ...] = DEEP_DEPTH_WEIGHTS,
    dip_deg: float = DEFAULT_DIP_DEG,
    confidence: np.ndarray | None = None,
) -> np.ndarray:
    """Pull deep-channel evidence back up-dip to estimate the surface trace.

    ``evidence`` (H, W) is a deep-channel lineament score (e.g. magnetic tilt,
    gravity gradient). For every pixel the evidence is copied to the up-dip
    position implied by the local Anderson dip and extension direction, with
    weights from the depth/dip banks and the local extension confidence. The result
    is the evidence re-expressed at the *surface trace* location — the correction
    for the 150-300 m down-dip displacement that leaves 45-70 deg dipping
    basin-bounding faults invisible to uncorrected horizontal gradients.
    """
    h, w = evidence.shape
    conf = extension_field.confidence if confidence is None else confidence
    out = np.zeros_like(evidence, dtype=np.float32)
    acc = np.zeros_like(evidence, dtype=np.float32)
    cot = 1.0 / np.tan(np.deg2rad(dip_deg))
    n_rows, n_cols = h // tile_px, w // tile_px
    for tr in range(n_rows):
        for tc in range(n_cols):
            y0, x0 = tr * tile_px, tc * tile_px
            y1, x1 = y0 + tile_px, x0 + tile_px
            cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
            ang = extension_field.angle_raster[cy, cx]
            c = float(conf[cy, cx])
            if c <= 0.0:
                continue
            d_row, d_col = float(np.sin(ang)), float(np.cos(ang))
            block = evidence[y0:y1, x0:x1]
            bh, bw = block.shape
            for z, wz in zip(depth_bank_m, depth_weights, strict=True):
                # z*cot(dip) is a horizontal offset in metres; /100 -> pixels on the
                # 100 m grid (must match dip_pullback_offsets; a missing /100 here is a
                # 100x shift that pushes the deep evidence out of tile).
                dist_px = z * cot / 100.0
                dy = int(round(-d_row * dist_px))
                dx = int(round(-d_col * dist_px))
                if dy == 0 and dx == 0:
                    continue
                # Up-dip gather: out_local[oy, ox] += block[oy - dy, ox - dx].
                oy0, oy1 = max(0, dy), min(bh, dy + bh)
                ox0, ox1 = max(0, dx), min(bw, dx + bw)
                if oy1 <= oy0 or ox1 <= ox0:
                    continue
                sy0, sy1 = oy0 - dy, oy1 - dy
                sx0, sx1 = ox0 - dx, ox1 - dx
                wy0, wx0 = y0 + oy0, x0 + ox0
                out[wy0 : wy0 + (oy1 - oy0), wx0 : wx0 + (ox1 - ox0)] += (
                    wz * c * block[sy0:sy1, sx0:sx1]
                ).astype(np.float32)
                acc[wy0 : wy0 + (oy1 - oy0), wx0 : wx0 + (ox1 - ox0)] += wz * c
    positive = acc > 0
    out[positive] /= acc[positive]
    return out
