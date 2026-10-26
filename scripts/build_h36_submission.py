#!/usr/bin/env python3
"""Build the unique H36-GPS GeoTIFF, run every fail-closed gate, and write the JSON run card.

Gates (knowledge/h36_preregistration_2026-10-25.md):
  1. holdout: candidate beats the matched baseline (paired CI > 0, >= 3/4 folds)
  2. holdout: candidate beats max(baseline, recorded group best 0.14876)
  3. leakage canary: no single-feature AUC > 0.90 (two polarities)
  4. uniqueness: surface AND final dots vs every registry raster (template gems.novelty)
  5. format: template check_variants format_valid + strict whole-array [0, 1] (zeros outside)
Verdict PROMOTE only if all pass; otherwise NEGATIVE (download for research; DO NOT SUBMIT).
A PROMOTE verdict still does not spend a slot: selection is a separate step.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.novelty import compare_registry  # noqa: E402  (shared template)
from gems.submission import check_variants, scored_content_id, write_submission, zip_single  # noqa: E402
from gemsdoe36.h36_emission import emit_dots  # noqa: E402
from gemsdoe36.h36_features import LANE_FEATURES, build_feature_stack  # noqa: E402

SEED = 20261025
BUDGET = 37654
ANNULUS_PX = 3  # H36-ANNULUS live-evidence rule: no dot within 300 m of the full catalogue
NOTE_LIMIT = 140
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
EXPERIMENTS = ROOT / "evidence/h36_holdout_experiments.json"
DOWNLOADS = ROOT / "docs/downloads"
HGB = dict(max_iter=250, learning_rate=0.06, max_leaf_nodes=48, min_samples_leaf=200,
           l2_regularization=1.0, early_stopping=False, random_state=SEED)


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    t0 = time.time()
    exp = json.loads(EXPERIMENTS.read_text())
    store, grid = build_feature_stack(ROOT / ".cache" / "h36")
    fp, labels = grid.footprint, grid.labels
    H, W = fp.shape
    names = store.names  # candidate arm C1 = base + lane features (the declared lane)
    lane = [n for n in names if n in LANE_FEATURES]
    assert lane, "lane features missing"
    fp_flat = np.flatnonzero(fp.ravel())
    fp_pos = np.full(H * W, -1, np.int64)
    fp_pos[fp_flat] = np.arange(store.n_fp)

    # ---- final full-map model (all catalogue; no holdout numbers are computed here) ----
    from sklearn.ensemble import HistGradientBoostingClassifier

    rng = np.random.default_rng(SEED)
    dcat = distance_transform_edt(~labels)
    pos = np.flatnonzero(labels.ravel())
    neg = np.flatnonzero((fp & (dcat > 3)).ravel())
    pos = rng.choice(pos, min(50000, len(pos)), replace=False)
    neg = rng.choice(neg, min(300000, len(neg)), replace=False)
    X = store.rows(np.r_[fp_pos[pos], fp_pos[neg]], names)
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    model = HistGradientBoostingClassifier(**HGB).fit(X, y)
    del X
    surface = np.zeros(H * W, np.float32)
    for s in range(0, len(fp_flat), 400000):
        chunk = fp_flat[s : s + 400000]
        surface[chunk] = model.predict_proba(store.rows(fp_pos[chunk], names))[:, 1]
    surface = surface.reshape(H, W)
    print(f"surface built {time.time() - t0:.0f}s", flush=True)

    reg = json.loads((ROOT / "registry/uniqueness_registry.json").read_text())["entries"]
    surf_check = compare_registry(surface, fp, reg, ROOT, separate_calibration_controls=True)
    print(f"surface check passed={surf_check['passed']} max|rho|={surf_check['max_abs_rank_correlation']}", flush=True)

    eligible = fp & (dcat > ANNULUS_PX)
    dots = emit_dots(surface, eligible, BUDGET, support=fp)
    dot_check = compare_registry(surface, fp, reg, ROOT, dots=dots, separate_calibration_controls=True)
    print(f"dot check passed={dot_check['passed']} competing={dot_check.get('competing_method_passed')} max overlap={dot_check.get('max_competing_dot_overlap')}", flush=True)

    pred = np.where(fp, dots.astype(np.float32), 0.0).astype(np.float32)
    cid = scored_content_id(pred, fp, labels)
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    stem = f"gemsdoe36-h36-gps-graben-pair-{date}-{cid}"
    tif_zero = write_submission(pred, TEMPLATE, DOWNLOADS / f"{stem}-zeros.tif", outside="zero")
    tif_nan = write_submission(pred, TEMPLATE, DOWNLOADS / f"{stem}-nan.tif", outside="nan")
    zip_p = zip_single(tif_zero, DOWNLOADS / f"{stem}-zeros.zip")
    v_zero = check_variants(tif_zero, TEMPLATE)
    v_nan = check_variants(tif_nan, TEMPLATE)
    with rasterio.open(tif_zero) as s:
        a = s.read(1)
    strict = bool(np.isfinite(a).all() and ((a >= 0) & (a <= 1)).all())
    nan_inside = int((~np.isfinite(a[fp])).sum())

    # ---- gates ----
    e1 = exp.get("E1", {})
    paired = e1.get("paired_C1_minus_B0", {})
    c1 = e1.get("C1", {}).get("dti")
    b0 = e1.get("B0", {}).get("dti")
    group_best = exp["recorded_group_best"]["value"]
    gates = {
        "G1_beats_matched_baseline": bool(paired.get("ci95_strictly_positive") and paired.get("fold_wins", 0) >= 3),
        "G2_beats_current_holdout_best": bool(c1 is not None and b0 is not None and c1 > max(b0, group_best)),
        "G3_leakage_canary": bool(exp.get("canary", {}).get("passed", False)),
        "G4a_unique_surface": bool(surf_check["passed"]),
        "G4b_unique_final_dots": bool(dot_check["passed"]),
        "G5_format_and_strict_range": bool(v_zero["format_valid"] and strict and nan_inside == 0),
    }
    promote = all(gates.values())
    verdict = "promote" if promote else "negative"
    status = "OK_TO_SUBMIT_AFTER_SELECTOR" if promote else "DO_NOT_SUBMIT"
    c1_ci = e1.get("C1", {}).get("ci95", {}).get("interval") or [float("nan"), float("nan")]
    n_pos = e1.get("C1", {}).get("n_withheld_positive_pixels")
    hd = (f"HOLDOUT-DTI {c1:.4f} [{c1_ci[0]:.4f},{c1_ci[1]:.4f}] seg-pooled-v1 {n_pos}pos"
          if c1 is not None else "no holdout")
    note = f"GEMSDOE36 H36-GPS graben-pair | {hd} | {'PROMOTE' if promote else 'NEGATIVE'} | id {cid}"
    if len(note) > NOTE_LIMIT:  # fail closed rather than truncate a label
        raise SystemExit(f"note is {len(note)} > {NOTE_LIMIT} characters")
    sub_name = f"{stem}-zeros"

    def slim(check):
        rows = sorted(check["rows"], key=lambda r: -(r.get("candidate_dot_overlap_within_3px") or 0))
        return {k: v for k, v in check.items() if k != "rows"} | {
            "top_overlap_rows": rows[:10],
            "top_rank_rows": sorted(check["rows"], key=lambda r: -max(abs(r.get("raw_spearman") or 0), abs(r.get("kernel_spearman") or 0)))[:5],
        }

    card = {
        "run_card_version": "gemsdoe36-h36-v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "lane": "H36-GPS: LiDAR scarp-polarity / graben-pair corroboration inside a fold-safe multi-sensor field",
        "hypothesis": "Off-catalogue faults visible to NLR/USGS experts on 1 m LiDAR include small grabens and antithetic scarps; conjugate (synthetic + antithetic) scarp pairs offset along the regional slope and strike-coherent 1.5 km scarp integrals add fault-specific evidence to a multi-sensor field.",
        "mechanism": "Normal faulting on piedmonts produces facing-opposed scarps (graben/horst margins) that are long and straight across drainages; the lane features encode that geometry from the 1 m LiDAR scarp product and organizer det_elev regional slope; an out-of-fold HistGradientBoosting model learns their weight jointly with 59 label-free base features; dots are emitted on ridge centre-lines at >= 3 px spacing outside a 300 m catalogue annulus.",
        "non_fault_mimic": "Pleistocene Lake Lahontan beach ridges / barrier bars (paired facing slopes along contours), plus fan-head trenches, road and canal embankments, landslide head-scarp/toe pairs.",
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": e1.get("C1", {}).get("evaluator_version"),
            "withheld_positive_pixels": e1.get("C1", {}).get("n_withheld_positive_pixels"),
            "candidate_C1": {"dti": c1, "ci95": e1.get("C1", {}).get("ci95", {}).get("interval")},
            "baseline_B0": {"dti": b0, "ci95": e1.get("B0", {}).get("ci95", {}).get("interval")},
            "paired_C1_minus_B0": {k: paired.get(k) for k in ("paired_delta_dti", "paired_delta_ci95", "fold_wins", "n_folds", "min_fold_delta")},
            "E2_physics_only": ({"dti": exp["E2"]["result"]["dti"], "ci95": exp["E2"]["result"]["ci95"]["interval"]} if "E2" in exp else None),
            "recorded_group_best_not_rerun": exp["recorded_group_best"],
        },
        "leakage_canary": {"passed": exp.get("canary", {}).get("passed"), "threshold": 0.90,
                           "max_auc_two_polarity": max((max(v["pooled_auc"], 1 - v["pooled_auc"]) for v in exp.get("canary", {}).get("features", {}).values()), default=None)},
        "registry_comparison": {"surface_before_placement": slim(surf_check), "final_dots": slim(dot_check)},
        "raster": {
            "zeros_tif": str(tif_zero.relative_to(ROOT)),
            "zeros_sha256": sha_file(tif_zero),
            "nan_tif": str(tif_nan.relative_to(ROOT)),
            "nan_sha256": sha_file(tif_nan),
            "zip": str(zip_p.relative_to(ROOT)),
            "zip_sha256": sha_file(zip_p),
            "content_id": cid,
            "dots": int(dots.sum()),
            "values": [0.0, 1.0],
            "annulus_px": ANNULUS_PX,
        },
        "validator": {
            "template_check_variants_zeros": {k: v_zero[k] for k in ("format_valid", "hard_failures", "in_footprint_positive_pixels")},
            "template_check_variants_nan": {k: v_nan[k] for k in ("format_valid", "hard_failures", "official_format_compliant")},
            "no_nan_inside_footprint": nan_inside == 0,
            "strict_whole_array_0_1_zeros_variant": strict,
            "crs_shape_transform_match": bool(v_zero["checks"]["crs_epsg_32611"]["pass"] and v_zero["checks"]["shape_matches_template"]["pass"] and v_zero["checks"]["geotransform_matches_template"]["pass"]),
        },
        "submission": {"name": sub_name, "file": tif_zero.name, "note": note, "note_chars": len(note)},
        "gates": gates,
        "verdict": verdict,
        "status": status,
        "organizer_score": None,
        "score_policy": "No ORGANIZER-CONFIRMED score exists for this file; no projection is written as a score.",
        "runtime_s": round(time.time() - t0, 1),
    }
    out = ROOT / "evidence/h36_run_card.json"
    out.write_text(json.dumps(card, indent=1, default=float) + "\n")
    (DOWNLOADS / f"{stem}-run-card.json").write_text(json.dumps(card, indent=1, default=float) + "\n")
    print(json.dumps({"verdict": verdict, "gates": gates, "name": sub_name, "note": note}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
