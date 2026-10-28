import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_registry_coverage as arc  # noqa: E402


def test_bound_reproduces_recorded_reg052_numbers():
    # Numbers recorded in evidence/literal_bound_20261027.json for reg-052.
    footprint, covered = 5167373, 5160724
    assert arc.first_forced_count(footprint, covered) == 22164
    share = arc.forced_overlap_bound(footprint, covered, 37654)
    assert round(share, 4) == 0.8234
    assert int(round(share * 37654)) == 31005


def test_coverage_counts_only_footprint_cells_within_radius():
    footprint = np.zeros((9, 9), dtype=bool)
    footprint[:, :] = True
    dots = np.zeros((9, 9), dtype=bool)
    dots[4, 4] = True
    # Euclidean disk of radius 3 around the centre dot: cells with d^2 <= 9.
    expected = sum(1 for y in range(9) for x in range(9) if (y - 4) ** 2 + (x - 4) ** 2 <= 9)
    assert arc.coverage_within_radius(dots, footprint, 3) == expected
    assert arc.coverage_within_radius(np.zeros((9, 9), dtype=bool), footprint, 3) == 0


def test_forced_share_is_one_when_reference_covers_everything():
    # Every footprint cell is within radius of the reference, so no dot can be unmatched.
    assert arc.forced_overlap_bound(100, 100, 50) == 1.0
    assert arc.first_forced_count(100, 100) == 1
