"""Differentiable, uncertainty-aware orientation regularization for fault probabilities.

PyTorch is an optional training dependency. Importing this package does not require it;
these functions raise a clear RuntimeError if a training caller invokes them without Torch.
Angles passed to the raster loss are in radians, measured from +column/east toward
+row/south. Geographic EN-frame angles (east toward north) must be negated first.

The principal-axis helper derives a *strain* axis from a full horizontal strain tensor. It is
not a direct stress measurement: use a defensible stress inversion or an observed stress
orientation product when the geological interpretation requires stress, and pass its local
uncertainty/regime confidence to the loss.
"""

from __future__ import annotations

import math
from typing import Any


def geographic_en_angle_to_raster(angle_en: Any) -> Any:
    """Convert an axial angle from east-toward-north to east-toward-south raster axes."""
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - exercised only without optional extra
        raise RuntimeError("Install the 'train' extra to use stress-orientation utilities") from exc
    return -torch.as_tensor(angle_en)


def principal_extension_raster_angle(
    strain_ee: Any,
    strain_en: Any,
    strain_nn: Any,
    *,
    epsilon: float = 1e-8,
) -> tuple[Any, Any]:
    """Return the maximum horizontal *strain* axis and a dimensionless confidence proxy.

    Inputs are east/north components of a symmetric, extension-positive horizontal strain
    tensor. The angle follows raster axes (east toward south) and is axial (modulo pi).
    Confidence combines normalized eigenvalue separation and a positive-maximum-strain gate
    in [0, 1]; zero, nearly isotropic, or wholly compressive tensors receive zero confidence.
    Absolute measurement uncertainty, regime probability, and interpolation uncertainty must
    still be supplied separately when building the loss confidence map.

    Components are normalized by their local maximum absolute magnitude before eigendirection
    calculations. This avoids the old `sqrt(epsilon)` artifact, which assigned nearly unit
    confidence to an exactly zero tensor, and makes confidence invariant to tensor units.

    This converts a *full tensor*. The competition's scalar dilatation, shear-rate, and
    second-invariant bands alone do not uniquely specify this direction. Strain orientation
    is not automatically stress orientation in a viscoelastic or anisotropic medium.
    """
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - exercised only without optional extra
        raise RuntimeError("Install the 'train' extra to use stress-orientation utilities") from exc

    if not math.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be finite and positive")

    components = [torch.as_tensor(value) for value in (strain_ee, strain_en, strain_nn)]
    if len({component.device for component in components}) != 1:
        raise ValueError("strain tensor components must be on the same device")
    dtype = components[0].dtype
    for component in components[1:]:
        dtype = torch.promote_types(dtype, component.dtype)
    if not dtype.is_floating_point or dtype in (torch.float16, torch.bfloat16):
        dtype = torch.float32
    components = [component.to(dtype=dtype) for component in components]
    ee, en, nn = torch.broadcast_tensors(*components)
    if not all(torch.isfinite(component).all() for component in (ee, en, nn)):
        raise ValueError("strain tensor components must be finite")

    magnitude = torch.maximum(ee.abs(), torch.maximum(en.abs(), nn.abs()))
    safe_magnitude = torch.where(magnitude > 0, magnitude, torch.ones_like(magnitude))
    ee_n, en_n, nn_n = ee / safe_magnitude, en / safe_magnitude, nn / safe_magnitude

    separation_sq = (ee_n - nn_n).square() + 4.0 * en_n.square()
    # Smoothly approaches zero at an isotropic tensor without giving the zero tensor a
    # spurious axis/confidence. epsilon is dimensionless because the components were scaled.
    separation = (torch.sqrt(separation_sq + epsilon**2) - epsilon).clamp_min(0.0)
    angle_en = 0.5 * torch.atan2(2.0 * en_n, ee_n - nn_n)
    angle_raster = -angle_en

    anisotropy_confidence = (
        separation / (ee_n.abs() + en_n.abs() + nn_n.abs() + epsilon)
    ).clamp(0.0, 1.0)
    maximum_strain = 0.5 * (ee_n + nn_n + separation)
    minimum_strain = 0.5 * (ee_n + nn_n - separation)
    extension_confidence = (
        maximum_strain.clamp_min(0.0)
        / (maximum_strain.abs() + minimum_strain.abs() + epsilon)
    ).clamp(0.0, 1.0)
    confidence = anisotropy_confidence * extension_confidence
    return angle_raster, confidence


def _single_channel_4d(value: Any, name: str) -> Any:
    import torch

    tensor = torch.as_tensor(value)
    if tensor.ndim == 2:
        tensor = tensor[None, None]
    elif tensor.ndim == 3:
        tensor = tensor[:, None]
    if tensor.ndim != 4 or tensor.shape[1] != 1:
        raise ValueError(f"{name} must have shape [H,W], [B,H,W], or [B,1,H,W]")
    return tensor


def stress_orientation_loss(
    probability: Any,
    stress_extension_angle_raster: Any,
    confidence: Any,
    *,
    valid_mask: Any | None = None,
    smoothing_sigma_px: float = 1.5,
    epsilon: float = 1e-6,
) -> Any:
    """Penalize predicted line-normal orientations inconsistent with local extension.

    A local structure tensor is built from probability gradients. For a line-like trace, the
    dominant image gradient is normal to the trace. In normal-faulting domains, that normal
    can be compared with the local horizontal extension axis. Axial orientation uses
    ``cos(2 * delta)`` so antiparallel vectors are equivalent. The caller's confidence map
    must combine data quality, uncertainty, and the probability that the assumed stress regime
    is applicable; it is zero where the prior is unavailable or physically inapplicable.

    A full-support mask erodes the valid region by the Sobel-plus-Gaussian receptive field, so
    invalid pixels and mask edges cannot create artificial line orientations. Outside-mask
    probabilities and inactive prior angles may be non-finite; they are ignored safely.

    The loss is differentiable with respect to valid ``probability`` pixels and is intended to
    be added during training, e.g. ``base_loss + lambda_stress * loss``. It is not a post-hoc
    filter. Flat predictions have zero orientation weight, so the term regularizes supervised
    candidate structures rather than hallucinating faults by itself.
    """
    try:
        import torch
        import torch.nn.functional as F
    except ImportError as exc:  # pragma: no cover - exercised only without optional extra
        raise RuntimeError("Install the 'train' extra to use stress-orientation utilities") from exc

    if not math.isfinite(smoothing_sigma_px) or smoothing_sigma_px <= 0:
        raise ValueError("smoothing_sigma_px must be finite and positive")
    if not math.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be finite and positive")

    p = _single_channel_4d(probability, "probability")
    if not p.is_floating_point() or p.dtype in (torch.float16, torch.bfloat16):
        p = p.float()
    angle = _single_channel_4d(stress_extension_angle_raster, "stress angle").to(
        device=p.device, dtype=p.dtype
    )
    conf = _single_channel_4d(confidence, "confidence").to(device=p.device, dtype=p.dtype)
    if angle.shape[0] not in (1, p.shape[0]) or angle.shape[-2:] != p.shape[-2:]:
        raise ValueError("stress angle spatial shape/batch must broadcast to probability")
    if conf.shape[0] not in (1, p.shape[0]) or conf.shape[-2:] != p.shape[-2:]:
        raise ValueError("confidence spatial shape/batch must broadcast to probability")
    angle = angle.expand(p.shape[0], -1, -1, -1)
    conf = conf.expand(p.shape[0], -1, -1, -1)

    if valid_mask is None:
        mask = torch.ones_like(p)
    else:
        mask = _single_channel_4d(valid_mask, "valid_mask").to(device=p.device, dtype=p.dtype)
        if mask.shape[0] not in (1, p.shape[0]) or mask.shape[-2:] != p.shape[-2:]:
            raise ValueError("valid_mask spatial shape/batch must broadcast to probability")
        mask = mask.expand(p.shape[0], -1, -1, -1)

    if not torch.isfinite(mask).all():
        raise ValueError("valid_mask must be finite")
    if torch.any((mask < 0.0) | (mask > 1.0)):
        raise ValueError("valid_mask must be in [0, 1]")
    valid_pixels = mask > 0.0

    if not torch.isfinite(conf[valid_pixels]).all():
        raise ValueError("confidence must be finite inside valid_mask")
    if torch.any((conf[valid_pixels] < 0.0) | (conf[valid_pixels] > 1.0)):
        raise ValueError("confidence must be in [0, 1] inside valid_mask")
    conf = torch.where(valid_pixels, conf, torch.zeros_like(conf))

    if not torch.isfinite(p.detach()[valid_pixels]).all():
        raise ValueError("probability must be finite inside valid_mask")
    if torch.any((p.detach()[valid_pixels] < 0.0) | (p.detach()[valid_pixels] > 1.0)):
        raise ValueError("probability must be in [0, 1] inside valid_mask")
    # Remove masked non-finite values before convolution (0 * NaN would remain NaN).
    p = torch.nan_to_num(p, nan=0.0, posinf=0.0, neginf=0.0)
    p = torch.where(valid_pixels, p, torch.zeros_like(p))

    active_prior = (conf > 0.0) & valid_pixels
    if torch.any(active_prior & ~torch.isfinite(angle)):
        raise ValueError(
            "stress angle must be finite wherever confidence and valid_mask are positive"
        )
    # Missing angles where the prior is explicitly inactive must not propagate NaNs via 0 * NaN.
    angle = torch.nan_to_num(angle, nan=0.0, posinf=0.0, neginf=0.0)

    # Sobel derivatives: x is increasing columns/east, y is increasing rows/south.
    sobel_x = p.new_tensor([[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]]) / 8.0
    sobel_y = p.new_tensor([[-1.0, -2.0, -1.0], [0.0, 0.0, 0.0], [1.0, 2.0, 1.0]]) / 8.0
    kernels = torch.stack((sobel_x, sobel_y))[:, None]
    padded_probability = F.pad(p, (1, 1, 1, 1), mode="replicate")
    grad = F.conv2d(padded_probability, kernels)
    gx, gy = grad[:, 0:1], grad[:, 1:2]

    # Smooth structure-tensor products with a fixed Gaussian kernel.
    radius = max(1, math.ceil(3.0 * smoothing_sigma_px))
    axis = torch.arange(-radius, radius + 1, device=p.device, dtype=p.dtype)
    gaussian_1d = torch.exp(-(axis.square()) / (2.0 * smoothing_sigma_px**2))
    gaussian = gaussian_1d[:, None] * gaussian_1d[None, :]
    gaussian = gaussian / gaussian.sum()
    smooth_kernel = gaussian[None, None].repeat(3, 1, 1, 1)
    products = torch.cat((gx.square(), gx * gy, gy.square()), dim=1)
    smoothed = F.conv2d(products, smooth_kernel, padding=radius, groups=3)
    jxx, jxy, jyy = smoothed[:, 0:1], smoothed[:, 1:2], smoothed[:, 2:3]

    anisotropy = torch.sqrt((jxx - jyy).square() + 4.0 * jxy.square() + epsilon)
    cos_2_normal = (jxx - jyy) / anisotropy
    sin_2_normal = (2.0 * jxy) / anisotropy
    cos_2_extension = torch.cos(2.0 * angle)
    sin_2_extension = torch.sin(2.0 * angle)
    alignment = (
        cos_2_normal * cos_2_extension + sin_2_normal * sin_2_extension
    ).clamp(-1.0, 1.0)

    coherence = anisotropy / (jxx + jyy + epsilon)
    # Weight by local structure energy as well as coherence. Coherence alone would give tiny
    # numerical gradients at raster borders the same influence as a strong line.
    energy = jxx + jyy

    # Retain only centers whose complete Sobel + Gaussian support lies inside valid data.
    support_radius = radius + 1
    support_width = 2 * support_radius + 1
    support_kernel = torch.ones(
        (1, 1, support_width, support_width), device=p.device, dtype=p.dtype
    )
    padded_valid = F.pad(
        valid_pixels.to(dtype=p.dtype),
        (support_radius, support_radius, support_radius, support_radius),
        mode="constant",
        value=0.0,
    )
    support_count = F.conv2d(padded_valid, support_kernel)
    support = support_count >= (support_width * support_width - 0.5)

    weight = conf * coherence * energy * mask * support.to(dtype=p.dtype)
    denominator = weight.sum()
    loss_map = (1.0 - alignment) * weight
    return loss_map.sum() / (denominator + epsilon)


def physics_informed_objective(
    base_loss: Any,
    probability: Any,
    stress_extension_angle_raster: Any,
    confidence: Any,
    *,
    lambda_stress: float,
    valid_mask: Any | None = None,
    smoothing_sigma_px: float = 1.5,
) -> tuple[Any, Any]:
    """Add stress orientation as a training-loss term and return (total, orientation)."""
    if not math.isfinite(lambda_stress) or lambda_stress < 0:
        raise ValueError("lambda_stress must be finite and non-negative")
    orientation = stress_orientation_loss(
        probability,
        stress_extension_angle_raster,
        confidence,
        valid_mask=valid_mask,
        smoothing_sigma_px=smoothing_sigma_px,
    )
    return base_loss + lambda_stress * orientation, orientation
