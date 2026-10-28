"""Historical H36 audit must not silently skip raster validation or approve uploads."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "verify_release_gate", ROOT / "scripts" / "verify_release_gate.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_missing_inputs_fail_closed(monkeypatch):
    mod = load_gate()
    original = Path.is_file

    def missing_raw(path):
        if path in (ROOT / "data/raw/sample_submission.tif", ROOT / "data/raw/labels.tif"):
            return False
        return original(path)

    monkeypatch.setattr(Path, "is_file", missing_raw)
    report = mod.verify_all(ROOT)
    assert not report["passed"]
    assert not report["raster_validation_performed"]
    assert not report["safe_to_download_and_submit"]
    assert any("Fresh raster validation unavailable" in e for e in report["errors"])


def test_wrong_input_hash_fails_closed(monkeypatch):
    mod = load_gate()
    original = Path.is_file
    sha = mod.sha256_file
    raw = {ROOT / "data/raw/sample_submission.tif", ROOT / "data/raw/labels.tif"}
    monkeypatch.setattr(Path, "is_file", lambda path: True if path in raw else original(path))
    monkeypatch.setattr(mod, "sha256_file", lambda path: "wrong" if path in raw else sha(path))
    report = mod.verify_all(ROOT)
    assert not report["passed"]
    assert not report["raster_validation_performed"]
    assert not report["safe_to_download_and_submit"]
    assert any("Raster input hash mismatch" in e for e in report["errors"])
