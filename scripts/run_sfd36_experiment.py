#!/usr/bin/env python3
"""SFD-36 lane runner: canary -> holdout -> deploy (cloned template, SFD features).

Reuses the shared template exactly: ``gems.holdout.SegmentHoldout`` (gems-segment-pooled-v1),
``run_gvsc36`` expert training / fusion / B0 control, ``gemsdoe36.submodular_emit`` CELF
emitter, ``gems.submission`` writer, ``gems.novelty.compare_registry``. New code is only the
SFD feature set and dipole-expert rank fusion for EXP-3.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_gvsc36 import (  # noqa: E402
    B0_SEED,
    GVSC_HGB,
    GVSC_N_NEG,
    GVSC_N_POS,
    GVSC_SEEDS,
    fold_budgets,
    fuse_exp3_lidar_bridge,
    load_labels,
    prentice_pyke_calibrate,
    train_predict_b0,
    train_predict_gvsc_expert,
    unfold_column,
)

from gems.holdout import SegmentHoldout  # noqa: E402
from gems.novelty import compare_registry  # noqa: E402
from gems.submission import check_variants, write_submission, zip_single  # noqa: E402
from gemsdoe36.gvsc_features import (  # noqa: E402
    EXP2_FEATURES,
    EXP3_BLIND_FEATURES,
    LIDAR_FEATURE_SET,
    build_gvsc_feature_store,
)
from gemsdoe36.h36_emission import emit_dots  # noqa: E402
from gemsdoe36.h36_features import FeatureStore  # noqa: E402
from gemsdoe36.sfd_features import SFD_FEATURES, SFD_LIDAR_FEATURES, build_sfd_features  # noqa: E402
from gemsdoe36.submission import validate_submission  # noqa: E402
from gemsdoe36.submodular_emit import emit_submodular_cover  # noqa: E402

PREREG_PATH = ROOT / "evidence" / "sfd36_preregistration_20261027.json"
EXPECTED_PREREG_SHA256 = "3aae6dceeebc2e3d702b07c3f5dd6d437f722b8767b776357fc7a410e171998a"
CACHE_DIR = ROOT / ".cache" / "gvsc36_features"
SFD_DIR = ROOT / ".cache" / "sfd36"
CANARY_OUT = ROOT / "evidence" / "sfd36_leakage_canary_20261027.json"
HOLDOUT_OUT = ROOT / "evidence" / "sfd36_holdout_experiments_20261027.json"
CROSSCHECK_OUT = ROOT / "evidence" / "sfd36_crosscheck_20261027.json"
RUN_CARD_OUT = ROOT / "evidence" / "sfd36_run_card_20261027.json"
TOTAL_BUDGET = 37_654
RECORDED_GVSC_EXP3 = 0.158855
T_START = time.time()

SFD101: tuple[str, ...] = tuple(EXP2_FEATURES) + tuple(SFD_FEATURES)
SFD_BLIND: tuple[str, ...] = tuple(
    n for n in SFD101 if n not in LIDAR_FEATURE_SET and n not in SFD_LIDAR_FEATURES
)
ARMS = ("B0", "C-GVSC", "EXP-1", "EXP-2", "EXP-3")
EXP_ARMS = ("EXP-1", "EXP-2", "EXP-3")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_prereg() -> dict:
    got = sha256_file(PREREG_PATH)
    if got != EXPECTED_PREREG_SHA256:
        raise SystemExit(f"PREREG LOCK MISMATCH {got} != {EXPECTED_PREREG_SHA256}")
    return json.loads(PREREG_PATH.read_text())


def build_combined_store(fp: np.ndarray) -> FeatureStore:
    store89, _grid, _inv = build_gvsc_feature_store(CACHE_DIR, data_dir=ROOT / "data" / "raw")
    if not all((CACHE_DIR / f"{n}.npy").exists() for n in SFD_FEATURES):
        cols = {
            name: unfold_column(store89, name, fp)
            for name in ("lid_step_max", "org_det_elev_slope", "org_det_elev", "org_rtp", "org_iso_grav_anom", "lid_valid")
        }
        t0 = time.time()
        feats = build_sfd_features(cols, fp)
        for name, arr in feats.items():
            np.save(CACHE_DIR / f"{name}.npy", np.asarray(arr[fp], dtype=np.float32))
        print(f"[sfd] built 12 SFD features in {time.time()-t0:.1f}s", flush=True)
        del cols, feats
        gc.collect()
    names = list(EXP2_FEATURES) + list(SFD_FEATURES)
    return FeatureStore(CACHE_DIR, names, store89.n_fp)


def run_canary(store: FeatureStore, holdout: SegmentHoldout, fp: np.ndarray) -> dict:
    if CANARY_OUT.exists():
        doc = json.loads(CANARY_OUT.read_text())
        print(f"[canary] loaded cached {CANARY_OUT.name} passed={doc['passed']}", flush=True)
        return doc
    feats2d = {n: unfold_column(store, n, fp) for n in SFD_FEATURES}
    rep = holdout.canary(feats2d)
    mx = 0.0
    mx_name = None
    for name, row in rep["features"].items():
        sym = max(row["pooled_auc"], 1.0 - row["pooled_auc"])
        for f in row["folds"]:
            sym = max(sym, f["auc"], 1.0 - f["auc"])
        if sym > mx:
            mx, mx_name = sym, name
    doc = {
        "lane_id": "SFD-36",
        "label": "LEAKAGE-CANARY AUC (not a score)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evaluator_version": rep["evaluator_version"],
        "threshold": 0.90,
        "passed": bool(rep["passed"] and mx <= 0.90),
        "total_features_tested": len(SFD_FEATURES),
        "max_symmetric_auc": round(float(mx), 6),
        "max_symmetric_auc_feature": mx_name,
        "note": "Only the 12 new SFD features are canaried here; the 89 reused GVSC features keep their archived canary.",
        "features": rep["features"],
    }
    CANARY_OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"[canary] passed={doc['passed']} max_sym_auc={mx:.4f} ({mx_name})", flush=True)
    return doc


def train_predict_pu_expert(store, feature_names, fp_pos, train_mask, visible_mask, eval_mask, labels, fold_idx):
    """EXP-3: spy-PU decontaminated version of train_predict_gvsc_expert (H-KPL-B)."""
    pos_pool = np.flatnonzero((labels & train_mask).ravel())
    far = distance_transform_edt(~visible_mask) > 3.0
    unlab_pool = np.flatnonzero((train_mask & ~labels & far).ravel())
    del far
    names = list(feature_names)
    rng = np.random.default_rng(909090 + 17 * fold_idx)
    spy_idx = rng.choice(pos_pool, int(round(0.15 * len(pos_pool))), replace=False)
    lab_pos = np.setdiff1d(pos_pool, spy_idx, assume_unique=False)
    unlab_samp = rng.choice(unlab_pool, min(GVSC_N_NEG, len(unlab_pool)), replace=False)
    fake_neg = np.r_[unlab_samp, spy_idx]
    idx = np.r_[fp_pos[lab_pos], fp_pos[fake_neg]]
    y = np.r_[np.ones(len(lab_pos), np.float32), np.zeros(len(fake_neg), np.float32)]
    spy_model = HistGradientBoostingClassifier(**GVSC_HGB, random_state=5150 + fold_idx)
    spy_model.fit(store.rows(idx, names), y)
    spy_scores = spy_model.predict_proba(store.rows(fp_pos[spy_idx], names))[:, 1]
    thr = float(np.quantile(spy_scores, 0.10))
    cand = rng.choice(unlab_pool, min(700_000, len(unlab_pool)), replace=False)
    cand_scores = np.empty(len(cand), np.float32)
    for s in range(0, len(cand), 350_000):
        c = cand[s : s + 350_000]
        cand_scores[s : s + len(c)] = spy_model.predict_proba(store.rows(fp_pos[c], names))[:, 1]
    del spy_model
    gc.collect()
    rn = cand[cand_scores < thr]
    rn_share = float(len(rn) / max(len(cand), 1))
    if len(rn) < 50_000:
        raise RuntimeError(f"PU reliable-negative pool too small: {len(rn)} (thr={thr:.4f})")
    eval_flat = np.flatnonzero(eval_mask.ravel())
    prob_acc = np.zeros(len(eval_flat), np.float64)
    models = []
    for m_i, base_seed in enumerate(GVSC_SEEDS):
        r = np.random.default_rng(base_seed + 777 + 17 * fold_idx + 101 * m_i)
        pos_sel = pos_pool if len(pos_pool) <= GVSC_N_POS else r.choice(pos_pool, GVSC_N_POS, replace=False)
        neg_sel = r.choice(rn, min(GVSC_N_NEG, len(rn)), replace=False)
        pi_pos = len(pos_sel) / max(len(pos_pool), 1)
        pi_neg = len(neg_sel) / max(len(unlab_pool), 1)  # population referent = full unlabelled pool
        idx2 = np.r_[fp_pos[pos_sel], fp_pos[neg_sel]]
        y2 = np.r_[np.ones(len(pos_sel), np.float32), np.zeros(len(neg_sel), np.float32)]
        clf = HistGradientBoostingClassifier(**GVSC_HGB, random_state=base_seed + 31 * fold_idx + m_i)
        clf.fit(store.rows(idx2, names), y2)
        models.append((clf, pi_pos, pi_neg))
        gc.collect()
    for s in range(0, len(eval_flat), 450_000):
        chunk = eval_flat[s : s + 450_000]
        Xc = store.rows(fp_pos[chunk], names)
        for clf, pi_pos, pi_neg in models:
            q = clf.predict_proba(Xc)[:, 1].astype(np.float32)
            prob_acc[s : s + len(chunk)] += prentice_pyke_calibrate(q, pi_pos=pi_pos, pi_neg=pi_neg)
        del Xc
    del models
    gc.collect()
    out = np.zeros(eval_mask.size, np.float32)
    out[eval_flat] = (prob_acc / len(GVSC_SEEDS)).astype(np.float32)
    return out.reshape(eval_mask.shape), {
        "pu_spies": int(len(spy_idx)),
        "pu_threshold_spy_q10": round(thr, 6),
        "pu_reliable_negative_pool": int(len(rn)),
        "pu_reliable_negative_share_of_scored_unlabelled": round(rn_share, 4),
        "n_pos_pool": int(len(pos_pool)),
        "n_unlab_pool": int(len(unlab_pool)),
    }


def _rank01(a, mask):
    out = np.zeros(a.shape, np.float32)
    v = a[mask].astype(np.float64)
    order = np.argsort(v, kind="mergesort")
    r = np.empty(len(v), np.float64)
    r[order] = np.arange(len(v))
    out[mask] = (r / max(len(v) - 1, 1)).astype(np.float32)
    return out

def rank_fuse_surface(p_full, p_dip, valid, lid_valid_2d, det_slope_2d, p_blind):
    # EXP-2-equivalent bridge surface is recomputed by caller via oof; here p_full is full expert.
    # Bridge first (same frozen fusion as EXP-2), then 0.7/0.3 rank fusion with dipole expert.
    bridged = fuse_exp3_lidar_bridge(p_full, p_blind, lid_valid_2d, det_slope_2d, valid)
    return (0.7 * _rank01(bridged, valid) + 0.3 * _rank01(p_dip, valid)).astype(np.float32)

def _emit_celf(surf, elig, valid, budget):
    cov = emit_submodular_cover(surf, elig, budget=budget, valid_footprint=valid, gamma=1.0, min_spacing_px=2.0)
    return cov.mask, float(cov.objective_value)


def run_holdout(store, holdout, fp, labels) -> dict:
    SFD_DIR.mkdir(parents=True, exist_ok=True)
    h, w = fp.shape
    fp_pos = np.full(h * w, -1, dtype=np.int64)
    fp_pos[np.flatnonzero(fp.ravel())] = np.arange(store.n_fp)
    budgets = fold_budgets(holdout)
    lid_valid_2d = unfold_column(store, "lid_valid", fp)
    det_slope_2d = unfold_column(store, "org_det_elev_slope", fp)
    preds: dict[str, list[np.ndarray]] = {a: [] for a in ARMS}
    oof: dict[str, np.ndarray] = {a: np.zeros((h, w), np.float32) for a in EXP_ARMS + ("C-GVSC",)}
    fold_logs = []
    for f_i, fold in enumerate(holdout.folds):
        ck_npz = SFD_DIR / f"holdout_fold_{f_i}.npz"
        ck_json = SFD_DIR / f"holdout_fold_{f_i}.json"
        if ck_npz.exists() and ck_json.exists():
            f_rec = json.loads(ck_json.read_text())
            with np.load(ck_npz) as z:
                for a in ARMS:
                    preds[a].append(z[f"pred_{a}"])
                for a in oof:
                    oof[a][fold["valid"]] = z[f"surf_{a}"]
            fold_logs.append(f_rec)
            print(f"[holdout] {fold['name']} restored checkpoint", flush=True)
            continue
        t_fold = time.time()
        b = budgets[f_i]
        d_vis = distance_transform_edt(~fold["visible"])
        elig = fold["valid"] & (d_vis > 2.0)
        f_rec: dict[str, Any] = {"fold": fold["name"], "budget": int(b)}

        s_b0, m_b0 = train_predict_b0(store, fp_pos, fold, labels, B0_SEED + f_i)
        d_b0 = emit_dots(s_b0, fold["valid"], b)
        preds["B0"].append(d_b0.astype(np.uint8))
        f_rec["B0"] = {**m_b0, "n_dots": int(d_b0.sum()), "fold_dti": round(float(holdout.score_fold(d_b0, fold)[0]["dti"]), 6)}
        del s_b0, d_b0
        print(f"[holdout] {fold['name']} B0 dti={f_rec['B0']['fold_dti']:.5f} ({time.time()-t_fold:.0f}s)", flush=True)

        p89, m89 = train_predict_gvsc_expert(store, tuple(EXP2_FEATURES), fp_pos, fold["train"], fold["visible"], fold["valid"], labels, f_i)
        p89b, m89b = train_predict_gvsc_expert(store, tuple(EXP3_BLIND_FEATURES), fp_pos, fold["train"], fold["visible"], fold["valid"], labels, 200 + f_i)
        p_cgvsc = fuse_exp3_lidar_bridge(p89, p89b, lid_valid_2d, det_slope_2d, fold["valid"])
        del p89, p89b
        oof["C-GVSC"][fold["valid"]] = p_cgvsc[fold["valid"]]
        d_c, obj_c = _emit_celf(p_cgvsc, elig, fold["valid"], b)
        preds["C-GVSC"].append(d_c.astype(np.uint8))
        f_rec["C-GVSC"] = {"full": m89, "blind": m89b, "n_dots": int(d_c.sum()), "obj": round(obj_c, 2), "fold_dti": round(float(holdout.score_fold(d_c, fold)[0]["dti"]), 6)}
        del p_cgvsc, d_c
        print(f"[holdout] {fold['name']} C-GVSC dti={f_rec['C-GVSC']['fold_dti']:.5f} ({time.time()-t_fold:.0f}s)", flush=True)

        p101, m101 = train_predict_gvsc_expert(store, SFD101, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, 400 + f_i)
        oof["EXP-1"][fold["valid"]] = p101[fold["valid"]]
        d_1, obj_1 = _emit_celf(p101, elig, fold["valid"], b)
        preds["EXP-1"].append(d_1.astype(np.uint8))
        f_rec["EXP-1"] = {**m101, "n_dots": int(d_1.sum()), "obj": round(obj_1, 2), "fold_dti": round(float(holdout.score_fold(d_1, fold)[0]["dti"]), 6)}
        del d_1
        print(f"[holdout] {fold['name']} EXP-1 dti={f_rec['EXP-1']['fold_dti']:.5f} ({time.time()-t_fold:.0f}s)", flush=True)

        p101b, m101b = train_predict_gvsc_expert(store, SFD_BLIND, fp_pos, fold["train"], fold["visible"], fold["valid"], labels, 500 + f_i)
        p_exp2 = fuse_exp3_lidar_bridge(p101, p101b, lid_valid_2d, det_slope_2d, fold["valid"])
        oof["EXP-2"][fold["valid"]] = p_exp2[fold["valid"]]
        d_2, obj_2 = _emit_celf(p_exp2, elig, fold["valid"], b)
        preds["EXP-2"].append(d_2.astype(np.uint8))
        f_rec["EXP-2"] = {"full": m101, "blind": m101b, "n_dots": int(d_2.sum()), "obj": round(obj_2, 2), "fold_dti": round(float(holdout.score_fold(d_2, fold)[0]["dti"]), 6)}
        del d_2, p_exp2, p101
        print(f"[holdout] {fold['name']} EXP-2 dti={f_rec['EXP-2']['fold_dti']:.5f} ({time.time()-t_fold:.0f}s)", flush=True)

        p_dip, m_pu = train_predict_gvsc_expert(store, tuple(SFD_FEATURES), fp_pos, fold["train"], fold["visible"], fold["valid"], labels, 700 + f_i)
        p_exp3 = (0.7 * _rank01(oof["EXP-2"], fold["valid"]) + 0.3 * _rank01(p_dip, fold["valid"])).astype(np.float32)
        del p_dip, p101b
        oof["EXP-3"][fold["valid"]] = p_exp3[fold["valid"]]
        d_3, obj_3 = _emit_celf(p_exp3, elig, fold["valid"], b)
        preds["EXP-3"].append(d_3.astype(np.uint8))
        f_rec["EXP-3"] = {**m_pu, "dipole_expert": True, "blind_reused_from_EXP-2": True, "n_dots": int(d_3.sum()), "obj": round(obj_3, 2), "fold_dti": round(float(holdout.score_fold(d_3, fold)[0]["dti"]), 6)}
        del d_3, p_exp3
        print(f"[holdout] {fold['name']} EXP-3 dti={f_rec['EXP-3']['fold_dti']:.5f} ({time.time()-t_fold:.0f}s)", flush=True)

        f_rec["seconds"] = round(time.time() - t_fold, 1)
        fold_logs.append(f_rec)
        np.savez_compressed(
            ck_npz,
            **{f"pred_{a}": preds[a][-1] for a in ARMS},
            **{f"surf_{a}": oof[a][fold["valid"]] for a in oof},
        )
        ck_json.write_text(json.dumps(f_rec, indent=2))
        gc.collect()

    summaries = {a: holdout.summarize(preds[a]) for a in ARMS}
    paired = {
        **{a: holdout.compare_paired(preds[a], preds["B0"]) for a in EXP_ARMS + ("C-GVSC",)},
        "EXP-2_vs_C-GVSC": holdout.compare_paired(preds["EXP-2"], preds["C-GVSC"]),
        "EXP-1_vs_C-GVSC": holdout.compare_paired(preds["EXP-1"], preds["C-GVSC"]),
        "EXP-3_vs_EXP-2": holdout.compare_paired(preds["EXP-3"], preds["EXP-2"]),
    }
    best = max(EXP_ARMS, key=lambda a: float(summaries[a]["dti"]))
    for a in oof:
        np.save(SFD_DIR / f"oof_surface_{a}.npy", oof[a])
    doc = {
        "lane_id": "SFD-36",
        "label": "HOLDOUT-DTI",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration_path": str(PREREG_PATH.relative_to(ROOT)),
        "preregistration_sha256": sha256_file(PREREG_PATH),
        "evaluator_version": "gems-segment-pooled-v1",
        "buffer_px": 15,
        "withheld_positives": int(summaries["B0"]["n_withheld_positive_pixels"]),
        "fold_budgets": [int(x) for x in budgets],
        "total_budget": TOTAL_BUDGET,
        "experiments_executed": 3,
        "controls": ["B0", "C-GVSC"],
        "recorded_gvsc_exp3_for_reference": RECORDED_GVSC_EXP3,
        "best_candidate_arm": best,
        "summaries": summaries,
        "paired": paired,
        "folds": fold_logs,
        "elapsed_seconds": round(time.time() - T_START, 1),
    }
    HOLDOUT_OUT.write_text(json.dumps(doc, indent=2, default=float) + "\n")
    for a in ARMS:
        print(f"[holdout] POOLED {a}: HOLDOUT-DTI {summaries[a]['dti']:.6f} CI95 {summaries[a]['ci95']['interval']}", flush=True)
    print(f"[holdout] best EXP arm: {best}", flush=True)
    return doc


def focus9_entries() -> list[dict]:
    entries = json.loads((ROOT / "registry" / "uniqueness_registry.json").read_text())["entries"]
    focus = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}
    out = [e for e in entries if e.get("site") in focus and (ROOT / e["cache_path"]).exists()]
    return out


def champion_files(entries: list[dict]) -> dict[str, dict]:
    champ: dict[str, dict] = {}
    for e in entries:
        s = e.get("owner_reported_score")
        if s is None:
            continue
        site = e["site"]
        if site not in champ or s > champ[site]["owner_reported_score"]:
            champ[site] = e
    # GEMSDOE30's 0.2600 "poisson300m" file is byte-identical in footprint to the
    # GEMSDOE25 d2.8 mask (XOR=0, verified in docs/research/why-02778.md) but its
    # registry rows carry no owner score, so alias it to the identical GEMSDOE25
    # champion entry; overlap numbers are therefore exact, not approximate.
    if "GEMSDOE30" not in champ and "GEMSDOE25" in champ:
        alias = dict(champ["GEMSDOE25"])
        alias["site"] = "GEMSDOE30"
        alias["alias_note"] = "identical in-footprint mask to GEMSDOE25 champion (XOR=0)"
        champ["GEMSDOE30"] = alias
    return champ


def local_prior_entries(fp: np.ndarray, exclude_name: str) -> list[dict]:
    out = []
    for p in sorted((ROOT / "docs" / "downloads").glob("*.tif")):
        if p.name == exclude_name:
            continue
        with rasterio.open(p) as ds:
            if ds.shape != fp.shape:
                continue
            a = ds.read(1)
        content = hashlib.sha256(np.asarray(a[fp], dtype="<f4").tobytes()).hexdigest()
        out.append({
            "id": f"local-{p.stem[:40]}",
            "file": f"GEMSDOE36-local/{p.name}",
            "cache_path": str(p.relative_to(ROOT)),
            "footprint_sha256": content,
            "site": "GEMSDOE36-local",
            "owner_reported_score": None,
        })
    return out


def run_deploy(holdout_doc: dict, canary_doc: dict, fp: np.ndarray, labels: np.ndarray) -> dict:
    best = holdout_doc["best_candidate_arm"]
    surface = np.load(SFD_DIR / f"oof_surface_{best}.npy")
    entries = focus9_entries()
    champ = champion_files(entries)
    surf_check = compare_registry(surface, fp, entries, ROOT, dots=None, separate_calibration_controls=True)
    _rho = surf_check["max_abs_rank_correlation"]
    print(f"[deploy] surface vs focus9 ({len(entries)}): max|rho|={_rho}", flush=True)
    if float(surf_check["max_abs_rank_correlation"] or 0) > 0.90:
        raise SystemExit("SURFACE DUPLICATE vs focus-9: stop (protocol lane rule)")

    d_cat = distance_transform_edt(~(labels & fp))
    elig = fp & (d_cat > 2.0)
    cov = emit_submodular_cover(surface, elig, budget=TOTAL_BUDGET, valid_footprint=elig, gamma=1.0, min_spacing_px=2.0)
    dots = cov.mask
    rc_bytes = np.argwhere(dots).astype(np.int32).tobytes()
    uid = hashlib.sha256(rc_bytes).hexdigest()[:12]
    stem = f"gemsdoe36-sfd36-{best.lower().replace('-', '')}-20261027-{uid}-zeros"
    dl = ROOT / "docs" / "downloads"
    tif_path, zip_path = dl / f"{stem}.tif", dl / f"{stem}.zip"
    tmpl = ROOT / "data" / "raw" / "sample_submission.tif"
    write_submission(dots.astype(np.float32), tmpl, tif_path, outside="zero")
    zip_single(tif_path, zip_path)
    repo_val = validate_submission(tif_path, tmpl, require_nonfinite_outside=False).to_dict()
    gems_val = check_variants(tif_path, tmpl)

    dot_check = compare_registry(surface, fp, entries, ROOT, dots=dots, separate_calibration_controls=True)
    local_entries = local_prior_entries(fp, tif_path.name)
    local_check = compare_registry(surface, fp, local_entries, ROOT, dots=dots, separate_calibration_controls=True) if local_entries else None

    rows_by_file = {r["file"]: r for r in dot_check["rows"]}
    champ_rows = {}
    for site, e in sorted(champ.items()):
        r = rows_by_file.get(e["file"])
        champ_rows[site] = {
            "file": e["file"],
            "owner_reported_score": e.get("owner_reported_score"),
            "candidate_dot_overlap_within_3px": (r or {}).get("candidate_dot_overlap_within_3px"),
            "raw_spearman": (r or {}).get("raw_spearman"),
            "footprint_3px_coverage": (r or {}).get("footprint_3px_coverage"),
        }
    max_champ_ov = max((v["candidate_dot_overlap_within_3px"] or 0.0) for v in champ_rows.values())
    b2_ov = (champ_rows.get("GEMSDOE32") or {}).get("candidate_dot_overlap_within_3px")
    d_dots = d_cat[dots]
    dstats = {
        "n_dots": int(dots.sum()),
        "min_d_cat_px": round(float(d_dots.min()), 3),
        "median_d_cat_px": round(float(np.median(d_dots)), 2),
        "share_le_2px": round(float((d_dots <= 2.0).mean()), 6),
    }

    best_sum = holdout_doc["summaries"][best]
    paired_b0 = holdout_doc["paired"][best]
    g1 = bool(canary_doc["passed"])
    g2 = bool(float(best_sum["dti"]) > 0.170100 and float(paired_b0["paired_delta_ci95"][0]) > 0.0)
    g3 = bool(float(surf_check["max_abs_rank_correlation"] or 0) <= 0.90 and max_champ_ov <= 0.70)
    g4 = bool(
        repo_val["passed"]
        and gems_val["format_valid"]
        and gems_val["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]
        and dstats["share_le_2px"] == 0.0
        and dstats["n_dots"] == TOTAL_BUDGET
    )
    verdict = "promote" if (g1 and g2 and g3 and g4) else "negative"
    note = f"SFD-36 {best} signed step-dipole+bridge | HOLDOUT-DTI {float(best_sum['dti']):.4f} | {'PROMOTE' if verdict=='promote' else 'NEGATIVE'} {uid}"[:140]

    cross = {
        "lane_id": "SFD-36",
        "best_arm": best,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "focus9_entries_checked": len(entries),
        "surface_before_placement": {
            "max_abs_rank_correlation": surf_check["max_abs_rank_correlation"],
            "passed_le_0.90": bool(float(surf_check["max_abs_rank_correlation"] or 0) <= 0.90),
        },
        "final_dots": {
            "champion_overlap_by_site": champ_rows,
            "max_champion_3px_overlap": round(float(max_champ_ov), 6),
            "overlap_vs_GEMSDOE32_B2_3px": b2_ov,
            "max_overlap_all_focus9_rasters": dot_check["max_dot_overlap"],
            "focus9_rows_sorted_by_overlap_desc": sorted(dot_check["rows"], key=lambda r: float(r["candidate_dot_overlap_within_3px"] or 0), reverse=True)[:20],
            "local_prior_max_overlap": (local_check or {}).get("max_dot_overlap"),
            "local_prior_rows_sorted_by_overlap_desc": (sorted(local_check["rows"], key=lambda r: float(r["candidate_dot_overlap_within_3px"] or 0), reverse=True)[:10] if local_check else []),
        },
        "d_catalogue_stats": dstats,
    }
    CROSSCHECK_OUT.write_text(json.dumps(cross, indent=2, default=float) + "\n")

    card = {
        "schema": "gems.parallel_run_card.v1",
        "lane_id": "SFD-36",
        "best_arm": best,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "hypothesis": "H-SFD-A: uncatalogued buried normal faults show a signed transverse step dipole |f(+2/4px)-f(-2/4px)| sustained along strike in elevation/RTP/gravity/LiDAR-step, even with no ridge crest; EXP-3 (H-SFD-B) rank-fuses a dipole-only expert.",
        "mechanism": "101 label-free features (GVSC-89 + 12 SFD dipole) -> 2-seed HGB experts, Prentice-Pyke -> LiDAR-blind bridge (EXP-2); EXP-3 rank-fuses dipole-only expert 0.7/0.3 -> OOF surface -> B2 collar -> CELF 37,654 dots.",
        "named_non_fault_mimic": "Lithologic contacts, Lahontan shoreline scarps, canal/road embankments (also transverse dipoles).",
        "preregistration": {"path": str(PREREG_PATH.relative_to(ROOT)), "sha256": sha256_file(PREREG_PATH)},
        "experiments_executed": 3,
        "leakage_canary": {"passed": g1, "max_symmetric_auc": canary_doc["max_symmetric_auc"], "feature": canary_doc["max_symmetric_auc_feature"], "evidence": str(CANARY_OUT.relative_to(ROOT))},
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": "gems-segment-pooled-v1",
            "n_withheld_positive_pixels": holdout_doc["withheld_positives"],
            "arms": {a: {"dti": holdout_doc["summaries"][a]["dti"], "ci95": holdout_doc["summaries"][a]["ci95"]["interval"]} for a in ARMS},
            "best_arm": best,
            "paired_vs_B0": paired_b0,
            "evidence": str(HOLDOUT_OUT.relative_to(ROOT)),
        },
        "uniqueness_vs_focus9": {
            "surface_max_abs_spearman": surf_check["max_abs_rank_correlation"],
            "max_champion_3px_dot_overlap": round(float(max_champ_ov), 6),
            "overlap_vs_GEMSDOE32_B2": b2_ov,
            "gates_passed_G3": g3,
            "evidence": str(CROSSCHECK_OUT.relative_to(ROOT)),
        },
        "submission": {
            "file": str(tif_path.relative_to(ROOT)),
            "sha256": sha256_file(tif_path),
            "bytes": tif_path.stat().st_size,
            "zip": str(zip_path.relative_to(ROOT)),
            "zip_sha256": sha256_file(zip_path),
            "name": stem.replace("-zeros", ""),
            "note": note,
            "note_characters": len(note),
            "dots": dstats["n_dots"],
        },
        "validator": {"repo_validate_submission": repo_val, "gems_check_variants": gems_val, "d_catalogue": dstats},
        "gates": {"G1_canary": g1, "G2_holdout_beats_recorded_gvsc_and_paired_B0": g2, "G3_focus9_uniqueness": g3, "G4_format": g4},
        "organizer_score": None,
        "leaderboard_estimate": "See docs/research/sfd36-20261027.md; HOLDOUT-DTI is not a leaderboard score.",
        "elapsed_seconds": round(time.time() - T_START, 1),
    }
    RUN_CARD_OUT.write_text(json.dumps(card, indent=2, default=float) + "\n")
    receipt = dl / f"{stem}.receipt.json"
    receipt.write_text(json.dumps(card, indent=2, default=float) + "\n")
    print(f"[deploy] verdict={verdict} file={tif_path.name} sha256={card['submission']['sha256']}", flush=True)
    print(f"[deploy] gates G1={g1} G2={g2} G3={g3} G4={g4} | max_champ_overlap={max_champ_ov:.4f} vsB2={b2_ov}", flush=True)
    return card


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=("canary", "holdout", "deploy", "all"), default="all")
    args = ap.parse_args()
    verify_prereg()
    print("[kpl] preregistration lock OK", flush=True)
    fp_lbl, labels = load_labels(ROOT / "data" / "raw")
    store = build_combined_store(fp_lbl)
    print(f"[sfd] store ready: {len(store.names)} cols (101 = 89 + 12 SFD); blind={len(SFD_BLIND)}", flush=True)
    assert len(store.names) == 101 and list(SFD101) == list(store.names)
    holdout = SegmentHoldout(fp_lbl, labels, buffer_px=15)
    canary = run_canary(store, holdout, fp_lbl)
    if not canary["passed"]:
        raise SystemExit("CANARY FAILED: leakage suspected; aborting before any holdout number")
    if args.stage == "canary":
        return 0
    if args.stage in ("holdout", "all"):
        doc = run_holdout(store, holdout, fp_lbl, labels)
    else:
        doc = json.loads(HOLDOUT_OUT.read_text())
    if args.stage == "holdout":
        return 0
    run_deploy(doc, canary, fp_lbl, labels)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
