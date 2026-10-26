import numpy as np
import pytest

from gemsdoe36.protocol import feature_canary, hide_segments, pooled_holdout, registry_check


def test_hide_whole_segment_and_collar():
    ids = np.zeros((20, 20), dtype=int)
    ids[3:8, 3] = 1
    ids[3:8, 5] = 2
    ids[3:8, 15] = 3
    visible, hidden, train, score = hide_segments(ids, [1], np.ones_like(ids, bool), 3)
    assert hidden.sum() == 5
    assert not visible[3:8, 5].any()
    assert visible[3:8, 15].all()
    assert not train[3:8, 3].any()
    assert not score[3:8, 5].any()
    assert not score[visible].any()
    assert score[hidden].all()


def test_canary_flags_both_polarities():
    truth = np.eye(10, dtype=bool)
    for x in [truth.astype(float), 1 - truth.astype(float)]:
        assert not feature_canary(x, truth, np.ones_like(truth))["passed"]
    assert feature_canary(np.zeros((10, 10)), truth, np.ones_like(truth))["passed"]


def test_pooled_metric_and_deterministic_ci():
    truth = np.eye(10, dtype=bool)
    cells = [(truth.astype(float), truth, np.ones_like(truth))] * 2
    result = pooled_holdout(cells, bootstrap=20)
    assert result["dti"] == pytest.approx(1)
    assert result["withheld_positives"] == 20
    assert result == pooled_holdout(cells, bootstrap=20)
    with pytest.raises(ValueError):
        pooled_holdout(cells[:1])


def test_registry_duplicate_and_missing_fail_closed():
    s = np.arange(400).reshape(20, 20)
    d = s % 31 == 0
    foot = np.ones_like(d)
    result = registry_check(s, d, foot, {"same": (s.copy(), d.copy())})
    assert not result["passed"]
    assert result["comparisons"][0]["dot_overlap_within_3px"] == 1
    with pytest.raises(ValueError):
        registry_check(s, d, foot, {})
    with pytest.raises(ValueError):
        registry_check(s, d, foot, {"bad": (s[:2], d)})
