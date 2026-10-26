"""Regression tests for truthful cross-group restore receipts."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from restore_data import collect_verified_entries  # noqa: E402


def test_receipt_includes_verified_prior_groups_and_excludes_missing_or_changed_files(
    tmp_path: Path,
) -> None:
    core_bytes = b"verified core fixture"
    scored_bytes = b"verified scored fixture"
    corrupt_bytes = b"not the manifest bytes"
    entries = [
        {
            "id": "core",
            "dest": "core/input.bin",
            "group": "core",
            "sha256": hashlib.sha256(core_bytes).hexdigest(),
        },
        {
            "id": "scored",
            "dest": "scored/reference.bin",
            "group": "scored",
            "sha256": hashlib.sha256(scored_bytes).hexdigest(),
        },
        {
            "id": "external-missing",
            "dest": "external/absent.bin",
            "group": "external",
            "sha256": hashlib.sha256(b"absent").hexdigest(),
        },
        {
            "id": "external-corrupt",
            "dest": "external/corrupt.bin",
            "group": "external",
            "sha256": hashlib.sha256(b"expected, not present").hexdigest(),
        },
    ]
    for relative, payload in (
        ("core/input.bin", core_bytes),
        ("scored/reference.bin", scored_bytes),
        ("external/corrupt.bin", corrupt_bytes),
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    result = collect_verified_entries(
        {"files": entries},
        tmp_path,
        [{"id": "scored", "status": "restored"}],
    )

    assert [(row["id"], row["status"]) for row in result] == [
        ("core", "present"),
        ("scored", "restored"),
    ]
    assert all(row["bytes"] > 0 for row in result)
    assert all(row["sha256"] == next(item["sha256"] for item in entries if item["id"] == row["id"]) for row in result)
