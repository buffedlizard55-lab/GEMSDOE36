"""Exact-marginal-gain dot emission with support confinement and catalogue exclusion.

Metric background (published DTI, alpha=0.2, beta=0.8, 300 m triangular kernel):

    DTI = T / (0.2*T + 0.2*F + 0.8*K)

where T = sum of credit delivered to truth pixels (scatter-aware: one dot can credit
several nearby truth pixels, each capped at 1), F = false-positive mass (sum over
prediction pixels of p*(1 - nearest-truth kernel), independent of other predictions),
and K = number of truth pixels.  1/DTI = 0.2 + 0.2F/T + 0.8K/T.

Emission rule (owner-verified against the live leaderboard, see
docs/research/results.md): place a unit of mass at x iff its incremental credit
dT(x) exceeds ``0.2 * DTI`` (the break-even bar).  This is the metric's own
first-order condition; mass placed below the bar lowers the score.

Correctness invariants (unit-tested in tests/test_emitter.py):
* **Support confinement** — every emitted pixel is one the belief field nominates.
* **Upper-bound heap keys** — a candidate's key is an upper bound on its current
  dT (initially the full-coverage credit, re-scored to the exact value on pop).
  dT only decreases as best_credit fills, so the bound is preserved and
  ``max_key <= bar`` proves termination at the right moment.
* **Scatter-aware credit** — dT(x) sums, over truth pixels within 300 m, the credit
  not already delivered by a previously placed dot (max-credit, not a shared budget),
  so overlapping dots are never double-counted.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np

# Triangular 300 m kernel on the 100 m grid: strictly positive weights, |d| <= 3 px.
_KERNEL: tuple[tuple[int, int, float], ...] = (
    (0, 0, 1.0),
    (0, 1, 2.0 / 3.0), (0, -1, 2.0 / 3.0), (1, 0, 2.0 / 3.0), (-1, 0, 2.0 / 3.0),
    (1, 1, 1.0 / 3.0), (1, -1, 1.0 / 3.0), (-1, 1, 1.0 / 3.0), (-1, -1, 1.0 / 3.0),
    (2, 1, 1.0 / 3.0), (2, -1, 1.0 / 3.0), (-2, 1, 1.0 / 3.0), (-2, -1, 1.0 / 3.0),
    (1, 2, 1.0 / 3.0), (-1, 2, 1.0 / 3.0), (1, -2, 1.0 / 3.0), (-1, -2, 1.0 / 3.0),
)
_DY = np.array([k[0] for k in _KERNEL], dtype=np.int32)
_DX = np.array([k[1] for k in _KERNEL], dtype=np.int32)
_K = np.array([k[2] for k in _KERNEL], dtype=np.float32)


@dataclass(frozen=True)
class EmissionResult:
    dots: np.ndarray  # (N, 2) int32 (row, col)
    dti_estimate: float  # running DTI under the truth proxy
    credit: float  # total credit T delivered to the truth proxy
    fp_mass: float  # total false-positive mass F
    stopped_by: str  # "budget" | "bar" | "empty"


def emit_dots(
    belief: np.ndarray,
    *,
    budget: int = 40000,
    support_quantile: float = 99.0,
    exclude_mask: np.ndarray | None = None,
    alpha: float = 0.2,
    beta: float = 0.8,
    truth_proxy: np.ndarray,
    scatter_radius_px: int = 3,
    max_candidates: int = 300000,
) -> EmissionResult:
    """Place up to ``budget`` unit-mass dots by exact marginal gain.

    ``truth_proxy`` must be a binary (0/1) mask of the estimated hidden-fault pixels;
    its pixel count is K.  ``belief`` supplies support confinement and the candidate
    ordering.  ``exclude_mask`` (bool, True = forbidden) removes pixels the official
    evaluation masks or that are barred by validated removal rules (e.g. the 200 m
    catalogue-flank rule that lifted the incumbent 0.2708 -> 0.2778 live).

    ``scatter_radius_px`` controls the H2 scatter-smoothing ablation: dots may be
    placed anywhere in the belief support within that radius of the truth proxy
    (the exact-gain rule then chooses off-peak positions whenever they credit the
    scattered hidden truth better).  0 = dots only on truth-proxy pixels.
    """
    h, w = belief.shape
    b = np.asarray(belief, dtype=np.float32)
    truth = (np.asarray(truth_proxy) > 0.5).astype(np.float32)
    K = float(truth.sum())
    if K <= 0:
        return EmissionResult(np.zeros((0, 2), dtype=np.int32), 0.0, 0.0, 0.0, "empty")

    if b.max() <= 0:
        return EmissionResult(np.zeros((0, 2), dtype=np.int32), 0.0, 0.0, 0.0, "empty")
    support_thresh = max(float(np.percentile(b, support_quantile)), b.max() * 0.05)
    support = b >= support_thresh
    if exclude_mask is not None:
        support &= ~np.asarray(exclude_mask, dtype=bool)

    # Candidates: the belief support within the metric radius (3 px = 300 m) of the
    # truth proxy. A dot farther than 300 m from every truth pixel has dT = 0 for its
    # entire life and can never beat the bar, so excluding it is complete. The radius
    # is clamped to the kernel support (3 px); a smaller radius (0) restricts dots to
    # truth pixels exactly (the scatter-smoothing ablation).
    from scipy.ndimage import binary_dilation

    radius = int(np.clip(scatter_radius_px, 0, 3))
    if radius == 0:
        truth_neigh = truth > 0
    else:
        yy, xx = np.ogrid[-radius : radius + 1, -radius : radius + 1]
        disk = (xx * xx + yy * yy) <= radius * radius
        truth_neigh = binary_dilation(truth > 0, structure=disk)
    cand = np.argwhere(support & truth_neigh)
    if len(cand) == 0:
        # Truth lies outside the nominated support: fall back to the whole support so
        # the caller still gets a (possibly empty) result rather than a crash.
        cand = np.argwhere(support)
    if len(cand) > max_candidates:
        order = np.argsort(-b[cand[:, 0], cand[:, 1]])
        cand = cand[order[:max_candidates]]
    cand = np.ascontiguousarray(cand, dtype=np.int32)

    # --- Initial keys: full-coverage credit (upper bound on current dT) ------------
    def credit_block(rows: np.ndarray, cols: np.ndarray, best: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        dts = np.zeros(len(rows), dtype=np.float32)
        kmaxs = np.zeros(len(rows), dtype=np.float32)
        for dy, dx, k in zip(_DY, _DX, _K, strict=True):
            r = rows + dy
            c = cols + dx
            good = (r >= 0) & (r < h) & (c >= 0) & (c < w)
            if not good.any():
                continue
            rt, ct = r[good], c[good]
            tv = truth[rt, ct]
            hit = tv > 0
            if not hit.any():
                continue
            idx = np.nonzero(good)[0][hit]
            # dT contribution: k * (1 - best_credit)  [scatter-aware, current best]
            dts[idx] += k * (1.0 - best[rt[hit], ct[hit]])
            kmaxs[idx] = np.maximum(kmaxs[idx], k)
        return dts, kmaxs

    rows_c = cand[:, 0]
    cols_c = cand[:, 1]
    best_credit = np.zeros((h, w), dtype=np.float32)
    keys = np.zeros(len(cand), dtype=np.float32)
    kmax_init = np.zeros(len(cand), dtype=np.float32)
    chunk = 50000
    for i in range(0, len(cand), chunk):
        keys[i : i + chunk], kmax_init[i : i + chunk] = credit_block(
            rows_c[i : i + chunk], cols_c[i : i + chunk], best_credit
        )

    used = np.zeros((h, w), dtype=bool)
    placed: list[tuple[int, int]] = []
    heap: list[tuple[float, int, int, int]] = []
    for i, (r, c) in enumerate(cand):
        heapq.heappush(heap, (-keys[i], i, int(r), int(c)))

    T = 0.0
    F = 0.0
    dti = 0.0  # 0 at start (no credit yet)
    bar = 0.0

    def exact_dtkmax(row: int, col: int) -> tuple[float, float]:
        dts = 0.0
        kmax = 0.0
        for dy, dx, k in zip(_DY, _DX, _K, strict=True):
            r, c = row + dy, col + dx
            if 0 <= r < h and 0 <= c < w and truth[r, c] > 0:
                if k > kmax:
                    kmax = k
                if k > best_credit[r, c]:
                    dts += k - best_credit[r, c]
        return float(dts), float(kmax)

    stopped_by = "budget"
    while len(placed) < budget:
        if not heap:
            stopped_by = "empty"
            break
        if -heap[0][0] <= bar:
            stopped_by = "bar"
            break
        _neg, i, row, col = heapq.heappop(heap)
        if used[row, col]:
            continue
        dts, kmax = exact_dtkmax(row, col)
        if dts <= bar:
            # Stale upper bound; re-key with the exact (lower) dT.
            keys[i] = dts
            heapq.heappush(heap, (-dts, i, row, col))
            continue
        # Place the dot: exact marginal credit beats the break-even bar.
        used[row, col] = True
        placed.append((row, col))
        for dy, dx, k in zip(_DY, _DX, _K, strict=True):
            r, c = row + dy, col + dx
            if 0 <= r < h and 0 <= c < w and truth[r, c] > 0 and k > best_credit[r, c]:
                best_credit[r, c] = k
        T += dts
        F += 1.0 - kmax
        dti = T / (alpha * T + alpha * F + beta * K + 1e-12)
        bar = alpha * dti

    dots = np.asarray(placed, dtype=np.int32).reshape(-1, 2)
    return EmissionResult(dots, float(dti), float(T), float(F), stopped_by)
