#!/usr/bin/env bash
set -euo pipefail

python tools/check_test_dependencies.py --suite unit --suite cli --suite websocket
python tools/check_package_data_files.py
python tools/check_canonical_repo_links.py
python tools/check_github_workflows.py
python -m pytest
python -m ruff check .
python -m black --check .
python -m mypy fletplus
python tools/check_bandit_command_sync.py
python -m bandit -c pyproject.toml -r fletplus
python -m pip_audit -r requirements.txt -r requirements-dev.txt --policy pip-audit.policy.json
python -m safety check -r requirements.txt -r requirements-dev.txt --policy-file safety-policy.yml
