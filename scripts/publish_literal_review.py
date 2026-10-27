"""Publish superseding literal-protocol decision without deleting historical evidence."""
from __future__ import annotations

import json
import re
from pathlib import Path


def publish(root: Path) -> None:
    review = json.loads((root / 'evidence/literal_release_review_20261027.json').read_text())
    if review['verdict'] != 'negative' or review['submit_ok']:
        raise ValueError('This publisher cannot authorize submissions')
    warning = '''<!-- LITERAL_REVIEW:START -->
<section aria-label="Superseding protocol review" style="padding:1.5rem;border:3px solid #ad3434;margin:1rem">
<h2>DO NOT SUBMIT — literal uniqueness gate failed</h2>
<p>27 October 2026: KPL overlap with registry reg-052 is <strong>99.17%</strong>, above the 70% limit.
The downloadable TIFF is <strong>research only</strong>. No new TIFF or slot was authorized.</p>
<p>Latest KPL result: <strong>0.1647 USER-REPORTED</strong>, no organizer receipt.
No calibrated leaderboard estimate is available; the older scenario range is withdrawn as a forecast.</p>
<p><a href="research/review-20261027.md">Executive review, ranked hypotheses, limitations and next steps</a> ·
<a href="downloads/literal-release-review.json">Machine-readable run card</a></p>
</section><!-- LITERAL_REVIEW:END -->'''
    for name in ('index.html', 'executive-summary.html'):
        path = root / 'docs' / name
        text = path.read_text()
        text = re.sub(r'<!-- LITERAL_REVIEW:START -->.*?<!-- LITERAL_REVIEW:END -->', '', text, flags=re.S)
        text = re.sub(r'(<main\b[^>]*>)', lambda m: m[0] + warning, text, count=1)
        path.write_text(text)
    (root / 'docs/downloads/literal-release-review.json').write_text(json.dumps(review, indent=2) + '\n')
    path = root / 'docs/current-run.json'
    current = json.loads(path.read_text())
    current.update(slot_approved=False, ok_to_download_and_submit=False,
                   research_downloads_only=True, score_estimate_scenario_range=None,
                   superseding_review='downloads/literal-release-review.json')
    path.write_text(json.dumps(current, indent=2) + '\n')
    path = root / 'docs/downloads/submissions_manifest.json'
    manifest = json.loads(path.read_text())
    manifest['research_candidate'] = manifest.get('current_candidate')
    manifest['current_candidate'] = None
    manifest['slot_approved'] = False
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    path = root / 'README.md'
    text = path.read_text()
    block = '''<!-- LITERAL_REVIEW:START -->
> **27 October 2026 superseding decision: DO NOT SUBMIT.** KPL is a literal-protocol duplicate: 99.17% 3-px overlap with reg-052. The owner reports KPL **0.1647 USER-REPORTED**, not organizer-confirmed. The prior forecast is uncalibrated and withdrawn. No new TIFF, training experiment or submission slot was authorized. See [executive review](docs/research/review-20261027.md) and [reproduced run card](evidence/literal_release_review_20261027.json). The method paragraph assigning this session's lane is absent. Historical cards and reported scores are preserved, not promoted.
<!-- LITERAL_REVIEW:END -->
'''
    text = re.sub(r'<!-- LITERAL_REVIEW:START -->.*?<!-- LITERAL_REVIEW:END -->\n?', '', text, flags=re.S)
    text = text.replace('\n', '\n\n' + block, 1)
    path.write_text(text)
