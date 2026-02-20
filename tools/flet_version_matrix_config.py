"""Configuración central de la matriz de versiones de Flet para pruebas."""

from __future__ import annotations

# Menores de Flet soportados para ejecución local cuando
# FLET_MATRIX_EXPECTED_MINOR no está definido por CI.
ALLOWED_FLET_MINORS: frozenset[str] = frozenset({"0.28", "0.80"})
