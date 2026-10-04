#!/usr/bin/env python3
"""Build the H6 full-area score grid for the competition submission.

H6 = off-catalogue SGMC fault-network prior + broad-coverage exact-marginal-gain
emission. This is the configuration that PASSED the 5-fold spatially-blocked
holdout gate (docs/research/holdout_results.json, run 6):

  * belief field  = 0.5 * geophysical corroboration + 0.5 * SGMC-prior
    (FieldConfig with enable_dip_projection=False — the dip projection measured a
    consistent small negative on the surface-trace target, see hypotheses.md);
  * emission target = the full off-catalogue SGMC line network (broad coverage,
    matching the incumbent's proven ~37k-dot coverage);
  * exact-marginal-gain dots, 200 m catalogue-flank exclusion, scatter radius 3 px,
    budget 40k (stops at the break-even bar at ~23-24k dots).

The output is a binary dot map (1.0 on dots, 0.0 elsewhere, NaN outside the
template footprint) — the metric's TP is a per-truth-pixel max-credit and its FP
sums p*(1-kernel) over all prediction pixels, so a binary dot map is the
optimal format (a soft halo adds FP without raising the max-credit TP). This is
the same format as the incumbent's study submissions (verified binary 0/1).

Run it, then format + validate + publish with scripts/build_submission.py.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe36.anderson_dip import local_extension_field  # noqa: E402
from gemsdoe36.emitter import emit_dots  # noqa: E402
from gemsdoe36.field import FieldConfig, build_belief_field  # noqa: E402
from gemsdoe36.metric import distance_weighted_tversky  # noqa: E402

BUDGET = 40000


def main() -> int:
    t0 = time.time()
    data_dir = ROOT / "data"

    data = np.load(data_dir / "processed" / "core_stack.npz")
    stack, names = data["stack"], [str(n) for n in data["names"]]
    channels = {n: stack[i] for i, n in enumerate(names)}
    del stack

    with rasterio.open(data_dir / "raw" / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1, masked=False))
    with rasterio.open(data_dir / "raw" / "labels.tif") as ds:
        lab = ds.read(1, masked=True)
    catalogue = np.asarray((~lab.mask) & (lab == 1) & footprint, dtype=np.float32)
    sgmc_off = channels["sgmc_off_catalogue"]

    # 200 m catalogue-flank exclusion (validated: lifted the incumbent 0.2708->0.2778).
    yy, xx = np.ogrid[-2:3, -2:3]
    flank = binary_dilation(catalogue > 0, structure=(xx * xx + yy * yy) <= 4)

    # Full-area extension field (no leak guard: the submission uses all data).
    extension = local_extension_field(catalogue, tile_px=120)

    # Best holdout-validated config: dip off (H6 lead), SGMC prior on.
    cfg = FieldConfig(enable_dip_projection=False)
    bf = build_belief_field(channels, footprint, catalogue, config=cfg, extension=extension)

    # Broad-coverage target: the full off-catalogue fault line network.
    sgmc_target = ((sgmc_off > 0) & footprint).astype(np.float32)

    res = emit_dots(
        bf.belief, budget=BUDGET, support_quantile=99.0,
        exclude_mask=flank, truth_proxy=sgmc_target, scatter_radius_px=3,
    )

    scores = np.zeros(footprint.shape, dtype=np.float32)
    if len(res.dots):
        scores[res.dots[:, 0], res.dots[:, 1]] = 1.0
    scores[~footprint] = np.nan

    # Diagnostics: self-score against the full off-catalogue target (reference).
    self_dti = distance_weighted_tversky(scores, sgmc_target, valid_mask=footprint)

    out_scores = ROOT / "outputs" / "scores_h6.npy"
    out_scores.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_scores, scores)

    diag = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": {
            "hypothesis": "H6 off-catalogue SGMC network prior + broad coverage",
            "dip_projection": False, "sgmc_prior": True, "scatter_radius_px": 3,
            "budget": BUDGET, "support_quantile": 99.0, "tile_px": 120,
            "emission_target": "full off-catalogue SGMC line network",
            "nominate_quantile": cfg.nominate_quantile,
        },
        "dots": int(len(res.dots)),
        "stopped_by": res.stopped_by,
        "credit_T": round(float(res.credit), 3),
        "fp_mass_F": round(float(res.fp_mass), 3),
        "K_target_px": int(sgmc_target.sum()),
        "self_dti_vs_offcatalog": round(float(self_dti), 4),
        "scores_npy": str(out_scores.relative_to(ROOT)),
        "elapsed_s": round(time.time() - t0, 1),
    }
    diag_path = ROOT / "outputs" / "h6_diagnostics.json"
    diag_path.write_text(json.dumps(diag, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diag, indent=2))
    print(f"\nNext: python scripts/build_submission.py {out_scores} "
          f"--template {data_dir / 'raw' / 'sample_submission.tif'} "
          f"--submission-name <unique> --note '<method+holdout+AI>'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
