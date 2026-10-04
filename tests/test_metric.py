import numpy as np
import pytest

from gemsdoe36.metric import DTIComponents, distance_weighted_tversky


def test_exact_match_scores_one():
    truth = np.zeros((9, 9), dtype=np.uint8)
    truth[4, 4] = 1
    pred = truth.astype(np.float32)
    result = distance_weighted_tversky(pred, truth, return_components=True)
    assert isinstance(result, DTIComponents)
    assert result.true_positive == pytest.approx(1.0)
    assert result.false_positive == pytest.approx(0.0)
    assert result.false_negative == pytest.approx(0.0)
    assert result.score == pytest.approx(1.0, abs=1e-7)


def test_one_pixel_offset_matches_triangular_kernel_and_tversky_weights():
    truth = np.zeros((9, 9), dtype=np.uint8)
    truth[4, 4] = 1
    pred = np.zeros_like(truth, dtype=np.float32)
    pred[4, 5] = 1.0  # 100 m away: k = 1 - 100/300 = 2/3
    result = distance_weighted_tversky(pred, truth, return_components=True)
    assert result.true_positive == pytest.approx(2.0 / 3.0, rel=1e-6)
    assert result.false_positive == pytest.approx(1.0 / 3.0, rel=1e-6)
    assert result.false_negative == pytest.approx(1.0 / 3.0, rel=1e-6)
    assert result.score == pytest.approx(2.0 / 3.0, rel=1e-6)


def test_redundant_prediction_gets_no_extra_tp_but_is_charged_as_fp():
    truth = np.zeros((11, 11), dtype=np.uint8)
    truth[5, 5] = 1
    pred = np.zeros_like(truth, dtype=np.float32)
    pred[5, 5] = 1.0
    pred[5, 1] = 0.7  # 400 m away: no TP credit, full FP mass
    result = distance_weighted_tversky(pred, truth, return_components=True)
    assert result.true_positive == pytest.approx(1.0)
    assert result.false_positive == pytest.approx(0.7)
    assert result.false_negative == pytest.approx(0.0)
    assert result.score == pytest.approx(1.0 / (1.0 + 0.2 * 0.7), rel=1e-6)


def test_max_over_predicted_pixels_not_sum():
    truth = np.zeros((9, 9), dtype=np.uint8)
    truth[4, 4] = 1
    pred = np.zeros_like(truth, dtype=np.float32)
    pred[4, 4] = 0.5
    pred[4, 5] = 0.8
    result = distance_weighted_tversky(pred, truth, return_components=True)
    assert result.true_positive == pytest.approx(0.8 * 2.0 / 3.0, rel=1e-6)
    assert result.false_negative == pytest.approx(1.0 - 0.8 * 2.0 / 3.0, rel=1e-6)


def test_empty_truth_has_zero_score_and_prediction_is_fp():
    truth = np.zeros((5, 5), dtype=np.uint8)
    pred = np.zeros_like(truth, dtype=np.float32)
    pred[2, 2] = 0.4
    result = distance_weighted_tversky(pred, truth, return_components=True)
    assert result.true_positive == 0.0
    assert result.false_positive == pytest.approx(0.4)
    assert result.false_negative == 0.0
    assert result.score == 0.0


def test_valid_mask_allows_nodata_only_outside_region():
    truth = np.zeros((5, 5), dtype=np.float32)
    pred = np.full((5, 5), np.nan, dtype=np.float32)
    valid = np.zeros((5, 5), dtype=bool)
    valid[1:4, 1:4] = True
    pred[valid] = 0.0
    truth[2, 2] = 1
    pred[2, 2] = 1
    assert distance_weighted_tversky(pred, truth, valid_mask=valid) == pytest.approx(1.0)


def test_range_and_shape_contract_is_fail_closed():
    truth = np.zeros((5, 5), dtype=np.uint8)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        distance_weighted_tversky(np.full((5, 5), 1.01), truth)
    with pytest.raises(ValueError, match="shape mismatch"):
        distance_weighted_tversky(np.zeros((4, 5)), truth)
    bad = np.zeros((5, 5), dtype=float)
    bad[0, 0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        distance_weighted_tversky(bad, truth)


def test_anisotropic_pixel_spacing_uses_map_distance():
    truth = np.zeros((9, 9), dtype=np.uint8)
    truth[4, 4] = 1
    pred = np.zeros_like(truth, dtype=np.float32)
    pred[5, 4] = 1.0
    # Row spacing 300 m puts this pixel exactly at the support radius.
    result = distance_weighted_tversky(
        pred, truth, pixel_size_m=(300.0, 100.0), radius_m=300.0, return_components=True
    )
    assert result.true_positive == pytest.approx(0.0)
    assert result.false_negative == pytest.approx(1.0)
    assert result.false_positive == pytest.approx(1.0)
