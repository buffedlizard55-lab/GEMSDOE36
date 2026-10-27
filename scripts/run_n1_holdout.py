#!/usr/bin/env python3
"""Hypothesis N1 — shear/dilation structure-tensor prior — whole-segment holdout test.

Lane: single-method experiment under the Parallel-Run Protocol.
  Hypothesis: blind normal faults in this extensional province concentrate at
  step-overs and dilatational jogs of mapped segments, where geodetic shear-rate
  (07_geod_shearrate) and dilation-rate (08_geod_dilaterate) gradients form a
  strong linear structural fabric. The structure-tensor coherence of those two
  gradient fields is a strike-independent, off-catalogue fault prior: it
  nominates concealed jogs that have no continuous surface scarp and are absent
  from the USGS/INGENIOUS catalogue, so the dots it emits sit outside the
  200 m catalogue-flank exclusion and are creditable mass rather than masked
  mass.

  Difference from the repo: bands 07/08 exist in the official stack but are
  used nowhere in any emission pipeline (they appear only as z-scored covariates
  in HGB arms). No structure-tensor pair of strain-rate channels exists in this
  repo. ATVR-36's H36-A uses gravity/magnetic tilt-THDR and relief-deconfounded
  slope/TC; H36-B uses RTP troughs and conductivity; H36-C uses basement
  flexure and regime probabilities. N1 is none of those.

  Named non-fault mimic: erosional drainage density and alluvial fan
  distributary channels also produce coherent linear strain-rate fabric; the
  300 m kernel DTI and off-catalogue eligibility (d_cat > 2 px) are the
  controls.

  Holdout (hide-and-recover): whole 8-connected fault segments withheld (buffer
  30 px / 3 km), features derived from visible faults only, visible faults
  masked pixel-exactly, pooled DTI alpha 0.2 / beta 0.8, 300 m triangular
  kernel, 4 folds x 4 spatial cells, bootstrap 2000 over cells.
  Leakage canary: two-polarity rank AUC of the N1 surface vs catalogue truth
  must be <= 0.90.

Outputs a JSON run card; does NOT touch a submission slot.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe36.atvr_features import build_or_load_static_feature_cache
from gemsdoe36.field import FieldConfig, build_belief_field  # noqa: F401 (shared stack)
from gemsdoe36.metric import distance_weighted_tversky
from gemsdoe36.paths import data_dir, work_dir
from gemsdoe36.protocol import (
    EVALUATOR_VERSION,
    feature_canary,
    hide_segments,
    pooled_holdout,
)

TOTAL_DOT_BUDGET = 37_654
COLLAR_PX = 2.0
BUFFER_PX = 30
N_FOLDS = 4
BOOTSTRAP = 2000
SEED = 36


def _sha256_file(p: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _grid(rows, cols, values, shape):
    g = np.zeros(shape, dtype=np.float32)
    g[rows, cols] = values
    return g


def _robust01(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    v = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    v = np.where(foot, v, 0.0)
    vals = v[foot]
    if vals.size == 0:
        return np.zeros_like(v)
    lo, hi = np.percentile(vals, [2, 98])
    hi = max(hi, 1e-9)
    out = np.clip((v - lo) / (hi - lo), 0.0, 1.0)
    return np.where(foot, out, 0.0).astype(np.float32)


def _n1_surface(shear: np.ndarray, dilation: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Structure-tensor coherence of the shear/dilation gradient fabric."""
    gx_s, gy_s = np.gradient(shear)
    gx_d, gy_d = np.gradient(dilation)
    s = 2.5  # tensor smoothing sigma, px (250 m)
    j11 = gaussian_filter(gx_s * gx_s + gx_d * gx_d, sigma=s, mode="nearest")
    j22 = gaussian_filter(gy_s * gy_s + gy_d * gy_d, sigma=s, mode="nearest")
    j12 = gaussian_filter(gx_s * gy_s + gx_d * gy_d, sigma=s, mode="nearest")
    tr = j11 + j22
    diff = np.hypot(j11 - j22, 2.0 * j12)
    lam_max = 0.5 * (tr + diff)
    lam_min = 0.5 * (tr - diff)
    coh = np.where(tr > 1e-12, (lam_max - lam_min) / (lam_max + lam_min + 1e-12), 0.0)
    del gx_s, gy_s, gx_d, gy_d, j11, j22, j12, tr, diff, lam_max, lam_min
    return _robust01(coh, foot)


def _top_k_mask(score2d: np.ndarray, elig2d: np.ndarray, budget: int) -> np.ndarray:
    rc = np.argwhere(elig2d)
    vals = score2d[rc[:, 0], rc[:, 1]]
    out = np.zeros(score2d.shape, dtype=bool)
    if len(vals) <= budget:
        out[rc[:, 0], rc[:, 1]] = True
        return out
    order = np.argpartition(-vals, budget - 1)[:budget]
    chosen = rc[order]
    out[chosen[:, 0], chosen[:, 1]] = True
    return out


def _allocate_budgets(elig_masks: list[np.ndarray], total: int) -> list[int]:
    counts = np.array([int(m.sum()) for m in elig_masks], dtype=np.float64)
    raw = counts / counts.sum() * total
    floors = np.floor(raw).astype(int)
    rem = int(total - floors.sum())
    order = np.argsort(-(raw - floors))
    for i in range(rem):
        floors[order[i]] += 1
    return floors.tolist()


def main() -> int:
    t0 = time.time()
    cache = build_or_load_static_feature_cache()
    foot = cache.footprint
    truth = cache.labels > 0.5

    # --- surfaces -------------------------------------------------------
    bands_dir = work_dir() / "bands"
    shear = np.load(bands_dir / "07_geod_shearrate.npy").astype(np.float32)
    dilation = np.load(bands_dir / "08_geod_dilaterate.npy").astype(np.float32)
    det_slope = np.load(bands_dir / "19_det_elev_slope.npy").astype(np.float32)
    shear[~foot] = 0.0
    dilation[~foot] = 0.0
    det_slope[~foot] = 0.0

    n1 = _n1_surface(shear, dilation, foot)
    base = _robust01(det_slope, foot)
    del shear, dilation, det_slope

    # --- holdout plan (identical design to ATVR-36 lane) ----------------
    known_bool = truth

    # Build plan via ATVR's builder semantics (4 folds, 16 cells, buffer 30).
    sys.path.insert(0, str(ROOT / "scripts"))
    import evaluate_holdout as _eh  # reuses the locked holdout-plan builder; import-only, no main()

    plan = _eh.build_whole_segment_holdout_plan(known_bool, foot, buffer_px=BUFFER_PX)
    print(
        f"[n1] holdout plan: {plan.n_segments:,} segments, {int(plan.truth.sum()):,} "
        f"positive px, {plan.n_folds} folds / 16 cells"
    )

    d_known = distance_transform_edt(~known_bool).astype(np.float32)

    def run_arm(surface2d: np.ndarray, arm_name: str) -> dict:
        dots = np.zeros(foot.shape, dtype=bool)
        per_cell = []
        elig_masks = []
        for k in range(plan.n_folds):
            vis_k = plan.visible_by_fold[k]
            dvis_k = distance_transform_edt(~vis_k).astype(np.float32)
            ev_k = plan.eval_mask_by_fold[k]
            elig_k = ev_k & (dvis_k > COLLAR_PX)
            elig_masks.append(elig_k)
        budgets = _allocate_budgets(elig_masks, TOTAL_DOT_BUDGET)
        for k in range(plan.n_folds):
            elig_k = elig_masks[k]
            ev_k = plan.eval_mask_by_fold[k]
            q_mask = (plan.fold_owner == k) & foot
            scores = surface2d[q_mask]
            elig_idx = np.flatnonzero(q_mask)
            rc = np.argwhere(elig_k)
            vals = surface2d[rc[:, 0], rc[:, 1]]
            budget = budgets[k]
            if len(vals) <= budget:
                pick = rc
            else:
                order = np.argpartition(-vals, budget - 1)[:budget]
                pick = rc[order]
            dots[pick[:, 0], pick[:, 1]] = True
            per_cell.append((dots.astype(np.float32), plan.hidden_by_fold[k], ev_k))
            del scores, elig_idx, rc, vals
        res = pooled_holdout(per_cell, bootstrap=BOOTSTRAP, seed=SEED)
        # unsplit full-footprint DTI (dots as probability grid, catalogue masked)
        unsplit = distance_weighted_tversky(
            dots.astype(np.float32),
            plan.truth.astype(np.float32),
            valid_mask=foot,
            return_components=True,
        )
        return {
            "arm": arm_name,
            "dots_emitted": int(dots.sum()),
            "dots_on_catalogue": int((dots & known_bool).sum()),
            "pooled_16block_dti": round(float(res["dti"]), 6),
            "pooled_16block_ci95": [round(float(v), 6) for v in res["ci95"]],
            "withheld_positives_px": int(res["withheld_positives"]),
            "independent_cells": int(res["independent_cells"]),
            "unsplit_pooled_dti": round(float(unsplit.score), 6),
            "unsplit_tp_w": round(float(unsplit.true_positive), 2),
            "unsplit_fp_w": round(float(unsplit.false_positive), 2),
            "unsplit_fn_w": round(float(unsplit.false_negative), 2),
        }

    results = []
    for arm_name, surface in (("BASELINE_det_elev_slope", base), ("N1_shear_dilation_coherence", n1)):
        t_arm = time.time()
        r = run_arm(surface, arm_name)
        r["elapsed_sec"] = round(time.time() - t_arm, 1)
        results.append(r)
        print(
            f"[n1] {arm_name}: dots={r['dots_emitted']:,} on-cat={r['dots_on_catalogue']} "
            f"HOLDOUT-DTI={r['pooled_16block_dti']:.4f} "
            f"CI95=[{r['pooled_16block_ci95'][0]:.4f}, {r['pooled_16block_ci95'][1]:.4f}] "
            f"unsplit={r['unsplit_pooled_dti']:.4f} ({r['elapsed_sec']}s)"
        )

    # --- leakage canary -------------------------------------------------
    canary = feature_canary(n1, plan.truth, foot)
    print(
        f"[n1] leakage canary: AUC={canary['auc']:.4f} two-polarity={canary['two_polarity_auc']:.4f} "
        f"passed={canary['passed']}"
    )

    # --- comparison -----------------------------------------------------
    cand = results[1]
    base_r = results[0]
    delta = cand["pooled_16block_dti"] - base_r["pooled_16block_dti"]
    print(f"[n1] N1 - BASELINE = {delta:+.4f} HOLDOUT-DTI")

    card = {
        "schema": "gemsdoe36.hypothesis-n1.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "GEMSDOE36",
        "hypothesis_id": "N1",
        "hypothesis": (
            "Shear/dilation structure-tensor coherence of geodetic strain-rate bands "
            "(07_geod_shearrate x 08_geod_dilaterate) as an off-catalogue blind "
            "step-over / dilatational-jog fault prior."
        ),
        "layers": ["07_geod_shearrate", "08_geod_dilaterate"],
        "physical_signature": (
            "Linear structural fabric (high structure-tensor coherence) of the "
            "shear-rate/dilation-rate gradient fields at concealed fault step-overs "
            "and jogs; no continuous scarp required."
        ),
        "why_off_catalogue": (
            "Step-overs and jogs of mapped segments are unmapped faults outside the "
            "USGS/INGENIOUS catalogue; dots land beyond the 200 m catalogue-flank "
            "exclusion, so they are creditable DTI mass rather than masked mass."
        ),
        "differs_from_repo": (
            "Bands 07/08 are unused in any emission pipeline in this repo; no "
            "structure-tensor pair of strain-rate channels exists anywhere in the "
            "stack. ATVR-36 uses gravity/magnetic tilt-THDR, relief-deconfounded "
            "slope/TC, RTP troughs, conductivity, basement flexure and regime "
            "probabilities — none of them strain-rate coherence."
        ),
        "named_non_fault_mimic": (
            "Erosional drainage density and alluvial-fan distributary channels also "
            "form coherent linear fabric; controlled by off-catalogue eligibility "
            "(d_cat > 2 px) and the 300 m kernel DTI."
        ),
        "expected_dti_improvement": "+0.005 to +0.015 over a single-channel baseline (unverified until this run)",
        "implementation_cost": "low — deterministic transforms, no training",
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": EVALUATOR_VERSION,
            "design": "whole-segment withholding, buffer 30 px, 4 folds x 4 spatial cells, "
            "pooled DTI alpha=0.2 beta=0.8, 300 m triangular kernel, bootstrap 2000 over cells",
            "n_withheld_segments": plan.n_segments,
            "n_withheld_positives_px": int(plan.truth.sum()),
            "budget_dots": TOTAL_DOT_BUDGET,
            "collar_px": COLLAR_PX,
        },
        "leakage_canary": {
            "auc": round(float(canary["auc"]), 6),
            "two_polarity_auc": round(float(canary["two_polarity_auc"]), 6),
            "cap": 0.90,
            "passed": bool(canary["passed"]),
        },
        "results": results,
        "delta_n1_vs_baseline": round(float(delta), 6),
        "raster_sha256_pending": True,
        "total_runtime_sec": round(time.time() - t0, 1),
    }
    out_path = ROOT / "evidence" / "n1_holdout_run_card.json"
    out_path.write_text(json.dumps(card, indent=2) + "\n")
    print(f"[n1] card written -> {out_path}")
    return 0 if cand["pooled_16block_dti"] > base_r["pooled_16block_dti"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
