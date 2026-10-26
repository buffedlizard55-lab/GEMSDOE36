"""Raissi-Anderson Anisotropic Structure-Tensor Variational Diffusion (pure float32 NumPy/SciPy).

Implements a memory-bounded (<250 MB peak RAM on 3730x3292 grids) variational PDE refinement
consistent with Anderson (1905) fault mechanics and Raissi, Perdikaris & Karniadakis (2019)
physics-informed orientation regularization:

  1. Coherence-enhancing tangent diffusion bridges short (100-400 m) alluvial wash gaps strictly
     along coherent ridge strikes t = (-sin phi_n, cos phi_n) without fattening across strike.
  2. Differentiable Anderson stress-orientation damping penalizes lineaments whose normal deviates
     into the mechanically forbidden sigma_3-parallel envelope (E-W flight-line / drainage noise),
     weighted by local extension confidence c(x) and ridge coherence kappa(x).
  3. Footprint support is eroded by the Sobel/Gaussian stencil radius so survey-boundary edges
     never inject spurious orientation gradients.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.ndimage import binary_erosion, gaussian_filter

from .anderson_dip import ExtensionField, azimuth_to_raster


def structure_tensor_orientation(
    field: np.ndarray,
    valid_mask: np.ndarray,
    *,
    grad_sigma_px: float = 1.0,
    tensor_sigma_px: float = 2.0,
    eps: float = 1e-7,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (normal_angle_rad, coherence, gx, gy) on valid interior support.

    ``normal_angle_rad`` is in raster coordinates (from +col/East toward +row/South),
    matching ``anderson_dip.py`` and ``orientation.py``.
    """
    foot = np.asarray(valid_mask, dtype=bool)
    clean = np.where(foot & np.isfinite(field), field, 0.0).astype(np.float32)
    sm = gaussian_filter(clean, sigma=grad_sigma_px) if grad_sigma_px > 0 else clean
    gy, gx = np.gradient(sm)
    gx = gx.astype(np.float32, copy=False)
    gy = gy.astype(np.float32, copy=False)
    del sm

    jxx = gaussian_filter(gx * gx, sigma=tensor_sigma_px).astype(np.float32)
    jxy = gaussian_filter(gx * gy, sigma=tensor_sigma_px).astype(np.float32)
    jyy = gaussian_filter(gy * gy, sigma=tensor_sigma_px).astype(np.float32)

    trace = jxx + jyy + eps
    diff = jxx - jyy
    aniso = np.hypot(diff, 2.0 * jxy).astype(np.float32)
    normal_angle = (0.5 * np.arctan2(2.0 * jxy, diff)).astype(np.float32)
    coherence = np.clip(aniso / trace, 0.0, 1.0).astype(np.float32)
    del jxx, jxy, jyy, trace, diff, aniso

    radius = max(1, math.ceil(2.0 * tensor_sigma_px))
    interior = binary_erosion(foot, iterations=radius, border_value=0)
    coherence = np.where(interior, coherence, 0.0).astype(np.float32)
    return normal_angle, coherence, gx, gy


def anderson_alignment_field(
    normal_angle_rad: np.ndarray,
    extension: ExtensionField,
    *,
    walker_lane_strike_az_deg: float = 145.0,
    walker_lane_weight: float = 0.65,
) -> np.ndarray:
    """Compute effective axial alignment in [-1, 1] with Andersonian normal & transtensional modes.

    +1: ridge normal aligns with local horizontal extension sigma_3 (normal fault perpendicular
        to sigma_3) or secondary NW-SE Walker Lane dextral transtensional mode.
    -1: ridge strikes parallel to sigma_3 (ridge normal perpendicular to sigma_3; mechanically
        forbidden opening mode / E-W flight-line striping).
    """
    ext_ang = extension.angle_raster.astype(np.float32, copy=False)
    align_normal = np.cos(2.0 * (normal_angle_rad - ext_ang)).astype(np.float32)

    # Walker Lane dextral transtensional strike (~145 deg azimuth -> normal at ~55 deg azimuth)
    wl_normal_rad = float(azimuth_to_raster((walker_lane_strike_az_deg - 90.0) % 180.0))
    align_wl = np.cos(2.0 * (normal_angle_rad - wl_normal_rad)).astype(np.float32)

    # Permit conjugate Walker Lane mode while preserving negative penalty on sigma_3-parallel E-W lines
    effective = np.where(
        align_normal >= 0.0,
        np.maximum(align_normal, walker_lane_weight * np.maximum(align_wl, 0.0)),
        np.where(
            align_wl > 0.35,
            walker_lane_weight * align_wl * 0.5,
            align_normal,
        ),
    )
    return np.clip(effective, -1.0, 1.0).astype(np.float32)


def stress_orientation_energy_np(
    probability: np.ndarray,
    extension: ExtensionField,
    valid_mask: np.ndarray,
    *,
    tensor_sigma_px: float = 1.5,
    eps: float = 1e-6,
) -> float:
    """NumPy scalar mirror of gemsdoe36.orientation.stress_orientation_loss for diagnostics/tests."""
    foot = np.asarray(valid_mask, dtype=bool)
    p = np.where(foot & np.isfinite(probability), probability, 0.0).astype(np.float32)
    gy, gx = np.gradient(p)
    jxx = gaussian_filter((gx * gx).astype(np.float32), sigma=tensor_sigma_px)
    jxy = gaussian_filter((gx * gy).astype(np.float32), sigma=tensor_sigma_px)
    jyy = gaussian_filter((gy * gy).astype(np.float32), sigma=tensor_sigma_px)
    energy = jxx + jyy
    aniso = np.sqrt((jxx - jyy) ** 2 + 4.0 * (jxy**2) + eps)
    coherence = aniso / (energy + eps)
    normal = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy)
    alignment = np.clip(np.cos(2.0 * (normal - extension.angle_raster)), -1.0, 1.0)
    radius = max(1, math.ceil(2.5 * tensor_sigma_px))
    support = binary_erosion(foot, iterations=radius, border_value=0)
    w = extension.confidence * coherence * energy * support.astype(np.float32)
    return float(np.sum((1.0 - alignment) * w, dtype=np.float64) / (np.sum(w, dtype=np.float64) + eps))


def variational_anderson_refine(
    probability: np.ndarray,
    extension: ExtensionField,
    valid_mask: np.ndarray,
    *,
    steps: int = 4,
    step_size: float = 0.22,
    lambda_cohere: float = 0.30,
    lambda_anderson: float = 0.18,
    lambda_anchor: float = 0.20,
    tensor_sigma_px: float = 2.0,
) -> tuple[np.ndarray, dict[str, float]]:
    """Apply variational anisotropic tangent diffusion + Anderson stress regularization in [0, 1]."""
    foot = np.asarray(valid_mask, dtype=bool)
    if probability.shape != foot.shape:
        raise ValueError("probability and valid_mask shapes must match")
    if steps < 0 or step_size < 0:
        raise ValueError("steps and step_size must be non-negative")

    p0 = np.zeros(foot.shape, dtype=np.float32)
    p0[foot] = np.clip(np.nan_to_num(probability[foot], nan=0.0), 0.0, 1.0).astype(np.float32)
    p = p0.copy()

    e_before = stress_orientation_energy_np(p0, extension, foot, tensor_sigma_px=1.5)

    for _ in range(steps):
        normal_ang, coherence, gx, gy = structure_tensor_orientation(
            p, foot, grad_sigma_px=0.8, tensor_sigma_px=tensor_sigma_px
        )
        # Tangent unit vector t = (-sin(normal), cos(normal)) in (col=x, row=y) coordinates:
        # normal = (cos a, sin a) in (x, y) => tangent = (-sin a, cos a) in (x, y)
        tx = -np.sin(normal_ang).astype(np.float32)
        ty = np.cos(normal_ang).astype(np.float32)

        # Directional derivative along fault strike: d_t p = tx * gx + ty * gy
        dt_p = tx * gx + ty * gy
        flux_x = coherence * tx * dt_p
        flux_y = coherence * ty * dt_p
        _, div_x = np.gradient(flux_x)
        div_y, _ = np.gradient(flux_y)
        tangent_laplacian = (div_x + div_y).astype(np.float32)
        del tx, ty, dt_p, flux_x, flux_y, div_x, div_y, gx, gy

        alignment = anderson_alignment_field(normal_ang, extension)
        conf = extension.confidence.astype(np.float32, copy=False)

        # Soft Raissi-Anderson directional force:
        # - damps coherent E-W sigma_3-parallel artifacts (alignment < 0)
        # - gently reinforces coherent Anderson-aligned ridges (alignment > 0) without hallucinating flat areas
        forbidden = np.maximum(0.0, -alignment)
        permitted = np.maximum(0.0, alignment)
        orient_force = conf * coherence * (0.35 * permitted * p * (1.0 - p) - forbidden * p)

        update = (
            lambda_cohere * tangent_laplacian
            + lambda_anderson * orient_force
            - lambda_anchor * (p - p0)
        )
        p[foot] = np.clip(p[foot] + step_size * update[foot], 0.0, 1.0)
        p[~foot] = 0.0
        del normal_ang, coherence, alignment, forbidden, permitted, orient_force, update

    e_after = stress_orientation_energy_np(p, extension, foot, tensor_sigma_px=1.5)
    diag = {
        "stress_energy_before": e_before,
        "stress_energy_after": e_after,
        "stress_energy_delta": e_after - e_before,
        "mean_prob_before": float(p0[foot].mean()) if foot.any() else 0.0,
        "mean_prob_after": float(p[foot].mean()) if foot.any() else 0.0,
    }
    return p, diag
