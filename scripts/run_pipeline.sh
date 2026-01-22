#!/usr/bin/env bash
set -euo pipefail

python scripts/ingest_mtrs.py
python scripts/ingest_msrs.py
python scripts/transform_fact_tables.py
python scripts/build_marts.py
python scripts/generate_reports.py
