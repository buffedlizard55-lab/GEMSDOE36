#!/usr/bin/env python3
"""KPL-36 leaderboard score-ESTIMATE model + H-KPL-C emission sensitivity (post-deploy).

The estimate is a transparent scenario model, NOT a score and NOT a projection claim:
  DTI = T / (0.2*(T + S - M) + 0.8*N')   with T ~ M for thin dots
      ~ (sum of per-dot expected credits) / (0.2*S + 0.8*N')
N' = 12,541 effective hidden-truth pixels (13GEMSDOE blind-lattice calibration,
docs/research/why-02778.md). Candidate dots are partitioned by measured geometry:
  A: within 3 px of GEMSDOE32-B2 champion dots  -> credit 0.130 (champion measured mean)
  B: within 3 px of H19-5 solid field, not A    -> credit 0.054 (H19-5 measured mean at 0.1922)
  C: novel remainder                            -> scenario {0.03, 0.07, 0.10, 0.13}
Every input is measured from the actual rasters in this script.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_gvsc36 import fold_budgets, load_labels  # noqa: E402

from gems.holdout import SegmentHoldout  # noqa: E402
from gemsdoe36.submodular_emit import emit_submodular_cover  # noqa: E402

OUT = ROOT / "evidence" / "kpl36_score_estimate_20261026.json"
N_PRIME = 12_541


def load_mask(path: Path, fp: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return fp & np.isfinite(a) & (a > 0)


def main() -> int:
    card = json.loads((ROOT / "evidence/kpl36_run_card_20261026.json").read_text())
    hold = json.loads((ROOT / "evidence/kpl36_holdout_experiments_20261026.json").read_text())
    cand_path = ROOT / card["submission"]["file"]
    entries = json.loads((ROOT / "registry/uniqueness_registry.json").read_text())["entries"]
    b2e = next(e for e in entries if "e5eb6e7e" in e["file"])
    fp_lbl, labels = load_labels(ROOT / "data" / "raw")

    cand = load_mask(cand_path, fp_lbl)
    b2 = load_mask(ROOT / b2e["cache_path"], fp_lbl)
    h195 = load_mask(ROOT / "data/raw/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif", fp_lbl)
    pts = np.argwhere(cand)
    d_b2 = cKDTree(np.argwhere(b2)).query(pts)[0]
    d_h = cKDTree(np.argwhere(h195)).query(pts)[0]
    in_a = d_b2 <= 3.0
    in_b = (~in_a) & (d_h <= 3.0)
    in_c = ~(in_a | in_b)
    S = int(cand.sum())
    part = {"A_within3px_B2": int(in_a.sum()), "B_within3px_H195_notA": int(in_b.sum()), "C_novel": int(in_c.sum())}
    assert sum(part.values()) == S
    denom = 0.2 * S + 0.8 * N_PRIME
    scenarios = {}
    for c_credit in (0.03, 0.07, 0.10, 0.13):
        T = part["A_within3px_B2"] * 0.130 + part["B_within3px_H195_notA"] * 0.054 + part["C_novel"] * c_credit
        scenarios[f"novel_credit_{c_credit:.2f}"] = {
            "expected_T": round(float(T), 1),
            "estimated_DTI_if_credit_assumptions_hold": round(float(T / denom), 4),
        }
    # break-even novel credit needed to match 0.2778 at this partition
    T_needed = 0.2778 * denom
    c_needed = (T_needed - part["A_within3px_B2"] * 0.130 - part["B_within3px_H195_notA"] * 0.054) / max(part["C_novel"], 1)

    # H-KPL-C sensitivity: re-emit best arm from saved fold surfaces at other budgets/collars.
    best = hold["best_candidate_arm"]
    holdout = SegmentHoldout(fp_lbl, labels, buffer_px=15)
    budgets = fold_budgets(holdout)
    sens = {}
    for cfg_name, scale, collar in (("44090_B2", 44090 / 37654, 2.0), ("37654_B3", 1.0, 3.0)):
        preds = []
        for f_i, fold in enumerate(holdout.folds):
            with np.load(ROOT / f".cache/kpl36/holdout_fold_{f_i}.npz") as z:
                surf_v = z[f"surf_{best}"]
            surf = np.zeros(fp_lbl.shape, np.float32)
            surf[fold["valid"]] = surf_v
            d_vis = distance_transform_edt(~fold["visible"])
            elig = fold["valid"] & (d_vis > collar)
            cov = emit_submodular_cover(surf, elig, budget=int(round(budgets[f_i] * scale)), valid_footprint=fold["valid"], gamma=1.0, min_spacing_px=2.0)
            preds.append(cov.mask.astype(np.uint8))
        s = holdout.summarize(preds)
        sens[cfg_name] = {"label": "HOLDOUT-DTI", "dti": s["dti"], "ci95": s["ci95"]["interval"], "n_dots": int(sum(int(p.sum()) for p in preds))}
        print(f"[sens] {cfg_name}: HOLDOUT-DTI {s['dti']:.6f}", flush=True)

    doc = {
        "lane_id": "KPL-36",
        "kind": "SCENARIO ESTIMATE - not a score, not HOLDOUT-DTI, not ORGANIZER-CONFIRMED",
        "candidate_file": card["submission"]["file"],
        "candidate_sha256": card["submission"]["sha256"],
        "formula": "DTI ~= (nA*0.130 + nB*0.054 + nC*c) / (0.2*S + 0.8*N'), N'=12541",
        "measured_partition": {**part, "S_total_dots": S,
                               "share_A": round(part["A_within3px_B2"] / S, 4),
                               "share_B": round(part["B_within3px_H195_notA"] / S, 4),
                               "share_C": round(part["C_novel"] / S, 4)},
        "credit_anchors": {
            "A_0.130": "GEMSDOE32-B2 measured mean credit/dot at OWNER-REPORTED 0.2778 (why-02778.md)",
            "B_0.054": "H19-5 solid field measured mean credit/px at OWNER-REPORTED 0.1922 (T=DTI*(0.2S+0.8N'))",
            "C_scenarios": "0.03 = historical independent-detector novel-dot credit; 0.13 = champion-grade novel dots",
        },
        "scenarios": scenarios,
        "novel_credit_needed_to_match_0.2778": round(float(c_needed), 4),
        "emission_sensitivity_best_arm": {"arm": best, "deployed_37654_B2_holdout_dti": hold["summaries"][best]["dti"], **sens},
        "caveats": [
            "A-dots are near but not on champion positions; their true mean credit is likely below 0.130.",
            "N' assumes hidden truth uniform w.r.t. the calibration lattice and a public/private split folded into N'.",
            "No organizer receipt exists for this file; only a real submission can measure its score.",
        ],
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps({"partition": part, "scenarios": scenarios, "c_needed": doc["novel_credit_needed_to_match_0.2778"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
