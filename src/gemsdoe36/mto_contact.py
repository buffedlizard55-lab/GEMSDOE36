"""MTO-36: label-free magnetic-contact termination near orthogonal gravity edges.

This is a new *physical feature*, not a copy of a sibling's prediction raster.
Only organizer-band observables and the organizer footprint may be passed here.
No catalogue, scored submission, or label-derived distance is an input.

Gradients use raster row/column coordinates in pixels; the Euclidean crossing
angle is invariant to reversing the northing axis. Distances and scales are
specified on the pinned 100 m grid (see preregistration in knowledge/).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, map_coordinates

MAG_SIGMA_PX = 2.0
GRAV_SIGMA_PX = 3.0
ARM_LENGTH_PX = 6.0
SUPPORT_MARGIN_PX = 15.0


@dataclass(frozen=True)
class ContactFeatures:
    rtp_edge: np.ndarray
    gravity_edge: np.ndarray
    rtp_tangent_asymmetry: np.ndarray
    mag_termination: np.ndarray
    contact_orthogonality: np.ndarray
    orthogonal_crosscut: np.ndarray
    mtop36_field: np.ndarray
    support: np.ndarray
    mag_scale_p95: float
    grav_scale_p95: float


def _nearest_fill(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Nearest *measured* value at unsurveyed cells, never sentinel zero."""
    if not valid.any():
        raise ValueError("An input band has no finite pixels inside the footprint")
    if valid.all():
        return np.asarray(a, np.float32).copy()
    nearest = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    out = np.asarray(a, np.float32)[nearest[0], nearest[1]]
    del nearest
    return out.astype(np.float32, copy=False)


def magnetic_gravity_contact(
    rtp: np.ndarray,
    gravity: np.ndarray,
    footprint: np.ndarray,
) -> ContactFeatures:
    """One-sided RTP contact endpoint crossed by an independent gravity boundary.

    The candidate has no fitted weights or label-based calibration; the only
    numeric constants are the frozen geometry and 0.75/0.25 blending weights.
    The 95th-percentile normalization is computed on observable magnitudes
    across the unlabelled survey footprint, never on withheld fault locations.
    """
    foot = np.asarray(footprint, dtype=bool)
    m = np.asarray(rtp, dtype=np.float32)
    g = np.asarray(gravity, dtype=np.float32)
    if m.ndim != 2 or m.shape != g.shape or m.shape != foot.shape or not foot.any():
        raise ValueError("Two footprint-aligned 2D physical grids required")
    good_m = foot & np.isfinite(m) & (m > -1e30) & (m < 1e30)
    good_g = foot & np.isfinite(g) & (g > -1e30) & (g < 1e30)
    if not (good_m.any() and good_g.any()):
        raise ValueError("No finite in-footprint magnetic or gravity observations")
    support = distance_transform_edt(good_m & good_g) > SUPPORT_MARGIN_PX
    if not support.any():
        raise ValueError("Physical support vanishes after unsurveyed-boundary margin")

    mf = gaussian_filter(_nearest_fill(m, good_m), MAG_SIGMA_PX, mode="nearest")
    gf = gaussian_filter(_nearest_fill(g, good_g), GRAV_SIGMA_PX, mode="nearest")
    my, mx = np.gradient(mf)
    gy, gx = np.gradient(gf)
    del mf, gf
    mag = np.hypot(my, mx).astype(np.float32)
    grav = np.hypot(gy, gx).astype(np.float32)
    m95 = max(float(np.percentile(mag[support], 95)), 1e-7)
    g95 = max(float(np.percentile(grav[support], 95)), 1e-7)
    m_edge = np.clip(mag / m95, 0.0, 1.0).astype(np.float32)
    g_edge = np.clip(grav / g95, 0.0, 1.0).astype(np.float32)

    # Tangent = (-mx, my) for gradient normal (my, mx). Sample both arms
    # at a fixed six-pixel distance; a genuinely continuous contact has
    # similarly strong arms, but a truncated contact has a strong/weak pair.
    rr, cc = np.indices(m.shape, dtype=np.float32)
    tangent_y = np.divide(-mx, mag + 1e-7, dtype=np.float32)
    tangent_x = np.divide(my, mag + 1e-7, dtype=np.float32)
    sine = np.abs(my * gx - mx * gy) / (mag * grav + np.float32(1e-7))
    sine = np.clip(sine, 0.0, 1.0).astype(np.float32)
    del mx, my, gx, gy
    left = map_coordinates(
        mag, (rr + ARM_LENGTH_PX * tangent_y, cc + ARM_LENGTH_PX * tangent_x),
        order=1, mode="nearest", prefilter=False,
    ).astype(np.float32)
    right = map_coordinates(
        mag, (rr - ARM_LENGTH_PX * tangent_y, cc - ARM_LENGTH_PX * tangent_x),
        order=1, mode="nearest", prefilter=False,
    ).astype(np.float32)
    del rr, cc, tangent_y, tangent_x
    max_arm = np.maximum(left, right)
    asym = np.divide(
        np.abs(left - right), max_arm + np.float32(0.1 * m95), dtype=np.float32
    )
    arm_present = np.sqrt(np.clip(max_arm / m95, 0.0, 1.0)).astype(np.float32)
    weighted_asym = (arm_present * asym).astype(np.float32)
    termination = (m_edge * weighted_asym).astype(np.float32)
    del left, right, max_arm, asym, arm_present, mag, grav
    crosscut = (termination * g_edge * sine).astype(np.float32)
    field = (0.75 * crosscut + 0.25 * termination).astype(np.float32)
    for a in (m_edge, g_edge, weighted_asym, termination, sine, crosscut, field):
        a[~support] = 0.0
        if not np.isfinite(a).all() or np.any((a < 0) | (a > 1)):
            raise ValueError("Contact feature violates finite [0,1] contract")
    return ContactFeatures(
        rtp_edge=m_edge,
        gravity_edge=g_edge,
        rtp_tangent_asymmetry=weighted_asym,
        mag_termination=termination,
        contact_orthogonality=sine,
        orthogonal_crosscut=crosscut,
        mtop36_field=field,
        support=support,
        mag_scale_p95=m95,
        grav_scale_p95=g95,
    )
