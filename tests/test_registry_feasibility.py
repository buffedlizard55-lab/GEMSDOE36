"""Regression tests for the strict lattice-overlap impossibility bound."""
import json
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import pytest

from gemsdoe36.feasibility import PreflightError, inspect_registered_lattice, overlap_bound

ROOT = Path(__file__).resolve().parents[1]


def test_pigeonhole_boundary_strict_not_greater_or_equal():
    # 3 uncovered out of 10 candidates => exactly 70%, which is allowed by this gate.
    at = overlap_bound(20, 17, 10)
    assert at["minimum_overlapping_dots"] == 7
    assert at["minimum_overlap_fraction"] == 0.7
    assert at["guaranteed_duplicate"] is False
    assert at["first_dot_count_forced_over_threshold"] == 11
    assert overlap_bound(20, 17, 11)["guaranteed_duplicate"] is True


def test_bound_is_one_sided_not_a_pass():
    b = overlap_bound(100, 50, 10)
    assert b["minimum_overlap_fraction"] == 0
    assert b["guaranteed_duplicate"] is False
    assert b["first_dot_count_forced_over_threshold"] is None


@pytest.mark.parametrize("args", [(0, 0, 1), (10, 11, 1), (10, -1, 1), (10, 2, 0), (10, 2, 11), (10, 2, True)])
def test_invalid_counts_raise(args):
    with pytest.raises(ValueError):
        overlap_bound(*args)


def test_invalid_threshold_raise():
    with pytest.raises(ValueError):
        overlap_bound(10, 8, 2, Fraction(1))


def test_real_lattice_when_owner_mirrors_are_present():
    if not (ROOT / "data/raw/sample_submission.tif").is_file():
        pytest.skip("restore SHA-pinned core/scored owner mirrors to recompute preflight")
    lattice = ROOT / "data/raw/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
    if not lattice.is_file():
        pytest.skip("restore SHA-pinned scored owner mirrors to recompute preflight")
    r = inspect_registered_lattice(ROOT)
    card = json.loads((ROOT / "evidence/registry_preflight_run_card_20261026.json").read_text())
    assert r == card["registry"]["literal_preflight"]
    assert r["reference_id"] == "reg-052"
    assert r["reference_dots"] == 206_895
    b = r["bound"]
    assert (b["footprint_pixels"], b["covered_pixels"], b["uncovered_pixels"]) == (5_167_373, 5_160_724, 6_649)
    assert b["minimum_overlapping_dots"] == 31_005
    assert b["minimum_overlap_fraction"] == pytest.approx(31_005 / 37_654)
    assert b["guaranteed_duplicate"] is True
    assert b["first_dot_count_forced_over_threshold"] == 22_164


def test_missing_pinned_inputs_fail_closed(tmp_path):
    (tmp_path / "registry").mkdir()
    for name in ("data_manifest.json", "uniqueness_registry.json"):
        (tmp_path / "registry" / name).write_bytes((ROOT / "registry" / name).read_bytes())
    with pytest.raises(PreflightError, match="Missing or hash-mismatched"):
        inspect_registered_lattice(tmp_path)


def test_actual_budget_threshold_transition():
    below = overlap_bound(5_167_373, 5_160_724, 22_163)
    above = overlap_bound(5_167_373, 5_160_724, 22_164)
    assert below["guaranteed_duplicate"] is False
    assert above["guaranteed_duplicate"] is True


def test_lower_bound_matches_exhaustive_subsets_on_small_footprints():
    for n in range(1, 9):
        for covered in range(n + 1):
            for k in range(1, n + 1):
                actual = min(sum(i < covered for i in selected)
                             for selected in combinations(range(n), k))
                assert overlap_bound(n, covered, k)["minimum_overlapping_dots"] == actual
