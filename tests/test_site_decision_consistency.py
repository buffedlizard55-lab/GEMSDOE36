"""Prevent withdrawn forecasts and selector overrides from returning to current Pages."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_pages_and_generators_do_not_revive_unsafe_claims():
    paths = [
        "docs/index.html", "docs/executive-summary.html", "scripts/build_s2d_site.py",
        "scripts/publish_tcd36_site.py", "scripts/build_kpl_site.py",
    ]
    banned = (
        "if selector overrides", "human selector review required", "human selector required",
        "Why GEMSDOE32 B2 achieved", "PhD synthesis of why GEMSDOE32 B2 achieved",
        "0.205–0.238 peer-matched scenario", "<strong>Scenario estimate ",
        "fixes prior portal error",
    )
    for path in paths:
        text = (ROOT / path).read_text(encoding="utf-8")
        for phrase in banned:
            assert phrase not in text, f"{path} contains unsafe claim: {phrase}"
