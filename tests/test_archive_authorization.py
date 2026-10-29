import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_release  # noqa: E402
from audit_release import archive_review_row  # noqa: E402


def test_historical_format_and_claimed_promotion_cannot_authorize_slot():
    for name in ("gemsdoe36-atvr36-20261026.tif", "another.tif"):
        row = archive_review_row(Path(name), "abc", {"passed": True}, {"verdict": "promote"})
        assert row["submit_ready"] is False
        assert "DO NOT SUBMIT" in row["reason"]


def test_archive_validation_is_strict_and_filename_invariant(monkeypatch):
    calls = []

    def fake_validate(path, template, *, require_nonfinite_outside):
        calls.append((Path(path).name, Path(template).name, require_nonfinite_outside))
        return object()

    monkeypatch.setattr(audit_release, "validate_submission", fake_validate)
    for name in (
        "candidate-nan.tif",
        "candidate-zeros.tif",
        "gemsdoe36-atvr36-20261026.tif",
    ):
        audit_release.validate_archived_raster(Path(name), Path("sample_submission.tif"))

    assert calls == [
        ("candidate-nan.tif", "sample_submission.tif", True),
        ("candidate-zeros.tif", "sample_submission.tif", True),
        ("gemsdoe36-atvr36-20261026.tif", "sample_submission.tif", True),
    ]
