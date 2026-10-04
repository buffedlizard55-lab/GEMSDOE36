import numpy as np
import pytest
import rasterio
from affine import Affine

from gemsdoe36.submission import (
    unique_submission_name,
    validate_submission,
    write_submission,
)


def _write_template(path):
    data = np.zeros((12, 10), dtype=np.float32)
    data[:2, :] = np.nan
    profile = {
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": Affine(100, 0, 300000, 0, -100, 4300000),
        "nodata": np.nan,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)


def test_writer_round_trip_matches_template_range_and_mask(tmp_path):
    template = tmp_path / "template.tif"
    output = tmp_path / "candidate.tif"
    manifest = tmp_path / "candidate.json"
    _write_template(template)
    scores = np.zeros((12, 10), dtype=np.float32)
    scores[4:6, 4] = 1.0
    scores[6:8, 5] = 0.25
    report = write_submission(
        scores,
        template,
        output,
        note="synthetic unit-test raster",
        submission_name="GEMS36-test-run",
        manifest_path=manifest,
    )
    assert report.passed
    assert report.template_match
    assert report.count == 1
    assert report.dtype == "float32"
    assert report.crs == "EPSG:32611"
    assert report.minimum == pytest.approx(0.0)
    assert report.maximum == pytest.approx(1.0)
    assert manifest.is_file()
    import json

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["validation"]["nodata"] == "NaN"
    assert manifest_data["submission_name"] == "GEMS36-test-run"
    with rasterio.open(output) as ds:
        arr = ds.read(1)
        assert ds.nodata is not None and np.isnan(ds.nodata)
        assert np.isnan(arr[:2]).all()
        assert np.isfinite(arr[2:]).all()


def test_validator_rejects_range_error(tmp_path):
    template = tmp_path / "template.tif"
    candidate = tmp_path / "bad.tif"
    _write_template(template)
    profile = {
        "driver": "GTiff",
        "height": 12,
        "width": 10,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": Affine(100, 0, 300000, 0, -100, 4300000),
        "nodata": np.nan,
    }
    arr = np.zeros((12, 10), dtype=np.float32)
    arr[3, 4] = 1.01
    arr[:2] = np.nan
    with rasterio.open(candidate, "w", **profile) as dst:
        dst.write(arr, 1)
    report = validate_submission(candidate, template)
    assert not report.passed
    assert any("outside [0, 1]" in error for error in report.errors)


def test_validator_rejects_finite_values_outside_template_bounds(tmp_path):
    template = tmp_path / "template.tif"
    candidate = tmp_path / "bad_outside.tif"
    _write_template(template)
    profile = {
        "driver": "GTiff",
        "height": 12,
        "width": 10,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": Affine(100, 0, 300000, 0, -100, 4300000),
        "nodata": np.nan,
    }
    arr = np.zeros((12, 10), dtype=np.float32)
    arr[:2, :] = np.nan
    arr[0, 0] = 0.5
    with rasterio.open(candidate, "w", **profile) as dst:
        dst.write(arr, 1)
    report = validate_submission(candidate, template)
    assert not report.passed
    assert report.finite_outside_bounds == 1


def test_writer_refuses_bad_scores_before_creating_candidate(tmp_path):
    template = tmp_path / "template.tif"
    output = tmp_path / "invalid.tif"
    _write_template(template)
    scores = np.zeros((12, 10), dtype=np.float32)
    scores[3, 3] = np.inf
    with pytest.raises(ValueError, match="non-finite"):
        write_submission(scores, template, output)
    assert not output.exists()

    scores[3, 3] = 1.01
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        write_submission(scores, template, output)
    assert not output.exists()


def test_writer_refuses_template_shape_mismatch(tmp_path):
    template = tmp_path / "template.tif"
    _write_template(template)
    with pytest.raises(ValueError, match="shape mismatch"):
        write_submission(np.zeros((11, 10)), template, tmp_path / "wrong.tif")


def test_writer_refuses_template_or_existing_output_overwrite(tmp_path):
    template = tmp_path / "template.tif"
    _write_template(template)
    scores = np.zeros((12, 10), dtype=np.float32)
    with pytest.raises(ValueError, match="must not overwrite the template"):
        write_submission(scores, template, template)

    output = tmp_path / "existing.tif"
    output.write_bytes(b"preserve existing data")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_submission(scores, template, output)
    assert output.read_bytes() == b"preserve existing data"


def test_writer_rejects_manifest_path_collisions(tmp_path):
    template = tmp_path / "template.tif"
    _write_template(template)
    scores = np.zeros((12, 10), dtype=np.float32)
    with pytest.raises(ValueError, match="manifest_path must not overwrite"):
        write_submission(scores, template, tmp_path / "candidate.tif", manifest_path=template)


def test_validator_rejects_infinite_values_outside_template_bounds(tmp_path):
    template = tmp_path / "template.tif"
    candidate = tmp_path / "infinite_outside.tif"
    _write_template(template)
    profile = {
        "driver": "GTiff",
        "height": 12,
        "width": 10,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": Affine(100, 0, 300000, 0, -100, 4300000),
        "nodata": np.nan,
    }
    arr = np.zeros((12, 10), dtype=np.float32)
    arr[:2, :] = np.nan
    arr[0, 0] = np.inf
    with rasterio.open(candidate, "w", **profile) as dst:
        dst.write(arr, 1)
    report = validate_submission(candidate, template)
    assert not report.passed
    assert report.infinite_outside_bounds == 1
    assert any("infinite values outside" in error for error in report.errors)


def test_unique_submission_names_are_sanitized_and_collision_resistant():
    scores = np.zeros((2, 3), dtype=np.float32)
    first = unique_submission_name(scores, prefix="GEMS36 H1 / run")
    second = unique_submission_name(scores, prefix="GEMS36 H1 / run")
    assert first != second
    assert first.startswith("GEMS36-H1-run_")
    assert first.endswith(".tif")
    assert "/" not in first and " " not in first
    with pytest.raises(ValueError, match="filename-safe"):
        unique_submission_name(scores, prefix=" / ")
    with pytest.raises(ValueError, match="two-dimensional"):
        unique_submission_name(np.zeros((1, 2, 3)))
