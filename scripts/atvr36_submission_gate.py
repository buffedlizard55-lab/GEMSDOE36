#!/usr/bin/env python3
"""Standardized GEMSDOE36 Submission Writer & Automated Validation/Registry Gate.

Reuses ``gemsdoe36.submission`` (``write_submission(..., mode="zeros")`` and
``validate_submission(..., require_nonfinite_outside=False)``) and ``gemsdoe36.protocol``
(``registry_check``) without private forks:
  1. Writes finite ``0.0`` float32 outside the template footprint (``mode="zeros"``,
     ``nodata=None``) and clamps inside-footprint values to ``[0.0, 1.0]``, permanently
     preventing DrivenData's ``"Predicted values must be in range [0, 1]"`` rejection.
  2. Zeros predictions on ``existing_faults.tif`` (organizers mask visible faults).
  3. Validates exact GeoTIFF grid contract (``EPSG:32611``, ``3730 x 3292``, 100 m pixel size,
     zero non-finite cells, all cells in ``[0, 1]``).
  4. Runs ``gemsdoe36.protocol.registry_check`` across all non-constant, non-lattice
     geological rasters (``|Spearman rho| <= 0.90``, ``3-px dot overlap <= 0.70``) and
     records the synthetic 5-px calibration lattice disclosure separately.
  5. Emits ``.tif``, ``.zip``, and ``.receipt.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe36.paths import data_dir, work_dir
from gemsdoe36.protocol import registry_check
from gemsdoe36.submission import sha256_file, validate_submission, write_submission

SPEARMAN_CAP = 0.90
OVERLAP_3PX_CAP = 0.70
SYNTHETIC_LATTICE_SUBSTR = "lattice-s5"


def discover_registry_rasters(extra_dirs: list[Path] | None = None) -> list[tuple[str, Path]]:
    """Collect unique reference rasters across scored, focus_registry, and legacy downloads."""
    search_roots = [
        ("scored", data_dir() / "scored"),
        ("focus", ROOT / ".cache" / "focus_registry"),
        ("legacy36", ROOT / "docs" / "downloads"),
    ]
    if extra_dirs:
        for d in extra_dirs:
            search_roots.append(("extra", d))

    seen_hashes: set[str] = set()
    items: list[tuple[str, Path]] = []
    for tag, directory in search_roots:
        if not directory.exists():
            continue
        for p in sorted(directory.rglob("*.tif")):
            if "atvr36" in p.name.lower():
                continue
            digest = sha256_file(p)
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            items.append((f"{tag}:{p.name}", p))
    return items


def run_registry_audit(
    surface: np.ndarray,
    dot_mask: np.ndarray,
    valid_eval_mask: np.ndarray,
    registry_items: list[tuple[str, Path]],
    *,
    exclude_tif_sha256: str | None = None,
) -> dict[str, object]:
    """Run protocol.registry_check across geological rasters + disclose synthetic lattice."""
    foot = np.asarray(valid_eval_mask, dtype=bool)
    surf_clean = np.where(foot & np.isfinite(surface), surface, 0.0).astype(np.float32)
    dots_bool = np.asarray(dot_mask, dtype=bool) & foot

    records: list[dict[str, object]] = []
    max_abs_rho = 0.0
    max_abs_rho_ref = ""
    max_geol_overlap = 0.0
    max_geol_overlap_ref = ""
    constant_placeholders: list[str] = []
    lattice_disclosures: list[dict[str, object]] = []
    all_passed = True

    for label, ref_path in registry_items:
        ref_sha = sha256_file(ref_path)
        if exclude_tif_sha256 and ref_sha == exclude_tif_sha256:
            continue
        with rasterio.open(ref_path) as src:
            if src.shape != surf_clean.shape:
                continue
            ref_arr = src.read(1).astype(np.float32)

        ref_clean = np.where(np.isfinite(ref_arr), ref_arr, 0.0).astype(np.float32)
        del ref_arr
        ref_dots = (ref_clean > 0.5) & foot

        if np.ptp(ref_clean[foot]) == 0:
            constant_placeholders.append(label)
            del ref_clean, ref_dots
            continue

        if SYNTHETIC_LATTICE_SUBSTR in ref_path.name.lower():
            rho_lat = float(spearmanr(surf_clean[foot], ref_clean[foot]).statistic)
            near_fwd = distance_transform_edt(~ref_dots) <= 3
            near_rev = distance_transform_edt(~dots_bool) <= 3
            lattice_disclosures.append(
                {
                    "reference": label,
                    "sha256_12": ref_sha[:12],
                    "n_ref_dots_off_catalogue": int(ref_dots.sum()),
                    "surface_spearman_rho": round(rho_lat, 6),
                    "dot_overlap_3px_forward": round(float(near_fwd[dots_bool].mean()), 6),
                    "dot_overlap_3px_reverse": round(float(near_rev[ref_dots].mean()), 6),
                    "note": (
                        "Synthetic 5x5 uniform calibration lattice (204,504 off-catalogue dots); "
                        "max Euclidean distance from any grid cell to nearest 5x5 node is "
                        "sqrt(2^2+2^2)=2.83 <= 3.0 px (99.9% map coverage by pigeonhole geometry)."
                    ),
                }
            )
            del ref_clean, ref_dots, near_fwd, near_rev
            continue

        # Stream one reference raster at a time through protocol.registry_check (<100 MB RAM)
        single_res = registry_check(surf_clean, dots_bool, foot, {label: (ref_clean, ref_dots)})
        del ref_clean, ref_dots
        row = single_res["comparisons"][0]
        rho = float(row["surface_rank_correlation"])
        ov = float(row["dot_overlap_within_3px"])
        dot_rho = row["dot_rank_correlation"]
        is_dup = bool(row["duplicate"])
        if is_dup:
            all_passed = False
        records.append(
            {
                "reference": label,
                "sha256_12": ref_sha[:12],
                "surface_spearman_rho": round(rho, 6),
                "dot_rank_correlation": None if dot_rho is None else round(float(dot_rho), 6),
                "dot_overlap_3px_forward": round(ov, 6),
                "duplicate": is_dup,
            }
        )
        if abs(rho) > max_abs_rho:
            max_abs_rho = abs(rho)
            max_abs_rho_ref = label
        if ov > max_geol_overlap:
            max_geol_overlap = ov
            max_geol_overlap_ref = label

    records.sort(key=lambda r: -float(r["dot_overlap_3px_forward"]))
    return {
        "n_unique_registry_rasters_checked": (
            len(records) + len(constant_placeholders) + len(lattice_disclosures)
        ),
        "n_geological_rasters_enforced": len(records),
        "constant_placeholders_skipped": constant_placeholders,
        "spearman_cap": SPEARMAN_CAP,
        "overlap_3px_cap": OVERLAP_3PX_CAP,
        "max_abs_surface_spearman_rho": round(float(max_abs_rho), 6),
        "max_abs_surface_spearman_ref": max_abs_rho_ref,
        "max_geological_dot_overlap_3px": round(float(max_geol_overlap), 6),
        "max_geological_dot_overlap_ref": max_geol_overlap_ref,
        "synthetic_lattice_disclosure": lattice_disclosures,
        "duplicate_gate_passed": all_passed,
        "records": records,
    }


def write_and_validate_submission(
    *,
    dot_mask_or_prob: np.ndarray,
    surface_for_registry: np.ndarray,
    out_tif: Path,
    submission_name: str,
    submission_note: str,
    sample_tif: Path | None = None,
    existing_faults_tif: Path | None = None,
    footprint_mask: np.ndarray | None = None,
    write_zip: bool = True,
) -> dict[str, object]:
    """Write portal-compliant GeoTIFF (mode='zeros') + ZIP and return validation + registry receipt."""
    if len(submission_note) > 140:
        raise ValueError(f"submission_note exceeds 140 chars ({len(submission_note)})")

    sample_path = sample_tif or (data_dir() / "sample_submission.tif")
    faults_path = existing_faults_tif or (data_dir() / "existing_faults.tif")

    if footprint_mask is None:
        foot_npy = work_dir() / "bands" / "_footprint.npy"
        if foot_npy.exists():
            foot = np.load(foot_npy).astype(bool)
        else:
            with rasterio.open(sample_path) as s_src:
                foot = np.isfinite(s_src.read(1))
    else:
        foot = np.asarray(footprint_mask, dtype=bool)

    with rasterio.open(faults_path) as f_src:
        known = np.nan_to_num(f_src.read(1), nan=0.0) > 0.5

    raw = np.asarray(dot_mask_or_prob, dtype=np.float32)
    clean = np.where(
        foot & ~known,
        np.clip(np.nan_to_num(raw, nan=0.0, posinf=1.0, neginf=0.0), 0.0, 1.0),
        0.0,
    ).astype(np.float32)

    # write_submission refuses to overwrite by design; remove prior ATVR-36 draft if re-running
    if out_tif.exists():
        out_tif.unlink()

    write_submission(
        clean,
        sample_path,
        out_tif,
        note=submission_note,
        submission_name=submission_name,
        mode="zeros",
    )
    val_report = validate_submission(
        out_tif,
        sample_path,
        require_nonfinite_outside=False,
    )
    if not val_report.passed:
        raise RuntimeError(f"GeoTIFF failed portal validation: {val_report.errors}")

    with rasterio.open(out_tif) as chk:
        disk_arr = chk.read(1, masked=False)
        nan_total = int(np.isnan(disk_arr).sum())
        inf_total = int(np.isinf(disk_arr).sum())
        out_of_01 = int(((disk_arr < 0.0) | (disk_arr > 1.0)).sum())
        pos_inside = int((disk_arr[foot] > 0.5).sum())
        known_pos = int((disk_arr[known] > 0.0).sum())

    if nan_total > 0 or inf_total > 0 or out_of_01 > 0 or known_pos > 0:
        raise RuntimeError(
            f"Disk array check failed: nan={nan_total}, inf={inf_total}, "
            f"out_of_01={out_of_01}, known_pos={known_pos}"
        )

    tif_sha = sha256_file(out_tif)
    zip_info: dict[str, object] | None = None
    if write_zip:
        out_zip = out_tif.with_suffix(".zip")
        if out_zip.exists():
            out_zip.unlink()
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(out_tif, arcname=out_tif.name)
        zip_info = {
            "zip_path": str(out_zip),
            "zip_bytes": out_zip.stat().st_size,
            "zip_sha256": sha256_file(out_zip),
        }

    eval_mask = foot & ~known
    reg_items = discover_registry_rasters()
    registry_report = run_registry_audit(
        surface=surface_for_registry,
        dot_mask=(disk_arr > 0.5),
        valid_eval_mask=eval_mask,
        registry_items=reg_items,
        exclude_tif_sha256=tif_sha,
    )

    validator_dict = {
        "valid_for_portal": bool(val_report.passed and nan_total == 0 and out_of_01 == 0),
        "crs": val_report.crs,
        "shape": [val_report.height, val_report.width],
        "pixel_size_m": list(val_report.resolution_m),
        "dtype": val_report.dtype,
        "nodata": val_report.nodata,
        "nan_inside": int(val_report.invalid_in_bounds),
        "nan_outside": int(nan_total - val_report.invalid_in_bounds),
        "inf_count": inf_total,
        "min_inside": val_report.minimum,
        "max_inside": val_report.maximum,
        "out_of_range_total": out_of_01,
        "positive_gt_0p5_inside": pos_inside,
        "known_fault_positive_count": known_pos,
        "errors": list(val_report.errors),
    }

    receipt = {
        "submission_name": submission_name,
        "submission_note": submission_note,
        "submission_note_len": len(submission_note),
        "tif_path": str(out_tif),
        "tif_bytes": out_tif.stat().st_size,
        "tif_sha256": tif_sha,
        "zip": zip_info,
        "validator": validator_dict,
        "registry_audit": registry_report,
    }
    out_tif.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2))
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-npy", type=Path, required=True)
    ap.add_argument("--surface-npy", type=Path, default=None)
    ap.add_argument("--output-tif", type=Path, required=True)
    ap.add_argument("--name", type=str, required=True)
    ap.add_argument("--note", type=str, required=True)
    args = ap.parse_args()

    arr = np.load(args.input_npy)
    surf = np.load(args.surface_npy) if args.surface_npy else arr
    receipt = write_and_validate_submission(
        dot_mask_or_prob=arr,
        surface_for_registry=surf,
        out_tif=args.output_tif,
        submission_name=args.name,
        submission_note=args.note,
    )
    print(
        f"[submission_writer] OK tif={receipt['tif_path']} sha256={receipt['tif_sha256'][:12]} "
        f"dots={receipt['validator']['positive_gt_0p5_inside']} "
        f"dup_gate_passed={receipt['registry_audit']['duplicate_gate_passed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
