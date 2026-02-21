"""Configuración central de la matriz de versiones de Flet para pruebas."""

from __future__ import annotations

# FUENTE DE VERDAD ÚNICA:
# este archivo define los minors aprobados para la matriz de Flet.
# Cualquier cambio aquí debe reflejarse en:
# - .github/workflows/reusable-quality.yml (flet-version-matrix)
# - docs/migration-flet-latest.md
FLET_MATRIX_MINORS: tuple[str, ...] = ("0.28", "0.80")

# Menores de Flet soportados para ejecución local cuando
# FLET_MATRIX_EXPECTED_MINOR no está definido por CI.
ALLOWED_FLET_MINORS: frozenset[str] = frozenset(FLET_MATRIX_MINORS)
