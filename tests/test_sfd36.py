import json
from pathlib import Path

import numpy as np

from gemsdoe36.sfd_features import SFD_FEATURES, build_sfd_features

ROOT = Path(__file__).resolve().parents[1]


def test_sfd_features_shape_and_finite_on_fp():
    rng = np.random.default_rng(0)
    shape = (40, 40)
    fp = np.ones(shape, bool)
    cols = {n: rng.normal(size=shape).astype(np.float32) for n in
            ("org_det_elev", "org_rtp", "org_iso_grav_anom", "org_det_elev_slope", "lid_step_max")}
    cols["lid_valid"] = np.ones(shape, np.float32)
    out = build_sfd_features(cols, fp)
    assert tuple(out) == SFD_FEATURES and len(out) == 12
    for a in out.values():
        assert a.shape == shape and np.isfinite(a[fp]).all()


def test_sfd_run_card_gates():
    card = json.loads((ROOT / "evidence/sfd36_run_card_20261027.json").read_text())
    assert card["verdict"] == "negative" and card["gates"]["G3_literal_any_registry"] is False  # literal registry rule (amendment)
    assert card["holdout"]["best_arm"] == "EXP-2"
    assert card["holdout"]["arms"]["EXP-2"]["dti"] > 0.170100  # beats KPL-36
    assert card["leakage_canary"]["max_symmetric_auc"] <= 0.90
    assert card["uniqueness_vs_focus9"]["max_champion_3px_dot_overlap"] <= 0.70  # champions only; literal gate fails vs reg-052
    assert len(card["submission"]["note"]) <= 140
    assert card["submission"]["dots"] == 37654
