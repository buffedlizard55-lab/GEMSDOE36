"""Fail-closed MTO-36 release + historical score provenance regression tests."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_mto_site import current_branch, ensure_status, site_table  # noqa: E402
from verify_mto_release import verify_all  # noqa: E402


def _card_and_ledger() -> tuple[dict, dict]:
    return (
        json.loads((ROOT / "evidence/mto36_run_card_20261026.json").read_text()),
        json.loads((ROOT / "evidence/focus_sites_9repo_summary_20261026.json").read_text()),
    )


def test_current_negative_release_is_locally_valid_but_never_submit_authorized() -> None:
    result = verify_all(ROOT)
    assert result["passed"], result["errors"]
    assert result["verdict"] == "negative"
    assert result["download_research"] is True
    assert result["download_and_submit"] is False


def test_generator_fails_closed_if_verdict_or_historical_score_labels_forged() -> None:
    card, ledger = _card_and_ledger()
    ensure_status(card, ledger)
    promoted = deepcopy(card)
    promoted["submit_ok"] = True
    with pytest.raises(RuntimeError, match="research download"):
        ensure_status(promoted, ledger)
    fake_score = deepcopy(ledger)
    fake_score["focus_sites"][6]["highest_historical_submission"]["score_label"] = "ORGANIZER-CONFIRMED"
    with pytest.raises(RuntimeError, match="owner-reported"):
        ensure_status(card, fake_score)


def test_working_branch_is_read_from_checkout_not_a_historical_run_card(monkeypatch) -> None:
    class Result:
        stdout = "arena/test-branch\n"

    def fake_run(*args, **kwargs):
        assert args[0] == ["git", "branch", "--show-current"]
        return Result()

    monkeypatch.setattr("build_mto_site.subprocess.run", fake_run)
    assert current_branch() == "arena/test-branch"


def test_nine_pinned_links_measured_not_organizer_authenticated() -> None:
    _, ledger = _card_and_ledger()
    table = site_table(ledger)
    checked = json.loads((ROOT / "evidence/mto36_ninesite_forensics.json").read_text())
    assert len(checked["sites"]) == 9
    for site in checked["sites"]:
        assert site["pinned_source_url"] in table
        assert site["sha256"][:12] in table
        assert f"{site['reported_score_not_organizer_authenticated']:.4f} OWNER-REPORTED" in table
    assert "ORGANIZER-CONFIRMED" not in table
    assert checked["nested_family_crosschecks"]["b2_vs_d28_gt_2px_xor"] == 0
    assert checked["nested_family_crosschecks"]["d28_removed_to_b2"] == 6436
    assert checked["nested_family_crosschecks"]["solo_removed_to_b2"] == 2545
