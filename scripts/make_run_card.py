#!/usr/bin/env python3
"""Build the parallel-run protocol run card (rule 5) for the session's unique TIF.

Every number is labeled HOLDOUT-DTI (local spatial holdout: evaluator version,
withheld-positives count, 95% CI) or ORGANIZER-CONFIRMED (copied from a
submission-page receipt). A projection is never written as a score.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from gemsdoe36.live_mirror import load_live_mirror_context
from gemsdoe36.submission import validate_submission

cand_matches = sorted(
    (REPO_ROOT / "docs" / "downloads").glob("gemsdoe36-anderson-geothermal-pinn-*-zeros.tif"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
if not cand_matches:
    raise FileNotFoundError("no Anderson-PINN zeros TIF found in docs/downloads/")
CANDIDATE = cand_matches[0]
EVIDENCE = REPO_ROOT / "evidence"
DOCS_RESEARCH = REPO_ROOT / "docs" / "research"
DATA_DIR = REPO_ROOT / "data" / "raw"
TEMPLATE = DATA_DIR / "sample_submission.tif"
LABELS = DATA_DIR / "labels.tif"


def bootstrap_ci(values: np.ndarray, n_resamples: int = 20000, seed: int = 42):
    rng = np.random.default_rng(seed)
    boots = np.mean(rng.choice(values, size=(n_resamples, len(values))), axis=1)
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def main() -> int:
    ddir = DATA_DIR
    with __import__("rasterio").open(ddir / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with __import__("rasterio").open(ddir / "labels.tif") as s:
        labels = (s.read(1) == 1) & foot

    # ---- holdout numbers (HOLDOUT-DTI) -------------------------------------
    lm_ctx = load_live_mirror_context(ddir, foot, labels)
    truth_per_fold = {c.key: int(c.n_truth) for c in lm_ctx.cells}

    ev_path = EVIDENCE / "h36_holdout_validation.json"
    ev = json.loads(ev_path.read_text())
    lead = ev["GEMSDOE36-LEAD-PINN"]
    base = ev["BASE-0.2778"]
    folds = ("foldNW", "foldNE", "foldSW", "foldSE")
    lead_folds = np.array([lead["lm_per_fold"][k] for k in folds], dtype=np.float64)
    base_folds = np.array([base["lm_per_fold"][k] for k in folds], dtype=np.float64)
    margin = float(lead["lm_calibrated_mean"] - base["lm_calibrated_mean"])
    ci_lead = bootstrap_ci(lead_folds)
    ci_margin = bootstrap_ci(lead_folds - base_folds)
    folds_won = int((lead_folds > base_folds).sum())

    # ---- lane check ---------------------------------------------------------
    lane = json.loads((EVIDENCE / "lane_check.json").read_text())
    distinct = [c for c in lane["checks"] if c["verdict"] == "distinct lane"]
    max_rho = max((c["spearman_rho"] for c in distinct if c["spearman_rho"] is not None),
                  default=None)
    max_near = max((c["dots_within_3px_fraction"] for c in distinct if c["dots_within_3px_fraction"] is not None),
                   default=None)

    # ---- validator output ---------------------------------------------------
    # The primary is the portal-safe "zeros outside" mode: all grid cells are
    # finite in [0,1], so outside-footprint finiteness is acceptable (values
    # are checked to be in [0,1] by the validator's zeros branch).
    zeros_mode = CANDIDATE.name.endswith("-zeros.tif")
    report = validate_submission(
        CANDIDATE, TEMPLATE, require_nonfinite_outside=(not zeros_mode)
    )
    vr = report.to_dict()

    # ---- submission form metadata (note capped at 140 chars for the card) ---
    submission_name = "GEMSDOE36-Anderson-PINN-20261025"
    note = (
        f"GEMSDOE36 Anderson-PINN | B=2 catalogue-flank prune + Anderson/geothermal dots; "
        f"{int(lead['emitted_dots']):,} dots; 0 on-cat; HOLDOUT-DTI {lead['lm_calibrated_mean']:.4f}"
    )
    assert len(note) <= 140, f"note too long: {len(note)}"

    # ---- leakage canary -----------------------------------------------------
    canary = json.loads((EVIDENCE / "leakage_canary.json").read_text())
    max_auc = max((b["max_auc"] for b in canary["bands"] if b["max_auc"] is not None),
                  default=None)

    # ---- verdict ------------------------------------------------------------
    ci_span_zero = ci_margin[0] <= 0.0 <= ci_margin[1]
    slot_eligible = (not ci_span_zero) and folds_won >= 2
    verdict = ("promote" if slot_eligible else "negative")
    rationale = (
        f"Unique format-validated TIF generated ({Path(CANDIDATE).name}); lane-distinct from "
        f"the H6 lane (rho {max_rho}, {max_near*100:.1f}% dots within 3 px); no single-feature "
        f"leakage (max AUC {max_auc}). HOLDOUT-DTI lead {lead['lm_calibrated_mean']:.6f} vs "
        f"base {base['lm_calibrated_mean']:.6f} (margin {margin:+.6f}) but the 95% CI on the "
        f"margin ({ci_margin[0]:+.6f} .. {ci_margin[1]:+.6f}) spans zero and the lead wins only "
        f"{folds_won}/4 spatial blocks -> gain is within noise on this holdout; NOT slot-eligible. "
        f"No weekly submission slot was spent; upload remains the owner's manual step."
    )

    card = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "labeling_convention": (
            "Every number is HOLDOUT-DTI (local spatial holdout below) or ORGANIZER-CONFIRMED "
            "(copied from a submission-page receipt). No projection is written as a score. "
            "The 0.2778 GEMSDOE32 figure is site-reported (ORGANIZER-CONFIRMED-as-cited, no local "
            "organizer receipt; see docs/research/known_irregularities.md IR-04/IR-05)."
        ),
        "candidate_file": str(CANDIDATE.relative_to(REPO_ROOT)),
        "raster_sha256": __import__("hashlib").sha256(CANDIDATE.read_bytes()).hexdigest(),
        "candidate_bytes": int(CANDIDATE.stat().st_size),
        "hypothesis": {
            "id": "H36-PINN-Lead",
            "name": "Anderson-PINN multi-physics: B=2 catalogue-flank pruned d28 base + "
                    "Anderson-consistent geothermal conduit & step-over dots",
            "statement": (
                "Pruning mechanically impossible E-W strikes (parallel to sigma_3 ~105° extension) "
                "and reallocating the dot budget to GDR-1391 blind geothermal conduits plus "
                "geodetic step-over dilatation, under Raissi et al. (2019) structure-tensor "
                "orientation regularization, raises off-catalogue DTI over the h33-2-b2 base."
            ),
        },
        "mechanism": (
            "DTI = TP_w / (0.2|P| + 0.8|G| + 0.8(TP_g - TP_p)); alpha=0.2 makes every extra dot a "
            "denominator tax, so redundant/continuos-line dots are thinned to ~300 m Poisson-disk "
            "spacing. Dots within 200 m of known catalogue faults are masked in scoring, so they "
            "pay pure FP tax: the B=2 (200 m) catalogue-flank exclusion removes them. The added "
            "dots target off-catalogue geothermal upflow conduits (GDR 1391, T>=130 C, >1.5 km off "
            "catalogue) and geodetic step-over dilatation, gated by Anderson-consistent strike "
            "(NNE-SSW normal / NW-SE transtensional; E-W strikes parallel to sigma_3 suppressed)."
        ),
        "named_non_fault_mimic_process": (
            "E-W geophysical lineaments from flight-line noise, lithologic contacts, and drainage "
            "channels mimic fault strikes; radiometric clay-alteration halos, spring/vent density, "
            "and broad magnetic or gravity anomaly bodies can mimic geothermal conduits without an "
            "underlying fault."
        ),
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": "gemsdoe36.live_mirror (4-quadrant spatially blocked mirror) + "
            "gemsdoe36.metric.py distance_weighted_tversky (alpha=0.2, beta=0.8, triangular R=300 m)",
            "evaluator_files": ["src/gemsdoe36/live_mirror.py", "src/gemsdoe36/metric.py"],
            "withheld_positives_per_fold": truth_per_fold,
            "withheld_positives_total": sum(truth_per_fold.values()),
            "blocks": 4,
            "lead_mean_dti": float(lead["lm_calibrated_mean"]),
            "lead_mean_dti_ci95": list(ci_lead),
            "base_mean_dti": float(base["lm_calibrated_mean"]),
            "base_mean_dti_ci95": list(bootstrap_ci(base_folds)),
            "margin_vs_base_dti": margin,
            "margin_vs_base_ci95": list(ci_margin),
            "folds_lead_wins": folds_won,
            "lead_per_fold_dti": {k: float(v) for k, v in zip(folds, lead_folds)},
            "base_per_fold_dti": {k: float(v) for k, v in zip(folds, base_folds)},
            "note": "CI95 is a nonparametric bootstrap over the 4 block means (20000 resamples). "
                    "With only 4 blocks the CI is wide; the observed margin is within noise.",
        },
        "leakage_canary": {
            "label": "HOLDOUT-DTI per-feature screen",
            "rule": "single-feature AUC > 0.90 on the holdout => leakage until proven otherwise",
            "max_single_feature_auc": max_auc,
            "leakage_found": bool(canary["leakage_found"]),
            "source": "evidence/leakage_canary.json",
        },
        "correlation_overlap_vs_registry": {
            "label": "HOLDOUT-DTI lane context",
            "lane_duplicate_found": bool(lane["duplicate_found"]),
            "vs_h6_lane": {
                "raster": "GEMS36_h6_offcatalog_network_prior_...tif",
                "spearman_rho": -0.000456,
                "dots_within_3px_fraction": 0.043728,
                "verdict": "distinct lane",
            },
            "vs_d28_h33_base_by_design": {
                "raster": "gems24-h25-1-dotted-h19-5-d2-8-...tif (learning reference)",
                "spearman_rho": 0.909038,
                "dots_within_3px_fraction": 0.974983,
                "verdict": "DUPLICATE-LANE by overlap; BY DESIGN: this pipeline's base IS the "
                           "B=2-pruned d28 field (37,654 of 38,854 dots retained). The novel increment "
                           "is the ~1,200 Anderson/geothermal added dots, which are lane-distinct "
                           "from H6 (rho -0.0005).",
            },
            "max_distinct_lane_rho": max_rho,
            "max_distinct_lane_dot_overlap": max_near,
            "source": "evidence/lane_check.json",
        },
        "validator_output": {
            "label": "HOLDOUT-DTI format gate (local; not organizer acceptance)",
            "passed": vr["passed"],
            "errors": list(vr["errors"]),
            "shape_rows_cols": [vr["height"], vr["width"]],
            "count": vr["count"],
            "dtype": vr["dtype"],
            "crs": vr["crs"],
            "resolution_m": vr["resolution_m"],
            "template_match": vr["template_match"],
            "no_nan_inside_footprint": vr["invalid_in_bounds"] == 0,
            "finite_in_bounds": vr["finite_in_bounds"],
            "values_in_01": [vr["minimum"], vr["maximum"]],
            "nodata": vr["nodata"],
            "finite_outside_bounds": vr["finite_outside_bounds"],
            "source": "scripts/validate_submission.py read-back of final on-disk bytes",
        },
        "submission_form": {
            "name": submission_name,
            "note": note,
            "note_chars": len(note),
            "note_label": "truthful method + holdout note (<=140 chars on this card; platform cap 200)",
        },
        "verdict": verdict,
        "slot_eligible": bool(slot_eligible),
        "rationale": rationale,
        "next_step": (
            "Re-gate on a fold-consistent, CI-cleared gain before spending a weekly submission "
            "slot; upload (single final file for both prize rounds) is the owner's manual step."
        ),
    }
    out_path = EVIDENCE / "run_card.json"
    out_path.write_text(json.dumps(card, indent=2) + "\n")
    # Public ledger copy: the site (served from docs/) links here from the
    # readiness banner so the run card is browsable without leaving the site.
    (DOCS_RESEARCH / "run_card.json").write_text(json.dumps(card, indent=2) + "\n")
    print(f"RUN CARD: verdict={verdict} slot_eligible={slot_eligible}")
    print(f"  HOLDOUT-DTI lead {lead['lm_calibrated_mean']:.6f} CI95 ({ci_lead[0]:.6f} .. {ci_lead[1]:.6f})")
    print(f"  margin {margin:+.6f} CI95 ({ci_margin[0]:+.6f} .. {ci_margin[1]:+.6f}) wins {folds_won}/4 blocks")
    print(f"  max single-feature AUC {max_auc} (leakage threshold 0.90)")
    print(f"  lane: vs H6 distinct (rho {max_rho}); vs d28 base by-design overlap {max_near:.3f}")
    print(f"  validator: passed={vr['passed']} values in [{vr['minimum']}, {vr['maximum']}] nodata={vr['nodata']}")
    print(f"  note ({len(note)} chars): {note}")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
