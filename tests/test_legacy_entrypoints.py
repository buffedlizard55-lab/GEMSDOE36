"""Unsafe historical scientific gates must not execute, even without data."""
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("name,reason", [
    ("run_pipeline.py", "copies historical submission pixels"),
    ("run_holdout.py", "exposes SGMC evaluation truth"),
])
def test_legacy_entrypoint_fails_closed(name, reason):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root / "scripts" / name)],
                            check=False, capture_output=True, text=True, cwd=root)
    assert result.returncode != 0
    assert reason in result.stderr
    assert "Traceback" not in result.stderr
