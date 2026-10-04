# Three-pass review log

## Pass 1 — user requirements, repository, and rules (2026-10-04)

- Read the existing README before implementation; confirmed the checkout had only `# GEMSDOE36`.
- Mapped every explicit request to an artifact: standing brief in README; ranked hypotheses; sources/limitations; differentiated stress loss; spatially blocked validation plan; [0,1] writer/validator; landing page + executive summary guide; AI disclosure; three review passes; PR/merge status.
- Confirmed official data requires a DrivenData login; no credentials were present or requested. Confirmed official rules require a generative-AI narrative, a single final entry, and at most three weekly feedback submissions.
- **Outcome:** do not fabricate a model score or publish a guessed submission TIFF. Keep the blocked status visible.

## Pass 2 — geoscience, target alignment, and validation risk (2026-10-04)

- Ranked five distinct methods with layers, off-catalogue rationale, comparison to this blank repo/reference, qualitative DTI opportunity, cost, and verified source/access status.
- Corrected a common orientation shortcut: scalar dilatation/shear/second invariant bands do not identify a principal direction; local GNSS strain/stress needs a full tensor plus uncertainty. The prior is a weak, spatially varying objective penalty, not a hard output filter.
- Separated fault discovery from geothermal favorability: resource layers may improve geological relevance but are not ground truth and can lower DTI recall.
- Predeclared spatial blocks, training collar, metric buffer, matched-budget baseline comparison, ablations, and release gate. Marked this as unrun because data are absent.
- **Outcome:** no numeric DTI-benefit forecast is claimed.

## Pass 3 — code, edge cases, site, and hand-off (2026-10-04)

- Added analytic DTI tests (offset, redundant predictions, empty truth, NoData mask, anisotropic pixels and range failures); differentiability/orientation tests; block-fold leakage tests; and template-bound GeoTIFF round-trip/range tests.
- Writer is designed to use the official sample mask rather than feature-derived nodata, preserve exact transform/CRS/shape, write float32 and NaN outside, disable TIFF predictor, write atomically, reread bytes, and hash a manifest. A local pass is explicitly not portal acceptance.
- Site and executive-summary guide must label the missing official data/no-TIF condition before any download control; no dummy raster may be labelled a submission.
- **Outcome:** 28 tests passed; Ruff passed; static-site link/download/warning check passed; the missing-input audit returned the expected exit 2. The only test-run warnings were removed by using explicit affine transforms; the final test run was clean. No PR/merge is claimed until GitHub reports completion.
