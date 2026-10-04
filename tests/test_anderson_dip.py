"""Unit tests for the Anderson (1905) fault-mechanics utilities.

Covers the angle conventions (azimuth->raster, axial mod-pi distance, axial
circular mean), the per-tile structure-tensor strike, the soft
strike-consistency weight, and the dip pullback / projection geometry.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemsdoe36.anderson_dip import (  # noqa: E402
    ExtensionField,
    axial_distance,
    azimuth_to_raster,
    catalogue_strikes,
    circular_mean_axial,
    dip_project,
    dip_pullback_offsets,
    strike_consistency_weight,
)

T = np.pi / 2


# --------------------------------------------------------------------------- #
# Angle conventions
# --------------------------------------------------------------------------- #
def test_azimuth_to_raster_cardinals():
    # 0=north -> -pi/2, 90=east -> 0, 180=south -> pi/2, 270=west -> pi.
    assert azimuth_to_raster(0.0) == pytest.approx(-T)
    assert azimuth_to_raster(90.0) == pytest.approx(0.0, abs=1e-9)
    assert azimuth_to_raster(180.0) == pytest.approx(T)
    assert azimuth_to_raster(270.0) == pytest.approx(np.pi)


def test_azimuth_to_raster_array_and_range():
    az = np.array([0.0, 45.0, 275.0, 359.0])
    out = azimuth_to_raster(az)
    assert out.shape == az.shape
    assert np.all(np.abs(out) <= np.pi + 1e-12)


def test_axial_distance_mod_pi():
    # Axial (line) directions: a and a+pi are the same line -> distance 0.
    assert axial_distance(0.0, 0.0) == pytest.approx(0.0)
    assert axial_distance(0.3, 0.3 + np.pi) == pytest.approx(0.0, abs=1e-12)
    # Orthogonal lines -> pi/2.
    assert axial_distance(0.0, T) == pytest.approx(T)
    assert axial_distance(np.pi / 4, 3 * np.pi / 4) == pytest.approx(T)
    # Always in [0, pi/2].
    a = np.linspace(-3, 3, 50)
    b = np.linspace(0, np.pi, 50)
    d = axial_distance(a, b)
    assert np.all(d >= 0) and np.all(d <= T + 1e-12)


def test_circular_mean_axial_same_line():
    # {0, pi} are the same axial line -> mean is that line (0 or ~pi after the %pi
    # wrap), R=1.
    mean, r = circular_mean_axial(np.array([0.0, np.pi]))
    assert axial_distance(mean, 0.0) < 1e-9
    assert r == pytest.approx(1.0, abs=1e-9)


def test_circular_mean_axial_orthogonal_cancels():
    # {0, pi/2} are orthogonal lines -> resultant cancels, R=0.
    mean, r = circular_mean_axial(np.array([0.0, T]))
    assert r == pytest.approx(0.0, abs=1e-9)


def test_circular_mean_axial_concentrated():
    mean, r = circular_mean_axial(np.array([0.2, 0.21, 0.19]))
    assert mean == pytest.approx(0.2, abs=1e-6)
    assert r == pytest.approx(1.0, abs=1e-3)  # tiny spread -> R just under 1


def test_circular_mean_axial_degenerate():
    mean, r = circular_mean_axial(np.array([np.nan, 0.5]), weights=np.array([0.0, 0.0]))
    assert mean == 0.0 and r == 0.0


# --------------------------------------------------------------------------- #
# Per-tile structure-tensor strike
# --------------------------------------------------------------------------- #
def _vertical_line(tile_px: int = 120, width: int = 3) -> np.ndarray:
    cat = np.zeros((tile_px, tile_px), dtype=np.float32)
    c = tile_px // 2
    cat[tile_px // 10 : 9 * tile_px // 10, c - width // 2 : c + width // 2 + 1] = 1.0
    return cat


def test_catalogue_strikes_vertical_line():
    strikes = catalogue_strikes(_vertical_line(), tile_px=120, min_pixels=40)
    assert (0, 0) in strikes
    strike, conc, n = strikes[(0, 0)]
    # A vertical (N-S) line has raster strike ~ pi/2.
    assert abs(strike - T) < 0.2 or abs(strike - (T - np.pi)) < 0.2
    assert conc > 0.5
    assert n > 100


def test_catalogue_strikes_isotropic_low_concentration():
    cat = np.zeros((120, 120), dtype=np.float32)
    cat[40:80, 40:80] = 1.0  # a filled blob: no preferred line orientation
    strikes = catalogue_strikes(cat, tile_px=120, min_pixels=40)
    if (0, 0) in strikes:
        _, conc, _ = strikes[(0, 0)]
        assert conc < 0.35


def test_catalogue_strikes_empty():
    assert catalogue_strikes(np.zeros((120, 120), np.float32)) == {}


# --------------------------------------------------------------------------- #
# Soft strike-consistency weight
# --------------------------------------------------------------------------- #
def _ef(angle: float, conf: float) -> ExtensionField:
    return ExtensionField(
        angle_raster=np.full((60, 60), angle, dtype=np.float32),
        confidence=np.full((60, 60), conf, dtype=np.float32),
    )


def _line_evidence(orientation: str) -> np.ndarray:
    e = np.zeros((60, 60), dtype=np.float32)
    if orientation == "vertical":  # N-S, strike ~ pi/2
        e[5:55, 28:32] = 1.0
    else:  # horizontal, strike ~ 0
        e[28:32, 5:55] = 1.0
    return e


def test_strike_weight_consistent_line_unpenalised():
    # Extension east (raster 0) -> Anderson strike N-S (pi/2). A vertical line is
    # consistent -> weight ~ 1 at the line.
    w = strike_consistency_weight(_line_evidence("vertical"), _ef(0.0, 1.0))
    assert w[30, 30] == pytest.approx(1.0, abs=0.05)


def test_strike_weight_inconsistent_line_at_floor():
    # Extension east (raster 0); a horizontal line (strike ~ 0, parallel to
    # extension) is inconsistent -> weight ~ floor (0.6) at the line.
    w = strike_consistency_weight(_line_evidence("horizontal"), _ef(0.0, 1.0), floor=0.6)
    assert w[30, 30] == pytest.approx(0.6, abs=0.08)
    assert np.all(w >= 0.6 - 1e-6) and np.all(w <= 1.0 + 1e-6)


def test_strike_weight_flat_no_penalty():
    # No lineament (flat) -> no orientation to judge -> weight ~ 1 everywhere.
    w = strike_consistency_weight(np.zeros((60, 60), np.float32), _ef(0.0, 1.0))
    assert np.all(w > 0.99)


def test_strike_weight_low_confidence_no_penalty():
    # Inconsistent line but zero extension confidence -> no penalty (weight ~ 1).
    w = strike_consistency_weight(_line_evidence("horizontal"), _ef(0.0, 0.0), floor=0.6)
    assert w[30, 30] == pytest.approx(1.0, abs=0.02)


def test_strike_weight_floor_validation():
    with pytest.raises(ValueError):
        strike_consistency_weight(np.zeros((10, 10), np.float32), _ef(0.0, 1.0), floor=1.5)


# --------------------------------------------------------------------------- #
# Dip pullback offsets and projection
# --------------------------------------------------------------------------- #
def test_dip_pullback_direction_against_extension():
    # Extension east (raster 0): up-dip is against extension -> west (-col).
    ef = ExtensionField(
        angle_raster=np.zeros((240, 240), np.float32),
        confidence=np.ones((240, 240), np.float32),
    )
    offs = dip_pullback_offsets(ef, tile_px=120)
    assert (0, 0) in offs
    for dy, dx, wgt in offs[(0, 0)]:
        assert dx <= 0, "up-dip of an eastward extension must be westward"
        assert dy == 0
        assert wgt > 0
    # Magnitude grows with depth (last bank depth is the largest offset).
    mags = [abs(dx) for _, dx, _ in offs[(0, 0)]]
    assert mags[-1] >= mags[0]


def test_dip_project_constant_block_interior():
    # A uniform deep-channel block, projected up-dip, stays ~1 in the interior and
    # never exceeds the source amplitude (it is a confidence-weighted average).
    ev = np.ones((120, 120), dtype=np.float32)
    ef = ExtensionField(
        angle_raster=np.zeros((120, 120), np.float32),
        confidence=np.ones((120, 120), np.float32),
    )
    out = dip_project(ev, ef, tile_px=120)
    assert out[60, 60] == pytest.approx(1.0, abs=0.05)
    assert np.all(out >= -1e-6) and np.all(out <= 1.0 + 1e-6)


def test_dip_project_zero_confidence_is_zero():
    ev = np.ones((120, 120), dtype=np.float32)
    ef = ExtensionField(
        angle_raster=np.zeros((120, 120), np.float32),
        confidence=np.zeros((120, 120), np.float32),
    )
    out = dip_project(ev, ef, tile_px=120)
    assert np.all(out == 0.0)


def test_dip_project_shifts_mass_up_dip():
    # A narrow deep line, extension east: projection shifts it west (up-dip), so the
    # mass centroid moves in -col and no mass is created (weighted-averaged <= source).
    ev = np.zeros((120, 120), dtype=np.float32)
    ev[10:110, 70:74] = 1.0  # a vertical deep line at col ~72
    ef = ExtensionField(
        angle_raster=np.zeros((120, 120), np.float32),
        confidence=np.ones((120, 120), np.float32),
    )
    out = dip_project(ev, ef, tile_px=120)
    ys, xs = np.nonzero(out > 0.05)
    assert len(xs) > 0
    src_centroid = np.mean(np.nonzero(ev > 0)[1])
    out_centroid = np.mean(xs)
    assert out_centroid < src_centroid, "projected mass must move up-dip (west)"
    assert out.max() <= 1.0 + 1e-6
