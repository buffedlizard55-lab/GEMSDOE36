"""Spacing-constrained greedy dot emission on ridge centrelines (H36-GPS).

Why dots: under the official metric ``DTI = T / (0.2 (T + S - M) + 0.8 N)`` (identity verified in
``evidence/forensics_champion.json``) every emitted pixel pays a 0.2 false-positive tax unless it
lies within 300 m of new truth, while one dot credits every truth pixel within 300 m. A >= 3 px
(300 m) spacing therefore keeps most of the coverage of a solid ridge at a fraction of its mass.
This is a generic emission rule, not a copy of any registry dot set.
"""

from __future__ import annotations

import numpy as np

from gems.metric import ridge_nms  # shared template primitive (vendored byte-for-byte)


def greedy_spaced(order_flat: np.ndarray, shape: tuple[int, int], budget: int, *, block: int = 2,
                  blocked: np.ndarray | None = None) -> np.ndarray:
    """Accept candidates in the given order unless a previously accepted dot lies within the
    (2*block+1)^2 square (block=2 -> accepted dots are >= 3 px apart in L-inf, hence Euclidean)."""
    h, w = shape
    taken = np.zeros(shape, bool) if blocked is None else blocked.copy()
    out = np.zeros(shape, bool)
    n = 0
    if budget <= 0:
        return out
    ys, xs = np.divmod(order_flat, w)
    for y, x in zip(ys.tolist(), xs.tolist(), strict=True):
        if taken[y, x]:
            continue
        out[y, x] = True
        taken[max(0, y - block) : y + block + 1, max(0, x - block) : x + block + 1] = True
        n += 1
        if n >= budget:
            break
    return out


def emit_dots(score: np.ndarray, eligible: np.ndarray, budget: int, *, sigma: float = 1.0,
              block: int = 2, support: np.ndarray | None = None) -> np.ndarray:
    """Ridge-NMS centreline candidates first (descending score), then any remaining eligible
    positive-score pixels, all under the same >= 3 px spacing rule. Deterministic tie-break by
    flat index (stable lexsort).

    ``support`` is the domain on which the score is physically defined (ridges are computed there);
    ``eligible`` only restricts where dots may be placed. Keeping them separate prevents the
    template ``ridge_nms`` boundary erosion (4*sigma+3 px) from silently widening an exclusion
    zone such as the catalogue annulus. Default: support = eligible.
    """
    score = np.asarray(score, np.float32)
    eligible = np.asarray(eligible, bool) & np.isfinite(score) & (score > 0)
    sup = eligible if support is None else (np.asarray(support, bool) & np.isfinite(score))
    ridge = ridge_nms(np.where(sup, score, 0.0), sup, sigma=sigma) & eligible
    flat = score.ravel()
    r_ids = np.flatnonzero(ridge.ravel())
    r_ord = r_ids[np.lexsort((r_ids, -flat[r_ids]))]
    o_ids = np.flatnonzero((eligible & ~ridge).ravel())
    o_ord = o_ids[np.lexsort((o_ids, -flat[o_ids]))]
    dots = greedy_spaced(r_ord, score.shape, budget, block=block)
    short = budget - int(dots.sum())
    if short > 0 and len(o_ord):
        blocked = np.zeros(score.shape, bool)
        for y, x in np.argwhere(dots):
            blocked[max(0, y - block) : y + block + 1, max(0, x - block) : x + block + 1] = True
        dots |= greedy_spaced(o_ord, score.shape, short, block=block, blocked=blocked)
    return dots
