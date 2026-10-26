#!/usr/bin/env python3
"""BDC-36: basement-depth contour × dilatation ridges (≤3 holdout experiments)."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.holdout import MTR_EVALUATOR_VERSION, SegmentHoldout  # noqa: E402
from gems.metric import ridge_nms, select_top_positive  # noqa: E402
from gems.novelty import correlation, dot_overlap, is_duplicate  # noqa: E402
from gems.submission import check_variants, write_submission, zip_single  # noqa: E402
from gemsdoe36.protocol import feature_canary  # noqa: E402

BUDGET = 18_000
SEED = 20261026
COLLAR = 2.0
LANE = "BDC-36"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_grid():
    raw = ROOT / "data" / "raw"
    with rasterio.open(raw / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
        profile_template = raw / "sample_submission.tif"
    with rasterio.open(raw / "labels.tif") as ds:
        labels = footprint & np.isfinite(ds.read(1)) & (ds.read(1) > 0.5)
    with rasterio.open(raw / "training_features.tif") as ds:
        depth = ds.read(15).astype(np.float32)
        dil = ds.read(8).astype(np.float32)
        gvg = ds.read(11).astype(np.float32)
        nodata = ds.nodata
    for arr in (depth, dil, gvg):
        bad = ~np.isfinite(arr)
        if nodata is not None:
            bad |= arr == nodata
        bad |= arr < -1e30
        arr[bad] = np.nan
    return footprint, labels, depth, dil, gvg, profile_template


def pct_rank(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    out = np.zeros(arr.shape, dtype=np.float32)
    m = foot & np.isfinite(arr)
    if not m.any():
        return out
    out[m] = (rankdata(arr[m], method="average") / m.sum()).astype(np.float32)
    return out


def grad_mag(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    filled = np.where(np.isfinite(arr), arr, 0.0)
    sm = gaussian_filter(filled, 1.0, mode="nearest")
    gy, gx = np.gradient(sm)
    mag = np.hypot(gy, gx).astype(np.float32)
    mag[~foot] = np.nan
    mag[~np.isfinite(arr)] = np.nan
    return mag


def emit(surface: np.ndarray, eligible: np.ndarray, k: int) -> np.ndarray:
    ridge = ridge_nms(surface, eligible, sigma=1.0)
    boosted = np.where(ridge, surface, 0.0)
    return select_top_positive(boosted, eligible, k)


def registry_paths():
    scored = ROOT / "data" / "raw" / "scored"
    paths = sorted(scored.glob("*.tif")) if scored.is_dir() else []
    dl = ROOT / "docs" / "downloads"
    for p in dl.glob("*.tif"):
        if "FORMAT_TEST" in p.name:
            continue
        paths.append(p)
    return paths


def uniqueness_audit(surface, dots, footprint):
    rows = []
    worst_rho, worst_ov = 0.0, 0.0
    worst_name = None
    fp = footprint
    for path in registry_paths():
        with rasterio.open(path) as ds:
            if ds.shape != footprint.shape:
                continue
            ref = ds.read(1)
        ref_f = np.where(fp & np.isfinite(ref), ref, 0.0)
        rho = correlation(surface[fp], ref_f[fp])
        ov = None
        if dots is not None:
            ref_d = fp & np.isfinite(ref) & (ref > 0.5)
            ov = dot_overlap(dots, ref_d)["candidate_within_3px_of_reference"]
        dup = is_duplicate(rho, ov)
        abs_rho = abs(rho) if rho is not None else 0.0
        ov_v = ov if ov is not None else 0.0
        if abs_rho > worst_rho or ov_v > worst_ov:
            if abs_rho > worst_rho:
                worst_rho = abs_rho
            if ov_v > worst_ov:
                worst_ov = ov_v
                worst_name = path.name
        rows.append(
            {
                "name": path.name,
                "rho": rho,
                "overlap": ov,
                "duplicate": dup,
            }
        )
    any_dup = any(r["duplicate"] for r in rows)
    return {
        "any_duplicate": any_dup,
        "worst_abs_rho": worst_rho,
        "worst_overlap": worst_ov,
        "worst_overlap_name": worst_name,
        "n_compared": len(rows),
        "rows": rows,
    }


def main() -> int:
    t0 = time.time()
    foot, labels, depth, dil, gvg, template = load_grid()
    gz = grad_mag(depth, foot)
    r_gz = pct_rank(gz, foot)
    r_dil = pct_rank(np.where(np.isfinite(dil), np.maximum(dil, 0.0), np.nan), foot)
    r_gvg = pct_rank(np.abs(gvg), foot)
    s1 = r_gz
    s2 = r_dil
    s3 = np.power(np.clip(r_gz * r_dil * r_gvg, 0, 1), 1.0 / 3.0).astype(np.float32)

    hold = SegmentHoldout(foot, labels, buffer_px=15)
    # Leakage canaries on pooled hidden vs score_mask using fold 0 geometry
    f0 = hold.folds[0]
    canaries = {}
    for name, feat in (("grad_z", gz), ("dil_pos", dil), ("grav_vg", gvg), ("s3", s3)):
        x = np.where(np.isfinite(feat), feat, 0.0)
        score_mask = f0["valid"]
        hidden = f0["truth"]
        canaries[name] = feature_canary(x, hidden, score_mask)
        if not canaries[name]["passed"]:
            raise SystemExit(f"LEAKAGE CANARY FAIL {name}: {canaries[name]}")

    experiments = {"EXP-1": s1, "EXP-2": s2, "EXP-3": s3}
    results = {}
    fold_preds = {}
    for eid, surf in experiments.items():
        preds = []
        for fold in hold.folds:
            vis = fold["visible"]
            dvis = distance_transform_edt(~vis)
            elig = fold["valid"] & (dvis > COLLAR) & np.isfinite(surf)
            k = int(round(BUDGET * fold["valid"].sum() / foot.sum()))
            pred = emit(surf, elig, k)
            preds.append(pred.astype(np.uint8))
        summary = hold.summarize(preds)
        fold_preds[eid] = preds
        ci = summary["ci95"]["interval"]
        results[eid] = {
            "holdout_dti": float(summary["dti"]),
            "ci95": [float(ci[0]), float(ci[1])],
            "evaluator_version": summary["evaluator_version"],
            "withheld_positives": int(summary["n_withheld_positive_pixels"]),
            "folds": summary["folds"],
        }
        print(eid, summary["dti"], ci)

    best_id = max(results, key=lambda k: results[k]["holdout_dti"])
    best_s = experiments[best_id]
    dvis_full = distance_transform_edt(~labels)
    elig_full = foot & (dvis_full > COLLAR)
    dots = emit(best_s, elig_full, BUDGET)
    uniq = uniqueness_audit(best_s, dots, foot)

    out_stem = f"gemsdoe36-bdc36-{best_id.lower()}-20261026-{BUDGET}dots"
    tif = ROOT / "docs" / "downloads" / f"{out_stem}-zeros.tif"
    write_submission(dots.astype(np.float32), template, tif, outside="zero")
    checks = check_variants(tif, template)
    zpath = zip_single(tif)
    tif_sha = sha256_file(tif)

    verdict = "negative"
    ok = False
    if (
        not uniq["any_duplicate"]
        and results[best_id]["ci95"][0] > 0.10
        and checks.get("format_valid")
    ):
        verdict = "promote"
        ok = True
    # uniqueness failure or weak holdout stays negative; file still published as research

    note = (
        f"BDC-36 {best_id} basement-step x dilatation | HOLDOUT-DTI "
        f"{results[best_id]['holdout_dti']:.4f} | {verdict} | {BUDGET} dots"
    )[:140]

    card = {
        "hypothesis": "Unmapped B&R faults sit on basement-depth steps under positive dilatation.",
        "mechanism": "Percentile ranks of |grad depth_to_base|, max(dilatation,0), |gravity VG|; geometric-mean EXP-3.",
        "named_non_fault_mimic": "Lithologic basement contact or basin-fill thickness jump without a through-going fault.",
        "holdout_dti": results[best_id]["holdout_dti"],
        "holdout_ci95": results[best_id]["ci95"],
        "evaluator_version": results[best_id]["evaluator_version"],
        "withheld_positives": results[best_id]["withheld_positives"],
        "label": "HOLDOUT-DTI",
        "correlation_overlap_vs_registry": {
            "worst_abs_rho": uniq["worst_abs_rho"],
            "worst_overlap": uniq["worst_overlap"],
            "worst_overlap_name": uniq["worst_overlap_name"],
            "any_duplicate": uniq["any_duplicate"],
            "n_compared": uniq["n_compared"],
        },
        "raster_sha256": tif_sha,
        "validator": checks,
        "submission_name": tif.name,
        "note": note,
        "verdict": verdict,
        "ok_to_download_and_submit": ok,
        "slot_approved": False,
        "lane_id": LANE,
        "best_experiment": best_id,
        "experiments": results,
        "canaries": canaries,
        "budget_dots": BUDGET,
        "wall_s": time.time() - t0,
        "utc": datetime.now(timezone.utc).isoformat(),
        "evaluator_pin": MTR_EVALUATOR_VERSION,
        "zip": str(zpath.name),
    }
    def _dump(obj) -> str:
        return json.dumps(obj, indent=2, default=float) + "\n"

    (ROOT / "evidence" / "bdc36_run_card_20261026.json").write_text(_dump(card))
    (ROOT / "docs" / "downloads" / "bdc36-run-card.json").write_text(_dump(card))
    (ROOT / "evidence" / "bdc36_uniqueness_20261026.json").write_text(
        json.dumps({k: uniq[k] for k in uniq if k != "rows"}, indent=2) + "\n"
    )
    print(json.dumps({k: card[k] for k in ("verdict", "holdout_dti", "ok_to_download_and_submit", "raster_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
