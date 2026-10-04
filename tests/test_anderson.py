"""Tests for Anderson's theory of faulting and kinematic consistency transforms."""

from __future__ import annotations

import numpy as np

from gemsdoe36.anderson import (
    anderson_kinematic_consistency,
    compute_lineament_strike_azimuth,
    filter_non_andersonian_candidates,
)


def test_strike_azimuth_of_vertical_and_horizontal_lines():
    H, W = 64, 64
    # Vertical line (runs N-S) -> normal is East-West (azimuth 90), strike is North-South (azimuth 0 / 180)
    vert = np.zeros((H, W), dtype=np.float32)
    vert[:, 30:34] = 1.0
    strike_v, _grad_v = compute_lineament_strike_azimuth(vert, sigma=1.0)
    # At line center (col 31, 32), strike should be close to 0 or 180 (N-S)
    center_strike = strike_v[32, 32]
    assert center_strike < 15.0 or center_strike > 165.0

    # Horizontal line (runs E-W) -> normal is North-South (azimuth 0/180), strike is East-West (azimuth 90)
    horiz = np.zeros((H, W), dtype=np.float32)
    horiz[30:34, :] = 1.0
    strike_h, _grad_h = compute_lineament_strike_azimuth(horiz, sigma=1.0)
    center_strike_h = strike_h[32, 32]
    assert 75.0 <= center_strike_h <= 105.0


def test_anderson_kinematic_consistency_scores():
    # Strikes near ~18 deg (Anderson normal fault strike in Great Basin) should score high (> 0.7)
    score_normal = anderson_kinematic_consistency(np.array([18.0, 20.0]))
    assert np.all(score_normal > 0.7)

    # Strikes near ~108 deg (parallel to regional extension direction) should score negative (< 0)
    score_forbidden = anderson_kinematic_consistency(np.array([105.0, 108.0]))
    assert np.all(score_forbidden < 0.0)

    # Strike-slip (Walker Lane ~145 deg) should score positive
    score_trans = anderson_kinematic_consistency(np.array([145.0]))
    assert float(score_trans[0]) > 0.4


def test_filter_non_andersonian_candidates():
    mask = np.array([True, True, True, True])
    strikes = np.array([20.0, 90.0, 100.0, 145.0])
    forbidden = filter_non_andersonian_candidates(mask, strikes, forbidden_az_min=75.0, forbidden_az_max=105.0)
    assert np.array_equal(forbidden, [False, True, True, False])
