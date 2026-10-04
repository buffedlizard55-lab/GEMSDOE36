"""Fail-closed GeoTIFF writer, pair emitter, and validator for the competition raster contract."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import uuid
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

EXPECTED_HEIGHT = 3730
EXPECTED_WIDTH = 3292
EXPECTED_TOTAL_PIXELS = EXPECTED_HEIGHT * EXPECTED_WIDTH
EXPECTED_FOOTPRINT_PIXELS = 5_167_373


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
    infinite_outside_bounds: int
    minimum: float | None
    maximum: float | None
    nodata: float | str | None
    template_match: bool
    passed: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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

    The valid region comes only from the sample/template raster. Values must be finite
    and within [0, 1] inside that region. If require_nonfinite_outside is True, cells outside
    must be NaN/null. A local PASS is not platform acceptance.
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
        xres = math.hypot(sub.transform.a, sub.transform.d)
        yres = math.hypot(sub.transform.b, sub.transform.e)
        if not (
            np.isclose(xres, expected_resolution_m) and np.isclose(yres, expected_resolution_m)
        ):
            errors.append(f"expected {expected_resolution_m} m pixels, found ({xres}, {yres})")

        values = sub.read(1, masked=False)
        template_valid = _template_valid_mask(template)
        if values.shape != template_valid.shape:
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
        infinite_outside = int(np.isinf(outside_values).sum())
        if infinite_outside:
            errors.append(f"{infinite_outside} infinite values outside the template bounds")
        if require_nonfinite_outside and finite_outside:
            errors.append(f"{finite_outside} finite values outside the template bounds")
        elif not require_nonfinite_outside and finite_outside:
            out_vals = outside_values[np.isfinite(outside_values)]
            if (out_vals < 0.0).any() or (out_vals > 1.0).any():
                errors.append("finite values outside the template bounds must be in [0, 1]")

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
            infinite_outside_bounds=infinite_outside,
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
    submission_name: str | None = None,
    manifest_path: str | Path | None = None,
    mode: str = "nan",
) -> ValidationReport:
    """Write scores on the exact template grid, reread, validate, and atomically publish."""
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

        if mode == "zeros":
            export = np.zeros(scores.shape, dtype=np.float32)
            export[valid] = scores[valid].astype(np.float32, copy=False)
            nodata_setting = None
        else:
            export = np.full(scores.shape, np.nan, dtype=np.float32)
            export[valid] = scores[valid].astype(np.float32, copy=False)
            nodata_setting = float("nan")

        profile.update(
            driver="GTiff",
            count=1,
            dtype="float32",
            nodata=nodata_setting,
            compress="deflate",
            predictor=1,
            tiled=False,
        )
        profile.pop("blockxsize", None)
        profile.pop("blockysize", None)
        profile.pop("interleave", None)
        profile.pop("photometric", None)

        fd, temp_name = tempfile.mkstemp(
            prefix=f".{output.stem}.", suffix=".partial.tif", dir=output.parent
        )
        os.close(fd)
        os.chmod(temp_name, 0o644)
        temp_path = Path(temp_name)
        try:
            with rasterio.open(temp_path, "w", **profile) as dst:
                dst.write(export, 1)
                tags = {
                    "AREA_OR_POINT": "Area",
                    "GEMS36_NOTE": note[:4000],
                    "GEMS36_WRITER": "gemsdoe36.submission.write_submission",
                }
                if submission_name is not None:
                    tags["GEMS36_SUBMISSION_NAME"] = submission_name[:256]
                dst.update_tags(**tags)

            require_nonfinite = mode != "zeros"
            report = validate_submission(
                temp_path, template_path, require_nonfinite_outside=require_nonfinite
            )
            if not report.passed:
                raise ValueError(
                    "submission read-back validation failed: " + "; ".join(report.errors)
                )
            try:
                os.link(temp_path, output)
            except FileExistsError:
                raise FileExistsError(f"refusing to overwrite existing output: {output}") from None
        finally:
            if temp_path.exists():
                temp_path.unlink()

    report = validate_submission(
        output, template_path, require_nonfinite_outside=(mode != "zeros")
    )
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
            "submission_name": submission_name,
            "note": note,
            "mode": mode,
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


def write_submission_bundle(
    scores: np.ndarray,
    template_path: str | Path,
    out_dir: str | Path,
    prefix: str = "gemsdoe36-anderson-geothermal",
    timestamp_tag: str = "20261004T230000Z",
    submission_name: str = "GEMSDOE36-Anderson-PINN",
    note: str = "",
    meta: dict | None = None,
) -> dict[str, Any]:
    """Emit the complete submission bundle: -zeros.tif, -nan.tif, .zip, and audit sidecar."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    array = np.ascontiguousarray(np.asarray(scores, dtype=np.float32))

    clean = np.clip(array, 0.0, 1.0)
    digest8 = hashlib.sha256(np.packbits(clean > 0.5)).hexdigest()[:8]
    dot_count = int((clean > 0.5).sum())

    zeros_filename = f"{prefix}-{dot_count}-{timestamp_tag}-{digest8}-zeros.tif"
    nan_filename = f"{prefix}-{dot_count}-{timestamp_tag}-{digest8}-nan.tif"
    zip_filename = f"{prefix}-{dot_count}-{timestamp_tag}-{digest8}-zeros.zip"
    audit_filename = f"{prefix}-{dot_count}-{timestamp_tag}-{digest8}-audit.json"

    zeros_path = out / zeros_filename
    nan_path = out / nan_filename
    zip_path = out / zip_filename
    audit_path = out / audit_filename

    # 1. Write zeros-outside (primary, portal-safe)
    write_submission(
        clean,
        template_path,
        zeros_path,
        note=note,
        submission_name=submission_name,
        mode="zeros",
    )

    # 2. Write nan-outside (companion)
    write_submission(
        clean,
        template_path,
        nan_path,
        note=note,
        submission_name=submission_name,
        mode="nan",
    )

    # 3. Create single-member zip archive
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(zeros_path, arcname=zeros_filename)

    zeros_sha256 = sha256_file(zeros_path)
    nan_sha256 = sha256_file(nan_path)
    zip_sha256 = sha256_file(zip_path)

    bundle = {
        "candidate_id": submission_name,
        "prefix": prefix,
        "content_digest8": digest8,
        "timestamp_tag": timestamp_tag,
        "emitted_positive_pixels": dot_count,
        "note": note,
        "zeros_tif": {
            "filename": zeros_filename,
            "path": str(zeros_path),
            "bytes": zeros_path.stat().st_size,
            "sha256": zeros_sha256,
            "mode": "zeros",
            "nodata": None,
            "in_footprint_all_finite": True,
            "full_grid_all_finite": True,
            "range_in_01": True,
        },
        "nan_tif": {
            "filename": nan_filename,
            "path": str(nan_path),
            "bytes": nan_path.stat().st_size,
            "sha256": nan_sha256,
            "mode": "nan",
            "nodata": "nan",
            "in_footprint_all_finite": True,
            "full_grid_all_finite": False,
            "range_in_01": True,
        },
        "zip_archive": {
            "filename": zip_filename,
            "path": str(zip_path),
            "bytes": zip_path.stat().st_size,
            "sha256": zip_sha256,
        },
        "meta": meta or {},
    }
    audit_path.write_text(json.dumps(bundle, indent=2) + "\n")
    return bundle


def unique_submission_name(scores: np.ndarray, *, prefix: str = "GEMS36_candidate") -> str:
    """Return collision-resistant, traceable UTC filename for one score grid."""
    array = np.ascontiguousarray(np.asarray(scores, dtype=np.float32))
    if array.ndim != 2:
        raise ValueError("scores must be a two-dimensional array")
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", prefix).strip("-_")[:48]
    if not slug:
        raise ValueError("prefix must contain at least one filename-safe character")
    fingerprint = f"{array.shape[0]}x{array.shape[1]}:float32:".encode("ascii") + array.tobytes()
    digest = hashlib.sha256(fingerprint).hexdigest()[:10]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{slug}_{timestamp}_{digest}_{unique_suffix}.tif"
