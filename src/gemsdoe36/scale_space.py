"""Fold-safe, label-free Gaussian scale-space potential-field descriptors.

This module implements one preregistered research feature only: concordance of
magnetic and gravity edge widths. It does not read labels, faults, registry
rasters, or geothermal point files. The inputs are the prepared 100 m band cache.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt, gaussian_filter

SCALES_PX: tuple[float, ...] = (1.0, 2.0, 4.0, 8.0)
SUPPORT_SIGMA_MULTIPLIER = 4


def _fill_invalid_nearest(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Nearest-valid fill for convolution only; invalid cells remain masked in output."""
    a = np.asarray(values, dtype=np.float32)
    mask = np.asarray(valid, dtype=bool)
    if a.ndim != 2 or a.shape != mask.shape or not mask.any():
        raise ValueError("values and a nonempty valid mask must be aligned 2D grids")
    if not np.isfinite(a[mask]).all():
        raise ValueError("valid cells must contain finite values")
    if mask.all():
        return a.copy()
    nearest = distance_transform_edt(~mask, return_distances=False, return_indices=True)
    return a[nearest[0], nearest[1]].astype(np.float32, copy=False)


def _normalized_peak_edge(
    values: np.ndarray,
    footprint: np.ndarray,
    *,
    scales: tuple[float, ...] = SCALES_PX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, float | int]]:
    """Return robust peak edge strength, peak scale, normal, and valid support.

    The response is the scale-normalized Gaussian first derivative
    ``sigma * hypot(dG_sigma/dx, dG_sigma/dy)``. A four-sigma erosion prevents
    NaN/sentinel or footprint silhouettes from being interpreted as geological
    edges. Gradient normals are unit vectors and are axial (sign is immaterial).
    """
    a = np.asarray(values, dtype=np.float32)
    foot = np.asarray(footprint, dtype=bool)
    if a.ndim != 2 or a.shape != foot.shape or not foot.any():
        raise ValueError("field and nonempty footprint must be aligned 2D grids")
    if not scales or any(not np.isfinite(s) or s <= 0 for s in scales):
        raise ValueError("scales must be finite positive Gaussian sigmas")
    valid = foot & np.isfinite(a) & (np.abs(a) < 1e30)
    if not valid.any():
        raise ValueError("field has no finite values inside the footprint")

    max_halo = int(np.ceil(SUPPORT_SIGMA_MULTIPLIER * max(scales)))
    support = binary_erosion(
        valid,
        structure=np.ones((3, 3), dtype=bool),
        iterations=max_halo,
        border_value=0,
    )
    if not support.any():
        raise ValueError("scale-space support is empty after boundary/missing-data erosion")

    filled = _fill_invalid_nearest(a, valid)
    peak = np.full(a.shape, -1.0, dtype=np.float32)
    peak_scale = np.zeros(a.shape, dtype=np.float32)
    normal_x = np.zeros(a.shape, dtype=np.float32)
    normal_y = np.zeros(a.shape, dtype=np.float32)

    for sigma in scales:
        gx = gaussian_filter(filled, sigma=sigma, order=(0, 1), mode="nearest")
        gy = gaussian_filter(filled, sigma=sigma, order=(1, 0), mode="nearest")
        magnitude = np.hypot(gx, gy).astype(np.float32, copy=False)
        response = (np.float32(sigma) * magnitude).astype(np.float32, copy=False)
        better = response > peak
        peak[better] = response[better]
        peak_scale[better] = np.float32(sigma)
        nonzero = better & (magnitude > 1e-12)
        normal_x[nonzero] = gx[nonzero] / magnitude[nonzero]
        normal_y[nonzero] = gy[nonzero] / magnitude[nonzero]
        del gx, gy, magnitude, response, better, nonzero

    finite_peak = peak[support]
    scale_ref = float(np.percentile(finite_peak, 99.0))
    if not np.isfinite(scale_ref) or scale_ref <= 0:
        raise ValueError("scale-space peak edge response has no positive 99th percentile")
    peak_norm = peak.copy()
    peak_norm /= np.float32(scale_ref)
    np.clip(peak_norm, 0.0, 1.0, out=peak_norm)
    peak_norm[~support] = 0.0
    peak_scale[~support] = 0.0
    normal_x[~support] = 0.0
    normal_y[~support] = 0.0
    diagnostics: dict[str, float | int] = {
        "valid_cells": int(valid.sum()),
        "support_cells": int(support.sum()),
        "support_fraction_of_footprint": float(support.sum() / foot.sum()),
        "peak_response_p99": scale_ref,
    }
    return peak_norm, peak_scale, normal_x, normal_y, support, diagnostics


def scale_space_edge_width_concordance(
    magnetic: np.ndarray,
    gravity: np.ndarray,
    footprint: np.ndarray,
    *,
    scales: tuple[float, ...] = SCALES_PX,
) -> tuple[np.ndarray, dict[str, object]]:
    """Build one [0,1] cross-sensor edge-width concordance surface.

    For magnetic and gravity fields separately, retain the largest scale-normalized
    Gaussian gradient over ``scales``. The output is

        sqrt(magnetic_peak * gravity_peak)
        * exp(-abs(log(magnetic_sigma / gravity_sigma)))
        * abs(dot(magnetic_normal, gravity_normal)).

    It is exactly zero outside conservative joint support and remains finite there.
    This is a geometry/scale statistic, not an inferred probability or fault label.
    """
    mag, foot = np.asarray(magnetic), np.asarray(footprint, dtype=bool)
    grav = np.asarray(gravity)
    if mag.ndim != 2 or grav.shape != mag.shape or foot.shape != mag.shape:
        raise ValueError("magnetic, gravity, and footprint must be equal-shaped 2D grids")

    (mag_peak, mag_scale, mag_nx, mag_ny, mag_support, mag_diag) = _normalized_peak_edge(
        mag, foot, scales=scales
    )
    (grav_peak, grav_scale, grav_nx, grav_ny, grav_support, grav_diag) = _normalized_peak_edge(
        grav, foot, scales=scales
    )
    support = mag_support & grav_support & foot
    if not support.any():
        raise ValueError("magnetic and gravity scale-space supports do not overlap")

    widths_match = np.zeros(mag.shape, dtype=np.float32)
    both_scales = support & (mag_scale > 0) & (grav_scale > 0)
    widths_match[both_scales] = np.exp(
        -np.abs(np.log(mag_scale[both_scales] / grav_scale[both_scales]))
    ).astype(np.float32)
    normal_match = mag_nx * grav_nx
    normal_match += mag_ny * grav_ny
    np.abs(normal_match, out=normal_match)
    np.clip(normal_match, 0.0, 1.0, out=normal_match)
    joint_amplitude = mag_peak * grav_peak
    np.sqrt(np.maximum(joint_amplitude, 0.0, out=joint_amplitude), out=joint_amplitude)
    np.multiply(joint_amplitude, widths_match, out=joint_amplitude)
    np.multiply(joint_amplitude, normal_match, out=joint_amplitude)
    feature = joint_amplitude
    feature[~support] = 0.0
    if not np.isfinite(feature).all() or np.any((feature < 0.0) | (feature > 1.0)):
        raise RuntimeError("scale-space feature violated finite [0,1] invariant")

    diagnostics: dict[str, object] = {
        "scales_px": list(scales),
        "support_cells": int(support.sum()),
        "support_fraction_of_footprint": float(support.sum() / foot.sum()),
        "magnetic": mag_diag,
        "gravity": grav_diag,
        "feature_min": float(feature.min()),
        "feature_max": float(feature.max()),
        "feature_nonzero_cells": int(np.count_nonzero(feature)),
    }
    return feature, diagnostics
