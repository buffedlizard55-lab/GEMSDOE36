# Public Pages · current research release

GitHub Pages content for GEMSDOE36 (`main:/`, root `index.html` redirects to `docs/`).

**Current file (MTO-36): DOWNLOAD: YES for research · DO NOT SUBMIT.** Its original GeoTIFF passes *local* template-grid, finite `[0,1]` and ZIP checks but fails both matched-holdout promotion and the literal any-registry 70% overlap gate. No DrivenData slot was used; no organizer score exists. It is **not** a cleared competition entry. See [`current-run.json`](current-run.json), [run card](downloads/mto36-run-card.json), [research TIFF](downloads/gemsdoe36-mto36-ortho-contact-20261026-c41282e9da7a-zeros.tif), [ZIP](downloads/gemsdoe36-mto36-ortho-contact-20261026-c41282e9da7a-zeros.zip), [nine-site report](research/mto36-evidence-and-nine-sites.md) and the [executive submission guide](executive-summary.html).

- `index.html`: prominent current verdict/download/holdout/uniqueness, nine pinned historical artifact links with **owner-reported** (not organizer-receipt-verified) scores; older negative lanes (including merged parallel MOE36) archived below.
- `assets/live-feed.js`: optional GitHub public commit timestamps only. It cannot and does not monitor authenticated competition scores or submission-page receipts; check the official leaderboard manually.
- `downloads/mto36-run-card.json`, `downloads/focus9-verified-source-ledger.json`, `downloads/focus9-source-integrity.json`: mirrors of machine-readable evidence in `evidence/`, refreshed by `python scripts/build_site.py`. The original per-TIFF `.receipt.json` is identical to the run card.
- `downloads/GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif`: synthetic QA fixture only, never for upload.
- `research/`: current source-linked MTO audit and clearly archived earlier research. `research/leaderboard.md` is superseded and must **not** be cited for current standings.

Regenerate with `python scripts/build_site.py` (delegates to `scripts/build_mto_site.py`, no longer overwrites current pages with the CTRB/GPS-only snapshot). Verify with `python scripts/check_site.py` and `python scripts/verify_mto_release.py` after restoring pinned owner mirrors. The original official competition and USGS data were not independently fetched in this run; the former owner-GitHub mirrors are integrity-checked only. A portal acceptance claim requires an actual organizer receipt.
