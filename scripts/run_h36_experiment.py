#!/usr/bin/env python3
"""H36-GPS experiments on the shared hide-and-recover evaluator (template SegmentHoldout).

E1: paired B0 (59 base features) vs C1 (B0 + 7 lane features), identical out-of-fold
HistGradientBoosting, identical emission. E2 (--e2): label-free physics-only field.
Every number written is HOLDOUT-DTI (gems-segment-pooled-v1, withheld positives, 95% CI).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.holdout import SegmentHoldout  # noqa: E402  (shared template evaluator)
from gemsdoe36.h36_emission import emit_dots  # noqa: E402
from gemsdoe36.h36_features import LANE_FEATURES, build_feature_stack  # noqa: E402

SEED = 20261025
TOTAL_BUDGET = 37654  # matched to the owner-reported best file's dot count (budget control only)
N_POS = 50000
N_NEG = 300000
HGB = dict(
    max_iter=250,
    learning_rate=0.06,
    max_leaf_nodes=48,
    min_samples_leaf=200,
    l2_regularization=1.0,
    early_stopping=False,
    random_state=SEED,
)
RECORDED_GROUP_BEST = {
    "value": 0.14876,
    "ci95": [0.13413, 0.16370],
    "source": "GEMSDOE24 H24-GVC1 README/run card (gems-segment-pooled-v1, 60,988 withheld positives); recorded, NOT re-run here",
    "url": "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1/README.md",
}


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def fold_budgets(holdout: SegmentHoldout) -> list[int]:
    n_fp = int(holdout.footprint.sum())
    return [int(round(TOTAL_BUDGET * int(f["valid"].sum()) / n_fp)) for f in holdout.folds]


def train_predict(store, names, fp_pos, fold, labels, rng_seed):
    from sklearn.ensemble import HistGradientBoostingClassifier

    rng = np.random.default_rng(rng_seed)
    train = fold["train"]
    vis = fold["visible"]
    pos_flat = np.flatnonzero((labels & train).ravel())
    far = distance_transform_edt(~vis) > 3
    neg_flat = np.flatnonzero((train & ~labels & far).ravel())
    pos_flat = rng.choice(pos_flat, min(N_POS, len(pos_flat)), replace=False)
    neg_flat = rng.choice(neg_flat, min(N_NEG, len(neg_flat)), replace=False)
    idx = np.r_[fp_pos[pos_flat], fp_pos[neg_flat]]
    y = np.r_[np.ones(len(pos_flat)), np.zeros(len(neg_flat))]
    X = store.rows(idx, names)
    model = HistGradientBoostingClassifier(**HGB)
    model.fit(X, y)
    del X
    valid_flat = np.flatnonzero(fold["valid"].ravel())
    score = np.zeros(fold["valid"].size, np.float32)
    for s in range(0, len(valid_flat), 400000):
        chunk = valid_flat[s : s + 400000]
        score[chunk] = model.predict_proba(store.rows(fp_pos[chunk], names))[:, 1]
    return score.reshape(fold["valid"].shape), {
        "n_pos_train": int(len(pos_flat)),
        "n_neg_train": int(len(neg_flat)),
    }


def physics_field(store, fp_pos, shape):
    """Label-free E2 field: mean of footprint percentile ranks of three lane features."""
    acc = np.zeros(store.n_fp, np.float64)
    used = []
    for n in ("gps_graben_pair", "gps_conjugate_line", "gps_coherent_scarp_line"):
        v = np.nan_to_num(np.asarray(store.column(n), np.float64), nan=0.0)
        acc += rankdata(v) / len(v)
        used.append(n)
    full = np.zeros(shape[0] * shape[1], np.float32)
    flat_fp = np.flatnonzero(fp_pos >= 0)
    full[flat_fp] = (acc / len(used)).astype(np.float32)
    return full.reshape(shape), used


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--e2", action="store_true", help="also run E2 (physics-only)")
    ap.add_argument("--skip-e1", action="store_true")
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "h36_holdout_experiments.json")
    args = ap.parse_args()
    t0 = time.time()
    store, grid = build_feature_stack(ROOT / ".cache" / "h36")
    names_all = store.names
    lane = [n for n in names_all if n in LANE_FEATURES]
    base = [n for n in names_all if n not in LANE_FEATURES]
    fp, labels = grid.footprint, grid.labels
    H, W = fp.shape
    fp_pos = np.full(H * W, -1, np.int64)
    fp_pos[np.flatnonzero(fp.ravel())] = np.arange(store.n_fp)
    holdout = SegmentHoldout(fp, labels, buffer_px=15)
    budgets = fold_budgets(holdout)
    out = {
        "label": "HOLDOUT-DTI",
        "evaluator": "gems.holdout.SegmentHoldout (template GEMSDOE24@fc2bc6f, byte-identical; registry/template_pins.json)",
        "evaluator_version": "gems-segment-pooled-v1",
        "buffer_px": 15,
        "preregistration": "knowledge/h36_preregistration_2026-10-25.md",
        "fold_budgets": budgets,
        "total_budget": int(sum(budgets)),
        "hgb": HGB,
        "n_pos_cap": N_POS,
        "n_neg_cap": N_NEG,
        "features_base": base,
        "features_lane": lane,
        "recorded_group_best": RECORDED_GROUP_BEST,
        "python": platform.python_version(),
    }
    if not args.skip_e1:
        preds = {"B0": [], "C1": []}
        fold_meta = []
        for f_i, fold in enumerate(holdout.folds):
            row = {"fold": fold["name"], "budget": budgets[f_i], "valid_px": int(fold["valid"].sum()),
                   "withheld_positive_px": int(fold["truth"].sum())}
            for arm, names in (("B0", base), ("C1", base + lane)):
                t1 = time.time()
                score, meta = train_predict(store, names, fp_pos, fold, labels, SEED + f_i)
                dots = emit_dots(score, fold["valid"], budgets[f_i])
                preds[arm].append(dots.astype(np.uint8))
                row[arm] = {**meta, "n_dots": int(dots.sum()), "seconds": round(time.time() - t1, 1)}
                print(f"[E1] fold {fold['name']} {arm}: {row[arm]}", flush=True)
                del score
            fold_meta.append(row)
        res_b0 = holdout.summarize(preds["B0"])
        res_c1 = holdout.summarize(preds["C1"])
        paired = holdout.compare_paired(preds["C1"], preds["B0"])
        out["E1"] = {"folds": fold_meta, "B0": res_b0, "C1": res_c1, "paired_C1_minus_B0": paired}
        print(f"[E1] B0 {res_b0['dti']:.5f} CI {res_b0['ci95']['interval']}  C1 {res_c1['dti']:.5f} CI {res_c1['ci95']['interval']}", flush=True)
        print(f"[E1] paired delta {paired['paired_delta_dti']:+.5f} CI {paired['paired_delta_ci95']} wins {paired['fold_wins']}/4", flush=True)
        np.savez_compressed(ROOT / ".cache" / "h36" / "e1_preds.npz", **{f"{a}_{i}": p for a in preds for i, p in enumerate(preds[a])})
        # leakage canary on every feature (label-free features; surfaces mapped to the grid)
        feats = {}
        for n in names_all:
            full = np.zeros(H * W, np.float32)
            full[np.flatnonzero(fp.ravel())] = np.asarray(store.column(n))
            feats[n] = full.reshape(H, W)
            if len(feats) == 12 or n == names_all[-1]:
                c = holdout.canary(feats)
                out.setdefault("canary", {"threshold": 0.90, "features": {}, "passed": True})
                out["canary"]["features"].update(c["features"])
                out["canary"]["passed"] &= c["passed"]
                feats = {}
        print(f"[E1] canary passed={out['canary']['passed']}", flush=True)
    if args.e2:
        field, used = physics_field(store, fp_pos, (H, W))
        preds = []
        for f_i, fold in enumerate(holdout.folds):
            preds.append(emit_dots(np.where(fold["valid"], field, 0), fold["valid"], budgets[f_i]).astype(np.uint8))
        res = holdout.summarize(preds)
        out["E2"] = {"field": "mean percentile rank of " + ", ".join(used), "result": res}
        if "E1" in out:
            out["E2"]["paired_E2_minus_B0"] = holdout.compare_paired(preds, [np.load(ROOT / ".cache/h36/e1_preds.npz")[f"B0_{i}"] for i in range(4)])
        print(f"[E2] {res['dti']:.5f} CI {res['ci95']['interval']}", flush=True)
    out["runtime_s"] = round(time.time() - t0, 1)
    out["template_sha256"] = {p: sha_file(ROOT / p) for p in ("src/gems/holdout.py", "src/gems/metric.py")}
    if args.out.exists():
        prev = json.loads(args.out.read_text())
        prev.update(out)
        out = prev
    args.out.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {args.out} in {out['runtime_s']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
