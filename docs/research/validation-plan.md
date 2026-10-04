# Spatial validation and release gates

**State:** plan only; no competition data, folds, DTI result, or candidate raster exists in this checkout.

## Why a holdout is mandatory

Training labels are incomplete known-fault catalogues; competition truth is expert-labeled new faults. Random pixel splits leak continuous traces and local geophysical context. Holding out spatial regions and/or whole systems is less optimistic, but it still uses known faults as a proxy and cannot reproduce the private newly discovered fault population. Report that limitation alongside every local score.

## Predeclared leading-candidate test

1. **Freeze inputs.** Record source URL, access/license, hashes, GeoTIFF geometry, band tags/units/nodata, mask, and processing software for the official features, labels and sample template. Keep data and outputs out of Git.
2. **Reproduce a comparator.** Train/score the organizer reference under the same train/validation partitions before claiming a gain.
3. **Partition spatially.** Start with deterministic 512-pixel tiles and five folds. Exclude a 30-pixel collar around held-out tiles from training labels (3 km); score only the held-out truth with a separate 3-pixel (300 m) metric-radius evaluation collar. If vector fault IDs are available, group whole fault systems and record how that changes fold membership. No random pixel split is a primary result.
4. **Prevent feature/label leakage.** Fit normalization, feature selection, calibration, and thresholds on training folds only. Any labels used for pseudo-labels, dilation, or augmentation must be inside the train mask. Assert zero intersection between train-label and validation-truth masks.
5. **Compare at fixed policy.** Score the reference and H1 on identical folds with exact DTI, fixed candidate/emission budget, and no tuning on validation folds. Report pooled DTI, per-fold DTI, prediction coverage, precision/recall diagnostics, and uncertainty. Score continuous values exactly as the published equation specifies.
6. **Ablate physics.** Compare stress `lambda=0` vs. the preregistered positive `lambda`, then a spatially shuffled orientation field and a broad-uncertainty field. A nominal gain that survives only one fold or does not beat the shuffled control is not evidence for a stress mechanism.
7. **Release gate.** Require positive pooled ΔDTI and improvement in at least 4 of 5 folds, no severe degradation in any fold, correct no-leak checks, complete source/hash records, and a full raster-format pass. If any condition fails or no run exists, do not spend a submission slot.

## Metric implementation

`src/gemsdoe36/metric.py` encodes the published DTI definition: each truth pixel receives the maximum nearby `p(x) k(d)` credit; false-positive mass is probability times one minus the maximum truth-proximity kernel; false-negative mass is one minus that per-truth credit. The kernel is triangular with a 300 m radius. Unit tests use analytic toy rasters; they do not validate performance on the contest AOI.

## Release gates for an uploadable TIFF

- Must use the organizer's local sample template, not guessed dimensions or public competitor metadata.
- Exact single-band float32 GeoTIFF; EPSG:32611; 100 m; same shape, bounds and transform as the template.
- Finite predictions within [0, 1] in the template-valid region; `NaN`/null outside that region as specified by the official problem page.
- Writer disables TIFF predictors for float data, writes atomically, reopens the bytes, verifies range/geometry/mask, and emits a SHA-256 manifest plus a short note.
- A local PASS is not an organizer acceptance receipt. The prior `[0, 1]` rejection cannot be attributed to a specific encoding cause from this repository because the rejected file and sample template are absent.
- **Current gate:** blocked. No official sample, no real score raster, no holdout winner; therefore no competitive TIFF is published or represented as ready to upload.
