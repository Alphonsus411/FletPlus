#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYPROJECT_PATH="${PROJECT_ROOT}/pyproject.toml"
OUTPUT_PATH="${PYRUST_AUTO_OUTPUT:-${PROJECT_ROOT}/tools/pyrust_auto_report.md}"

cat <<INFO
Ejecutando pipeline "pyrust auto" (pyrust-native 0.0.4).
- Configuración de módulos: ${PYPROJECT_PATH} ([tool.pyrust-native])
- Reporte: ${OUTPUT_PATH}
INFO

pyrust auto "${PROJECT_ROOT}" --format markdown --output "${OUTPUT_PATH}" "$@"
