# BDC-36 preregistration (locked before holdout numbers)

Lane: **BDC-36 — basement-depth contour × geodetic dilatation ridges**.

## Physical hypothesis

Basin-and-Range **range-front / intra-basin normal faults that are missing from the
provided USGS/INGENIOUS catalogue** often sit on **steps in inverted basement depth**
(`depth_to_base_surf`, GeoDAWN band 15) while the crust is **extending**
(`geod_dilaterate`, band 8). Magnetic-worm / LiDAR-openness families (H19-5 → B2)
do not use this pair. A lithologic basement contact or a basin-fill thickness
jump without a fault is the named mimic.

## Why off-catalogue

Catalogue traces already occupy the mapped range fronts. Unmapped splays and
buried basin-bounding strands should appear as **depth-to-basement gradients
offset from the labelled pixels**, not as copies of H19 ridges.

## Experiments (max 3)

| id | surface | budget | collar |
|---|---|---|---|
| EXP-1 | percentile rank of \|\∇ depth_to_base\| | 18,000 | d(visible) > 2 px |
| EXP-2 | percentile rank of max(dilatation, 0) | 18,000 | same |
| EXP-3 | geometric mean of ranks(\|∇z\|, max(dil,0), \|grav VG\|) | 18,000 | same |

Emission: ridge-NMS then top-k with 2 px self-spacing. No prior submission raster.
Holdout: `gems.holdout.SegmentHoldout` (gems-segment-pooled-v1, 15 px buffer).
Canary: `protocol.feature_canary`, fail if two-polarity AUC > 0.90.

Verdict promote only if HOLDOUT-DTI 95% CI lower bound exceeds the matched
catalogue-distance control on this evaluator **and** registry |ρ| ≤ 0.90 and
3-px overlap ≤ 0.70 versus competing detectors (lattice treated as space-filling
control).
