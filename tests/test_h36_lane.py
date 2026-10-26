"""Unit tests for the H36-GPS lane primitives (synthetic grids only; no competition data needed)."""
import numpy as np
from scipy.spatial import cKDTree

from gemsdoe36.h36_emission import emit_dots, greedy_spaced
from gemsdoe36.h36_features import (
    _shift,
    coherent_line,
    dequantize,
    graben_pair,
    regional_slope_azimuth,
)


def test_dequantize_roundtrip_and_nodata():
    q = np.array([0, 1, 128, 255], np.uint8)
    x = dequantize(q, 1.0, "sqrt")
    assert np.isnan(x[0]) and x[1] == 0.0 and abs(x[3] - 1.0) < 1e-6
    lin = dequantize(q, 180.0, "linear")
    assert abs(lin[3] - 180.0) < 1e-4


def test_shift_has_no_wraparound():
    a = np.arange(16, dtype=np.float32).reshape(4, 4)
    s = _shift(a, 1, 0)  # out[y, x] = a[y + 1, x]
    assert (s[:3] == a[1:]).all() and (s[3] == 0).all()


def test_regional_slope_azimuth_east_dipping_surface():
    h, w = 60, 60
    z = -np.tile(np.arange(w, dtype=np.float32), (h, 1))  # elevation falls to the east
    az = regional_slope_azimuth(z, np.ones((h, w), bool), sigma=2.0)
    assert abs(np.nanmedian(az) - 90.0) < 1.0  # downslope azimuth = east (axial)


def test_graben_pair_requires_opposite_facing_partner():
    h, w = 80, 80
    z = -np.tile(np.arange(w, dtype=np.float32), (h, 1))
    slope_az = regional_slope_azimuth(z, np.ones((h, w), bool), sigma=2.0)
    down = np.zeros((h, w), np.float32)
    up = np.zeros((h, w), np.float32)
    coh = np.ones((h, w), np.float32)
    down[:, 30] = 1.0  # synthetic scarp
    up[:, 36] = 1.0  # antithetic scarp 6 px downslope -> graben
    gp = graben_pair(down, up, slope_az, coh)
    assert gp[40, 30] > 0.9 and gp[40, 36] > 0.9
    lone = graben_pair(down, np.zeros_like(up), slope_az, coh)
    assert lone.max() == 0.0  # a single-facing step (e.g. shoreline riser) scores zero


def test_coherent_line_prefers_straight_contour_parallel_scarps():
    h, w = 80, 80
    z = -np.tile(np.arange(w, dtype=np.float32), (h, 1))
    slope_az = regional_slope_azimuth(z, np.ones((h, w), bool), sigma=2.0)
    s = np.zeros((h, w), np.float32)
    s[:, 40] = 1.0  # N-S scarp, perpendicular to the eastward slope
    own, mx = coherent_line(s, slope_az)
    assert own[40, 40] > 0.9 and mx[40, 40] >= own[40, 40] - 1e-6


def test_greedy_spacing_and_budget():
    order = np.arange(100 * 100)
    d = greedy_spaced(order, (100, 100), 50)
    pts = np.argwhere(d)
    assert len(pts) == 50
    assert cKDTree(pts).query(pts, k=2)[0][:, 1].min() >= 3.0


def test_emit_dots_respects_eligibility_and_spacing():
    rng = np.random.default_rng(1)
    score = rng.random((120, 120)).astype(np.float32)
    elig = np.zeros((120, 120), bool)
    elig[20:100, 20:100] = True
    d = emit_dots(score, elig, 300)
    pts = np.argwhere(d)
    assert len(pts) == 300 and not (d & ~elig).any()
    assert cKDTree(pts).query(pts, k=2)[0][:, 1].min() >= 3.0


def test_emit_dots_support_keeps_ridges_next_to_an_exclusion_zone():
    h, w = 120, 120
    yy, xx = np.mgrid[0:h, 0:w]
    score = np.exp(-((xx - 60) ** 2) / 8.0).astype(np.float32)  # N-S ridge at x = 60
    support = np.ones((h, w), bool)
    eligible = support.copy()
    eligible[55:65, :] = False  # an exclusion band crossing the ridge
    with_support = emit_dots(score, eligible, 30, support=support)
    pts = np.argwhere(with_support)
    near = pts[(np.abs(pts[:, 0] - 60) <= 12) & (np.abs(pts[:, 1] - 60) <= 1)]
    assert not (with_support & ~eligible).any()
    assert len(near) >= 2  # ridge dots survive right next to the excluded band
