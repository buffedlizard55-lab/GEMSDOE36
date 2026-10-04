"""Fail-closed GeoTIFF writer and validator for the competition raster contract."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio


@dataclass(frozen=True)
class ValidationReport:
    path: str
    width: int
    height: int
    count: int
    dtype: str
    crs: str | None
    resolution_m: tuple[float, float]
    finite_in_bounds: int
    invalid_in_bounds: int
    finite_outside_bounds: int
    minimum: float | None
    maximum: float | None
    nodata: float | str | None
    template_match: bool
    passed: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _template_valid_mask(dataset: rasterio.io.DatasetReader) -> np.ndarray:
    template = dataset.read(1, masked=False)
    valid = np.isfinite(template) & (dataset.read_masks(1) > 0)
    nodata = dataset.nodata
    if nodata is not None and np.isfinite(nodata):
        valid &= template != nodata
    return valid


def _same_grid(a: rasterio.io.DatasetReader, b: rasterio.io.DatasetReader) -> bool:
    return (
        a.width == b.width
        and a.height == b.height
        and a.crs == b.crs
        and a.transform == b.transform
    )


def validate_submission(
    submission_path: str | Path,
    template_path: str | Path,
    *,
    expected_crs: str = "EPSG:32611",
    expected_resolution_m: float = 100.0,
    require_nonfinite_outside: bool = True,
) -> ValidationReport:
    """Validate a single-band float32 file against an organizer template.

    The valid region comes only from the sample/template raster, never from feature-band
    NoData.  Values must be finite and within [0, 1] inside that region.  By default,
    cells outside the template's valid region must be non-finite (the published format
    calls for null/NaN outside the data bounds).  A local PASS is not platform acceptance.
    """
    sub_path, tmpl_path = Path(submission_path), Path(template_path)
    errors: list[str] = []
    if not sub_path.is_file():
        raise FileNotFoundError(sub_path)
    if not tmpl_path.is_file():
        raise FileNotFoundError(tmpl_path)

    with rasterio.open(tmpl_path) as template, rasterio.open(sub_path) as sub:
        same_grid = _same_grid(sub, template)
        if not same_grid:
            errors.append("shape/CRS/transform differs from organizer template")
        if sub.count != 1:
            errors.append(f"expected one band, found {sub.count}")
        if sub.dtypes[0] != "float32":
            errors.append(f"expected float32, found {sub.dtypes[0]}")
        if sub.crs is None or sub.crs.to_string() != expected_crs:
            errors.append(f"expected {expected_crs}, found {sub.crs}")
        xres, yres = abs(sub.transform.a), abs(sub.transform.e)
        if not (
            np.isclose(xres, expected_resolution_m) and np.isclose(yres, expected_resolution_m)
        ):
            errors.append(f"expected {expected_resolution_m} m pixels, found ({xres}, {yres})")

        values = sub.read(1, masked=False)
        template_valid = _template_valid_mask(template)
        if values.shape != template_valid.shape:
            # Do not index mismatched arrays after recording the primary failure.
            inside = np.zeros(values.shape, dtype=bool)
            outside = np.zeros(values.shape, dtype=bool)
        else:
            inside = template_valid
            outside = ~template_valid
        inside_values = values[inside]
        outside_values = values[outside]
        finite_inside = np.isfinite(inside_values)
        invalid_inside = int((~finite_inside).sum())
        if invalid_inside:
            errors.append(f"{invalid_inside} non-finite values inside the template bounds")
        if finite_inside.any():
            finite_values = inside_values[finite_inside]
            minimum, maximum = float(finite_values.min()), float(finite_values.max())
            if minimum < 0.0 or maximum > 1.0:
                errors.append(
                    f"finite in-bounds values range from {minimum} to {maximum}, outside [0, 1]"
                )
        else:
            minimum = maximum = None
            errors.append("template has no finite prediction values inside its valid region")

        finite_outside = int(np.isfinite(outside_values).sum())
        if require_nonfinite_outside and finite_outside:
            # The official page requires null/NaN outside bounds; fail closed.
            errors.append(f"{finite_outside} finite values outside the template bounds")

        nodata = sub.nodata
        report = ValidationReport(
            path=str(sub_path),
            width=sub.width,
            height=sub.height,
            count=sub.count,
            dtype=sub.dtypes[0] if sub.count else "unknown",
            crs=sub.crs.to_string() if sub.crs else None,
            resolution_m=(xres, yres),
            finite_in_bounds=int(finite_inside.sum()),
            invalid_in_bounds=invalid_inside,
            finite_outside_bounds=finite_outside,
            minimum=minimum,
            maximum=maximum,
            nodata=(None if nodata is None else (float(nodata) if np.isfinite(nodata) else "NaN")),
            template_match=same_grid,
            passed=not errors,
            errors=tuple(errors),
        )
    return report


def write_submission(
    scores: np.ndarray,
    template_path: str | Path,
    output_path: str | Path,
    *,
    note: str = "",
    manifest_path: str | Path | None = None,
) -> ValidationReport:
    """Write scores on the exact template grid, reread, validate, and atomically publish.

    The writer uses the template's valid mask and writes NaN outside it, matching the
    published null/NaN-outside requirement.  TIFF Predictor is explicitly disabled for
    maximum reader compatibility; the read-back range gate catches encoding corruption
    before the final output path is exposed.
    """
    scores = np.asarray(scores)
    if scores.ndim != 2:
        raise ValueError("scores must be a two-dimensional array")
    template_file = Path(template_path)
    output = Path(output_path)
    manifest_file = Path(manifest_path) if manifest_path is not None else None
    if output.resolve() == template_file.resolve():
        raise ValueError("output_path must not overwrite the template")
    if manifest_file is not None and manifest_file.resolve() in {
        output.resolve(),
        template_file.resolve(),
    }:
        raise ValueError("manifest_path must not overwrite the output or template")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    if manifest_file is not None and manifest_file.exists():
        raise FileExistsError(f"refusing to overwrite existing manifest: {manifest_file}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.name.lower().endswith((".tif", ".tiff")):
        raise ValueError("output_path must end in .tif or .tiff")

    with rasterio.open(template_path) as template:
        if template.count < 1:
            raise ValueError("template has no raster bands")
        valid = _template_valid_mask(template)
        if scores.shape != valid.shape:
            raise ValueError(f"score/template shape mismatch: {scores.shape} != {valid.shape}")
        inside_scores = scores[valid]
        if not np.all(np.isfinite(inside_scores)):
            raise ValueError("scores contain non-finite values inside the template valid region")
        if np.any((inside_scores < 0) | (inside_scores > 1)):
            raise ValueError("scores must be in [0, 1] inside the template valid region")
        profile = template.profile.copy()
        profile.update(
            driver="GTiff",
            count=1,
            dtype="float32",
            nodata=float("nan"),
            compress="deflate",
            predictor=1,
            tiled=False,
        )
        profile.pop("blockxsize", None)
        profile.pop("blockysize", None)
        profile.pop("interleave", None)
        profile.pop("photometric", None)

        export = np.full(scores.shape, np.nan, dtype=np.float32)
        export[valid] = scores[valid].astype(np.float32, copy=False)
        if np.any(~np.isfinite(export[valid])) or np.any((export[valid] < 0) | (export[valid] > 1)):
            raise ValueError("float32 conversion produced values outside finite [0, 1]")

        fd, temp_name = tempfile.mkstemp(
            prefix=f".{output.stem}.", suffix=".partial.tif", dir=output.parent
        )
        os.close(fd)
        temp_path = Path(temp_name)
        try:
            with rasterio.open(temp_path, "w", **profile) as dst:
                dst.write(export, 1)
                dst.update_tags(
                    AREA_OR_POINT="Area",
                    GEMS36_NOTE=note[:4000],
                    GEMS36_WRITER="gemsdoe36.submission.write_submission",
                )
            # Read-back from disk before atomic publish.
            report = validate_submission(temp_path, template_path)
            if not report.passed:
                raise ValueError(
                    "submission read-back validation failed: " + "; ".join(report.errors)
                )
            try:
                # A hard link publishes the complete same-filesystem TIFF atomically and
                # fails rather than replacing a file created concurrently.
                os.link(temp_path, output)
            except FileExistsError:
                raise FileExistsError(f"refusing to overwrite existing output: {output}") from None
        finally:
            if temp_path.exists():
                temp_path.unlink()

    report = validate_submission(output, template_path)
    if not report.passed:
        output.unlink(missing_ok=True)
        raise ValueError("published file failed validation: " + "; ".join(report.errors))

    if manifest_file is not None:
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        manifest_data = {
            "file": output.name,
            "sha256": digest,
            "bytes": output.stat().st_size,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "validation": report.to_dict(),
            "note": note,
            "limitations": [
                "A local format pass is not proof of acceptance by the competition platform.",
                "No scientific score or spatial holdout result is implied by this manifest.",
            ],
        }
        json_bytes = (json.dumps(manifest_data, indent=2, allow_nan=False) + "\n").encode("utf-8")
        json_temp: Path | None = None
        try:
            manifest_file.parent.mkdir(parents=True, exist_ok=True)
            fd, json_temp_name = tempfile.mkstemp(
                prefix=f".{manifest_file.name}.", suffix=".partial", dir=manifest_file.parent
            )
            json_temp = Path(json_temp_name)
            with os.fdopen(fd, "wb") as stream:
                stream.write(json_bytes)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(json_temp, manifest_file)
        except Exception:
            output.unlink(missing_ok=True)
            raise
        finally:
            if json_temp is not None and json_temp.exists():
                json_temp.unlink()
    return report


def unique_submission_name(scores: np.ndarray, *, prefix: str = "GEMS36_candidate") -> str:
    """Create a traceable UTC filename from the prediction bytes and current time."""
    array = np.ascontiguousarray(np.asarray(scores, dtype=np.float32))
    digest = hashlib.sha256(array.tobytes()).hexdigest()[:8]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{timestamp}_{digest}.tif"
