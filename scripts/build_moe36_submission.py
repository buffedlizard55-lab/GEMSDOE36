#!/usr/bin/env python3
"""Build the MOE36 full-catalogue submission from the winning EXP-1 fusion.

Refits the 3 preregistered experts on the FULL visible catalogue (no holdout
withholding — this is the competition model, not a validation run), fuses
rank-normalised surfaces with equal weights (EXP-1, the holdout winner),
emits 37,654 dots by 300 m submodular cover outside d_cat > 2 px, and writes
a zeros-variant portal GeoTIFF via the shared submission gate (whole-array
[0,1] verified on disk). Verdict logic lives in the run card / site, driven
by evidence/moe36_holdout_20261026.json: HOLDOUT-DTI 0.124900 < B0 0.13375,
so this file is DO NOT SUBMIT (research download only).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from atvr36_submission_gate import write_and_validate_submission  # noqa: E402
from gemsdoe36.ctrb import (  # noqa: E402
    ALL_FEATURE_NAMES,
    LOCAL_FEATURE_NAMES,
    STRUCTURAL_FEATURE_NAMES,
    build_or_load_feature_stack,
    submodular_dti_emit,
)
from run_moe36_experiment import CACHE, RAW_DIR, fit_predict, load_grid, rank_norm, raw19_matrix  # noqa: E402

NAME = "gemsdoe36-moe36-exp1-20261026"
NOTE = "GEMSDOE36 MOE36 EXP-1 equal rank fusion RAW19+CTRB-local+struct | HOLDOUT-DTI 0.1249 | NEGATIVE do not submit"


def main():
    t0 = time.time()
    assert len(NOTE) <= 140, len(NOTE)
    footprint, catalogue = load_grid()
    fp_ids = np.flatnonzero(footprint)
    n_fp = len(fp_ids)
    Xc, _ = build_or_load_feature_stack(RAW_DIR, ROOT / "data" / "prepared")
    Xr = raw19_matrix(footprint)
    experts = {
        "E_RAW": (Xr, list(range(19))),
        "E_LOCAL": (Xc, [ALL_FEATURE_NAMES.index(n) for n in LOCAL_FEATURE_NAMES]),
        "E_STRUCT": (Xc, [ALL_FEATURE_NAMES.index(n) for n in STRUCTURAL_FEATURE_NAMES]),
    }
    train_fp = np.ones(n_fp, dtype=bool)
    vis_fp = catalogue.ravel()[fp_ids]
    dcat = distance_transform_edt(~catalogue)
    d_fp = dcat.ravel()[fp_ids].astype(np.float32)
    fused = np.zeros(n_fp, dtype=np.float32)
    for ei, (ename, (X, cols)) in enumerate(experts.items()):
        pred = fit_predict(X, cols, train_fp, vis_fp, d_fp, train_fp,
                           seed=20261026 + 900 + ei)
        fused += rank_norm(pred, train_fp) / 3.0
        del pred
        print(f"[moe36-build] {ename} refit done {time.time()-t0:.0f}s", flush=True)
    surf2d = np.zeros(footprint.shape, dtype=np.float32)
    surf2d.ravel()[fp_ids] = fused
    np.save(CACHE / "full_surface.npy", surf2d)
    allowed = footprint & (dcat > 2.0)
    dots = submodular_dti_emit(surf2d, allowed, footprint=footprint,
                               n_dots=37_654, dstar_ref=0.22, min_gain=0.0)
    print(f"[moe36-build] dots={int((dots>0.5).sum())}", flush=True)
    out_tif = ROOT / "docs" / "downloads" / f"{NAME}.tif"
    receipt = write_and_validate_submission(
        dot_mask_or_prob=(dots > 0.5),
        surface_for_registry=surf2d,
        out_tif=out_tif,
        submission_name=NAME,
        submission_note=NOTE,
        sample_tif=RAW_DIR / "sample_submission.tif",
        existing_faults_tif=RAW_DIR / "existing_faults.tif",
        footprint_mask=footprint,
        write_zip=True,
    )
    (ROOT / "docs" / "downloads" / f"{NAME}.receipt.json").write_text(
        json.dumps(receipt, indent=1, default=float) + "\n")
    print(json.dumps({"tif": str(out_tif), "receipt_keys": list(receipt)[:20],
                      "elapsed": round(time.time() - t0, 1)}, indent=1, default=str))


if __name__ == "__main__":
    main()
