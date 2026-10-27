# Three-pass review receipt — 2026-10-27

## Pass 1 — implementation and evidence
- Read README/current decision, shared evaluator, feasibility gate and previous cards.
- Restored SHA-verified sample and lattice via GitHub owner mirrors, not official auth.
- Recomputed literal coverage and KPL final-dot overlap; format checks independently passed.
- Revoked KPL promotion via explicit failing literal-registry gate; historical prior verdict preserved.
- Published research report, reported-result correction and run card. No new candidate/lane or slot.

## Pass 2 — bugs and edge cases
- Initial site checker exposed negative-card/non-null current-candidate mismatch. Fixed the manifest:
  research candidate retained separately; current submission candidate is null.
- Updated an existing mutation test that assumed the current verdict must always be positive:
  it now flips the actual current authorization flags, testing both state directions.
- Restored small pinned external fixtures and catalogue required by pre-existing integration tests.
- Confirmed values, byte hash and dot count before overlap measurement; shared preflight verifies
  template/reference hashes, footprint hash and matching grid before the comparison.

## Pass 3 — original-requirement recheck
- Ran the standard build_site.py path (not only the lane-specific builder): superseding stop persists.
- Added three regression tests for revocation, exact coverage arithmetic and public-page stop notices.
- Full ruff: passed. Full pytest: 157 passed, 1 skipped (PyTorch not installed).
- check_site.py: passed including mirrored card hashes, archives and bundles.
- Not fulfilled: a new unique higher-scoring TIFF, new holdout experiments, all-site live inventory,
  official-source line-by-line research, current standings and slot-cap verification. These are
  explicitly blocked or unverified, not represented as completed.
- Network permits GitHub/npm/PyPI hosts only. Official non-GitHub sources remain links for review,
  not freshly verified content. Public organizer GitHub repository metadata was retrieved with gh.
