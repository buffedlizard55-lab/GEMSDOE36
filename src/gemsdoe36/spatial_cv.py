"""Deterministic spatial-block folds with explicit collars against local leakage."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import binary_dilation


@dataclass(frozen=True)
class SpatialFold:
    """Masks for one block-held-out fold."""

    fold_index: int
    train_label_mask: np.ndarray
    validation_truth_mask: np.ndarray
    evaluation_domain_mask: np.ndarray
    held_out_block_ids: tuple[int, ...]


def _disk(radius_px: int) -> np.ndarray:
    if radius_px < 0:
        raise ValueError("radius_px must be non-negative")
    yy, xx = np.ogrid[-radius_px : radius_px + 1, -radius_px : radius_px + 1]
    return (xx * xx + yy * yy) <= radius_px * radius_px


def make_spatial_folds(
    height: int,
    width: int,
    *,
    n_splits: int = 5,
    block_size_px: int = 512,
    train_buffer_px: int = 30,
    metric_radius_px: int = 3,
    valid_area: np.ndarray | None = None,
    seed: int = 36,
) -> list[SpatialFold]:
    """Partition an image into contiguous tiles and produce seeded block CV folds.

    Each tile (not individual pixel) is assigned wholly to one fold.  A configurable
    collar is removed from the *label-training mask* around held-out tiles.  The metric
    evaluation domain includes a separate metric-radius buffer so nearby predictions may
    receive the same triangular-kernel credit they would receive in the full raster.

    This is a mechanics scaffold, not an evaluation result.  Before reporting science
    results, use the organizer's real labels, group connected fault systems/IDs where
    available, document the tile/collar parameters, and keep proxy-to-private-test limits
    explicit.
    """
    for name, value in (
        ("height", height),
        ("width", width),
        ("n_splits", n_splits),
        ("block_size_px", block_size_px),
    ):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if train_buffer_px < 0 or metric_radius_px < 0:
        raise ValueError("buffer sizes must be non-negative")

    if valid_area is None:
        domain = np.ones((height, width), dtype=bool)
    else:
        domain = np.asarray(valid_area, dtype=bool)
        if domain.shape != (height, width):
            raise ValueError("valid_area shape must match height and width")

    n_block_cols = (width + block_size_px - 1) // block_size_px
    n_block_rows = (height + block_size_px - 1) // block_size_px
    block_grid = np.arange(n_block_rows * n_block_cols, dtype=np.int32).reshape(
        n_block_rows, n_block_cols
    )
    block_ids = block_grid.ravel()
    if len(block_ids) < n_splits:
        raise ValueError(
            f"only {len(block_ids)} spatial blocks for {n_splits} folds; reduce block_size_px"
        )

    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(block_ids)
    assignments = np.empty(block_ids.shape, dtype=np.int32)
    assignments[shuffled] = np.arange(len(shuffled), dtype=np.int32) % n_splits
    block_to_fold = dict(zip(block_ids.tolist(), assignments.tolist(), strict=True))

    folds: list[SpatialFold] = []
    for fold_index in range(n_splits):
        held_ids = tuple(
            sorted(block_id for block_id, owner in block_to_fold.items() if owner == fold_index)
        )
        validation = np.zeros((height, width), dtype=bool)
        for block_id in held_ids:
            block_row, block_col = divmod(block_id, n_block_cols)
            y0, x0 = block_row * block_size_px, block_col * block_size_px
            y1, x1 = min(height, y0 + block_size_px), min(width, x0 + block_size_px)
            validation[y0:y1, x0:x1] = True
        validation &= domain

        # A disk collar (at least the metric support in any real run) stops adjacent labels
        # from appearing on both sides of a held-out border.
        collar_radius = max(train_buffer_px, metric_radius_px)
        expanded_train_exclusion = (
            binary_dilation(validation, structure=_disk(collar_radius))
            if collar_radius
            else validation.copy()
        )
        train_mask = domain & ~expanded_train_exclusion

        evaluation_domain = (
            binary_dilation(validation, structure=_disk(metric_radius_px))
            if metric_radius_px
            else validation.copy()
        )
        evaluation_domain &= domain
        folds.append(
            SpatialFold(
                fold_index=fold_index,
                train_label_mask=train_mask,
                validation_truth_mask=validation,
                evaluation_domain_mask=evaluation_domain,
                held_out_block_ids=held_ids,
            )
        )
    return folds
