#!/usr/bin/env python3
"""Hypothesis N2 — hydrothermal alteration x thermal-probe blind-conduit halo.

Lane: single-method experiment under the Parallel-Run Protocol.
  Hypothesis: concealed faults in this extensional province bleed heat upward
  along blind conduits. Hydrothermal alteration (magnetite-destruction RTP
  trough on band 02_rtp; GeoDAWN radiometric K/Th ratio) should concentrate
  DTI credit inside the anomaly halo of INGENIOUS 2 m temperature-probe
  stations (F2mDAB > 0, UTM_E/UTM_N in the station table) where no continuous
  scarp exists and the USGS/INGENIOUS catalogue is silent.
  Difference from the repo: no existing arm multiplies a radiometric/RTP
  alteration surface by a probe-proximity halo; H36-B uses GDR thermal springs,
  not the INGENIOUS 2 m network.
  Named non-fault mimic: shallow groundwater-driven near-surface temperature
  anomalies and alluvial-fan moisture also warm 2 m probes; the off-catalogue
  eligibility (d_cat > 2 px collar), 300 m kernel DTI and catalogue masking
  are the controls.

Holdout (hide-and-recover): whole 8-connected fault segments withheld
(buffer 30 px / 3 km), features derived from visible faults only, visible
faults masked pixel-exactly, pooled DTI alpha 0.2 / beta 0.8, 300 m
triangular kernel, 4 folds x 4 spatial cells, bootstrap 2000 over cells.
Leakage canary: two-polarity rank AUC of the N2 surface vs catalogue truth
must be <= 0.90.
Outputs a JSON run card; does NOT touch a submission slot.
"""

from __future__ import annotations

import json
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import rasterio  # noqa: E402 (template transform)
from gemsdoe36.atvr_features import build_or_load_static_feature_cache
from gemsdoe36.metric import distance_weighted_tversky
from gemsdoe36.paths import data_dir, work_dir
from gemsdoe36.protocol import (
    EVALUATOR_VERSION,
    feature_canary,
    pooled_holdout,
    registry_check,
)

TOTAL_DOT_BUDGET = 37_654
COLLAR_PX = 2.0
BUFFER_PX = 30
N_FOLDS = 4
BOOTSTRAP = 2000
SEED = 36
PROBE_SIGMA_PX = 10.0  # ~1 km conduit-halo smoothing


def _sha256_file(p: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _parse_probe_dbf(dbf: Path) -> dict[str, np.ndarray]:
    """Read OBJECTID, UTM_E, UTM_N, F2mDAB from an ESRI dBASE III file."""
    with dbf.open("rb") as fh:
        hdr = fh.read(32)
        nrec = struct.unpack("<l", hdr[4:8])[0]
        hlen = struct.unpack("<H", hdr[8:10])[0]
        fh.seek(32)
        fields = []
        while True:
            desc = fh.read(32)
            if desc[0] == 0x0D:
                break
            name = desc[:11].split(b"\x00")[0].decode("ascii", "ignore")
            size = desc[16]
            fields.append((name, size))
        wanted = {"OBJECTID", "UTM_E", "UTM_N", "F2mDAB"}
        offsets = {}
        off = 1  # 1-byte deletion flag leads each record
        for name, size in fields:
            if name in wanted and name not in offsets:
                offsets[name] = off
            off += size
        if not {"UTM_E", "UTM_N", "F2mDAB"} <= set(offsets):
            raise RuntimeError(f"Probe DBF missing expected fields: {list(offsets)}")
        rec_len = off
        fh.seek(hlen)
        ids, e, n, f2m = [], [], [], []
        for _ in range(nrec):
            rec = fh.read(rec_len)
            if len(rec) < rec_len:
                break

            def num(field: str) -> str:
                return rec[offsets[field] : offsets[field] + {
                    "OBJECTID": 10, "UTM_E": 10, "UTM_N": 10, "F2mDAB": 19,
                }[field]].decode("ascii", "ignore").strip()

            try:
                ids.append(int(num("OBJECTID")))
                e.append(float(num("UTM_E")))
                n.append(float(num("UTM_N")))
            except ValueError:
                continue
            raw = num("F2mDAB")
            f2m.append(float(raw) if raw and raw not in ("*", "N/A") else np.nan)
    return {
        "id": np.asarray(ids, dtype=np.int64),
        "e": np.asarray(e, dtype=np.float64),
        "n": np.asarray(n, dtype=np.float64),
        "f2m": np.asarray(f2m, dtype=np.float64),
    }


def _probe_halo(probe: dict[str, np.ndarray], shape, transform, foot: np.ndarray):
    """Nadaraya-Watson anomaly halo of INGENIOUS 2 m probes on the template grid."""
    a = transform.a  # easting per column (+100 m)
    f = transform.e  # northing per row (-100 m)
    x0, y0 = transform.c, transform.f
    rows = np.rint((y0 - probe["n"]) / (-f)).astype(np.int64)
    cols = np.rint((probe["e"] - x0) / a).astype(np.int64)
    in_grid = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    safe_r = np.clip(rows, 0, shape[0] - 1)
    safe_c = np.clip(cols, 0, shape[1] - 1)
    valid = in_grid & foot[safe_r, safe_c]
    w = np.clip(probe["f2m"], 0.0, None)  # warm anomalies only
    w = np.where(np.isfinite(w) & valid, w, 0.0)
    v_ok = valid & np.isfinite(probe["f2m"]) & (probe["f2m"] > 0)
    print(f"[n2] probes total={len(probe['id'])} mapped_inside_footprint={int(valid.sum())} "
          f"anomalous_warm={int(v_ok.sum())}")
    if not v_ok.any():
        return np.zeros(shape, dtype=np.float32), np.zeros(shape, dtype=bool)
    weights = np.zeros(shape, dtype=np.float64)
    counts = np.zeros(shape, dtype=np.float64)
    np.add.at(weights, (rows[v_ok], cols[v_ok]), w[v_ok])
    np.add.at(counts, (rows[v_ok], cols[v_ok]), 1.0)
    weights_s = gaussian_filter(weights, sigma=PROBE_SIGMA_PX, mode="nearest")
    counts_s = gaussian_filter(counts, sigma=PROBE_SIGMA_PX, mode="nearest")
    halo = weights_s / (counts_s + 1e-9)
    halo = np.nan_to_num(halo, nan=0.0, posinf=0.0, neginf=0.0)
    return halo.astype(np.float32), v_ok


def _grid(rows, cols, values, shape):
    g = np.zeros(shape, dtype=np.float32)
    g[rows, cols] = values
    return g


def _top_k_mask(score2d, elig2d, budget):
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


def _allocate_budgets(elig_masks, total):
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
    mm = cache.open_matrix()
    name_to_col = {name: i for i, name in enumerate(cache.feature_names)}
    for want in ("h36b_rtp_trough_2_15", "h36b_geodawn_k_th_ratio"):
        if want not in name_to_col:
            raise RuntimeError(f"Missing cache feature {want}")

    # --- template grid for probe mapping --------------------------------
    tmpl = ROOT / "data" / "raw" / "sample_submission.tif"
    with rasterio.open(tmpl) as src:
        transform = src.transform
        print(f"[n2] template {src.shape} crs={src.crs} transform={transform}")

    # --- surfaces --------------------------------------------------------
    bands_dir = work_dir() / "bands"
    det_slope = np.load(bands_dir / "19_det_elev_slope.npy").astype(np.float32)
    det_slope[~foot] = 0.0

    rtp = np.zeros(foot.shape, dtype=np.float32)
    kth = np.zeros(foot.shape, dtype=np.float32)
    rtp[cache.foot_rows, cache.foot_cols] = mm[:, name_to_col["h36b_rtp_trough_2_15"]]
    kth[cache.foot_rows, cache.foot_cols] = mm[:, name_to_col["h36b_geodawn_k_th_ratio"]]
    hydro = np.clip(rtp, 0, None) * np.clip(kth, 0, None)
    del rtp, kth

    ext_root = data_dir() / "external"
    probe_dir = ext_root / "2m_temperature_probe_INGENIOUS_regional_data"
    dbf = probe_dir / "2m_temperature_probe_n83geo" / "2m_temperature_probe_n83geo.dbf"
    zip_path = ext_root / "2m_temperature_probe_INGENIOUS_regional_data.zip"
    if not dbf.is_file():
        if not zip_path.is_file():
            raise FileNotFoundError(f"Probe archive not found: {zip_path}")
        import zipfile

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(ext_root)
        if not dbf.is_file():
            raise FileNotFoundError(f"Extraction did not yield {dbf}")
    probe = _parse_probe_dbf(dbf)
    halo, probe_mask = _probe_halo(probe, foot.shape, transform, foot)
    del probe

    n2 = _robust01(hydro, foot) * (0.25 + 0.75 * _robust01(halo, foot))
    n2 = np.where(foot, n2, 0.0).astype(np.float32)
    base = _robust01(det_slope, foot)
    del hydro, halo, det_slope

    # --- holdout plan (identical design to N1 / ATVR-36 lane) ------------
    sys.path.insert(0, str(ROOT / "scripts"))
    import evaluate_holdout as _eh  # noqa: E402 (import-only, locked plan builder)

    plan = _eh.build_whole_segment_holdout_plan(truth, foot, buffer_px=BUFFER_PX)
    print(
        f"[n2] holdout plan: {plan.n_segments:,} segments, {int(plan.truth.sum()):,} "
        f"positive px, {plan.n_folds} folds / 16 cells"
    )

    d_known = distance_transform_edt(~truth).astype(np.float32)

    def run_arm(surface2d, arm_name):
        dots = np.zeros(foot.shape, dtype=bool)
        elig_masks = []
        for k in range(plan.n_folds):
            vis_k = plan.visible_by_fold[k]
            dvis_k = distance_transform_edt(~vis_k).astype(np.float32)
            ev_k = plan.eval_mask_by_fold[k]
            elig_masks.append(ev_k & (dvis_k > COLLAR_PX))
        budgets = _allocate_budgets(elig_masks, TOTAL_DOT_BUDGET)
        for k in range(plan.n_folds):
            elig_k = elig_masks[k]
            q_mask = (plan.fold_owner == k) & foot
            rc = np.argwhere(elig_k)
            vals = surface2d[rc[:, 0], rc[:, 1]]
            budget = budgets[k]
            if len(vals) <= budget:
                pick = rc
            else:
                order = np.argpartition(-vals, budget - 1)[:budget]
                pick = rc[order]
            dots[pick[:, 0], pick[:, 1]] = True
        per_cell = []
        for k in range(plan.n_folds):
            ev_k = plan.eval_mask_by_fold[k]
            per_cell.append((dots.astype(np.float32), plan.hidden_by_fold[k], ev_k))
        res = pooled_holdout(per_cell, bootstrap=BOOTSTRAP, seed=SEED)
        unsplit = distance_weighted_tversky(
            dots.astype(np.float32),
            plan.truth.astype(np.float32),
            valid_mask=foot,
            return_components=True,
        )
        return {
            "arm": arm_name,
            "dots_emitted": int(dots.sum()),
            "dots_on_catalogue": int((dots & truth).sum()),
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
    for arm_name, surface in (("BASELINE_det_elev_slope", base), ("N2_hydrothermal_x_probe_halo", n2)):
        t_arm = time.time()
        r = run_arm(surface, arm_name)
        r["elapsed_sec"] = round(time.time() - t_arm, 1)
        results.append(r)
        print(
            f"[n2] {arm_name}: dots={r['dots_emitted']:,} on-cat={r['dots_on_catalogue']} "
            f"HOLDOUT-DTI={r['pooled_16block_dti']:.4f} "
            f"CI95=[{r['pooled_16block_ci95'][0]:.4f}, {r['pooled_16block_ci95'][1]:.4f}] "
            f"unsplit={r['unsplit_pooled_dti']:.4f} ({r['elapsed_sec']}s)"
        )

    # --- leakage canary --------------------------------------------------
    canary = feature_canary(n2, truth, foot)
    print(
        f"[n2] leakage canary: AUC={canary['auc']:.4f} two-polarity={canary['two_polarity_auc']:.4f} "
        f"passed={canary['passed']}"
    )

    # --- comparison ------------------------------------------------------
    cand = results[1]
    base_r = results[0]
    delta = cand["pooled_16block_dti"] - base_r["pooled_16block_dti"]
    print(f"[n2] N2 - BASELINE = {delta:+.4f} HOLDOUT-DTI; vs KPL-36 EXP-3 0.1701: "
          f"{cand['pooled_16block_dti'] - 0.1701:+.4f}")

    card = {
        "schema": "gemsdoe36.hypothesis-n2.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "GEMSDOE36",
        "hypothesis_id": "N2",
        "hypothesis": (
            "Hydrothermal alteration (RTP magnetite-destruction trough x GeoDAWN K/Th "
            "radiometric ratio) modulated by the INGENIOUS 2 m temperature-probe "
            "blind-conduit halo (F2mDAB warm-anomaly kernel density) as an "
            "off-catalogue concealed-fault prior."
        ),
        "layers": ["02_rtp", "geodawn_rad_u8 (K/Th)", "INGENIOUS 2 m probe F2mDAB"],
        "physical_signature": (
            "Hydrothermal alteration concentrated within ~1 km kernel halo of warm "
            "2 m temperature probes, at concealed faults with no mapped scarp."
        ),
        "why_off_catalogue": (
            "INGENIOUS 2 m probe anomalies with no catalogue fault and no continuous "
            "surface scarp are blind conduits; dots on them are off-catalogue mass."
        ),
        "differs_from_repo": (
            "No repo arm multiplies alteration by a temperature-probe halo; H36-B uses "
            "GDR thermal-spring IDW, not the INGENIOUS 2 m network (n=3800 stations)."
        ),
        "named_non_fault_mimic": (
            "Shallow groundwater/near-surface moisture warming 2 m probes, and "
            "alluvial-fan evaporative anomalies; controlled by d_cat > 2 px off-"
            "catalogue eligibility, 300 m kernel DTI and catalogue masking."
        ),
        "implementation_cost": "low — deterministic transforms, no training",
        "probe_source": str(dbf),
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
        "delta_n2_vs_baseline": round(float(delta), 6),
        "delta_n2_vs_kpl36_exp3": round(float(cand["pooled_16block_dti"] - 0.1701), 6),
        "raster_sha256_pending": True,
        "total_runtime_sec": round(time.time() - t0, 1),
    }
    out_path = ROOT / "evidence" / "n2_holdout_run_card.json"
    out_path.write_text(json.dumps(card, indent=2) + "\n")
    print(f"[n2] card written -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
