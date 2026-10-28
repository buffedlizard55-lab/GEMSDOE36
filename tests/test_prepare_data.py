"""Preparation must not silently align rasters by array shape alone."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import prepare_data as prep  # noqa: E402

TRANSFORM = Affine(100, 0, 243350, 0, -100, 4508550)
NAMES = ["feature_a", "feature_b"]


def _write(path: Path, arrays, *, transform=TRANSFORM, crs="EPSG:32611", nodata=None, names=None):
    arrays = np.asarray(arrays, dtype="float32")
    if arrays.ndim == 2:
        arrays = arrays[None, :, :]
    with rasterio.open(
        path, "w", driver="GTiff", height=arrays.shape[1], width=arrays.shape[2],
        count=arrays.shape[0], dtype="float32", crs=crs, transform=transform, nodata=nodata,
    ) as dst:
        dst.write(arrays)
        for idx, name in enumerate(names or [], 1):
            dst.update_tags(idx, band_name=name)


@pytest.fixture
def inputs(tmp_path):
    template = tmp_path / "sample_submission.tif"
    labels = tmp_path / "labels.tif"
    features = tmp_path / "training_features.tif"
    t = np.zeros((4, 4), dtype="float32")
    t[0, 0] = np.nan
    y = np.zeros((4, 4), dtype="float32")
    y[0, 0] = -1
    y[1, 1] = 1
    x = np.stack([np.ones((4, 4)), np.full((4, 4), 2)]).astype("float32")
    _write(template, t, nodata=np.nan)
    _write(labels, y, nodata=-1)
    _write(features, x, names=NAMES)
    return template, labels, features


def _inspect(inputs):
    return prep.inspect_core_inputs(
        *inputs, expected_shape=(4, 4), expected_transform=tuple(TRANSFORM)[:6],
        expected_footprint_pixels=15, expected_names=NAMES,
    )


def test_core_inputs_aligned_and_binary(inputs):
    footprint, labels, transform = _inspect(inputs)
    assert footprint.sum() == 15
    assert labels.sum() == 1 and labels[1, 1]
    assert transform == tuple(TRANSFORM)[:6]


@pytest.mark.parametrize("index,changes", [
    (1, {"transform": Affine(100, 0, 243450, 0, -100, 4508550)}),
    (1, {"crs": "EPSG:4326"}),
    (2, {"transform": Affine(100, 0, 243450, 0, -100, 4508550)}),
    (2, {"crs": "EPSG:4326"}),
])
def test_same_shape_wrong_crs_or_transform_is_rejected(inputs, index, changes):
    arrays = np.zeros((4, 4), dtype="float32") if index == 1 else np.zeros((2, 4, 4), dtype="float32")
    _write(inputs[index], arrays, names=NAMES if index == 2 else None, **changes)
    with pytest.raises(ValueError, match="shape/CRS/geotransform"):
        _inspect(inputs)


def test_wrong_band_names_or_unmasked_nonbinary_labels_are_rejected(inputs):
    _write(inputs[2], np.ones((2, 4, 4)), names=["feature_b", "feature_a"])
    with pytest.raises(ValueError, match="band order"):
        _inspect(inputs)
    _write(inputs[2], np.ones((2, 4, 4)), names=NAMES)
    invalid = np.zeros((4, 4), dtype="float32")
    invalid[2, 2] = 2
    _write(inputs[1], invalid)
    with pytest.raises(ValueError, match="unmasked binary"):
        _inspect(inputs)


def test_label_nodata_inside_footprint_is_rejected(inputs):
    invalid = np.zeros((4, 4), dtype="float32")
    invalid[2, 2] = -1
    _write(inputs[1], invalid, nodata=-1)
    with pytest.raises(ValueError, match="unmasked binary"):
        _inspect(inputs)


def test_incomplete_cache_build_preserves_previous_cache(inputs, tmp_path, monkeypatch):
    # Feature metadata is valid, but the second band has no usable footprint values.
    x = np.stack([np.ones((4, 4)), np.full((4, 4), np.nan)]).astype("float32")
    _write(inputs[2], x, names=NAMES)
    cache = tmp_path / "work" / "bands"
    cache.mkdir(parents=True)
    marker = cache / "previous.txt"
    marker.write_text("prior complete cache")
    monkeypatch.setattr(prep, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(prep, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(prep, "ROOT", tmp_path)
    monkeypatch.setattr(prep, "BASE_NAMES", NAMES)
    original = prep.inspect_core_inputs
    monkeypatch.setattr(prep, "inspect_core_inputs", lambda *paths: original(
        *paths, expected_shape=(4, 4), expected_transform=tuple(TRANSFORM)[:6],
        expected_footprint_pixels=15, expected_names=NAMES,
    ))
    with pytest.raises(ValueError, match="No valid values"):
        prep.prepare()
    assert marker.read_text() == "prior complete cache"
    assert not (tmp_path / "data/prepared_manifest.json").exists()


def test_successful_cache_replaces_previous_and_writes_manifest(inputs, tmp_path, monkeypatch):
    cache = tmp_path / "work" / "bands"
    cache.mkdir(parents=True)
    (cache / "previous.txt").write_text("old")
    monkeypatch.setattr(prep, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(prep, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(prep, "ROOT", tmp_path)
    monkeypatch.setattr(prep, "BASE_NAMES", NAMES)
    original = prep.inspect_core_inputs
    monkeypatch.setattr(prep, "inspect_core_inputs", lambda *paths: original(
        *paths, expected_shape=(4, 4), expected_transform=tuple(TRANSFORM)[:6],
        expected_footprint_pixels=15, expected_names=NAMES,
    ))
    manifest = prep.prepare()
    assert not (cache / "previous.txt").exists()
    assert np.load(cache / "_labels.npy").sum() == 1
    assert np.load(cache / "01_feature_a.npy")[1, 1] == 1
    assert manifest["input_grid_checks"]["labels_and_features_match_template_shape_crs_transform"]
    assert (tmp_path / "data/prepared_manifest.json").is_file()


def test_manifest_install_error_rolls_back_cache(inputs, tmp_path, monkeypatch):
    import prepare_data as prep

    cache = tmp_path / "work" / "bands"
    cache.mkdir(parents=True)
    (cache / "previous.txt").write_text("old cache")
    manifest = tmp_path / "data" / "prepared_manifest.json"
    manifest.parent.mkdir()
    manifest.write_text("old manifest")
    monkeypatch.setattr(prep, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(prep, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(prep, "ROOT", tmp_path)
    monkeypatch.setattr(prep, "BASE_NAMES", NAMES)
    original_inspect = prep.inspect_core_inputs
    monkeypatch.setattr(prep, "inspect_core_inputs", lambda *paths: original_inspect(
        *paths, expected_shape=(4, 4), expected_transform=tuple(TRANSFORM)[:6],
        expected_footprint_pixels=15, expected_names=NAMES,
    ))
    original_replace = Path.replace

    def failing_replace(self, target):
        if Path(target) == manifest:
            raise OSError("simulated manifest failure")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", failing_replace)
    with pytest.raises(OSError, match="simulated manifest failure"):
        prep.prepare()
    assert (cache / "previous.txt").read_text() == "old cache"
    assert manifest.read_text() == "old manifest"
    assert not list(manifest.parent.glob("*.tmp"))
