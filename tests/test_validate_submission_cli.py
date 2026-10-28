"""The pre-upload CLI must give identical bytes an identical verdict, whatever the filename.

Regression for an audit finding (28 Oct 2026): the CLI previously relaxed the outside-footprint
rule when the filename ended in ``-zeros.tif``, so byte-identical files could pass or fail
depending only on their names. The official format says data outside the bounds is null or NaN.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "validate_submission.py"
TEMPLATE = ROOT / "data" / "raw" / "sample_submission.tif"
NAN_TWIN = (
    ROOT
    / "docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-nan.tif"
)

rasterio = pytest.importorskip("rasterio")


def _run(path: Path, *extra: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(CLI), str(path), "--json", *extra],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, json.loads(proc.stdout)


@pytest.mark.skipif(not (TEMPLATE.is_file() and NAN_TWIN.is_file()), reason="inputs not restored")
def test_same_bytes_same_verdict_regardless_of_name(tmp_path):
    with rasterio.open(NAN_TWIN) as ds:
        profile = ds.profile.copy()
        values = ds.read(1)
    zeros_outside = np.where(np.isnan(values), 0.0, values).astype("float32")
    profile.update(nodata=None)
    paths = {}
    for name in ("candidate-nan.tif", "candidate-zeros.tif"):
        paths[name] = tmp_path / name
        with rasterio.open(paths[name], "w", **profile) as dst:
            dst.write(zeros_outside, 1)
    assert paths["candidate-nan.tif"].read_bytes() == paths["candidate-zeros.tif"].read_bytes()

    code_nan, rep_nan = _run(paths["candidate-nan.tif"])
    code_zeros, rep_zeros = _run(paths["candidate-zeros.tif"])
    # Default (strict) mode: finite values outside the footprint are rejected under both names.
    assert code_nan == code_zeros == 1
    assert rep_nan["passed"] is False and rep_zeros["passed"] is False
    assert rep_nan["errors"] == rep_zeros["errors"]

    # Explicit opt-in is the only way to accept the historical zeros-outside profile.
    code_opt, rep_opt = _run(paths["candidate-nan.tif"], "--zeros-mode")
    assert code_opt == 0 and rep_opt["passed"] is True


@pytest.mark.skipif(not (TEMPLATE.is_file() and NAN_TWIN.is_file()), reason="inputs not restored")
def test_official_nan_outside_twin_passes_strict_mode():
    code, report = _run(NAN_TWIN)
    assert code == 0 and report["passed"] is True
    assert report["finite_outside_bounds"] == 0
    assert report["minimum"] >= 0.0 and report["maximum"] <= 1.0
