"""WDP-36: upward-continuation worm-persistence features (buried-fault lane).

Implements exactly the detector locked in
``evidence/wdp36_preregistration_20261026.json``:

* For the TMI (band 14) and isostatic gravity (band 13) potential fields,
  total-horizontal-derivative (THDR) worms are recomputed after FFT upward
  continuation to heights 0/200/400/800 m.  Persistence is the geometric mean
  of the per-height footprint percentile ranks, so deep basement-fault edges
  (which survive continuation) outrank shallow sources and 200-400 m
  flight-line striping (which decay as ``exp(-|k| h)``).
* EXP-2 adds geodetic strain-rate gradient ridges (bands 04/07/08).
* EXP-3 adds a seismic proximity/intensity composite (bands 16/10).

The detector is fully unsupervised: it reads no catalogue-derived quantity.
All grids are float32 and processed one field at a time to stay within a
small RAM budget (one 3730x3292 float32 grid is ~49 MB).
"""

from __future__ import annotations

import numpy as np
from scipy import fft as spfft
from scipy.ndimage import gaussian_filter

SENTINEL = -3.4028235e38
HEIGHTS_M: tuple[float, ...] = (0.0, 200.0, 400.0, 800.0)
PIXEL_M = 100.0


def clean_band(raw: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Return float32 grid with sentinel/non-finite cells set to NaN outside use.

    Valid cells are ``footprint & finite & > SENTINEL/2``.  Invalid cells are
    filled with the footprint median of valid cells (the value locked in the
    preregistration) so spectral operations see a complete grid.
    """
    a = np.asarray(raw, dtype=np.float32)
    foot = np.asarray(footprint, dtype=bool)
    if a.shape != foot.shape:
        raise ValueError("band and footprint shapes must match")
    valid = foot & np.isfinite(a) & (a > np.float32(SENTINEL / 2.0))
    if not valid.any():
        raise ValueError("band has no valid footprint cells")
    median = float(np.median(a[valid]))
    out = np.where(valid, a, np.float32(median)).astype(np.float32)
    return out


def footprint_percentile_ranks(values: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Percentile ranks in [0, 1] over footprint cells; 0 outside footprint.

    Ties receive distinct ranks in stable (row-major) order; THDR/strain
    fields are continuous so tie handling is immaterial beyond determinism.
    """
    v = np.asarray(values, dtype=np.float32)
    foot = np.asarray(footprint, dtype=bool)
    if v.shape != foot.shape:
        raise ValueError("values and footprint shapes must match")
    vals = v[foot]
    if vals.size == 0:
        raise ValueError("empty footprint")
    if not np.isfinite(vals).all():
        raise ValueError("non-finite values inside footprint cannot be ranked")
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(vals.size, dtype=np.float32)
    denom = max(vals.size - 1, 1)
    ranks[order] = (np.arange(vals.size, dtype=np.float64) / denom).astype(np.float32)
    out = np.zeros(v.shape, dtype=np.float32)
    out[foot] = ranks
    return out


def thdr_ranks_by_height(
    field_filled: np.ndarray,
    footprint: np.ndarray,
    heights_m: tuple[float, ...] = HEIGHTS_M,
    pixel_m: float = PIXEL_M,
) -> dict[float, np.ndarray]:
    """Footprint percentile ranks of THDR after upward continuation per height.

    Uses one real FFT of the demeaned filled field; each height applies the
    Laplace continuation factor ``exp(-|k| h)`` and spectral derivatives.
    """
    f = np.asarray(field_filled, dtype=np.float32)
    foot = np.asarray(footprint, dtype=bool)
    if f.shape != foot.shape or f.ndim != 2:
        raise ValueError("2D field aligned with footprint required")
    if not np.isfinite(f).all():
        raise ValueError("filled field must be finite everywhere before FFT")
    h_px, w_px = f.shape
    work = (f - np.float32(f.mean(dtype=np.float64))).astype(np.float32)
    spec = spfft.rfft2(work, workers=2)
    del work
    fy = spfft.fftfreq(h_px, d=pixel_m).astype(np.float64)
    fx = spfft.rfftfreq(w_px, d=pixel_m).astype(np.float64)
    ky = (2.0 * np.pi * fy)[:, None]
    kx = (2.0 * np.pi * fx)[None, :]
    kabs = np.sqrt(ky * ky + kx * kx)
    out: dict[float, np.ndarray] = {}
    for height in heights_m:
        cont = np.exp(-kabs * float(height))
        gx = spfft.irfft2(spec * cont * (1j * kx), s=(h_px, w_px), workers=2).astype(np.float32)
        gy = spfft.irfft2(spec * cont * (1j * ky), s=(h_px, w_px), workers=2).astype(np.float32)
        thdr = np.sqrt(gx * gx + gy * gy, dtype=np.float64).astype(np.float32)
        del gx, gy, cont
        out[float(height)] = footprint_percentile_ranks(thdr, foot)
        del thdr
    del spec
    return out


def persistence_from_ranks(ranks_by_height: dict[float, np.ndarray]) -> np.ndarray:
    """Geometric mean of per-height ranks (eps-guarded), float32 full grid."""
    if not ranks_by_height:
        raise ValueError("at least one height required")
    acc: np.ndarray | None = None
    for ranks in ranks_by_height.values():
        log_r = np.log(np.asarray(ranks, dtype=np.float32) + np.float32(1e-6))
        acc = log_r if acc is None else acc + log_r
    assert acc is not None
    return np.exp(acc / float(len(ranks_by_height))).astype(np.float32)


def gradient_rank_surface(
    field_filled: np.ndarray, footprint: np.ndarray, sigma_px: float
) -> np.ndarray:
    """Percentile rank of gradient magnitude after Gaussian smoothing."""
    f = np.asarray(field_filled, dtype=np.float32)
    foot = np.asarray(footprint, dtype=bool)
    if sigma_px > 0:
        sm = gaussian_filter(f, sigma=sigma_px, mode="nearest").astype(np.float32)
    else:
        sm = f
    gy, gx = np.gradient(sm)
    mag = np.sqrt(gx.astype(np.float64) ** 2 + gy.astype(np.float64) ** 2).astype(np.float32)
    del gx, gy, sm
    return footprint_percentile_ranks(mag, foot)


def weighted_rank_fusion(
    parts: list[tuple[np.ndarray, float]], footprint: np.ndarray
) -> np.ndarray:
    """Percentile rank of a weighted mean of rank surfaces (weights renormalised)."""
    if not parts:
        raise ValueError("at least one fusion part required")
    total_w = float(sum(w for _, w in parts))
    if not np.isfinite(total_w) or total_w <= 0:
        raise ValueError("fusion weights must sum to a positive finite value")
    acc: np.ndarray | None = None
    for surf, weight in parts:
        term = np.asarray(surf, dtype=np.float32) * np.float32(weight / total_w)
        acc = term if acc is None else acc + term
    assert acc is not None
    return footprint_percentile_ranks(acc, footprint)
