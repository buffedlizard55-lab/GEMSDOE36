"""Synthetic unit tests for the WDP-36 persistence detector, plus a
tracked-artifact release-consistency test (run card vs published TIF)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from gemsdoe36.wdp_features import (
    clean_band,
    footprint_percentile_ranks,
    persistence_from_ranks,
    thdr_ranks_by_height,
    weighted_rank_fusion,
)

ROOT = Path(__file__).resolve().parents[1]


def _foot(shape=(64, 64)):
    f = np.ones(shape, dtype=bool)
    f[:5, :] = False
    return f


def test_percentile_ranks_range_and_outside_zero():
    rng = np.random.default_rng(36)
    foot = _foot()
    vals = rng.normal(size=foot.shape).astype(np.float32)
    r = footprint_percentile_ranks(vals, foot)
    assert r.dtype == np.float32
    assert float(r[foot].min()) == 0.0
    assert float(r[foot].max()) == 1.0
    assert float(r[~foot].max()) == 0.0
    # Monotone: the largest value must hold rank 1.
    assert np.unravel_index(np.argmax(vals * foot), vals.shape) == np.unravel_index(
        np.argmax(r), r.shape
    )


def test_clean_band_fills_sentinel_with_median():
    foot = _foot((10, 10))
    raw = np.ones((10, 10), dtype=np.float32) * 3.0
    raw[5, 5] = np.float32(-3.4028235e38)
    raw[6, 6] = np.nan
    out = clean_band(raw, foot)
    assert np.isfinite(out).all()
    assert out[5, 5] == 3.0 and out[6, 6] == 3.0


def test_upward_continuation_suppresses_short_wavelength():
    """A compact shallow blob (short-wavelength analogue) must lose THDR rank
    with continuation height far faster than a broad step edge (deep-fault
    analogue), whose long wavelengths survive exp(-|k| h)."""
    n = 128
    foot = np.ones((n, n), dtype=bool)
    yy, xx = np.indices((n, n))
    field = np.where(xx >= n // 2, 10.0, -10.0).astype(np.float32)  # broad step
    blob = 50.0 * np.exp(-(((yy - 32) ** 2 + (xx - 32) ** 2) / (2 * 1.5**2)))
    field = (field + blob).astype(np.float32)  # shallow compact source
    ranks = thdr_ranks_by_height(field, foot, heights_m=(0.0, 800.0))
    edge_col = n // 2
    # Broad edge stays highly ranked at 800 m.
    assert float(np.median(ranks[800.0][:, edge_col - 1 : edge_col + 1])) > 0.85
    # Blob neighbourhood holds top ranks at h=0 but collapses by h=800 m.
    blob0 = float(ranks[0.0][28:37, 28:37].max())
    blob800 = float(ranks[800.0][28:37, 28:37].max())
    assert blob0 > 0.95
    assert blob800 < blob0 - 0.20


def test_persistence_rewards_consistent_edge():
    foot = _foot((20, 20))
    a = np.full((20, 20), 0.1, dtype=np.float32)
    a[:, 10] = 0.99
    b = np.full((20, 20), 0.1, dtype=np.float32)
    b[:, 5] = 0.99  # strong at one height only
    p = persistence_from_ranks({0.0: a, 800.0: np.where(np.arange(20)[None, :] == 10, 0.99, 0.1).astype(np.float32)})
    p_one = persistence_from_ranks({0.0: b, 800.0: np.full((20, 20), 0.1, dtype=np.float32)})
    assert float(p[0, 10]) > float(p_one[0, 5])
    assert np.isfinite(p).all() and np.isfinite(p_one).all()
    assert foot.any()


def test_wdp36_run_card_matches_published_tif():
    """Fail-closed consistency: card, receipt, TIF/ZIP hashes, note, verdict."""
    import rasterio

    card_p = ROOT / "evidence/wdp36_run_card_20261026.json"
    card = json.loads(card_p.read_text())
    assert card["lane"] == "GEMSDOE36 / WDP-36"
    assert len(card["submission_note"]) <= 140
    assert card["submission_note_chars"] == len(card["submission_note"])
    # Note must truthfully describe the winning arm (Pass-2 regression guard).
    if card["winning_experiment"] == "EXP-1":
        assert "only" in card["submission_note"]
        assert "+strain" not in card["submission_note"]
    gates = card["gates"]
    expect_promote = all(gates.values())
    assert (card["verdict"] == "promote") == expect_promote
    assert card["validator_output"]["safe_to_download_and_submit"] == expect_promote
    assert card["experiment_budget"]["experiments_executed"] <= 3
    assert card["experiment_budget"]["elapsed_walltime_seconds"] <= 7200
    tif = ROOT / "docs/downloads" / card["submission_file"]
    zip_p = ROOT / "docs/downloads" / card["submission_zip"]
    receipt = ROOT / "docs/downloads" / (tif.stem + ".receipt.json")
    assert receipt.read_bytes() == card_p.read_bytes()
    for f, key in ((tif, "raster_sha256"), (zip_p, "zip_sha256")):
        assert hashlib.sha256(f.read_bytes()).hexdigest() == card[key], f.name
    with rasterio.open(tif) as s:
        a = s.read(1)
        assert s.count == 1 and s.dtypes == ("float32",)
        assert s.crs is not None and s.crs.to_epsg() == 32611
        assert s.shape == (3730, 3292)
        assert s.nodata is None  # zeros-only portal bundle
    assert np.isfinite(a).all()
    assert float(a.min()) >= 0.0 and float(a.max()) <= 1.0
    assert int((a > 0).sum()) == card["validator_output"]["positive_dots_emitted"] == 37_654


def test_weighted_rank_fusion_in_unit_interval():
    rng = np.random.default_rng(7)
    foot = _foot((16, 16))
    a = footprint_percentile_ranks(rng.normal(size=(16, 16)).astype(np.float32), foot)
    b = footprint_percentile_ranks(rng.normal(size=(16, 16)).astype(np.float32), foot)
    fused = weighted_rank_fusion([(a, 0.7), (b, 0.3)], foot)
    assert float(fused[foot].min()) >= 0.0 and float(fused[foot].max()) <= 1.0
