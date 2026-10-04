"""Reference implementation of the published GEMS distance-weighted Tversky metric.

This is a local scoring utility, not a differentiable training loss.  It follows the
competition page's per-truth-pixel maximum-credit definition and triangular 300 m kernel.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import ceil

import numpy as np
from scipy.ndimage import distance_transform_edt


@dataclass(frozen=True)
class DTIComponents:
    """Weighted metric terms and the resulting score."""

    true_positive: float
    false_positive: float
    false_negative: float
    score: float


def _as_pair(value: float | Iterable[float], name: str) -> tuple[float, float]:
    if np.isscalar(value):
        pair = (float(value), float(value))
    else:
        pair = tuple(float(v) for v in value)
        if len(pair) != 2:
            raise ValueError(f"{name} must be a scalar or a pair (row, column)")
    if not all(np.isfinite(v) and v > 0 for v in pair):
        raise ValueError(f"{name} values must be finite and positive")
    return pair


def distance_weighted_tversky(
    prediction: np.ndarray,
    truth: np.ndarray,
    *,
    valid_mask: np.ndarray | None = None,
    pixel_size_m: float | tuple[float, float] = 100.0,
    radius_m: float = 300.0,
    alpha: float = 0.2,
    beta: float = 0.8,
    epsilon: float = 1e-8,
    return_components: bool = False,
) -> float | DTIComponents:
    """Compute the published continuous-prediction distance-weighted Tversky index.

    ``truth`` is interpreted as binary.  The prediction must be finite and in [0, 1]
    wherever ``valid_mask`` is true; NaNs outside that mask are allowed.  Distances use
    Euclidean map units and the triangular kernel ``max(1 - d / radius_m, 0)``.

    The TP calculation is deliberately a maximum over nearby prediction pixels for each
    truth pixel, not a sum.  Nearby redundant predictions still contribute to FP mass.
    ``pixel_size_m`` is ``(row_spacing, column_spacing)`` when anisotropic.
    """
    pred = np.asarray(prediction)
    labels = np.asarray(truth)
    if pred.ndim != 2 or labels.ndim != 2:
        raise ValueError("prediction and truth must be two-dimensional arrays")
    if pred.shape != labels.shape:
        raise ValueError(f"prediction/truth shape mismatch: {pred.shape} != {labels.shape}")
    if not np.isfinite(radius_m) or radius_m <= 0:
        raise ValueError("radius_m must be finite and positive")
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be finite and positive")
    if alpha < 0 or beta < 0 or not np.isfinite(alpha + beta):
        raise ValueError("alpha and beta must be finite and non-negative")

    row_size, col_size = _as_pair(pixel_size_m, "pixel_size_m")
    if valid_mask is None:
        valid = np.ones(pred.shape, dtype=bool)
    else:
        valid = np.asarray(valid_mask, dtype=bool)
        if valid.shape != pred.shape:
            raise ValueError("valid_mask shape must match prediction and truth")

    if np.any(~np.isfinite(labels[valid])):
        raise ValueError("truth contains non-finite values inside valid_mask")
    if np.any((labels[valid] != 0) & (labels[valid] != 1)):
        raise ValueError("truth must contain only binary 0/1 values inside valid_mask")
    if np.any(~np.isfinite(pred[valid])):
        raise ValueError("prediction contains non-finite values inside valid_mask")
    if np.any((pred[valid] < 0) | (pred[valid] > 1)):
        raise ValueError("prediction values must be in [0, 1] inside valid_mask")

    # Outside-valid values never enter either term, even if they are NaN or a NoData code.
    p = np.zeros(pred.shape, dtype=np.float32)
    p[valid] = pred[valid].astype(np.float32, copy=False)
    g = (labels == 1) & valid

    # Distance to the nearest true pixel.  With no truth, the metric has no TP credit and
    # every positive prediction is false-positive mass.
    if not np.any(g):
        tp = 0.0
        fp = float(np.sum(p[valid], dtype=np.float64))
        fn = 0.0
        score = tp / (tp + alpha * fp + beta * fn + epsilon)
        result = DTIComponents(tp, fp, fn, score)
        return result if return_components else result.score

    distance_to_truth = distance_transform_edt(~g, sampling=(row_size, col_size))
    kernel_to_truth = np.maximum(1.0 - distance_to_truth / radius_m, 0.0)
    fp = float(np.sum(p[valid] * (1.0 - kernel_to_truth[valid]), dtype=np.float64))

    # For every truth pixel, collect the maximum p(x) k(d(x,g)) over all prediction
    # pixels within R.  The offset window is small for the official 100 m / 300 m grid.
    rows, cols = p.shape
    best_credit = np.zeros(p.shape, dtype=np.float32)
    max_row_offset = ceil(radius_m / row_size)
    max_col_offset = ceil(radius_m / col_size)
    for dy in range(-max_row_offset, max_row_offset + 1):
        for dx in range(-max_col_offset, max_col_offset + 1):
            distance = float(np.hypot(dy * row_size, dx * col_size))
            if distance > radius_m:
                continue
            y0 = max(0, -dy)
            y1 = min(rows, rows - dy)
            x0 = max(0, -dx)
            x1 = min(cols, cols - dx)
            if y0 >= y1 or x0 >= x1:
                continue
            target = best_credit[y0:y1, x0:x1]
            source = p[y0 + dy : y1 + dy, x0 + dx : x1 + dx]
            np.maximum(target, source * (1.0 - distance / radius_m), out=target)

    tp = float(np.sum(best_credit[g], dtype=np.float64))
    fn = float(np.sum(1.0 - best_credit[g], dtype=np.float64))
    score = tp / (tp + alpha * fp + beta * fn + epsilon)
    result = DTIComponents(tp, fp, fn, score)
    return result if return_components else result.score
