"""Unit tests for the exact-marginal-gain dot emitter (src/gemsdoe36/emitter.py).

These pin the correctness invariants the emitter docstring commits to:
support confinement, the upper-bound heap keys (stale re-keying), scatter-aware
max-credit, the dF = 1 - k_max accounting, budget, and termination at the
break-even bar. All cases are small analytic grids with a known answer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemsdoe36.emitter import emit_dots  # noqa: E402

H = W = 24
C = 12  # centre row/col


def _belief(box: tuple[int, int, int, int] | None = None, peak: tuple[int, int] | None = None) -> np.ndarray:
    b = np.zeros((H, W), dtype=np.float32)
    if box is not None:
        r0, r1, c0, c1 = box
        b[r0:r1, c0:c1] = 1.0
    if peak is not None:
        b[peak] = 1.0
    return b


def _truth(px: list[tuple[int, int]]) -> np.ndarray:
    t = np.zeros((H, W), dtype=np.float32)
    for r, c in px:
        t[r, c] = 1.0
    return t


def test_single_truth_stops_after_one_dot():
    # One truth pixel, belief covering it. The first dot fully credits it; every
    # further dot has dT = 0 and must be rejected by the (now positive) bar.
    res = emit_dots(_belief(box=(10, 15, 10, 15)), budget=400,
                    support_quantile=99.0, truth_proxy=_truth([(C, C)]), scatter_radius_px=3)
    assert len(res.dots) == 1
    assert (res.dots[0] == (C, C)).all()
    assert res.stopped_by in ("bar", "empty")
    assert res.credit == pytest.approx(1.0)
    assert res.fp_mass == pytest.approx(0.0)


def test_budget_caps_dots():
    # 20 well-separated truth pixels, scatter 0 -> dots only on truth pixels.
    # Odd rows -> 2 px apart, so no two truth pixels share a 300 m kernel.
    px = [(1 + 2 * i, 3) for i in range(10)] + [(1 + 2 * i, 8) for i in range(10)]
    b = np.zeros((H, W), dtype=np.float32)
    for r, c in px:
        b[r, c] = 1.0
    res = emit_dots(b, budget=7, support_quantile=99.0,
                    truth_proxy=_truth(px), scatter_radius_px=0)
    assert len(res.dots) == 7
    assert res.stopped_by == "budget"
    # Every dot must sit exactly on a truth pixel (scatter 0).
    t = _truth(px)
    for r, c in res.dots:
        assert t[r, c] == 1.0


def test_support_confinement():
    # No emitted pixel may fall outside the nominated belief support.
    b = _belief(box=(8, 17, 8, 17))  # 9x9 support box
    res = emit_dots(b, budget=400, support_quantile=99.0,
                    truth_proxy=_truth([(C, C)]), scatter_radius_px=3)
    assert len(res.dots) > 0
    for r, c in res.dots:
        assert 8 <= r < 17 and 8 <= c < 17, (r, c)


def test_dots_are_unique_and_in_range():
    b = _belief(box=(8, 17, 8, 17))
    res = emit_dots(b, budget=400, support_quantile=99.0,
                    truth_proxy=_truth([(C, C), (C, C + 1), (C, C - 1)]), scatter_radius_px=3)
    seen = set(map(tuple, res.dots.tolist()))
    assert len(seen) == len(res.dots), "duplicate dots emitted"
    assert res.dots.dtype == np.int32
    assert res.dots.min() >= 0
    assert res.dots[:, 0].max() < H and res.dots[:, 1].max() < W


def test_empty_truth_is_empty():
    res = emit_dots(_belief(box=(8, 17, 8, 17)), budget=400,
                    support_quantile=99.0, truth_proxy=np.zeros((H, W), np.float32),
                    scatter_radius_px=3)
    assert len(res.dots) == 0
    assert res.stopped_by == "empty"
    assert res.dti_estimate == 0.0


def test_zero_belief_is_empty():
    res = emit_dots(np.zeros((H, W), np.float32), budget=400,
                    support_quantile=99.0, truth_proxy=_truth([(C, C)]), scatter_radius_px=3)
    assert len(res.dots) == 0
    assert res.stopped_by == "empty"


def test_no_gain_no_dots():
    # Truth in one corner, belief support in the opposite corner: no candidate has
    # a truth pixel in its 300 m kernel, so dT = 0 everywhere and nothing is placed.
    b = np.zeros((H, W), np.float32)
    b[0:4, 0:4] = 1.0  # top-left support
    res = emit_dots(b, budget=400, support_quantile=99.0,
                    truth_proxy=_truth([(22, 22)]), scatter_radius_px=3)
    assert len(res.dots) == 0
    assert res.stopped_by == "bar"


def test_full_coverage_zero_fp():
    # Three isolated truth pixels each with belief; scatter 0 places one dot exactly
    # on each -> kmax = 1 for every dot -> fp_mass = sum(1 - kmax) = 0, credit = K.
    px = [(C - 4, C - 4), (C, C), (C + 4, C + 4)]
    b = np.zeros((H, W), np.float32)
    for r, c in px:
        b[r, c] = 1.0
    res = emit_dots(b, budget=400, support_quantile=99.0,
                    truth_proxy=_truth(px), scatter_radius_px=0)
    assert res.credit == pytest.approx(3.0)
    assert res.fp_mass == pytest.approx(0.0)
    assert len(res.dots) == 3


def test_scatter_moves_the_first_dot_off_peak():
    # Two truth pixels 2 px apart on an axis; belief fills the 5x5 box around the
    # midpoint. scatter=0 restricts candidates to the truth pixels themselves, so the
    # first dot lands on a peak (credit 1.0). scatter=3 admits the midpoint, which
    # credits BOTH truth pixels at 2/3 each (4/3 > 1.0), so the first dot is the
    # off-peak midpoint. This is the documented H2 scatter behaviour.
    b = _belief(box=(10, 15, 10, 15))
    truths = [(C, C - 1), (C, C + 1)]
    res0 = emit_dots(b, budget=400, support_quantile=99.0,
                     truth_proxy=_truth(truths), scatter_radius_px=0)
    assert tuple(res0.dots[0]) in {(C, C - 1), (C, C + 1)}, "scatter=0 must start on a peak"

    res3 = emit_dots(b, budget=400, support_quantile=99.0,
                     truth_proxy=_truth(truths), scatter_radius_px=3)
    assert (res3.dots[0] == (C, C)).all(), "scatter=3 must start on the off-peak midpoint"
    # Both reach the same full credit (K = 2) eventually.
    assert res0.credit == pytest.approx(2.0)
    assert res3.credit == pytest.approx(2.0)


def test_credit_bounded_by_K():
    b = _belief(box=(8, 17, 8, 17))
    t = _truth([(C - 2, C - 2), (C, C), (C + 2, C + 2)])
    res = emit_dots(b, budget=400, support_quantile=99.0,
                    truth_proxy=t, scatter_radius_px=3)
    assert 0.0 <= res.credit <= t.sum() + 1e-6
    assert res.fp_mass >= 0.0


def test_dti_estimate_consistent():
    b = _belief(box=(8, 17, 8, 17))
    t = _truth([(C, C)])
    res = emit_dots(b, budget=400, support_quantile=99.0,
                    truth_proxy=t, scatter_radius_px=3)
    K = float(t.sum())
    expected = res.credit / (0.2 * res.credit + 0.2 * res.fp_mass + 0.8 * K + 1e-12)
    assert res.dti_estimate == pytest.approx(expected, rel=1e-5)
