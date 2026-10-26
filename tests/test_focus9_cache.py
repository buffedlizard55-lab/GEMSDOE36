"""Pinned audit inputs cannot silently move to a branch head or an unrelated file."""
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from cache_focus9_audit import build_tasks  # noqa: E402


def sources():
    ledger = json.loads((ROOT / "evidence/focus_sites_9repo_summary_20261026.json").read_text())
    registry = json.loads((ROOT / "registry/scored_registry.json").read_text())
    return ledger, registry


def test_exact_ten_pinned_audit_inputs():
    ledger, registry = sources()
    tasks = build_tasks(ledger, registry)
    assert len(tasks) == 10
    assert len({(t["repo"], t["path"]) for t in tasks}) == 10
    assert all(len(t["ref"]) == 40 and t["ref"] != "main" for t in tasks)
    assert sum(t["repo"] == "GEMSDOE28" for t in tasks) == 2


def test_mismatched_source_url_fails_closed():
    ledger, registry = sources()
    fake = deepcopy(ledger)
    fake["focus_sites"][0]["highest_historical_submission"]["pinned_raster_source_url"] = \
        "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/main/not-a-pinned-file.tif"
    with pytest.raises(ValueError, match="Invalid pinned source"):
        build_tasks(fake, registry)
