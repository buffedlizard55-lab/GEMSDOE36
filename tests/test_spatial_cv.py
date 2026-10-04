import numpy as np
import pytest

from gemsdoe36.spatial_cv import make_spatial_folds


def test_spatial_folds_are_deterministic_and_tile_aligned():
    folds = make_spatial_folds(
        120, 160, n_splits=4, block_size_px=40, train_buffer_px=2, metric_radius_px=1, seed=7
    )
    repeat = make_spatial_folds(
        120, 160, n_splits=4, block_size_px=40, train_buffer_px=2, metric_radius_px=1, seed=7
    )
    assert len(folds) == 4
    for left, right in zip(folds, repeat, strict=True):
        np.testing.assert_array_equal(left.validation_truth_mask, right.validation_truth_mask)
        np.testing.assert_array_equal(left.train_label_mask, right.train_label_mask)
        assert not np.any(left.train_label_mask & left.validation_truth_mask)
        assert len(left.held_out_block_ids) >= 1


def test_training_collar_excludes_neighboring_labels():
    fold = make_spatial_folds(
        80, 80, n_splits=2, block_size_px=40, train_buffer_px=3, metric_radius_px=2, seed=1
    )[0]
    assert not np.any(fold.train_label_mask & fold.validation_truth_mask)
    # Every validation pixel and its 3-pixel neighborhood is excluded from training labels.
    y, x = np.argwhere(fold.validation_truth_mask)[0]
    y0, y1 = max(0, y - 3), min(80, y + 4)
    x0, x1 = max(0, x - 3), min(80, x + 4)
    assert not np.any(fold.train_label_mask[y0:y1, x0:x1])


def test_evaluation_domain_contains_metric_radius_collars():
    fold = make_spatial_folds(
        60, 60, n_splits=2, block_size_px=30, train_buffer_px=0, metric_radius_px=2, seed=4
    )[0]
    assert np.all(fold.evaluation_domain_mask[fold.validation_truth_mask])
    assert fold.evaluation_domain_mask.sum() >= fold.validation_truth_mask.sum()


def test_rejects_too_few_blocks_and_bad_shapes():
    with pytest.raises(ValueError, match="only"):
        make_spatial_folds(10, 10, n_splits=5, block_size_px=10)
    with pytest.raises(ValueError, match="valid_area shape"):
        make_spatial_folds(10, 10, valid_area=np.zeros((9, 10), dtype=bool))
