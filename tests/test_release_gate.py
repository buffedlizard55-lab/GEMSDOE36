"""Automated project release gate test: verifies Run Card, GeoTIFFs, uniqueness, canary, and HTML links."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_automated_release_and_submission_gate() -> None:
    spec = importlib.util.spec_from_file_location(
        "verify_release_gate", ROOT / "scripts" / "verify_release_gate.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    report = mod.verify_all(ROOT)
    assert report["passed"], f"Automated release gate failed: {report['errors']}"
    assert report["ok_to_download_research_tif"] is True
    assert report["verdict"] in ("promote", "negative")
    assert report["safe_to_download_and_submit"] == (report["verdict"] == "promote")
