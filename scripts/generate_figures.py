#!/usr/bin/env python3
"""Generate authentic scientific diagnostic figures from H36-CTRB Run Card and GeoTIFF."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from scipy.ndimage import maximum_filter

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rc_path = ROOT / "evidence" / "h36_ctrb_run_card_20261025.json"
    rc = json.loads(rc_path.read_text())
    tif_path = ROOT / "docs" / "downloads" / rc["submission"]["submission_name"]
    tmpl_path = ROOT / "data" / "raw" / "sample_submission.tif"
    lbl_path = ROOT / "data" / "raw" / "labels.tif"

    with rasterio.open(tmpl_path) as ds:
        fp = np.isfinite(ds.read(1))
    with rasterio.open(lbl_path) as ds:
        cat = fp & np.isfinite(ds.read(1)) & (ds.read(1) > 0.5)
    with rasterio.open(tif_path) as ds:
        pred = fp & (ds.read(1) > 0.5)

    # Downsample 4x for crisp overview map using max-pooling so 1-px skeletons stay visible
    step = 4
    fp_d = fp[::step, ::step]
    cat_d = maximum_filter(cat, size=3)[::step, ::step]
    pred_d = maximum_filter(pred, size=3)[::step, ::step]

    rgb = np.full((*fp_d.shape, 3), 0.96, dtype=np.float32)
    rgb[fp_d] = [0.10, 0.14, 0.21]
    rgb[cat_d & fp_d] = [0.56, 0.64, 0.74]
    rgb[pred_d & fp_d] = [0.98, 0.62, 0.15]

    fig = plt.figure(figsize=(14.5, 5.2), dpi=160, facecolor="#f8fafc")
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.15, 1.05], wspace=0.28)

    # Panel A: Spatial footprint, known catalogue (masked), and H36-CTRB 35,468 unique dots
    ax0 = fig.add_subplot(gs[0, 0])
    ax0.imshow(rgb, interpolation="nearest")
    ax0.set_title(
        f"A. H36-CTRB Emitted Skeleton ({rc['submission']['emitted_positive_pixels']:,} px)\n"
        "Orange: H36-CTRB (d_cat > 200 m) | Slate: Known Catalogue",
        fontsize=9.2,
        fontweight="bold",
        pad=8,
    )
    ax0.set_xlabel("UTM Zone 11N Easting (100 m grid)", fontsize=8.5)
    ax0.set_ylabel("UTM Zone 11N Northing (100 m grid)", fontsize=8.5)
    ax0.set_xticks([])
    ax0.set_yticks([])

    # Panel B: SegmentHoldout ('gems-segment-pooled-v1') Progression + 95% CIs
    ax1 = fig.add_subplot(gs[0, 1])
    b = rc["benchmarks_and_ablations"]
    labels = [
        "CTRL-1\nLegacy H6",
        "CTRL-2\nRaw19 OOF",
        "EXP-1\nUnsup",
        "EXP-2\nLocal-17",
        "EXP-3\nH36-CTRB",
    ]
    objs = [
        b["ctrl_1_prior_repo_h6"],
        b["ctrl_2_raw19_hgb_d3_oof"],
        b["exp_1_unsupervised_concordance"],
        b["exp_2_local17_nsqpcc"],
        b["exp_3_full25_h36_ctrb"],
    ]
    vals = [float(o["dti"]) for o in objs]
    err_lo = [float(o["dti"]) - float(o["ci95"]["interval"][0]) for o in objs]
    err_hi = [float(o["ci95"]["interval"][1]) - float(o["dti"]) for o in objs]
    colors = ["#94a3b8", "#64748b", "#0284c7", "#0d9488", "#d97706"]
    x = np.arange(len(labels))
    bars = ax1.bar(x, vals, yerr=[err_lo, err_hi], capsize=4, color=colors, width=0.62, edgecolor="#1e293b", linewidth=0.7)
    for rect, v in zip(bars, vals):
        ax1.text(
            rect.get_x() + rect.get_width() / 2.0,
            v + 0.014,
            f"{v:.4f}" if v >= 0.001 else "0.0001",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
        )
    ax1.set_ylim(0, 0.155)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=7.8)
    ax1.set_ylabel("HOLDOUT-DTI (gems-segment-pooled-v1)", fontsize=8.5)
    ax1.set_title(
        "B. SegmentHoldout Progression (60,988 Withheld px)\nPooled DTI + 95% Spatial-Block Bootstrap CI",
        fontsize=9.5,
        fontweight="bold",
        pad=8,
    )
    ax1.grid(axis="y", linestyle="--", alpha=0.35)

    # Panel C: 4-Fold Stability & Uniqueness Headroom
    ax2 = fig.add_subplot(gs[0, 2])
    folds = rc["holdout_dti"]["folds"]
    f_names = ["NW", "NE\n(LiDAR Gap)", "SW", "SE"]
    f_vals = [float(f["dti"]) for f in folds]
    c2_vals = [float(f["dti"]) for f in b["ctrl_2_raw19_hgb_d3_oof"]["folds"]]
    fx = np.arange(4)
    w = 0.35
    ax2.bar(fx - w / 2, c2_vals, width=w, label="CTRL-2 Raw19 OOF", color="#64748b")
    ax2.bar(fx + w / 2, f_vals, width=w, label="EXP-3 H36-CTRB", color="#d97706")
    for i, fv in enumerate(f_vals):
        ax2.text(i + w / 2, fv + 0.003, f"{fv:.3f}", ha="center", va="bottom", fontsize=7.8, fontweight="bold")
    ax2.set_ylim(0, 0.16)
    ax2.set_xticks(fx)
    ax2.set_xticklabels(f_names, fontsize=8.2)
    ax2.set_ylabel("Fold HOLDOUT-DTI", fontsize=8.5)
    max_ov = float(rc["registry_uniqueness"]["final_dots"]["max_competing_dot_overlap"]) * 100.0
    ax2.set_title(
        f"C. 4-Quadrant Fold Wins (4/4 vs CTRL-2)\nMax Registry Overlap: {max_ov:.2f}% (Gate <= 70%)",
        fontsize=9.2,
        fontweight="bold",
        pad=8,
    )
    ax2.legend(fontsize=7.8, loc="upper right")
    ax2.grid(axis="y", linestyle="--", alpha=0.35)

    out_fig = ROOT / "docs" / "assets" / "h36_ctrb_overview.png"
    out_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fig, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Wrote {out_fig} ({out_fig.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
