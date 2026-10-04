# Score attribution and prior-site history

**Review date:** 2026-10-04 UTC. This is an attribution audit, not a leaderboard mirror. The [official live leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) is authoritative for current public standings; consult it manually. No score table, participant names, scraper, poller, or live feed is stored here. DrivenData's [Terms of Use](https://www.drivendata.org/termsofuse/) restrict automated monitoring/copying and manual monitoring/copying without prior written consent.

## Reported values in the request

- **`0.2778`: not attributable to a GEMSDOE32 file or this repository.** No organizer receipt, submission ID, file hash, or owner-to-account mapping is present here. A number seen in a public board cannot prove which file produced it.
- **`0.3195` as “current highest”: not verified.** A one-time read of the public page on 2026-10-04 showed entries above that user-supplied value. No detailed scoreboard snapshot is retained. Rankings change; the value must not be treated as current without manually checking the official page.
- **`0.2708`: contradictory owner-site history.** GEMSDOE31's README describes an owner-reported geometry “behind” a 0.2708 row. GEMSDOE32's own later verification says its linked H33-2-B2 artifact is unscored, states that no organizer score exists for its artifacts, and questions whether the 0.2708 row was actually theirs. Neither site supplies an organizer receipt that resolves this contradiction. Treat 0.2708 as an owner/user report with unresolved attribution—not as a local baseline.

## What the GEMSDOE32 site actually establishes

The [GEMSDOE32 repository README](https://github.com/buffedlizard55-lab/GEMSDOE32) is useful prior art, but explicitly separates organizer scores from local instruments/projections:

- It labels the H33-2-B2 downloadable artifact **UNSCORED** and describes 0.2747 as a model projection, not an organizer return. Its note reports a 37,654-pixel emission formed by removing cells within 200 m of the public catalogue from a prior candidate; it labels the live-mirror gain/projection as unscored.
- The README says **no organizer score exists for any artifact in that repository**. That statement does not substantiate the request's 0.2778 value.
- Its own history reports a previous download-selection mismatch: the site advertised a candidate that underperformed the file named in the slot table; a later site audit corrected the link. This is a useful process failure to guard against: site primary/download, manifest, measured file, and submission name must all resolve to the same bytes.
- A local “live-mirror” or proxy improvement can motivate a hypothesis but does not identify the private hidden truth, prove a public board score, or authorize a weekly slot.

**Decision for GEMSDOE36:** do not copy the H33-2-B2 TIFF or its pixels, and do not adopt the 200 m exclusion as a default. DrivenData staff say known-fault pixels are masked from evaluation; the public description's 300 m kernel may still reward a distinct nearby hidden trace. Any such emission policy would need a fresh, matched spatial holdout under the official scoring mask.

## Other site-history warnings

- The [GEMSDOE31 README](https://github.com/buffedlizard55-lab/GEMSDOE31) labels the 0.2708 row as owner-reported, says no organizer receipt exists, and does not promote proxy gains to slot-approved results. Its own decision was to hold the slot pending stronger evidence.
- The [GEMSDOE25 README](https://github.com/buffedlizard55-lab/GEMSDOE25) records the 0.3195 claim as user/owner-reported and unverified. GEMSDOE32's later source audit flags that ranking claim as stale relative to its single public-page observation. We preserve neither its score table nor a mirrored ranking here.
- GEMSDOE25/31/32 repositories contain large owner mirrors of competition data and historical outputs. **This repository has not copied or consumed those raster files.** Only public documentation/evidence labels were reviewed for learning; authorized local competition data are still absent.

## Terms and procedure

One public page read occurred on 2026-10-04 in response to the explicit request. Because the platform Terms prohibit monitoring/copying absent written permission, we do not refresh, scrape, reproduce participant names, or store a score history. If a future run needs current standings, open the official page manually; do not use them as spatial-holdout evidence. Ask the organizer for written permission or an authorized API before retaining a snapshot.
