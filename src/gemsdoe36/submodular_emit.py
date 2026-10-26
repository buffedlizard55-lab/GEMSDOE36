"""Exact Euclidean 300 m Submodular Expected-Credit Emitter (CELF Lazy Greedy).

Unlike legacy ``emitter.py`` (which required a binary ``truth_proxy`` and used an
incomplete Manhattan/diagonal kernel table), this module maximizes expected weighted
coverage directly on a continuous calibrated fault-probability surface ``p(x) in [0, 1]``
using the exact 25-offset Euclidean 300 m triangular kernel ``max(0, 1 - hypot(dy, dx)/3)``
matching ``gemsdoe36.metric.distance_weighted_tversky``:

    Phi(S) = sum_{y in V} w(y) * max_{x in S} k(d(x, y))

Because ``Phi(S)`` is monotone non-negative submodular, Minoux (1978) / Leskovec et al.
(2007) lazy-greedy (CELF) heap evaluation returns the exact greedy submodular cover in
seconds on CPU while respecting fold-safe visible-catalogue exclusion (``d_vis > 2.0 px``)
and minimum self-spacing.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

import numpy as np


def build_euclidean_kernel_300m(
    pixel_size_m: float = 100.0,
    radius_m: float = 300.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return exact positive-weight (dy, dx, weight) arrays matching metric.py."""
    max_off = math.ceil(radius_m / pixel_size_m)
    rows: list[tuple[int, int, float]] = []
    for dy in range(-max_off, max_off + 1):
        for dx in range(-max_off, max_off + 1):
            dist = math.hypot(dy * pixel_size_m, dx * pixel_size_m)
            w = 1.0 - dist / radius_m
            if w > 1e-7:
                rows.append((dy, dx, w))
    # Sort descending by kernel weight for cache friendliness
    rows.sort(key=lambda t: -t[2])
    dy_arr = np.array([r[0] for r in rows], dtype=np.int32)
    dx_arr = np.array([r[1] for r in rows], dtype=np.int32)
    kw_arr = np.array([r[2] for r in rows], dtype=np.float32)
    return dy_arr, dx_arr, kw_arr


_DY25, _DX25, _KW25 = build_euclidean_kernel_300m()


@dataclass(frozen=True)
class SubmodularCoverResult:
    mask: np.ndarray  # (H, W) bool
    dots_rc: np.ndarray  # (N, 2) int32
    objective_value: float
    n_candidates_pool: int


def emit_submodular_cover(
    probability: np.ndarray,
    eligible_mask: np.ndarray,
    *,
    budget: int = 37_654,
    valid_footprint: np.ndarray | None = None,
    gamma: float = 1.15,
    min_spacing_px: float = 2.0,
    pool_size: int = 240_000,
) -> SubmodularCoverResult:
    """Select ``budget`` binary dots maximizing 300 m submodular expected Tversky credit.

    Parameters
    ----------
    probability:
        2D continuous fault probability map in ``[0, 1]``.
    eligible_mask:
        2D boolean mask of allowed dot locations (e.g., ``footprint & (d_vis > 2.0)``).
    budget:
        Target number of unit-mass dots to place.
    valid_footprint:
        2D boolean domain over which truth credit is accumulated (defaults to ``eligible_mask``).
    gamma:
        Probability sharpening exponent ``w(y) = p(y)**gamma`` focusing coverage on high-odds ridges.
    min_spacing_px:
        Minimum Euclidean separation between emitted dots (default ``2.0 px = 200 m``).
    pool_size:
        Candidate pool size of top-scoring eligible pixels entering the CELF priority queue.
    """
    prob = np.asarray(probability, dtype=np.float32)
    elig = np.asarray(eligible_mask, dtype=bool)
    foot = elig if valid_footprint is None else np.asarray(valid_footprint, dtype=bool)
    if prob.shape != elig.shape or prob.shape != foot.shape:
        raise ValueError("probability, eligible_mask, and valid_footprint shapes must match")
    if budget <= 0 or not elig.any():
        return SubmodularCoverResult(
            np.zeros(prob.shape, dtype=bool),
            np.zeros((0, 2), dtype=np.int32),
            0.0,
            0,
        )

    h, w = prob.shape
    clean_p = np.where(foot & np.isfinite(prob), np.clip(prob, 0.0, 1.0), 0.0).astype(np.float32)
    mass = np.power(clean_p, float(gamma)).astype(np.float32)

    # Pad mass and best_credit by 3 pixels on all sides so inner CELF loop needs zero bounds checks!
    pad = 3
    mass_pad = np.zeros((h + 2 * pad, w + 2 * pad), dtype=np.float32)
    mass_pad[pad : pad + h, pad : pad + w] = mass
    best_pad = np.zeros((h + 2 * pad, w + 2 * pad), dtype=np.float32)

    # Initial marginal gain for EVERY pixel via vectorized shifted accumulation:
    # gain0(r, c) = sum_k kw[k] * mass(r + dy[k], c + dx[k])
    init_gain = np.zeros((h, w), dtype=np.float32)
    for dy, dx, kw in zip(_DY25.tolist(), _DX25.tolist(), _KW25.tolist(), strict=True):
        init_gain += kw * mass_pad[pad + dy : pad + dy + h, pad + dx : pad + dx + w]

    cand_rc = np.argwhere(elig & (init_gain > 0.0))
    if len(cand_rc) == 0:
        cand_rc = np.argwhere(elig)
    target_pool = max(int(budget * 4), int(pool_size))
    if len(cand_rc) > target_pool:
        gains_all = init_gain[cand_rc[:, 0], cand_rc[:, 1]]
        top_idx = np.argpartition(-gains_all, target_pool)[:target_pool]
        cand_rc = cand_rc[top_idx]

    # Deterministic tie-breaking order: sort by (-init_gain, row, col)
    gains_c = init_gain[cand_rc[:, 0], cand_rc[:, 1]]
    order = np.lexsort((cand_rc[:, 1], cand_rc[:, 0], -gains_c))
    cand_rc = np.ascontiguousarray(cand_rc[order], dtype=np.int32)
    gains_c = gains_c[order]
    n_pool = len(cand_rc)

    # Precompute exclusion disk offsets for min_spacing_px
    blocked = ~elig.copy()
    if min_spacing_px > 0:
        r_int = math.ceil(min_spacing_px)
        gy, gx = np.mgrid[-r_int : r_int + 1, -r_int : r_int + 1]
        disk_mask = (gy * gy + gx * gx) < (min_spacing_px * min_spacing_px - 1e-6)
        blk_dy = gy[disk_mask].astype(np.int32).tolist()
        blk_dx = gx[disk_mask].astype(np.int32).tolist()
    else:
        blk_dy, blk_dx = [0], [0]

    # Build min-heap of (-upper_bound_gain, tie_idx, row, col)
    heap: list[tuple[float, int, int, int]] = [
        (-float(gains_c[i]), i, int(cand_rc[i, 0]), int(cand_rc[i, 1]))
        for i in range(n_pool)
    ]
    heapq.heapify(heap)

    dy_list = _DY25.tolist()
    dx_list = _DX25.tolist()
    kw_list = _KW25.tolist()
    n_k = len(kw_list)

    selected = np.zeros((h, w), dtype=bool)
    placed_rows: list[int] = []
    placed_cols: list[int] = []
    total_obj = 0.0

    while len(placed_rows) < budget and heap:
        _neg_ub, idx, r, c = heapq.heappop(heap)
        if blocked[r, c]:
            continue

        # Recompute exact current marginal gain at padded coordinates (rp, cp)
        rp = r + pad
        cp = c + pad
        exact_gain = 0.0
        for k in range(n_k):
            rr = rp + dy_list[k]
            cc = cp + dx_list[k]
            kw = kw_list[k]
            rem = kw - best_pad[rr, cc]
            if rem > 0.0:
                exact_gain += mass_pad[rr, cc] * rem

        # CELF check: is exact_gain still >= the next best upper bound in the heap?
        next_ub = -heap[0][0] if heap else -1.0
        if exact_gain < next_ub - 1e-9:
            heapq.heappush(heap, (-exact_gain, idx, r, c))
            continue

        # Accept (r, c)! Update best_pad and block min_spacing_px disk
        selected[r, c] = True
        placed_rows.append(r)
        placed_cols.append(c)
        total_obj += exact_gain

        for k in range(n_k):
            rr = rp + dy_list[k]
            cc = cp + dx_list[k]
            kw = kw_list[k]
            best_pad[rr, cc] = max(best_pad[rr, cc], kw)

        for bdy, bdx in zip(blk_dy, blk_dx, strict=True):
            br = r + bdy
            bc = c + bdx
            if 0 <= br < h and 0 <= bc < w:
                blocked[br, bc] = True

    # Fallback top-up if pool exhausted slightly before budget (rare)
    if len(placed_rows) < budget:
        rem_rc = np.argwhere(elig & ~blocked)
        if len(rem_rc):
            rem_scores = init_gain[rem_rc[:, 0], rem_rc[:, 1]]
            rem_order = np.argsort(-rem_scores, kind="mergesort")
            for j in rem_order:
                if len(placed_rows) >= budget:
                    break
                r, c = int(rem_rc[j, 0]), int(rem_rc[j, 1])
                if blocked[r, c]:
                    continue
                selected[r, c] = True
                placed_rows.append(r)
                placed_cols.append(c)
                for bdy, bdx in zip(blk_dy, blk_dx, strict=True):
                    br, bc = r + bdy, c + bdx
                    if 0 <= br < h and 0 <= bc < w:
                        blocked[br, bc] = True

    dots_rc = np.column_stack([placed_rows, placed_cols]).astype(np.int32) if placed_rows else np.zeros((0, 2), dtype=np.int32)
    return SubmodularCoverResult(
        mask=selected,
        dots_rc=dots_rc,
        objective_value=float(total_obj),
        n_candidates_pool=n_pool,
    )
