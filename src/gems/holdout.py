"""Spatially blocked holdout used to gate hypotheses *before* any weekly submission slot is spent."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.ndimage import label as ndi_label

from .metric import dti_score_fast, ridge_nms, select_top_positive

BUDGET_FRAC = 0.025
FOLD_NAMES = ["NW", "NE_LidarGapHeavy", "SW", "SE"]


def make_quadrant_folds(footprint: np.ndarray) -> tuple[np.ndarray, list[str]]:
    footprint = np.asarray(footprint, bool)
    if footprint.ndim != 2 or not footprint.any():
        raise ValueError("A nonempty 2D footprint is required")
    yy, xx = np.nonzero(footprint)
    y_med, x_med = int(np.median(yy)), int(np.median(xx))
    H, W = footprint.shape
    gy, gx = np.ogrid[:H, :W]
    fold = np.full((H, W), -1, dtype=np.int8)
    fold[(gy < y_med) & (gx < x_med) & footprint] = 0
    fold[(gy < y_med) & (gx >= x_med) & footprint] = 1
    fold[(gy >= y_med) & (gx < x_med) & footprint] = 2
    fold[(gy >= y_med) & (gx >= x_med) & footprint] = 3
    return fold, list(FOLD_NAMES)


def thin_components(truth_2d: np.ndarray, keep_frac: float, seed: int) -> np.ndarray:
    if not 0 <= keep_frac <= 1:
        raise ValueError("Component fraction must be in [0,1]")
    comp, n = ndi_label(truth_2d, structure=np.ones((3, 3), dtype=int))
    if n == 0 or keep_frac == 0:
        return np.zeros_like(truth_2d, dtype=bool)
    rng = np.random.default_rng(seed)
    keep = rng.choice(np.arange(1, n + 1), size=max(1, int(round(keep_frac * n))), replace=False)
    return np.isin(comp, keep)


class Holdout:
    def __init__(
        self,
        footprint: np.ndarray,
        labels: np.ndarray,
        budget: float = BUDGET_FRAC,
        sparse_seed_offset: int = 0,
    ):
        footprint, labels = np.asarray(footprint, bool), np.asarray(labels, bool)
        if footprint.shape != labels.shape or not 0 <= budget <= 1:
            raise ValueError("Aligned grids and budget in [0,1] required")
        self.footprint = footprint
        self.labels = labels
        self.budget = budget
        self.fp_idx = np.flatnonzero(footprint.ravel())
        self.fold_2d, self.fold_names = make_quadrant_folds(footprint)
        self.quads = []
        for f_id, name in enumerate(self.fold_names):
            f_mask = (self.fold_2d == f_id) & footprint
            if not f_mask.any():
                raise ValueError(
                    f"Spatial quadrant {name} is empty; cannot claim a four-fold holdout"
                )
            r0, r1 = np.nonzero(f_mask.any(axis=1))[0][[0, -1]]
            c0, c1 = np.nonzero(f_mask.any(axis=0))[0][[0, -1]]
            sl = (slice(r0, r1 + 1), slice(c0, c1 + 1))
            t_dense = labels & f_mask
            t_sparse = thin_components(
                t_dense, keep_frac=0.20, seed=4242 + f_id + sparse_seed_offset
            )
            known = t_dense & ~t_sparse
            self.quads.append(
                (f_id, name, f_mask, sl, t_dense[sl], t_sparse[sl], known[sl], f_mask[sl])
            )

    def to_2d(self, p_fp: np.ndarray) -> np.ndarray:
        if np.asarray(p_fp).shape != (len(self.fp_idx),):
            raise ValueError("Footprint score vector length mismatch")
        a = np.zeros(self.footprint.shape, dtype=np.float32)
        a.ravel()[self.fp_idx] = p_fp
        return a

    def emit(
        self, p_fp: np.ndarray, *, ridge: bool = True, budget_per_quad: list[int] | None = None
    ) -> np.ndarray:
        """Per-quadrant top-budget binary mask over the full grid (ridge-thinned unless ``ridge=False``)."""
        score = self.to_2d(p_fp)
        if ridge:
            r = ridge_nms(score, self.footprint, sigma=1.0)
            boosted = np.where(r, score, 0)
        else:
            boosted = score
        out = np.zeros(self.footprint.shape, dtype=bool)
        for f_id, _n, f_mask, _sl, _td, _ts, _kc, fm in self.quads:
            k = (
                int(budget_per_quad[f_id])
                if budget_per_quad is not None
                else int(round(self.budget * fm.sum()))
            )
            out |= select_top_positive(boosted, f_mask, k)
        return out

    def score_mask(self, pred: np.ndarray) -> dict[str, Any]:
        dense, sparse, detail = [], [], {}
        for _f, name, _m, sl, td, ts, kc, fm in self.quads:
            rd = dti_score_fast(pred[sl], td, valid_mask=fm)
            rs = dti_score_fast(pred[sl], ts, valid_mask=fm, catalogue_mask=kc)
            dense.append(rd["dti"])
            sparse.append(rs["dti"])
            detail[name] = {
                "dense_dti": round(rd["dti"], 5),
                "sparse_dti": round(rs["dti"], 5),
                "dense_coverage": round(rd["coverage"], 4),
                "sparse_coverage": round(rs["coverage"], 4),
                "emitted_px": int(pred[sl].sum()),
            }
        return {
            "mean_dense_dti": round(float(np.mean(dense)), 5),
            "mean_sparse_dti": round(float(np.mean(sparse)), 5),
            "fold_dense": [round(x, 5) for x in dense],
            "fold_sparse": [round(x, 5) for x in sparse],
            "folds": detail,
        }

    def evaluate(self, p_fp: np.ndarray, *, ridge: bool = True) -> dict[str, Any]:
        return self.score_mask(self.emit(p_fp, ridge=ridge))

    def emit_quadrant(
        self, p_fp: np.ndarray, f_id: int, *, ridge: bool = True, k_override: int | None = None
    ) -> np.ndarray:
        score = self.to_2d(p_fp)
        boosted = (
            np.where(ridge_nms(score, self.footprint, sigma=1.0), score, 0) if ridge else score
        )
        _f, _n, f_mask, _sl, _td, _ts, _kc, fm = self.quads[f_id]
        k = int(k_override) if k_override is not None else int(round(self.budget * fm.sum()))
        return select_top_positive(boosted, f_mask, k)

    def score_quadrant(
        self, pred: np.ndarray, f_id: int, mode: str, mask_predictions: bool = False
    ) -> float:
        _f, _n, _m, sl, td, ts, kc, fm = self.quads[f_id]
        if mode == "dense":
            return dti_score_fast(pred[sl], td, valid_mask=fm)["dti"]
        return dti_score_fast(
            pred[sl], ts, valid_mask=fm, catalogue_mask=kc, mask_predictions=mask_predictions
        )["dti"]

    def known_for(self, f_id: int, mode: str) -> np.ndarray:
        _f, _n, f_mask, sl, _td, _ts, kc, _fm = self.quads[f_id]
        known = self.labels & ~f_mask
        if mode == "sparse":
            known = known.copy()
            known[sl] |= kc
        return known

    def evaluate_by_quadrant(self, surface_fn) -> dict[str, Any]:
        dense, sparse = [], []
        for f_id in range(len(self.quads)):
            dense.append(
                self.score_quadrant(
                    self.emit_quadrant(surface_fn(f_id, "dense"), f_id), f_id, "dense"
                )
            )
            sparse.append(
                self.score_quadrant(
                    self.emit_quadrant(surface_fn(f_id, "sparse"), f_id), f_id, "sparse"
                )
            )
        return {
            "mean_dense_dti": round(float(np.mean(dense)), 5),
            "mean_sparse_dti": round(float(np.mean(sparse)), 5),
            "fold_dense": [round(x, 5) for x in dense],
            "fold_sparse": [round(x, 5) for x in sparse],
        }


def gate(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    *,
    max_fold_loss: float = 0.01,
    min_mean_gain: float = 0.001,
) -> dict[str, Any]:
    """Pre-registered promotion rule.

    PASS requires: higher mean dense AND mean sparse DTI than the baseline; higher sparse DTI in >= 3 of 4 folds;
    and no fold losing more than ``max_fold_loss`` DTI (dense or sparse) relative to the baseline.
    """
    cd, cs = candidate["fold_dense"], candidate["fold_sparse"]
    bd, bs = baseline["fold_dense"], baseline["fold_sparse"]
    arrays = [np.asarray(a, float) for a in (cd, cs, bd, bs)]
    if any(a.shape != (4,) or np.any(~np.isfinite(a)) or np.any((a < 0) | (a > 1)) for a in arrays):
        raise ValueError("Gate requires four finite [0,1] fold scores for both candidates")
    if max_fold_loss < 0 or min_mean_gain < 0:
        raise ValueError("Gate tolerances must be nonnegative")
    means_consistent = all(
        abs(d[k] - float(np.mean(a))) <= 1e-4
        for d, a, k in (
            (candidate, arrays[0], "mean_dense_dti"),
            (candidate, arrays[1], "mean_sparse_dti"),
            (baseline, arrays[2], "mean_dense_dti"),
            (baseline, arrays[3], "mean_sparse_dti"),
        )
    )
    sparse_wins = int(sum(c > b for c, b in zip(cs, bs)))
    dense_wins = int(sum(c > b for c, b in zip(cd, bd)))
    worst_dense = round(min(c - b for c, b in zip(cd, bd)), 5)
    worst_sparse = round(min(c - b for c, b in zip(cs, bs)), 5)
    rules = {
        "reported_means_match_four_fold_scores": means_consistent,
        "mean_dense_improves": candidate["mean_dense_dti"] - baseline["mean_dense_dti"]
        > min_mean_gain,
        "mean_sparse_improves": candidate["mean_sparse_dti"] - baseline["mean_sparse_dti"]
        > min_mean_gain,
        "sparse_fold_wins_ge_3_of_4": sparse_wins >= 3,
        "no_fold_loses_more_than_0_01": worst_dense >= -max_fold_loss
        and worst_sparse >= -max_fold_loss,
    }
    return {
        "passed": all(rules.values()),
        "rules": rules,
        "sparse_fold_wins": sparse_wins,
        "dense_fold_wins": dense_wins,
        "worst_fold_delta_dense": worst_dense,
        "worst_fold_delta_sparse": worst_sparse,
        "delta_mean_dense": round(candidate["mean_dense_dti"] - baseline["mean_dense_dti"], 5),
        "delta_mean_sparse": round(candidate["mean_sparse_dti"] - baseline["mean_sparse_dti"], 5),
    }


# Legacy Holdout above remains for reproduction of historical evidence. It is NOT
# the authority for the parallel-run segment protocol below.
SEGMENT_EVALUATOR_VERSION = "segment-hide-recover-pooled-v1"


def segment_folds(footprint, labels, buffer_px=30):
    """Hide whole 8-connected components touching each quadrant.

    Components are a conservative raster proxy for segments, not expert trace IDs.
    Components that cross quadrant boundaries can be withheld in multiple folds,
    but each scored positive pixel belongs to only one quadrant.
    All catalogue-based features MUST consume only the yielded visible grid.
    """
    from scipy.ndimage import distance_transform_edt

    fp, truth = np.asarray(footprint, bool), np.asarray(labels, bool)
    if (
        fp.shape != truth.shape
        or np.any(truth & ~fp)
        or not np.isfinite(buffer_px)
        or buffer_px < 0
    ):
        raise ValueError("Aligned footprint/truth, truth inside footprint and buffer >=0 required")
    components, count = ndi_label(truth, structure=np.ones((3, 3), int))
    if not count:
        raise ValueError("No fault components to withhold")
    fold_grid, names = make_quadrant_folds(fp)
    for fold, name in enumerate(names):
        test = fp & (fold_grid == fold)
        ids = np.unique(components[test & truth])
        if not len(ids):
            raise ValueError(f"No withheld positive components in {name}")
        selected = np.zeros(count + 1, bool)
        selected[ids] = True
        hidden = selected[components]
        visible = truth & ~hidden
        # Exclude the entire test region and a buffer from every hidden segment
        # and test boundary when deriving/fitting any train-dependent features.
        training = fp & (distance_transform_edt(~(test | hidden)) > buffer_px)
        yield {
            "name": name,
            "fold": fold,
            "test": test,
            "hidden": hidden,
            "visible": visible,
            "training": training,
            "n_withheld_components": int(len(ids)),
            "n_withheld_whole_segment_pixels": int(hidden.sum()),
            "n_withheld_positives": int((hidden & test).sum()),
            "buffer_px": buffer_px,
        }


def pooled_dti(components):
    """Ratio of SUMMED TP/FP/FN, never an average of fold scores."""
    from .metric import ALPHA, BETA, EPS

    a = np.asarray(components, dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != 3 or not np.isfinite(a).all() or np.any(a < -1e-8):
        raise ValueError("Finite nonnegative [TP,FP,FN] rows required")
    tp, false_positive, fn = a.sum(axis=0)
    return float(tp / (tp + ALPHA * false_positive + BETA * fn + EPS))


def spatial_components(prediction, truth, valid, visible, tile_px=200):
    """Exact binary DTI decomposed by spatial tile for cluster bootstrap.

    Distances are computed on the full evaluation domain BEFORE tile attribution;
    there are no artificial tile-edge penalties. Known pixels are masked exactly.
    Contributions are assigned to the truth pixel for TP/FN, prediction pixel for FP.
    """
    from scipy.spatial import cKDTree

    from .metric import RADIUS_PX, dti_score_fast

    if tile_px < 1:
        raise ValueError("Positive spatial tile size required")
    # Reference call validates inputs, masks visible faults and supplies exact
    # components. KD-trees only attribute these same components to spatial tiles.
    reference = dti_score_fast(prediction, truth, valid_mask=valid, catalogue_mask=visible)
    active = np.asarray(valid, bool) & ~np.asarray(visible, bool)
    pp = np.argwhere(active & (np.asarray(prediction) > 0))
    gg = np.argwhere(active & np.asarray(truth, bool))
    ncols = (active.shape[1] + tile_px - 1) // tile_px
    nrows = (active.shape[0] + tile_px - 1) // tile_px
    rows = np.zeros((ncols * nrows, 3), dtype=np.float64)

    def tile_ids(points):
        return (points[:, 0] // tile_px) * ncols + points[:, 1] // tile_px

    credit = np.zeros(len(gg))
    if len(pp) and len(gg):
        credit = np.maximum(1 - cKDTree(pp).query(gg)[0] / RADIUS_PX, 0)
    if len(gg):
        np.add.at(rows[:, 0], tile_ids(gg), credit)
        np.add.at(rows[:, 2], tile_ids(gg), 1 - credit)
    penalty = np.ones(len(pp))
    if len(gg) and len(pp):
        penalty = 1 - np.maximum(1 - cKDTree(gg).query(pp)[0] / RADIUS_PX, 0)
    if len(pp):
        np.add.at(rows[:, 1], tile_ids(pp), penalty)
    expected = [reference[k] for k in ("TP_w", "FP_w", "FN_w")]
    if not np.allclose(rows.sum(axis=0), expected, rtol=1e-10, atol=1e-7):
        raise AssertionError("Spatial components disagree with shared exact metric")
    return rows, reference


def pooled_bootstrap(rows, *, paired=None, resamples=1000, seed=20261025):
    """Conditional spatial cluster-bootstrap CI; paired rows must use identical tiles."""
    a = np.asarray(rows, dtype=np.float64)
    pooled_dti(a)  # validates even when all tiles have zero contribution
    if len(a) < 2 or resamples < 2:
        raise ValueError("At least two clusters and two resamples required")
    b = None if paired is None else np.asarray(paired, dtype=np.float64)
    if b is not None:
        pooled_dti(b)
        if b.shape != a.shape:
            raise ValueError("Paired cluster grids must match")
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(resamples):
        ids = rng.integers(0, len(a), len(a))
        value = pooled_dti(a[ids])
        if b is not None:
            value -= pooled_dti(b[ids])
        scores.append(value)
    return [float(x) for x in np.quantile(scores, [0.025, 0.975])]


# Frozen MTR1 policy adapter: 1.5 km collar selection and 10 km CI blocks.
# Numerical source evidence for the original run is pinned at b6b4cc0.
MTR_EVALUATOR_VERSION = "gems-segment-pooled-v1"


def pooled_components(rows):
    """Pool metric components, never average region-level DTI ratios."""
    keys = ("TP_w", "FP_w", "FN_w", "n_truth", "n_emitted")
    out = {k: float(sum(r[k] for r in rows)) for k in keys}
    triples = np.asarray([[r[k] for k in keys[:3]] for r in rows], dtype=float).reshape(-1, 3)
    out["dti"] = pooled_dti(triples)
    return out


def spatial_bootstrap_ci(blocks, *, draws=1999, seed=20261025):
    """Approximate 95% CI, resampling 10 km blocks and pooling their components."""
    x = np.asarray(blocks, np.float64)
    if x.ndim != 2 or x.shape[1] != 3 or not len(x) or not np.isfinite(x).all():
        raise ValueError("Finite nonempty block TP/FP/FN components required")
    if draws < 100 or np.any(x < -1e-9):
        raise ValueError("At least 100 draws and nonnegative components required")
    interval = pooled_bootstrap(x, resamples=draws, seed=seed)
    return {
        "level": 0.95,
        "interval": interval,
        "method": "percentile spatial-block bootstrap of pooled TPw/FPw/FNw",
        "block_pixels": 100,
        "block_size_m": 10000,
        "n_blocks": len(x),
        "resamples": draws,
        "seed": seed,
        "limitation": "Internal-validation uncertainty; geologic structures may cross blocks. Not a hidden-score interval.",
    }


class SegmentHoldout:
    """Whole-component, buffered, quadrant-blocked hide-and-recover context.

    ``visible`` is the ONLY catalogue a detector may read. Whole connected
    components touching validation or its collar are hidden everywhere, not
    merely clipped at a split line. ``train`` is independently spatially purged.
    The positive class is an imperfect mapped-fault proxy, not hidden new truth.
    """

    def __init__(self, footprint, labels, *, buffer_px=15):
        from scipy.ndimage import distance_transform_edt

        self.footprint = np.asarray(footprint, bool)
        self.labels = np.asarray(labels, bool)
        if (
            self.footprint.shape != self.labels.shape
            or self.footprint.ndim != 2
            or not np.isfinite(buffer_px)
            or buffer_px < 3
            or np.any(self.labels & ~self.footprint)
            or not self.labels.any()
        ):
            raise ValueError("Aligned nonempty catalogue, footprint and >=3 px collar required")
        self.components, self.n_components = ndi_label(self.labels, structure=np.ones((3, 3), int))
        self.fold_grid, names = make_quadrant_folds(self.footprint)
        self.folds = []
        for f, name in enumerate(names):
            valid = self.footprint & (self.fold_grid == f)
            if not valid.any():
                raise ValueError(f"Empty spatial fold: {name}")
            collar = distance_transform_edt(~valid) <= buffer_px
            hidden_ids = np.unique(self.components[collar & self.labels])
            hidden_ids = hidden_ids[hidden_ids > 0]
            hidden = self.labels & np.isin(self.components, hidden_ids)
            visible = self.labels & ~hidden
            truth = hidden & valid
            if not truth.any():
                raise ValueError(f"No withheld positives: {name}")
            self.folds.append(
                {
                    "id": f,
                    "name": name,
                    "valid": valid,
                    "train": self.footprint
                    & (distance_transform_edt(~(valid | hidden)) > buffer_px),
                    "visible": visible,
                    "truth": truth,
                    "hidden_component_ids": hidden_ids,
                }
            )
        self.buffer_px = buffer_px

    def score_fold(self, prediction, fold):
        """Use the same exact metric/tile attribution as every current lane."""
        pred = np.asarray(prediction)
        if pred.shape != self.footprint.shape or not np.isin(pred, [0, 1]).all():
            raise ValueError("A finite aligned binary prediction is required")
        blocks, reference = spatial_components(
            pred, fold["truth"], fold["valid"], fold["visible"], tile_px=100
        )
        return reference, blocks

    def summarize(self, predictions, *, ci_draws=1999):
        if len(predictions) != len(self.folds):
            raise ValueError("One independent prediction per held-out fold required")
        rows, block_rows = [], []
        for pred, fold in zip(predictions, self.folds):
            result, blocks = self.score_fold(pred, fold)
            rows.append({"fold": fold["name"], **result})
            block_rows.append(blocks)
        blocks = np.sum(block_rows, axis=0)
        yy, xx = np.nonzero(self.footprint)
        nx = (self.footprint.shape[1] + 99) // 100
        active_blocks = np.unique((yy // 100) * nx + xx // 100)
        total = pooled_components(rows)
        return {
            "label": "HOLDOUT-DTI",
            "evaluator_version": MTR_EVALUATOR_VERSION,
            **total,
            "n_withheld_positive_pixels": int(total["n_truth"]),
            "n_unique_withheld_components": self.n_components,
            "ci95": spatial_bootstrap_ci(blocks[active_blocks], draws=ci_draws),
            "folds": rows,
            "protocol": {
                "aggregation": "pooled TPw/FPw/FNw, not mean fold DTI",
                "buffer_m": self.buffer_px * 100,
                "whole_components_hidden_everywhere": True,
                "visible_fault_mask": "pixel-exact, applied before credit and FP calculation",
                "catalogue_features": "must be constructed from fold.visible only",
                "alpha": 0.2,
                "beta": 0.8,
                "triangular_kernel_radius_m": 300,
            },
        }

    def compare_paired(
        self, candidate_predictions, baseline_predictions, *, ci_draws=1999, seed=20261025
    ):
        """Paired 10 km block-bootstrap comparison of two fold-aligned prediction sets."""
        if len(candidate_predictions) != len(self.folds) or len(baseline_predictions) != len(
            self.folds
        ):
            raise ValueError(
                "One independent prediction per held-out fold required for both series"
            )
        cand_rows, cand_blocks = [], []
        base_rows, base_blocks = [], []
        fold_deltas = []
        for c_pred, b_pred, fold in zip(candidate_predictions, baseline_predictions, self.folds):
            c_res, c_blk = self.score_fold(c_pred, fold)
            b_res, b_blk = self.score_fold(b_pred, fold)
            cand_rows.append({"fold": fold["name"], **c_res})
            base_rows.append({"fold": fold["name"], **b_res})
            cand_blocks.append(c_blk)
            base_blocks.append(b_blk)
            fold_deltas.append(
                {
                    "fold": fold["name"],
                    "candidate_dti": float(c_res["dti"]),
                    "baseline_dti": float(b_res["dti"]),
                    "delta_dti": float(c_res["dti"] - b_res["dti"]),
                    "candidate_wins": bool(c_res["dti"] > b_res["dti"]),
                }
            )
        c_sum = np.sum(cand_blocks, axis=0)
        b_sum = np.sum(base_blocks, axis=0)
        yy, xx = np.nonzero(self.footprint)
        nx = (self.footprint.shape[1] + 99) // 100
        active = np.unique((yy // 100) * nx + xx // 100)
        c_tot = pooled_components(cand_rows)
        b_tot = pooled_components(base_rows)
        delta_ci = pooled_bootstrap(
            c_sum[active], paired=b_sum[active], resamples=ci_draws, seed=seed
        )
        delta = float(c_tot["dti"] - b_tot["dti"])
        wins = int(sum(1 for d in fold_deltas if d["candidate_wins"]))
        return {
            "evaluator_version": MTR_EVALUATOR_VERSION,
            "candidate_dti": float(c_tot["dti"]),
            "baseline_dti": float(b_tot["dti"]),
            "paired_delta_dti": delta,
            "paired_delta_ci95": delta_ci,
            "ci95_strictly_positive": bool(delta_ci[0] > 0.0),
            "fold_wins": wins,
            "n_folds": len(self.folds),
            "min_fold_delta": float(min(d["delta_dti"] for d in fold_deltas)),
            "folds": fold_deltas,
        }

    def canary(self, features, *, seed=20261025, max_per_class=15000):
        """One-feature AUC diagnostics, never silently change a feature after a flag."""
        from scipy.ndimage import distance_transform_edt
        from sklearn.metrics import roc_auc_score

        if not isinstance(features, dict) or not features:
            raise ValueError("At least one actual feature required for leakage canary")
        if (
            isinstance(max_per_class, bool)
            or not isinstance(max_per_class, int)
            or max_per_class < 1
        ):
            raise ValueError("Positive integer canary sample limit required")
        rng = np.random.default_rng(seed)
        rows, samples = {}, []
        for fold in self.folds:
            truth, valid = fold["truth"], fold["valid"]
            positive = np.flatnonzero(truth)
            negative = np.flatnonzero(
                valid & ~fold["visible"] & (distance_transform_edt(~truth) >= 9)
            )
            positive = rng.choice(positive, min(len(positive), max_per_class), replace=False)
            negative = rng.choice(negative, min(len(negative), max_per_class), replace=False)
            samples.append((np.r_[positive, negative], len(positive), len(negative)))
        for name, surface in features.items():
            surface = np.asarray(surface)
            if surface.shape != self.footprint.shape:
                raise ValueError("Canary feature shape mismatch")
            details, values, labels = [], [], []
            for fold, (ids, n_positive, n_negative) in zip(self.folds, samples):
                x = surface.ravel()[ids]
                # Missingness itself is tested: use the same fixed zero sentinel
                # that the detector uses outside its supported physical domain.
                x = np.where(np.isfinite(x), x, 0)
                y = np.r_[np.ones(n_positive), np.zeros(n_negative)]
                auc = float(roc_auc_score(y, x))
                details.append(
                    {
                        "fold": fold["name"],
                        "auc": auc,
                        "positives": n_positive,
                        "background": n_negative,
                    }
                )
                values.append(x)
                labels.append(y)
            auc = float(roc_auc_score(np.concatenate(labels), np.concatenate(values)))
            suspicious = (
                max([max(auc, 1 - auc)] + [max(x["auc"], 1 - x["auc"]) for x in details]) > 0.90
            )
            rows[name] = {"pooled_auc": auc, "leakage_suspected": suspicious, "folds": details}
        return {
            "diagnostic": "LEAKAGE-CANARY AUC, not a DTI or organizer score",
            "evaluator_version": MTR_EVALUATOR_VERSION,
            "threshold": 0.90,
            "two_polarities_checked": True,
            "passed": not any(x["leakage_suspected"] for x in rows.values()),
            "features": rows,
            "interpretation": "AUC > .90 is leakage until explained; lower AUC does not prove independence or fault discovery.",
        }
