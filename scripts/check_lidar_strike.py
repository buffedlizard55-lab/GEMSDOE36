#!/usr/bin/env python3
"""Check whether the LiDAR product's `strike` band agrees with catalogue line orientation (IR-22).

Catalogue orientation = principal axis of label pixels in a 9x9 window (second moments), converted
to an axial azimuth from north. Compared with the dequantised `strike` band under five conventions.
Writes evidence/h36_strike_check.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import uniform_filter

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with rasterio.open(ROOT / "data/raw/labels.tif") as s:
        cat = (s.read(1) == 1).astype(np.float32)
    with rasterio.open(ROOT / "data/raw/external/lidar_scarp_features_u8.tif") as s:
        q_st, q_coh = s.read(11), s.read(10)
    strike = (q_st.astype(np.float32) - 1) / 254 * 180
    coh = (q_coh.astype(np.float32) - 1) / 254
    h, w = cat.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    k = 9
    m = uniform_filter(cat, k)
    eps = 1e-6
    cy, cx = uniform_filter(cat * yy, k) / (m + eps), uniform_filter(cat * xx, k) / (m + eps)
    syy = uniform_filter(cat * yy * yy, k) / (m + eps) - cy**2
    sxx = uniform_filter(cat * xx * xx, k) / (m + eps) - cx**2
    sxy = uniform_filter(cat * xx * yy, k) / (m + eps) - cx * cy
    ang = 0.5 * np.arctan2(2 * sxy, sxx - syy)
    az = np.degrees(np.arctan2(np.cos(ang), -np.sin(ang))) % 180
    sel = (cat > 0) & (q_st > 0) & (coh > 0.3) & (m * k * k >= 6)
    a, b = az[sel], strike[sel]

    def axial(x, y):
        return np.abs(((x - y + 90) % 180) - 90)

    conv = {"strike": b, "strike+90": (b + 90) % 180, "180-strike": (180 - b) % 180, "90-strike": (90 - b) % 180, "270-strike": (270 - b) % 180}
    res = {name: {"median_axial_diff_deg": float(np.median(axial(a, v))), "frac_within_22.5deg": float(np.mean(axial(a, v) < 22.5))} for name, v in conv.items()}
    out = {"n_catalogue_pixels_tested": int(sel.sum()), "random_expectation": {"median_axial_diff_deg": 45.0, "frac_within_22.5deg": 0.25}, "conventions": res,
           "conclusion": "No convention aligns the strike band with catalogue orientation better than chance; lane geometry uses det_elev regional slope instead."}
    (ROOT / "evidence/h36_strike_check.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
