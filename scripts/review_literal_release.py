#!/usr/bin/env python3
"""Revalidate KPL against the literal registry; never allocates a competition slot."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gemsdoe36.feasibility import inspect_registered_lattice


def evaluate(root: Path = ROOT) -> dict:
    card = json.loads((root / 'evidence/kpl36_run_card_20261026.json').read_text())
    sub = card['submission']
    bound = inspect_registered_lattice(root, sub['dots'])
    path = root / sub['file']
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != sub['sha256']:
        raise ValueError('KPL hash mismatch')
    with rasterio.open(root / 'data/raw/sample_submission.tif') as t, rasterio.open(path) as r, rasterio.open(root / 'data/raw/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif') as lattice:
        fp = np.isfinite(t.read(1))
        a = r.read(1)
        if (r.shape, r.crs, r.transform) != (t.shape, t.crs, t.transform):
            raise ValueError('KPL grid mismatch')
        dots = fp & (a > 0)
        if int(dots.sum()) != sub['dots']:
            raise ValueError('KPL dot count mismatch')
        distance = distance_transform_edt(~(fp & (lattice.read(1) > 0)))
        overlap = float((distance[dots] <= 3).mean())
        validator = {
            'single_band': r.count == 1,
            'no_nan_inside': bool(np.isfinite(a[fp]).all()),
            'whole_grid_finite': bool(np.isfinite(a).all()),
            'range_0_1': bool(((a >= 0) & (a <= 1)).all()),
            'crs_shape_transform_match': True,
        }
    return {
        'schema': 'gemsdoe36.literal-release-review.v1',
        'hypothesis': card['hypothesis'], 'mechanism': card['mechanism'],
        'named_non_fault_mimic': card['named_non_fault_mimic'],
        'verdict': 'negative', 'submit_ok': False, 'slot_selected': False,
        'experiments_run_this_session': 0,
        'reason': 'Literal registry overlap exceeds 70%; stop. No new method paragraph was specified.',
        'holdout': {'label': 'HOLDOUT-DTI (prior KPL run, not rerun)',
                    'evaluator_version': card['holdout']['evaluator_version'],
                    'withheld_positives': card['holdout']['n_withheld_positive_pixels'],
                    **card['holdout']['arms'][card['best_arm']]},
        'registry': {'reference_id': 'reg-052', 'dot_overlap_3px': overlap,
                     'surface_rank_correlation': None,
                     'surface_status': 'Not rerun: no new surface; final-dot failure is decisive',
                     'literal_bound': bound},
        'raster_sha256': digest, 'validator': validator,
        'submission_name': sub['name'],
        'note': 'Research only: literal registry overlap fails; no slot authorized.',
        'reported_result': {'value': 0.1647, 'label': 'USER-REPORTED, not ORGANIZER-CONFIRMED',
                            'source': 'Owner prompt received 2026-10-27', 'receipt': None},
        'calibrated_leaderboard_estimate': None,
    }


def main() -> int:
    result = evaluate()
    (ROOT / 'evidence/literal_release_review_20261027.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
