import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_release import archive_review_row, validate_archive_raster  # noqa: E402


def test_archive_raster_always_uses_strict_outside_footprint_rule(monkeypatch):
    import audit_release

    calls = []

    class Report:
        def to_dict(self):
            return {"passed": False}

    monkeypatch.setattr(
        audit_release, "validate_submission",
        lambda path, template, **kwargs: (calls.append(kwargs), Report())[1],
    )
    for name in ("candidate-zeros.tif", "gemsdoe36-atvr36-20261026.tif"):
        validate_archive_raster(Path(name), Path("sample.tif"))
    assert calls == [
        {"require_nonfinite_outside": True},
        {"require_nonfinite_outside": True},
    ]


def test_historical_format_and_claimed_promotion_cannot_authorize_slot():
    for name in ("gemsdoe36-atvr36-20261026.tif", "another.tif"):
        row = archive_review_row(Path(name), "abc", {"passed": True}, {"verdict": "promote"})
        assert row["submit_ready"] is False
        assert "DO NOT SUBMIT" in row["reason"]
