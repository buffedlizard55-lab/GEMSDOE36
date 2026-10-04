#!/usr/bin/env bash
set -euo pipefail
python -m pytest -q
python -m ruff check src scripts tests
python scripts/check_site.py
