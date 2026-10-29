import numpy as np
import pytest

from gemsdoe36.scale_space import scale_space_edge_width_concordance


def test_edge_width_concordance_is_finite_bounded_and_detects_shared_edge():
    footprint = np.ones((96, 96), dtype=bool)
    magnetic = np.zeros((96, 96), dtype=np.float32)
    magnetic[:, 48:] = 1.0
    gravity = 3.0 * magnetic

    feature, diagnostics = scale_space_edge_width_concordance(
        magnetic, gravity, footprint, scales=(1.0, 2.0)
    )

    assert feature.shape == footprint.shape
    assert np.isfinite(feature).all()
    assert np.all((feature >= 0.0) & (feature <= 1.0))
    assert np.count_nonzero(feature) > 0
    assert np.max(feature[:, 43:53]) > np.max(feature[:, :35])
    assert diagnostics["support_cells"] > 0
    assert diagnostics["feature_nonzero_cells"] == np.count_nonzero(feature)


def test_invalid_and_footprint_boundaries_are_excluded_from_convolution_support():
    footprint = np.ones((96, 96), dtype=bool)
    footprint[:5, :] = False
    magnetic = np.zeros((96, 96), dtype=np.float32)
    magnetic[:, 48:] = 1.0
    gravity = magnetic.copy()
    magnetic[40:44, 40:44] = np.nan

    feature, diagnostics = scale_space_edge_width_concordance(
        magnetic, gravity, footprint, scales=(1.0, 2.0)
    )

    assert np.isfinite(feature).all()
    assert np.all(feature[~footprint] == 0.0)
    assert diagnostics["support_cells"] < footprint.sum()


def test_mismatched_inputs_are_rejected():
    with pytest.raises(ValueError, match="equal-shaped"):
        scale_space_edge_width_concordance(
            np.zeros((32, 32)), np.zeros((32, 31)), np.ones((32, 32), dtype=bool)
        )
