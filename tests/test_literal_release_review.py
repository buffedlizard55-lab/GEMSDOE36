"""Regression: a format-valid, holdout-improving artifact can still be ineligible."""
import json
from pathlib import Path

from gemsdoe36.feasibility import overlap_bound

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def test_kpl_literal_duplicate_revokes_release():
    review = load('evidence/literal_release_review_20261027.json')
    card = load('evidence/kpl36_run_card_20261026.json')
    current = load('docs/current-run.json')
    manifest = load('docs/downloads/submissions_manifest.json')
    assert review['registry']['dot_overlap_3px'] > 0.70
    assert review['verdict'] == card['verdict'] == current['verdict'] == 'negative'
    assert not all(card['gates'].values())
    assert current['ok_to_download_and_submit'] is False
    assert current['slot_approved'] is False
    assert manifest['current_candidate'] is None
    assert manifest['research_candidate']['submit_ok'] is False
    assert all(review['validator'].values())  # validity alone must never imply authorization
    assert review['reported_result']['receipt'] is None
    assert review['calibrated_leaderboard_estimate'] is None
    assert len(review['note']) <= 140


def test_recorded_bound_recomputes_exactly():
    bound = load('evidence/literal_bound_20261027.json')['bound']
    assert overlap_bound(bound['footprint_pixels'], bound['covered_pixels'],
                         bound['candidate_distinct_dots']) == bound
    assert bound['guaranteed_duplicate']


def test_public_pages_show_superseding_stop():
    for name in ('index.html', 'executive-summary.html'):
        text = (ROOT / 'docs' / name).read_text()
        assert text.count('<!-- LITERAL_REVIEW:START -->') == 1
        assert 'DO NOT SUBMIT — literal uniqueness gate failed' in text
        assert '0.1647 USER-REPORTED' in text
        assert 'downloads/literal-release-review.json' in text
