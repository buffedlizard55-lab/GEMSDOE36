"""MTO-36 tests use synthetic physics-only grids, never copied predictions."""

import numpy as np
import pytest

from gemsdoe36.mto_contact import magnetic_gravity_contact


def test_termination_prefers_one_sided_magnetic_contact() -> None:
    n = 151
    yy, xx = np.indices((n, n))
    footprint = np.ones((n, n), bool)
    gravity = np.where(yy >= 75, 1.0, -1.0).astype(np.float32)
    # A continuous lithologic contact has no true endpoint. A displaced or
    # eroded contact ends at the crossing gravity structure near (75, 75).
    continuous = np.where(xx >= 75, 1.0, -1.0).astype(np.float32)
    ended = np.where(yy < 75, continuous, 0.0).astype(np.float32)
    a = magnetic_gravity_contact(continuous, gravity, footprint)
    b = magnetic_gravity_contact(ended, gravity, footprint)
    roi = np.s_[69:79, 73:77]
    assert float(np.max(b.mag_termination[roi])) > float(np.max(a.mag_termination[roi]))
    assert float(np.max(b.orthogonal_crosscut[roi])) > float(np.max(a.orthogonal_crosscut[roi]))
    for result in (a, b):
        assert result.mtop36_field.dtype == np.float32
        assert np.isfinite(result.mtop36_field).all()
        assert result.mtop36_field.min() >= 0 and result.mtop36_field.max() <= 1


def test_missing_survey_boundaries_cannot_form_prediction() -> None:
    shape = (75, 75)
    m = np.tile(np.arange(shape[1], dtype=np.float32), (shape[0], 1))
    g = np.tile(np.arange(shape[0], dtype=np.float32)[:, None], (1, shape[1]))
    foot = np.ones(shape, bool)
    m[:, :7] = np.nan
    features = magnetic_gravity_contact(m, g, foot)
    assert not features.support[:, :22].any()
    assert not features.mtop36_field[:, :22].any()
    with pytest.raises(ValueError, match="No finite in-footprint"):
        magnetic_gravity_contact(np.full(shape, np.nan), g, foot)
