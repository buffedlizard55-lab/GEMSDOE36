"""Fail-closed protocol primitives; not a replacement for the missing shared template.

Callbacks receive only visible faults. This interface cannot prove a callback has
not captured full labels: provenance review and per-feature canaries remain required.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata, spearmanr

from .metric import distance_weighted_tversky

EVALUATOR_VERSION = "gems36-segment-audit-v1"


def hide_segments(segment_ids, withheld_ids, footprint, buffer_px=30):
    """Hide complete precomputed geological segments, including a training collar.

    IDs must come from an independently frozen segment partition, not random pixels.
    Visible faults are removed pixel-exactly from scoring, not dilated for scoring.
    """
    ids = np.asarray(segment_ids)
    foot = np.asarray(footprint, dtype=bool)
    if ids.ndim != 2 or ids.shape != foot.shape or not np.issubdtype(ids.dtype, np.integer):
        raise ValueError("segment IDs must be a 2D integer grid matching footprint")
    if np.any(ids < 0) or buffer_px < 0 or not np.isfinite(buffer_px):
        raise ValueError("non-negative IDs and finite non-negative buffer required")
    chosen = np.asarray(list(withheld_ids))
    if not chosen.size or np.any(chosen <= 0) or not np.all(np.isin(chosen, ids[foot])):
        raise ValueError("withheld IDs must name existing positive segments")
    hidden = np.isin(ids, chosen) & foot
    collar = distance_transform_edt(~hidden) <= buffer_px
    known_unwithheld = (ids > 0) & foot & ~hidden
    visible = known_unwithheld & ~collar
    train_mask = foot & ~collar
    # Collar-removed training faults are not hidden positives or negative truth.
    # Exclude every unwithheld catalogue pixel exactly, without dilating it.
    score_mask = foot & ~known_unwithheld
    return visible, hidden, train_mask, score_mask


def feature_canary(feature, hidden, score_mask):
    """Two-polarity rank AUC; >0.90 is presumptive leakage, never auto-excused."""
    x = np.asarray(feature)[score_mask]
    y = np.asarray(hidden, dtype=bool)[score_mask]
    if not np.all(np.isfinite(x)) or not y.any() or y.all():
        raise ValueError("canary needs finite features and both classes")
    n1, n0 = int(y.sum()), int((~y).sum())
    auc = float((rankdata(x)[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    return {"auc": auc, "two_polarity_auc": max(auc, 1 - auc),
            "passed": max(auc, 1 - auc) <= 0.90}


def pooled_holdout(cells, *, bootstrap=2000, seed=36):
    """Pool TP/FP/FN; bootstrap whole independent spatial cells, never pixels.

    Each cell is (prediction, hidden_truth, score_mask). Cells must be disjoint
    independent spatial units; correlated repeats must be grouped by the caller.
    """
    if len(cells) < 2 or bootstrap < 2:
        raise ValueError("need at least two independent cells and bootstrap replicates")
    terms = []
    positives = 0
    for pred, truth, mask in cells:
        c = distance_weighted_tversky(pred, truth, valid_mask=mask, return_components=True)
        terms.append((c.true_positive, c.false_positive, c.false_negative))
        positives += int(np.count_nonzero(np.asarray(truth)[mask]))
    if positives == 0:
        raise ValueError("no withheld positives")
    terms = np.asarray(terms)

    def ratio(t):
        tp, fp, fn = np.moveaxis(t, -1, 0)
        return tp / (tp + 0.2 * fp + 0.8 * fn + 1e-8)

    rng = np.random.default_rng(seed)
    resamples = terms[rng.integers(len(terms), size=(bootstrap, len(terms)))].sum(axis=1)
    return {"label": "HOLDOUT-DTI", "evaluator_version": EVALUATOR_VERSION,
            "withheld_positives": positives, "independent_cells": len(cells),
            "dti": float(ratio(terms.sum(axis=0))),
            "ci95": np.quantile(ratio(resamples), [0.025, 0.975]).tolist(),
            "bootstrap": "whole-spatial-cell percentile", "seed": seed}


def registry_check(surface, dots, footprint, registry):
    """Exact full-footprint rank comparison and directed <=3px dot overlap.

    Registry is a mapping name -> (surface, binary dots). Missing or constant
    surfaces cannot establish uniqueness. No sampling or random jitter of ties.
    """
    foot = np.asarray(footprint, dtype=bool)
    s, d = np.asarray(surface), np.asarray(dots, dtype=bool)
    if s.shape != foot.shape or d.shape != foot.shape or not foot.any():
        raise ValueError("surface/dots must match a nonempty footprint")
    if not registry or not d[foot].any() or not np.all(np.isfinite(s[foot])):
        raise ValueError("nonempty registry, finite surface and positive dots required")
    rows = []
    for name, (reference, reference_dots) in registry.items():
        r, rd = np.asarray(reference), np.asarray(reference_dots, dtype=bool)
        if r.shape != foot.shape or rd.shape != foot.shape:
            raise ValueError(f"registry shape mismatch: {name}")
        if not np.all(np.isfinite(r[foot])) or np.ptp(r[foot]) == 0 or np.ptp(s[foot]) == 0:
            raise ValueError(f"unverifiable constant/nonfinite surface: {name}")
        rho = float(spearmanr(s[foot], r[foot]).statistic)
        near = distance_transform_edt(~(rd & foot)) <= 3 if rd[foot].any() else foot & False
        overlap = float(near[d & foot].mean())
        dot_rho = (float(spearmanr(d[foot], rd[foot]).statistic)
                   if rd[foot].any() and not rd[foot].all() and not d[foot].all() else None)
        rows.append({"name": name, "surface_rank_correlation": rho,
                     "dot_rank_correlation": dot_rho,
                     "dot_overlap_within_3px": overlap,
                     "duplicate": abs(rho) > 0.90 or overlap > 0.70
                     or (dot_rho is not None and abs(dot_rho) > 0.90)})
    return {"passed": not any(r["duplicate"] for r in rows), "comparisons": rows,
            "scope": "provided registry only; completeness must be verified separately"}
