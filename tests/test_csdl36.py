"""Unit and integration tests for CSDL-36 and live 9-focus-site refresh."""
from __future__ import annotations

import inspect
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from build_mto_site import ensure_csdl_card  # noqa: E402
from verify_csdl36_release import verify_csdl36  # noqa: E402

from gemsdoe36.csdl_features import (  # noqa: E402
    BASE_FEATURES,
    CSDL_CONDUIT_FEATURES,
    CSDL_STRUCTURAL_FEATURES,
    EXP1_FEATURES,
    EXP2_FEATURES,
    EXP3_BLIND_FEATURES,
    LIDAR_FEATURE_SET,
    load_footprint_grid,
    rasterize_deconfounded_geothermal_layers,
)


def test_csdl36_feature_list_invariants_ir04() -> None:
    assert len(BASE_FEATURES) == 59
    assert len(CSDL_STRUCTURAL_FEATURES) == 16
    assert len(CSDL_CONDUIT_FEATURES) == 12
    assert len(EXP1_FEATURES) == 75
    assert len(EXP2_FEATURES) == 87
    assert len(LIDAR_FEATURE_SET) == 14
    assert len(EXP3_BLIND_FEATURES) == 73
    assert len(set(EXP2_FEATURES)) == 87
    assert set(BASE_FEATURES).isdisjoint(CSDL_STRUCTURAL_FEATURES)
    assert set(BASE_FEATURES).isdisjoint(CSDL_CONDUIT_FEATURES)
    assert set(CSDL_STRUCTURAL_FEATURES).isdisjoint(CSDL_CONDUIT_FEATURES)
    assert set(LIDAR_FEATURE_SET).issubset(EXP2_FEATURES)
    assert set(EXP3_BLIND_FEATURES).isdisjoint(LIDAR_FEATURE_SET)
    assert set(EXP3_BLIND_FEATURES) | set(LIDAR_FEATURE_SET) == set(EXP2_FEATURES)


@pytest.mark.skipif(
    not (ROOT / "data/raw/sample_submission.tif").is_file(),
    reason="data/raw not restored",
)
def test_csdl36_mineralogical_deconfounding_no_det_elev_ir02() -> None:
    src_lines = [
        line for line in inspect.getsource(rasterize_deconfounded_geothermal_layers).splitlines()
        if not line.strip().startswith(("#", '"""'))
    ]
    assert "det_elev" not in "\n".join(src_lines)
    grid = load_footprint_grid(ROOT / "data/raw")
    _, inv = rasterize_deconfounded_geothermal_layers(ROOT / "data/raw", grid)
    assert inv.paleo_throat_in_footprint == 82
    assert inv.paleo_apron_in_footprint == 195
    assert inv.temp2m_stations_in_footprint == 2782
    assert inv.temp2m_positive_dab_in_footprint == 456
    assert inv.geochem_excess_in_footprint == 27092
    assert inv.volcanic_vents_in_footprint == 21


@pytest.mark.skipif(
    not (ROOT / "data/raw/sample_submission.tif").is_file(),
    reason="data/raw not restored",
)
def test_csdl36_release_verification_passes() -> None:
    res = verify_csdl36()
    assert res["lane_id"] == "CSDL-36"
    assert res["verdict"] == "negative"
    assert res["best_arm"] == "EXP-2"
    assert res["holdout_dti"] == pytest.approx(0.155970, abs=1e-6)
    assert res["focus9_passed"] is True
    assert res["focus9_max_overlap_3px"] <= 0.70


def test_ensure_csdl_card_fails_closed_on_mutations() -> None:
    rc = json.loads((ROOT / "evidence/csdl36_run_card_20261026.json").read_text(encoding="utf-8"))
    ensure_csdl_card(rc)

    promoted = deepcopy(rc)
    promoted["verdict"] = "promote"
    with pytest.raises(RuntimeError, match="negative research download"):
        ensure_csdl_card(promoted)

    bad_chron = deepcopy(rc)
    bad_chron["chronology_proof"]["surface_checked_strictly_before_dot_placement"] = False
    with pytest.raises(RuntimeError, match="chronology"):
        ensure_csdl_card(bad_chron)

    bad_sha = deepcopy(rc)
    bad_sha["submission"]["raster_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="artifact mismatch"):
        ensure_csdl_card(bad_sha)


def test_focus9_live_refresh_ledger_integrity() -> None:
    refresh = json.loads((ROOT / "evidence/focus9_live_refresh_20261026.json").read_text(encoding="utf-8"))
    assert len(refresh["focus_sites"]) == 9
    assert refresh["uniqueness_registry_verified"] == {"total": 198, "missing": 0}
    assert refresh["scored_and_peer_registry_verified"] == {"total": 233, "missing": 0}
    assert refresh["priority_9site_unique_rasters_verified"] == {"total": 107, "missing": 0}
    g36 = next(s for s in refresh["focus_sites"] if s["site"] == "GEMSDOE36")
    lane_ids = [lane["lane_id"] for lane in g36["latest_2026_10_26_lanes"]]
    assert {"GVSC-36 (EXP-3)", "CSDL-36 (EXP-2)", "BDC-36 (EXP-2)"}.issubset(lane_ids)
