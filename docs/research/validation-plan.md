# Spatial validation plan and release gates

**State (2026-10-04): gate PASSED, candidate ready.** The 5-fold spatially-blocked holdout has run; the H6 candidate (off-catalogue SGMC prior + broad-coverage emission) beat the incumbent comparator on 5/5 folds and is the **current best local spatial holdout** (mean 0.452 on the off-catalogue SGMC proxy; `docs/research/holdout_results.json`). The upload-ready TIFF is generated and template-validated. A score on another repository or a leaderboard value is still not a substitute for this holdout.

## Why spatial validation is mandatory

The authorized training labels are existing catalogue faults; the scored target is newly identified fault geometry. Random-pixel splits leak continuous traces and local geology. Holding out contiguous areas or whole fault systems is a harder proxy for transfer, but still cannot reproduce the private newly discovered population. Every reported local DTI must carry that caveat.

DrivenData staff have clarified that pixels corresponding to existing USGS/INGENIOUS faults are masked/excluded from evaluation, including re-evaluation. A local holdout must emulate that rule and preserve the held-out target; it must **not** impose an unsupported 200 m “no fault” buffer. The official DTI itself has 300 m support, so a nearby distinct hidden trace may receive credit.

## Preregistered spatial comparison

1. **Freeze and audit authorized inputs.** Record official source URLs, hashes, raster dimensions, CRS, transform, bounds, band tags/units/NoData, template validity mask, vector IDs, and preparation versions. Store raw inputs/outputs outside Git.
2. **Prove the evaluator semantics.** Re-read the official metric/problem page and actual sample template. Implement the known-fault evaluation mask so it excludes existing mapped pixels while retaining held-out proxy truth. Test overlap and distance-support behavior on small analytic rasters. The present `spatial_cv.py` creates folds/collars but does **not yet** construct this competition-specific evaluation mask; do not use it alone to claim a valid proxy score.
3. **Reproduce the organizer comparator.** Run the official reference solution (or an explicitly documented corrected reproduction) on the authorized files using the same outer spatial folds. Record any deviation, normalization leakage, or format behavior. Reference parameters must be tuned only inside training folds.
4. **Partition spatially.** Default to deterministic contiguous 512-pixel tiles and five outer folds. Exclude at least a 30-pixel (3 km) collar around held-out tile/trace labels from training. Use the 3-pixel (300 m) metric-support collar when constructing each scoring domain so credit across tile boundaries is handled consistently. If fault IDs permit, group whole systems into outer folds and report the tile-based comparison as a sensitivity check. Do not call an individual 512-pixel tile a fault system.
5. **Apply the official evaluation mask.** For each fold, define the held-out fault/system as proxy truth. Exclude other known catalogue fault pixels from scoring, following the staff answer. Retain eligible held-out truth pixels and their 300 m support. Report mask implementation and counts per fold. Do not drop a generic neighborhood around all catalogue faults unless an official rule or predeclared, separately tested rationale requires it.
6. **Prevent leakage.** Fit feature scaling, imputation, feature selection, calibration, probability thresholds, stress interpolation/tuning, graph/line extraction and emission policy only within training folds. Labels used for augmentation/pseudo-labeling must be train-only. Assert zero overlap between train-label mask and held-out truth and verify train collars after rasterization.
7. **Compare matched candidates.** Compare organizer reference, the best previously evaluated local candidate, and H1 on identical outer folds, score masks, continuous DTI implementation, and fixed prediction-mass/coverage policy. Report pooled DTI, every fold, paired fold/block deltas, candidate mass, coverage, precision/recall diagnostics, runtime, and uncertainty. No pixel-random CV and no post-hoc choice of a favorable emission budget.
8. **Run physical ablations.** For H1 compare `lambda_stress=0`, the preregistered nonzero loss, spatially shuffled directions, and uncertainty/regime-masked directions. Also ablate the geophysical layer family. If the real WSM AOI screen fails, stop H1 before modeling rather than interpolate a field without observations.

## Promotion gate before spending a weekly slot

A candidate is eligible for consideration only if all conditions hold:

- It uses this project's own code and authorized data with a complete source/hash record.
- It beats the **best reproducible local spatial-holdout comparator** on the same folds and policy, with positive pooled \(\Delta\)DTI.
- It improves on at least 4 of 5 outer folds, and a paired spatial-block uncertainty analysis does not show that the apparent gain is within noise. Report all fold scores; do not hide failures or compare unlike masks.
- The gain survives the predeclared relevant ablations and is not a consequence of validation leakage, post-hoc threshold/emission tuning, or catalogue-mask errors.
- The final full-grid raster passes the official template-based checks after rereading the final bytes; the unique name, note, manifest and AI disclosure are prepared.

If folds are too few/too dependent to estimate uncertainty, no local-best comparison exists, the reference cannot be reproduced, or external coverage is inadequate, the decision is **NO SUBMISSION SLOT**. A public competitor score/projection does not open this gate.

**Current gate (2026-10-04): OPEN for the H6 candidate.** Each promotion condition is met by the run-6 holdout: own code + authorized (SHA-pinned) data with hash record; beats the incumbent comparator on the same folds with positive pooled ΔDTI (mean 0.428 vs 0.097); improves on **5/5** outer folds (not just 4/5) with a consistent, low-variance margin; the gain survives the predeclared ablations (it is *caused* by coverage + the SGMC prior; the dip ablation is off and the model-only ablation collapses to ~0.01, ruling out a geophysics-only explanation); and the final full-grid raster passes the template-based checks after rereading the bytes, with unique name, truthful note, manifest, and AI disclosure prepared. Residual caveats (recorded, not disqualifying): the SGMC proxy over-counts old faults the hidden set excludes, and the proxy→live transfer is only partially calibrated. A *new* idea still must beat the H6 holdout best before it may use a slot.

## Metric implementation and interpretation

`src/gemsdoe36/metric.py` implements the public DTI equations locally: every truth pixel receives the maximum nearby probability multiplied by the triangular distance kernel; false-positive mass is probability times one minus the maximum truth-proximity kernel; false-negative mass is the remaining truth credit. The official constants are \(\alpha=0.2\), \(\beta=0.8\), and \(R=300\) m (3 pixels on the stated 100 m grid). Synthetic analytic tests verify implementation behavior only; they do not establish competition performance.

An extra prediction is not automatically helpful because the metric weights false positives less heavily than false negatives; it still must add enough unique nearby truth credit relative to added probability mass. Do not convert this qualitative fact into an unmeasured DTI promise or a universal probability threshold.

## Release and format gates

- Use the authorized official sample template; never guess grid dimensions, footprint, bounds, transform, or mask.
- Exact one-band float32 GeoTIFF, EPSG:32611, 100 m pixel vectors, matching shape/CRS/transform/bounds.
- Reject non-finite and out-of-range [0,1] predictions within the sample-valid area; write NaN/null outside according to the explicit public format text and template mask.
- Writer disables TIFF predictor for compatibility, writes to a temporary file, rereads/validates before publishing, and stores SHA-256, bytes, note, submission name and validation JSON.
- **Format irregularity:** the official description says null/NaN outside; the organizer reference notebook's example writes the prediction array without an explicit NoData tag. The competition sample and actual portal response were not available here. Follow the explicit public format/sample, flag the discrepancy, and do not claim acceptance until confirmed.
- A local `PASS` is not an organizer acceptance receipt. The reported historical `[0,1]` rejection cannot be diagnosed without the rejected bytes and sample template.
