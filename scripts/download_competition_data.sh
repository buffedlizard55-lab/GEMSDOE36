#!/usr/bin/env bash
# Autonomous Competition Data Placement & SHA-256 Verification Script
# Restores competition rasters, external USGS/DOE layers, and historical scored rasters
# into data/raw (or GEMS_DATA_DIR) and writes data/restore_receipt.json.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${GEMS_DATA_DIR:-$ROOT/data/raw}"
mkdir -p "$TARGET_DIR" "$ROOT/data"

echo "[GEMSDOE36] Verifying and restoring competition data into: $TARGET_DIR"
python3 "$ROOT/scripts/restore_data.py" --group all --target-dir "$TARGET_DIR"

echo "[GEMSDOE36] Competition data placement and SHA-256 verification succeeded."
