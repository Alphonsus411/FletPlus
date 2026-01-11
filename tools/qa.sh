#!/usr/bin/env bash
set -euo pipefail

python -m pytest
python -m ruff check .
python -m black --check .
python -m mypy fletplus
python -m bandit -r fletplus
python -m pip_audit -r requirements.txt -r requirements-dev.txt
python -m safety check -r requirements.txt -r requirements-dev.txt
