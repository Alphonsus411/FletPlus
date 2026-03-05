#!/usr/bin/env bash
set -euo pipefail

QA_SCOPE="all"

while (($# > 0)); do
  case "$1" in
    --scope)
      if (($# < 2)); then
        echo "ERROR: --scope requiere un valor (all|tests-matrix|static-security)." >&2
        exit 1
      fi
      QA_SCOPE="$2"
      shift 2
      ;;
    *)
      echo "ERROR: argumento no soportado: $1" >&2
      exit 1
      ;;
  esac
done

run_tests_matrix_scope() {
  python tools/check_test_dependencies.py --suite unit --suite cli --suite websocket
  python tools/check_package_data_files.py
  python tools/check_canonical_repo_links.py
  python tools/check_github_workflows.py
  python -m pytest
}

run_static_security_scope() {
  python -m ruff check .
  python -m black --check .
  python -m mypy fletplus
  python tools/check_bandit_command_sync.py
  python -m bandit -c pyproject.toml -r fletplus
  python -m pip_audit -r requirements.txt -r requirements-dev.txt
  python -m safety check -r requirements.txt -r requirements-dev.txt --policy-file safety-policy.yml
}

case "$QA_SCOPE" in
  all)
    run_tests_matrix_scope
    run_static_security_scope
    ;;
  tests-matrix)
    run_tests_matrix_scope
    ;;
  static-security)
    run_static_security_scope
    ;;
  *)
    echo "ERROR: scope inválido '$QA_SCOPE'. Usa all|tests-matrix|static-security." >&2
    exit 1
    ;;
esac
