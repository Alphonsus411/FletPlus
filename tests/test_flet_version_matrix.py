"""Prueba mínima para validar versiones objetivo de Flet en CI."""

from __future__ import annotations

import os
from importlib import metadata

import flet as ft

from tools.flet_version_matrix_config import ALLOWED_FLET_MINORS


def _read_flet_version() -> str:
    version = getattr(ft, "__version__", "")
    if version:
        return version
    return metadata.version("flet")


def test_flet_version_in_supported_matrix() -> None:
    expected_minor = os.getenv("FLET_MATRIX_EXPECTED_MINOR")
    version = _read_flet_version()
    parts = version.split(".")
    current_minor = ".".join(parts[:2]) if len(parts) >= 2 else version

    if expected_minor:
        assert current_minor == expected_minor, (
            "FLET_MATRIX_EXPECTED_MINOR tiene prioridad y no coincide con la versión detectada: "
            f"detectada={version!r} (minor={current_minor!r}), esperada={expected_minor!r}."
        )
    else:
        allowed_sorted = sorted(ALLOWED_FLET_MINORS)
        assert current_minor in ALLOWED_FLET_MINORS, (
            "La versión de Flet detectada no está en la lista permitida para ejecución local: "
            f"detectada={version!r} (minor={current_minor!r}), permitidas={allowed_sorted!r}."
        )


def _require_symbol(container: object, symbol_name: str, qualified_name: str) -> object:
    assert hasattr(container, symbol_name), (
        f"Símbolo sensible faltante: {qualified_name}. "
        f"Requerido para compatibilidad de la matriz de Flet."
    )
    return getattr(container, symbol_name)


def test_flet_matrix_sensitive_contracts_still_exist() -> None:
    _require_symbol(ft, "NavigationDrawer", "ft.NavigationDrawer")
    _require_symbol(ft, "PageTransitionsTheme", "ft.PageTransitionsTheme")
    _require_symbol(ft.Page, "window", "ft.Page.window")
    _require_symbol(ft.Page, "update", "ft.Page.update")

    update_async = getattr(ft.Page, "update_async", None)
    if update_async is not None:
        assert callable(update_async), "Símbolo sensible inválido: ft.Page.update_async no es callable."
