"""Fail closed if any vendored shared-template file differs from its pinned upstream bytes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_vendored_template_is_byte_identical():
    pins = json.loads((ROOT / "registry/template_pins.json").read_text())
    assert pins["files"], "no pinned files"
    for row in pins["files"]:
        data = (ROOT / row["local"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row["sha256"], row["local"]
        assert len(data) == row["bytes"], row["local"]
        assert row["upstream_commit"] == "fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1"


def test_template_metric_matches_official_worked_example():
    from gems.metric import verify_organizer_worked_example

    r = verify_organizer_worked_example()
    assert r["matches_0_60"] and r["DTI_rounded_2dec"] == 0.60
