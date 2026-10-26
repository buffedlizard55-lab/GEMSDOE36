#!/usr/bin/env python3
"""Lane36 finalize: prevalence-calibrated operating-point check, bootstrap CI,
submission write (fail-closed zeros mode), uniqueness vs full registry, run card."""
from __future__ import annotations
import json, sys, time, hashlib
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gemsdoe36.metric import distance_weighted_tversky
from gemsdoe36.submission import write_submission, validate_submission, sha256_file
from lane36_pipeline import emit, read_dots, overlap_frac, pooled, dti_components, H, W, DATA, WORK

rng = np.random.default_rng(36)
def log(*a): print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def best_credit_map(pred, truth):
    """Per-truth-pixel max kernel credit (mirrors metric.py inner loop, binary pred)."""
    from scipy.ndimage import distance_transform_edt
    dp = distance_transform_edt(~pred)
    return np.maximum(1.0 - dp / 3.0, 0.0)  # binary pred: max credit = kernel(dist to nearest dot)

def score_config_oof(oof, spacing, budget, truth_subsample=None):
    z = np.load(WORK/"folds.npz"); foot, lab, comp, fold_of_px, edges = z["foot"], z["lab"], z["comp"], z["fold_of_px"], list(z["edges"])
    per = []; nd = 0; credits = []; comp_ids = []
    for f in range(5):
        visible = lab & (fold_of_px != f); truth = lab & (fold_of_px == f)
        if truth_subsample is not None: truth = truth & truth_subsample
        c0, c1 = edges[f], edges[f+1]
        domain = np.zeros((H, W), bool); domain[:, c0+4:c1-4] = True; domain &= foot
        b = int(budget * domain.sum() / foot.sum())
        dots = emit(oof, foot, visible, spacing, b, domain=domain); nd += int(dots.sum())
        sl = (slice(0, H), slice(max(0, c0-6), min(W, c1+6)))
        valid = foot[sl].copy(); valid[:, :(c0-sl[1].start)+4] = False; valid[:, (c1-sl[1].start)-4:] = False
        d = dots[sl] & ~visible[sl]
        per.append(dti_components(d, truth[sl], valid))
        bc = best_credit_map(d, truth[sl]); tc = np.nonzero(truth[sl] & valid)
        credits.append(bc[tc]); comp_ids.append(comp[sl][tc])
    s, tp, fp, fn = pooled(per)
    return s, nd, tp, fp, fn, np.concatenate(credits), np.concatenate(comp_ids), per

def bootstrap_ci(credits, comp_ids, fp, n=1000):
    # segment-cluster bootstrap (FP held fixed -> conditional CI, disclosed)
    uniq, inv = np.unique(comp_ids, return_inverse=True)
    csum = np.bincount(inv, weights=credits); ccnt = np.bincount(inv).astype(float)
    idx = rng.integers(0, len(uniq), size=(n, len(uniq)))
    tp = csum[idx].sum(axis=1); ng = ccnt[idx].sum(axis=1); fn = ng - tp
    dti = tp / (tp + 0.2 * fp + 0.8 * fn + 1e-8)
    return float(np.percentile(dti, 2.5)), float(np.percentile(dti, 97.5)), int(len(uniq))

def main():
    spacing, budget = float(sys.argv[1]), int(sys.argv[2])
    oof = np.load(WORK/"oof_surface.npy")
    z = np.load(WORK/"folds.npz"); foot, lab, comp = z["foot"], z["lab"], z["comp"]
    # 1) full-density holdout + CI at chosen config
    s, nd, tp, fp, fn, credits, cids, per = score_config_oof(oof, spacing, budget)
    lo, hi, nseg = bootstrap_ci(credits, cids, fp)
    log(f"CHOSEN s={spacing} b={budget}: HOLDOUT-DTI={s:.4f} CI[{lo:.4f},{hi:.4f}] dots={nd} segs={nseg}")
    # 2) prevalence-calibrated: subsample withheld segments to ~20.8% of px (live-density proxy 12,691/60,988)
    uniq = np.unique(comp[lab]); keep = rng.random(len(uniq)) < 0.208
    keep_ids = set(uniq[keep].tolist()); sub = np.isin(comp, list(keep_ids))
    s2, nd2, *_ = score_config_oof(oof, spacing, budget, truth_subsample=sub)
    # champion-analog under same subsample for fair calibrated comparison
    from lane36_pipeline import score_dots
    fold_of_px, edges = z["fold_of_px"], list(z["edges"])
    d28 = read_dots(DATA/"scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    # analog with subsampled truth: quick inline
    per_a = []
    for f in range(5):
        truth = lab & (fold_of_px == f) & sub; visible = lab & (fold_of_px != f)
        c0, c1 = edges[f], edges[f+1]
        sl = (slice(0, H), slice(max(0, c0-6), min(W, c1+6)))
        valid = foot[sl].copy(); valid[:, :(c0-sl[1].start)+4] = False; valid[:, (c1-sl[1].start)-4:] = False
        d = d28[sl].copy(); d &= ndi.distance_transform_edt(~visible[sl]) > 2.0; d &= ~visible[sl]
        per_a.append(dti_components(d, truth[sl], valid))
    sa, *_ = pooled(per_a)
    log(f"PREVALENCE-CALIBRATED (~20.8% truth px): lane={s2:.4f} champion-analog={sa:.4f}")
    # 3) write submission from final dots
    dots = np.load(WORK/"final_dots.npy")
    scores = np.where(foot, dots.astype(np.float32), 0.0).astype(np.float32)
    ndots = int(dots.sum())
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    tag = hashlib.sha256(dots.tobytes()).hexdigest()[:8]
    name = f"gemsdoe36-lane36-supgbm-{ndots}-{stamp}-{tag}-zeros.tif"
    out = ROOT/"docs"/"downloads"/name
    note = f"Lane36 supervised GBM lineament surf, seg-holdout DTI {s:.3f} vs champ-analog 0.162; s{spacing} b{ndots} B2"
    assert len(note) <= 140, len(note)
    rep = write_submission(scores, DATA/"sample_submission.tif", out, note=note,
                           submission_name=f"GEMSDOE36-Lane36-SupGBM-{stamp}", manifest_path=out.with_suffix(".json"), mode="zeros")
    log("WROTE", out.name, "passed", rep.passed, "sha", sha256_file(out))
    # uniqueness full registry
    regs = {"champion_h33-2-b2": DATA/"registry/champion_h33-2-b2_02778.tif",
            "solo_h27-4": DATA/"registry/solo_h27-4_02708.tif",
            "h33d": DATA/"registry/h33d_02632.tif",
            "d28poisson": DATA/"registry/d28poisson_02600.tif",
            "anderson_pinn36": ROOT/"docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
            "h6": ROOT/"docs/downloads/GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif",
            "gems27": DATA/"scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif"}
    uni = {k: overlap_frac(dots, read_dots(p)) for k, p in regs.items()}
    from scipy.stats import spearmanr
    surf = np.load(WORK/"final_surface.npy")
    with rasterio.open(DATA/"scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") as ds:
        h195 = np.nan_to_num(ds.read(1), nan=0.0)
    idx = np.argwhere(foot); smp = idx[rng.choice(len(idx), 200000, replace=False)]
    rho = float(spearmanr(surf[smp[:,0],smp[:,1]], h195[smp[:,0],smp[:,1]]).statistic)
    e1 = json.loads((WORK/"e1.json").read_text()); e2 = json.loads((WORK/"e2.json").read_text())
    card = {
        "lane": "supervised GBM on label-free lineament transforms; Poisson emission B=2; no catalogue-derived feature, no SGMC prior, no prior raster",
        "hypothesis": "A supervised ranker of catalogue-fault geophysical expression ranks hidden-fault pixels better than the hand-weighted h19-5 corroboration surface behind the 0.2778 champion, whose margin is exhausted (champion+1200 adds scored 0.2750)",
        "mechanism": "66 label-free features (multi-scale gradients/Laplacians/ridges of RTP/TMI/gravity/elevation/basement/conductivity, structure-tensor coherence + Anderson deviation, LiDAR scarp, radiometrics); HistGBM catalogue-vs-background; priority Poisson thinning; B=2 flank exclusion",
        "non_fault_mimic": "lithologic contacts, GeoDAWN flight-line stripes, roads in LiDAR bands, playa terraces",
        "holdout": {"protocol": "hide-and-recover, whole segments in 5 spatial strips, 500m buffer, visible masked pixel-exact, pooled organizer DTI a0.2 b0.8 R300m (gemsdoe36.metric v1)",
                    "withheld_positives": 60988, "lane_dti": s, "ci95_segment_bootstrap_fp_fixed": [lo, hi],
                    "champion_analog_dti": e1["champion_analog_d28_B2visible"]["pooled_dti"],
                    "champion_as_submitted_dti_handicapped": e1["champion_as_submitted"]["pooled_dti"],
                    "h6_dti": e1["h6_sgmc_prior"]["pooled_dti"],
                    "prevalence_calibrated_lane": s2, "prevalence_calibrated_champion_analog": sa,
                    "leakage_canary_max_feature_auc": e1["canary"]["max_feature_auc"],
                    "label": "HOLDOUT-DTI (not an organizer score; all leaderboard numbers owner-reported, no receipts in repo)"},
        "uniqueness": {"spearman_vs_h19_5_surface": rho, "dot_overlap_le3px": uni,
                       "gates": "rank-corr<=0.90 and overlap<=0.70 vs every registry raster"},
        "emission": {"spacing_px": spacing, "budget_target": budget, "dots": ndots},
        "raster": {"file": name, "sha256": sha256_file(out), "validator_passed": rep.passed,
                   "mode": "zeros (all 12,279,160 cells finite in [0,1], nodata None) - portal-safe vs historic [0,1] rejection"},
        "submission_name": f"GEMSDOE36-Lane36-SupGBM-{stamp}", "note_140": note,
        "verdict": "PLACEHOLDER_SET_AFTER_GATES"}
    lane_ok = rho <= 0.90 and max(uni.values()) <= 0.70
    beats = s > e1["champion_analog_d28_B2visible"]["pooled_dti"]
    card["verdict"] = "promote" if (lane_ok and beats and rep.passed) else "negative"
    card["ok_to_submit"] = bool(lane_ok and beats and rep.passed)
    (WORK/"run_card.json").write_text(json.dumps(card, indent=1, default=float))
    (ROOT/"docs"/"downloads"/"lane36_run_card.json").write_text(json.dumps(card, indent=1, default=float))
    log("RUN CARD verdict", card["verdict"], "rho", round(rho,3), "maxoverlap", round(max(uni.values()),3))

if __name__ == "__main__":
    main()
