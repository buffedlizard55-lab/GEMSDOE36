import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import spearmanr

_RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_gsewc36_experiment.py"
_SPEC = importlib.util.spec_from_file_location("gsewc36_runner_test", _RUNNER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_RUNNER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RUNNER)
_rank_correlation_with_binary_reference = _RUNNER._rank_correlation_with_binary_reference


def test_binary_registry_surface_rank_correlation_matches_spearmanr():
    surface = np.array(
        [[0.1, 0.1, 0.2, 0.4], [0.7, 0.8, 0.0, 0.3], [0.9, 0.1, 0.5, 0.2]],
        dtype=np.float32,
    )
    reference = np.array(
        [[1, 0, 0, 1], [0, 1, 0, 0], [1, 0, 1, 0]],
        dtype=bool,
    )
    footprint = np.ones(surface.shape, dtype=bool)

    got = _rank_correlation_with_binary_reference(surface, reference, footprint)
    expected = float(spearmanr(surface.ravel(), reference.ravel()).statistic)

    assert got == pytest.approx(expected, abs=1e-12)


def test_registry_rank_correlation_respects_footprint_mask():
    surface = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    reference = np.array([[0, 1], [1, 0]], dtype=bool)
    footprint = np.array([[True, True], [False, False]])

    got = _rank_correlation_with_binary_reference(surface, reference, footprint)

    assert np.isfinite(got)
    assert got == pytest.approx(1.0)
