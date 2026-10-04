import math

import pytest

torch = pytest.importorskip("torch")

from gemsdoe36.orientation import (
    geographic_en_angle_to_raster,
    physics_informed_objective,
    principal_extension_raster_angle,
    stress_orientation_loss,
)


def _stripe(vertical: bool) -> torch.Tensor:
    p = torch.zeros((1, 1, 40, 40), dtype=torch.float32)
    if vertical:
        p[:, :, :, 18:22] = 1.0
    else:
        p[:, :, 18:22, :] = 1.0
    return p


def test_vertical_line_normal_aligns_with_east_west_extension_axis():
    confidence = torch.ones((40, 40))
    vertical = _stripe(vertical=True)
    horizontal = _stripe(vertical=False)
    angle_east_west = torch.zeros((40, 40))
    loss_vertical = stress_orientation_loss(vertical, angle_east_west, confidence)
    loss_horizontal = stress_orientation_loss(horizontal, angle_east_west, confidence)
    assert loss_vertical < 0.05
    assert loss_horizontal > loss_vertical + 0.5


def test_axial_orientation_treats_opposite_directions_as_equivalent():
    p = _stripe(vertical=True)
    confidence = torch.ones((40, 40))
    zero = stress_orientation_loss(p, torch.zeros((40, 40)), confidence)
    pi = stress_orientation_loss(p, torch.full((40, 40), math.pi), confidence)
    assert zero.item() == pytest.approx(pi.item(), abs=1e-6)


def test_zero_confidence_removes_orientation_penalty():
    p = _stripe(vertical=False)
    loss = stress_orientation_loss(p, torch.zeros((40, 40)), torch.zeros((40, 40)))
    assert loss.item() == pytest.approx(0.0, abs=1e-6)


def test_flat_probability_has_no_orientation_signal():
    p = torch.full((1, 1, 24, 24), 0.5)
    loss = stress_orientation_loss(p, torch.zeros((24, 24)), torch.ones((24, 24)))
    assert loss.item() == pytest.approx(0.0, abs=1e-6)


def test_unavailable_nan_angle_is_ignored_but_active_nan_is_rejected():
    p = _stripe(vertical=False)
    angle = torch.full((40, 40), torch.nan)
    confidence = torch.zeros((40, 40))
    assert stress_orientation_loss(p, angle, confidence).item() == pytest.approx(0.0)

    confidence[10, 10] = 1.0
    with pytest.raises(ValueError, match="stress angle must be finite"):
        stress_orientation_loss(p, angle, confidence)


def test_orientation_objective_is_differentiable_and_additive():
    p = _stripe(vertical=False).requires_grad_()
    angle = torch.zeros((40, 40))
    confidence = torch.ones((40, 40))
    base = torch.tensor(0.4, requires_grad=True)
    total, orientation = physics_informed_objective(base, p, angle, confidence, lambda_stress=0.25)
    assert total.item() == pytest.approx(0.4 + 0.25 * orientation.item())
    total.backward()
    assert p.grad is not None
    assert torch.isfinite(p.grad).all()
    assert p.grad.abs().sum().item() > 0
    assert base.grad.item() == pytest.approx(1.0)


def test_principal_extension_axis_and_raster_angle_conversion():
    # East-west extension: eigenvector is east, hence raster angle 0.
    angle, confidence = principal_extension_raster_angle(2.0, 0.0, 0.0)
    assert angle.item() == pytest.approx(0.0, abs=1e-6)
    assert confidence.item() > 0.9

    # Northward EN vector maps to negative raster angle because rows increase southward.
    assert geographic_en_angle_to_raster(torch.tensor(math.pi / 2)).item() == pytest.approx(
        -math.pi / 2
    )


def test_isotropic_tensor_has_low_direction_confidence():
    _, confidence = principal_extension_raster_angle(1.0, 0.0, 1.0)
    assert confidence.item() < 0.01
    # A tensor with only compressive principal strains must not act as an extension prior.
    _, compressive_confidence = principal_extension_raster_angle(-2.0, 0.0, -1.0)
    assert compressive_confidence.item() < 0.01


def test_invalid_regularization_weight_is_rejected():
    with pytest.raises(ValueError, match="lambda_stress"):
        physics_informed_objective(
            torch.tensor(1.0),
            _stripe(vertical=True),
            torch.zeros((40, 40)),
            torch.ones((40, 40)),
            lambda_stress=-0.1,
        )
