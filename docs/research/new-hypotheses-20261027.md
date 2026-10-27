# GEMSDOE36 — historical hypothesis register (2026-10-27)

> **Superseded.** The original version of this document contained stale holdout status, unvalidated numerical improvement ranges, and false claims that magnetic analytic-signal, drainage/chi, and seismicity features were absent from the repository. Do not use those claims or estimates. The current review and candidate screen are in [`session-review-20261027-continuation.md`](session-review-20261027-continuation.md).

This file preserves only the already-recorded N1/N2 experiments and identifies older ideas that should not be relabeled as new. All reported values below are **HOLDOUT-DTI**, not leaderboard scores.

## N1 — shear/dilation structure-tensor coherence (negative)

- Layers: competition bands `07_geod_shearrate` and `08_geod_dilaterate`.
- Hypothesis: coherent strain-rate fabric may mark concealed step-overs or dilatational jogs.
- Named mimic: erosional drainage density or alluvial-fan distributary channels.
- Evidence: `evidence/n1_holdout_run_card.json`.
- **HOLDOUT-DTI 0.017003**, 95% CI **[0.014493, 0.019976]**; evaluator `gems36-segment-audit-v1`; 60,988 withheld positive pixels. Matched baseline: **HOLDOUT-DTI 0.021746**, 95% CI **[0.018991, 0.024228]**. Difference: -0.004743. Canary two-polarity AUC: 0.509478. Verdict: negative; do not promote.

## N2 — hydrothermal alteration × INGENIOUS probe halo (negative)

- Layers: competition band `02_rtp`, GeoDAWN radiometric K/Th proxy, and INGENIOUS 2 m temperature-probe `F2mDAB` observations from DOE GDR submission 1391.
- Hypothesis: co-located shallow thermal and alteration evidence may indicate concealed fluid conduits without a continuous surface scarp.
- Named mimic: shallow groundwater/moisture effects and alluvial-fan evaporative anomalies.
- Evidence: `evidence/n2_holdout_run_card.json`.
- **HOLDOUT-DTI 0.010285**, 95% CI **[0.007327, 0.013786]**; evaluator `gems36-segment-audit-v1`; 60,988 withheld positive pixels. Matched baseline: **HOLDOUT-DTI 0.021746**, 95% CI **[0.018991, 0.024228]**. Difference: -0.011461. Canary AUC: 0.509963. Verdict: negative; do not promote.

## Ideas already represented in this repository

These are not eligible to be described as new or untried solely on the basis of this historical note:

- **Magnetic analytic signal:** implemented in `src/gemsdoe36/ctrb.py`.
- **Drainage / chi / knickpoint features:** implemented and evaluated in TCD-36; see `src/gemsdoe36/tcd_features.py`, `scripts/run_tcd36_experiment.py`, and `docs/research/tcd36-20261027.md`.
- **Seismicity features:** present in WDP/GVSC paths; see `src/gemsdoe36/wdp_features.py` and `src/gemsdoe36/gvsc_features.py`.
- **Contact and crosscut concepts:** explored in MTO and related lanes.

This local code audit does not prove whether another independent repository has tried a method. A full registry comparison, data provenance, and a specific lane assignment are required before claiming uniqueness.

## Protocol and sources

Use the shared whole-segment buffered hide-and-recover evaluator, recompute catalogue-derived features from visible faults only, run each feature-alone leakage canary, and apply surface correlation and final-dot overlap gates against the frozen registry. A negative result is a valid deliverable. No weekly slot is considered without a separate selector decision.

Sources cited in historical records: [DOE GDR 1391](https://gdr.openei.org/submissions/1391), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS ComCat](https://earthquake.usgs.gov/fdsnws/event/1/), [USGS TNM 3DEP](https://tnmaccess.nationalmap.gov/api/v1/products), and [GBCGE INGENIOUS](https://gbcge.org/current-projects/ingenious/). These are pointers, not a claim that each source was fetched or re-verified during this continuation review.
