# Three-pass review receipt — 28 October 2026

## Pass 1 — implement and verify

- Restored 30 SHA-pinned core/external/scored owner-mirror files; this is integrity verification, not organizer authentication. Prepared all 19 feature bands after checking template/labels/features CRS, shape, exact transform, bands and footprint. Staged cache and manifest writes now roll back on handled failure; sudden process/power failure across filesystems is not guaranteed atomic.
- Independently reproduced the 37,654-dot literal registry bound (82.341849% minimum), KPL's 99.168747% overlap and local format checks; rechecked nine historical raster hashes, lineage and 72 directed pairwise comparisons. None of these comparisons authorizes submission.
- Reproduced the shared novelty comparator's missing CRS/transform validation and reported [GEMSDOE24 issue #77](https://github.com/buffedlizard55-lab/GEMSDOE24/issues/77); pinned shared bytes remain unchanged.
- Added a current negative no-candidate run card and reviewed official problem, metric, rules, source pages and public leaderboard; no model experiment or slot was used.

## Pass 2 — review and fix

- Found that legacy generators could reinstate KPL upload/slot-spending instructions, unsupported portal-error causation and withdrawn projections. Consolidated active entrypoints onto one fail-closed, source-checked publisher, preserving historical research bundles, cards and both S2D/TCD summaries. Added idempotence, mutation and negative-manifest tests.
- Removed a format-only historical ATVR authorization shortcut. The refreshed format-only audit inspected 23 archived TIFFs: 22 passed their local format checks; the deliberately small format fixture failed; zero were promoted. Improved core raster grid/mask preflight and staged-cache rollback tests; repaired a data-dependent test's partial-restore behavior while retaining its static source assertion.
- Clarified the B2 lineage interpretation and official FP 0.2 / FN 0.8 weights, distinguished owner reports from organizer receipts, and preserved the standing owner brief byte-for-byte.
- Initial full local check: 186 passed, 1 skipped (optional PyTorch absent); Ruff, Pages/link checks, JavaScript syntax and archived MTO validation passed. Final checks follow integration with updated main.

## Pass 3 — recheck original requirements

- No lane-defining method paragraph was identified. Three genuinely distinct leads are ranked as blocked proposals with physics, mimics, sources, differences and data/rights gates; no new hypothesis was implemented or purported TIFF produced. No numerical leaderboard forecast is justified.
- The negative run card has null new-candidate holdout, registry, raster, validator, submission name and note fields. Historical S2D results are explicitly labeled as prior and not rerun. Neither a slot nor an organizer receipt was fabricated.
- The separate selector, ≤3-experiment/two-hour ceiling, whole-segment buffered holdout, per-feature leakage canaries, surface/final-dot thresholds, official template and outside-NaN caveat are documented. The session start time was not captured; no under-two-hour claim is made.
- Main advanced with a concurrent safety review during this session; integrated its historical release-gate fix and preserved its separate run card and research record. After integration and a final feature-mask/forged-evidence review, the full local suite reported **191 passed, 1 skipped** (optional PyTorch absent); Ruff, Pages/link checks, JavaScript syntax, historical H36 fresh raster validation and archived MTO validation passed. Final PR/merge state is recorded by GitHub, not inferred in advance.

## Current-checkout re-run after data restore — 28 October 2026

- Restored 30 files listed in `registry/data_manifest.json` from pinned GitHub owner mirrors (591,020,452 bytes total), verified hashes, and reran preparation. These data remain owner mirrors, not organizer-authenticated source files.
- Downloaded the ten hash-pinned focus comparison rasters to the ignored cache, then reran `audit_focus_sources.py` (9 sites plus all 8 inherited family checks) and `audit_focus_uniqueness.py` (72 directed pairs; no site unique vs all eight). The first audit attempt before caching those rasters failed closed on a missing file; the cache step resolved that input omission.
- Re-ran `registry_feasibility.py`; expected exit 2 and the bound was reproduced: at 37,654 dots minimum overlap is 31,005 / 37,654 = 82.341849%; the literal gate forces a stop from 22,164 dots. Concurrent `registry_coverage_audit_20261028.json` shows reg-052 is a regular 5-pixel lattice covering 99.8713% of the footprint, so this comparison is degenerate and is not proof of actual candidate duplication. The protocol still blocks a candidate; changing the threshold or omitting the raster would require explicit owner approval. No candidate raster was created.
- Final checkout verification after the publisher/test update: `pytest -q` reported **195 passed, 1 skipped** (optional Torch missing); Ruff and `scripts/check_site.py` passed. No model experiment or submission slot was used. The missing lane assignment still blocks holdout experiments; data restoration does not relax the strict registry gate.

## Open limitations

- Shared comparator fix remains upstream; template bytes cannot be privately patched under the protocol.
- Pinned mirrors do not prove organizer authenticity; current account-side submission quota and portal acceptance were not verified. The precise cause of the reported range error is unknown.
- A unique, high-scoring new TIFF, its validation/holdout, and an independently selected submission remain unfulfilled and blocked. No competition slot was consumed.
