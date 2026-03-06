"""Prueba mínima para validar versiones objetivo de Flet en CI."""

from __future__ import annotations

import os
from importlib import metadata

import flet as ft

from tools.flet_version_matrix_config import ALLOWED_FLET_MINORS, FLET_MATRIX_MINORS


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


def test_matrix_minors_contract_shape() -> None:
    assert len(FLET_MATRIX_MINORS) == 2, (
        "El contrato activo debe declarar exactamente baseline y target en FLET_MATRIX_MINORS. "
        f"actual={FLET_MATRIX_MINORS!r}."
    )


def test_allowed_minors_match_active_contract() -> None:
    assert ALLOWED_FLET_MINORS == frozenset(FLET_MATRIX_MINORS), (
        "ALLOWED_FLET_MINORS no debe incluir minors legacy fuera del contrato activo. "
        f"contrato={FLET_MATRIX_MINORS!r}, permitidos={sorted(ALLOWED_FLET_MINORS)!r}."
    )


def _require_symbol(container: object, symbol_name: str, qualified_name: str) -> object:
    assert hasattr(container, symbol_name), (
        f"Símbolo sensible faltante: {qualified_name}. "
        f"Requerido para compatibilidad de la matriz de Flet."
    )
    return getattr(container, symbol_name)


def test_flet_matrix_sensitive_contracts_still_exist() -> None:
    # Símbolos clave para componentes/router/tema.
    _require_symbol(ft, "Theme", "ft.Theme")
    _require_symbol(ft, "ThemeMode", "ft.ThemeMode")
    _require_symbol(ft, "NavigationBar", "ft.NavigationBar")
    _require_symbol(ft, "NavigationRail", "ft.NavigationRail")
    _require_symbol(ft, "NavigationDrawer", "ft.NavigationDrawer")
    _require_symbol(ft, "PageTransitionsTheme", "ft.PageTransitionsTheme")

    icons_namespace = getattr(ft, "Icons", None) or getattr(ft, "icons", None)
    assert icons_namespace is not None, "Símbolo sensible faltante: ft.Icons/ft.icons."
    _require_symbol(icons_namespace, "HOME", "ft.Icons.HOME")

    _require_symbol(ft.Page, "run_task", "ft.Page.run_task")
    _require_symbol(ft.Page, "update", "ft.Page.update")
    _require_symbol(ft.Page, "go", "ft.Page.go")

    update_async = getattr(ft.Page, "update_async", None)
    if update_async is not None:
        assert callable(
            update_async
        ), "Símbolo sensible inválido: ft.Page.update_async no es callable."


def test_flet_compat_helpers_tolerate_missing_sensitive_symbols(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    monkeypatch.delattr(flet_compat.ft, "NavigationBarDestination", raising=False)
    monkeypatch.delattr(flet_compat.ft, "NavigationRailDestination", raising=False)
    monkeypatch.delattr(flet_compat.ft, "NavigationDrawerDestination", raising=False)

    nav_bar = flet_compat.make_navigation_bar_destination(icon="home", label="Inicio")
    nav_rail = flet_compat.make_navigation_rail_destination(icon="home", label="Inicio")
    nav_drawer = flet_compat.make_navigation_drawer_destination(
        icon="home", label="Inicio"
    )

    assert isinstance(nav_bar, flet_compat.ft.Container)
    assert isinstance(nav_rail, flet_compat.ft.Container)
    assert isinstance(nav_drawer, flet_compat.ft.Container)


def test_flet_compat_icon_resolution_falls_back_when_icons_namespace_changes(
    monkeypatch,
) -> None:
    from fletplus.utils import flet_compat

    monkeypatch.setattr(flet_compat.ft, "Icons", None, raising=False)
    monkeypatch.setattr(
        flet_compat.ft, "icons", type("icons", (), {"MENU": "menu"})(), raising=False
    )

    assert flet_compat.get_flet_icon("MENU", "fallback") == "menu"
    assert flet_compat.get_flet_icon("MISSING", "fallback") == "fallback"
