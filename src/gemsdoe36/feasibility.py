"""A literal-registry impossibility preflight; never approves a candidate.

For K distinct footprint pixels and U footprint pixels farther than the radius
from a registered raster, at least K-U candidate pixels must be within it.  A
failed lower bound is decisive; a non-failing lower bound is NOT a novelty pass.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
import rasterio

from gems.novelty import classify_space_filling_control


class PreflightError(ValueError):
    """Pinned inputs are absent, inconsistent, or insufficient for a proof."""


def overlap_bound(
    footprint_pixels: int,
    covered_pixels: int,
    candidate_dots: int,
    threshold: Fraction = Fraction(7, 10),
) -> dict:
    """Return exact pigeonhole lower bound and the strict > threshold decision."""
    values = (footprint_pixels, covered_pixels, candidate_dots)
    if any(isinstance(x, bool) or not isinstance(x, int) for x in values):
        raise ValueError("Pixel and dot counts must be integers")
    if not 0 <= covered_pixels <= footprint_pixels or not 1 <= candidate_dots <= footprint_pixels:
        raise ValueError("Counts must describe a nonempty subset of the footprint")
    if not isinstance(threshold, Fraction) or not Fraction(0) <= threshold < Fraction(1):
        raise ValueError("Threshold must be a Fraction in [0, 1)")
    uncovered = footprint_pixels - covered_pixels
    forced = max(0, candidate_dots - uncovered)
    ratio = Fraction(forced, candidate_dots)
    # Strict greater-than, so equality is not automatically a duplicate.
    first_duplicate_count = int(Fraction(uncovered, 1) / (1 - threshold)) + 1
    return {
        "footprint_pixels": footprint_pixels,
        "covered_pixels": covered_pixels,
        "uncovered_pixels": uncovered,
        "candidate_distinct_dots": candidate_dots,
        "minimum_overlapping_dots": forced,
        "minimum_overlap_fraction": float(ratio),
        "threshold_fraction": float(threshold),
        "guaranteed_duplicate": ratio > threshold,
        # None means the proof cannot force a duplicate at any valid dot count.
        "first_dot_count_forced_over_threshold": (
            first_duplicate_count if first_duplicate_count <= footprint_pixels else None
        ),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_registered_lattice(root: Path, candidate_dots: int = 37_654) -> dict:
    """Recompute coverage from SHA-pinned owner mirrors of reg-052 and the grid.

    This is a *necessary* feasibility test against one literal registry entry,
    not a surface correlation, a full registry sweep, or a format validator.
    """
    root = Path(root)
    manifest = json.loads((root / "registry/data_manifest.json").read_text())
    registry = json.loads((root / "registry/uniqueness_registry.json").read_text())
    template_item = next(x for x in manifest["files"] if x["id"] == "sample_submission")
    lattice_item = next(
        x for x in manifest["files"] if x["dest"] == "scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
    )
    reference = next(x for x in registry["entries"] if x["id"] == "reg-052")
    if reference["file_sha256"] != lattice_item["sha256"]:
        raise PreflightError("Registry and mirror manifest disagree about lattice identity")
    template = root / "data/raw" / template_item["dest"]
    lattice = root / "data/raw" / lattice_item["dest"]
    for path, item in ((template, template_item), (lattice, lattice_item)):
        if not path.is_file() or _sha256(path) != item["sha256"]:
            raise PreflightError(f"Missing or hash-mismatched pinned owner mirror: {path}")
    with rasterio.open(template) as t, rasterio.open(lattice) as r:
        if t.count != 1 or r.count != 1 or (t.shape, t.crs, t.transform) != (r.shape, r.crs, r.transform):
            raise PreflightError("Lattice and template must have one band and the same grid")
        if t.crs is None or t.crs.to_epsg() != 32611:
            raise PreflightError("Expected EPSG:32611 template grid")
        footprint = np.isfinite(t.read(1))
        pixels = r.read(1)
        if not footprint.any() or not np.isfinite(pixels[footprint]).all():
            raise PreflightError("Empty footprint or nonfinite registered pixels inside it")
        if np.any((pixels[footprint] < 0) | (pixels[footprint] > 1)):
            raise PreflightError("Registered pixel values outside [0, 1]")
        content_sha = hashlib.sha256(np.asarray(pixels[footprint], dtype="<f4").tobytes()).hexdigest()
        if content_sha != reference["footprint_sha256"]:
            raise PreflightError("Registry footprint checksum mismatch")
        # compare_registry treats any positive registered pixel as a dot.
        registered_dots = footprint & (pixels > 0)
        coverage = classify_space_filling_control(
            footprint=footprint, reference_dots=registered_dots,
            radius_px=3, candidate_dot_count=candidate_dots,
        )
    bound = overlap_bound(int(footprint.sum()), coverage["footprint_3px_covered_pixels"], candidate_dots)
    return {
        "schema_version": "gemsdoe36.literal-registry-feasibility.v1",
        "reference_id": reference["id"],
        "reference_registry_path": reference["file"],
        "reference_sha256": reference["file_sha256"],
        "reference_footprint_sha256": reference["footprint_sha256"],
        "reference_dots": int(registered_dots.sum()),
        "template_sha256": template_item["sha256"],
        "provenance": "SHA-pinned owner mirrors, not independently authenticated organizer data",
        "radius_pixels": 3,
        "bound": bound,
        "conclusion": (
            "STOP: guaranteed to exceed the literal 70% overlap gate"
            if bound["guaranteed_duplicate"]
            else "NOT PROVEN: still requires surface and final-dot comparison against every registry entry"
        ),
    }
