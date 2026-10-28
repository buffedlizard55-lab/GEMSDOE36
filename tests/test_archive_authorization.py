import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_release import archive_review_row  # noqa: E402


def test_historical_format_and_claimed_promotion_cannot_authorize_slot():
    for name in ("gemsdoe36-atvr36-20261026.tif", "another.tif"):
        row = archive_review_row(Path(name), "abc", {"passed": True}, {"verdict": "promote"})
        assert row["submit_ready"] is False
        assert "DO NOT SUBMIT" in row["reason"]
