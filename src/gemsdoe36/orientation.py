"""Differentiable stress-orientation regularization for raster fault probabilities.

PyTorch is an optional training dependency.  Importing this package does not require it;
these functions raise a clear RuntimeError if a training caller invokes them without Torch.
Angles passed to the raster loss are in radians, measured from +column/east toward
+row/south.  A geographic EN-frame angle (east toward north) must be negated first.
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
    """Return the maximum horizontal extension axis and an anisotropy confidence.

    Inputs are tensor components in an east/north coordinate frame.  The returned angle
    follows raster axes (east toward south), and is axial (modulo pi).  Confidence combines
    normalized eigenvalue separation with a positive-maximum-strain gate in [0, 1]; it
    approaches zero where the tensor is nearly isotropic, the direction is poorly determined,
    or the tensor has no positive extensional eigenvalue (assuming extension-positive signs).

    This converts a *full tensor*.  The competition's listed scalar dilatation, shear-rate,
    and second-invariant bands alone do not uniquely specify this direction.
    """
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - exercised only without optional extra
        raise RuntimeError("Install the 'train' extra to use stress-orientation utilities") from exc

    ee, en, nn = torch.broadcast_tensors(
        torch.as_tensor(strain_ee), torch.as_tensor(strain_en), torch.as_tensor(strain_nn)
    )
    discriminant = torch.sqrt((ee - nn).square() + 4.0 * en.square() + epsilon)
    angle_en = 0.5 * torch.atan2(2.0 * en, ee - nn)
    angle_raster = -angle_en
    anisotropy_confidence = (discriminant / (ee.abs() + nn.abs() + epsilon)).clamp(0.0, 1.0)
    maximum_strain = 0.5 * (ee + nn + discriminant)
    extension_confidence = (maximum_strain.clamp_min(0.0) / (maximum_strain.abs() + epsilon)).clamp(
        0.0, 1.0
    )
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

    A local structure tensor is built from probability gradients.  For a line-like trace,
    the dominant image gradient is normal to the trace.  Under a normal-faulting regime,
    that normal is expected to be approximately aligned with the least-compressive /
    extensional horizontal axis.  Axial orientation uses ``cos(2 * delta)`` so antiparallel
    vectors are equivalent.  Stress confidence and tensor coherence downweight uncertain or
    isotropic locations.  Flat predictions have zero orientation weight, so this term
    regularizes supervised candidate structures; it does not invent faults on its own.

    The loss is differentiable with respect to ``probability`` and is intended to be added
    during training, e.g. ``base_loss + lambda_stress * loss``.  It is not a post-hoc filter.
    Mixed normal/strike-slip domains must be represented by a regime/uncertainty field rather
    than forcing one uniform regional direction.
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
    if not p.is_floating_point():
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

    if not torch.isfinite(p.detach()).all():
        raise ValueError("probability must be finite")
    if torch.any((p.detach() < 0.0) | (p.detach() > 1.0)):
        raise ValueError("probability must be in [0, 1]")
    if not torch.isfinite(conf).all():
        raise ValueError("confidence must be finite; use zero where the prior is unavailable")
    if not torch.isfinite(mask).all():
        raise ValueError("valid_mask must be finite")
    conf = conf.clamp(0.0, 1.0)
    mask = mask.clamp(0.0, 1.0)
    active_prior = (conf > 0.0) & (mask > 0.0)
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
    alignment = (cos_2_normal * cos_2_extension + sin_2_normal * sin_2_extension).clamp(-1.0, 1.0)

    coherence = anisotropy / (jxx + jyy + epsilon)
    # Weight by local structure energy as well as coherence.  Coherence alone would
    # give tiny numerical gradients at raster borders the same influence as a strong line.
    energy = jxx + jyy
    weight = conf * coherence * energy * mask
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
