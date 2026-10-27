# Three-pass review — Focus-9 summary and release language (2026-10-27)

## Pass 1 — implement the requested executive decision
- Added a nine-row executive table for GEMSDOE24/25/27/28/30/31/32/33/36 with pinned historical best file links, hashes, dot counts, reported-score provenance, newest additional results supplied by the owner where present, pairwise 3-px overlap, Spearman correlation, leaderboard-estimate status and action.
- Explicitly separated reported scores from prospective estimates. Since no calibrated score transfer or current organizer receipt exists, every estimate is **not estimable**, not a fabricated point estimate.
- Added the same evidence as `evidence/focus9_decision_table_20261027.json`, a Pages-accessible copy under `docs/downloads/`, and a detailed Markdown executive review.
- Kept the selection negative: all nine pinned historical champions fail the pairwise uniqueness rule against at least one of the other eight.

## Pass 2 — audit errors, provenance and confusing UI
- Compared every historical table row against `evidence/focus_sites_9repo_summary_20261026.json` and `evidence/focus_sites_pairwise_uniqueness_20261026.json`; added tests for exact site/file/hash/score/overlap/correlation matches.
- Labeled recent additional score/name entries as owner-prompt transcriptions without pinned bytes or receipts.
- Removed “DOWNLOAD: YES” / “submission GeoTIFF” wording that could be read as upload approval; surviving S2D/TCD/KPL buttons explicitly say research-only / not for submission.
- Replaced the older S2D and KPL leaderboard scenario ranges with “not defensibly estimable / withdrawn”; neither is calibrated to the portal result.
- Corrected the README lattice-bound explanation: 6,649 cells are outside the 3-px neighborhood; the pigeonhole minimum first exceeds 70% at 22,164 dots, not 6,650. A smaller dot count does not prove uniqueness.

## Pass 3 — full requirement and regression check
- Added the table link to the landing-page stop banner, placed the table before research-download sections, checked local links and stable section markers.
- `pytest -q`: **165 passed, 6 skipped**. Skips: PyTorch not installed; raw competition data absent (four tests); local mirror restore needed (one test).
- `ruff check src scripts tests`: passed.
- `scripts/check_site.py`: passed; the current run manifest remains negative and hash-bound to its run card.
- Public copies of the decision JSON and historical summary are byte-identical to their evidence sources.
- No lane experiment or TIFF was produced: the prompt's lane-assignment paragraph is absent, and the current 37,654-dot candidate budget is already proven to violate the literal registry threshold. No submission slot was chosen or spent.

## Open blockers / integrity notes
- Nine-site raster inventory is a pinned 26 October snapshot, not a current full registry refresh.
- Historical score values have no archived DrivenData submission-page receipt; they remain OWNER-/USER-REPORTED.
- Newer names/scores were supplied in the user prompt; they were not fetched from live source pages.
- Official DrivenData pages/data, current leaderboard/cap, and external sources were not freshly fetched in this pass. The user-supplied URLs remain review links, not claimed line-by-line confirmations.
- The 0.2778 B2 mechanism is a plausible lineage/pruning explanation, not proof of hidden-label causality; the available material cannot establish that a new candidate will exceed 0.2778 or current standings.
