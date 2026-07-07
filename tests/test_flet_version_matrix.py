"""Prueba mínima para validar versiones objetivo de Flet en CI."""

from __future__ import annotations

import os
from importlib import metadata

import flet as ft

from tools.flet_version_matrix_config import (
    ALLOWED_FLET_MINORS,
    FLET_MATRIX_MINORS,
    FLET_MATRIX_PINNED_PATCHES,
)


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
        pinned_patch = FLET_MATRIX_PINNED_PATCHES.get(expected_minor)
        if pinned_patch is not None:
            assert version == pinned_patch, (
                "El minor esperado está bloqueado a un patch documentado y no coincide: "
                f"detectada={version!r}, esperada={pinned_patch!r}."
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


def test_pinned_patch_versions_are_part_of_active_contract() -> None:
    assert set(FLET_MATRIX_PINNED_PATCHES).issubset(FLET_MATRIX_MINORS)
    for minor, version in FLET_MATRIX_PINNED_PATCHES.items():
        assert version.startswith(f"{minor}."), (
            "Cada patch bloqueado debe pertenecer al minor activo que documenta. "
            f"minor={minor!r}, version={version!r}."
        )


def test_flet_0853_sensitive_page_contracts() -> None:
    version = _read_flet_version()
    if version != FLET_MATRIX_PINNED_PATCHES.get("0.85"):
        return

    assert callable(_require_symbol(ft.Page, "show_dialog", "ft.Page.show_dialog"))
    assert callable(_require_symbol(ft.Page, "close_drawer", "ft.Page.close_drawer"))
    assert not hasattr(ft.Page, "open"), (
        "FletPlus no debe depender todavía de ft.Page.open en el target bloqueado 0.85.3; "
        "usar flet_compat.safe_show_dialog para mantener compatibilidad."
    )


def test_flet_0853_public_equivalents_for_compat_internal_fallbacks() -> None:
    version = _read_flet_version()
    if version != FLET_MATRIX_PINNED_PATCHES.get("0.85"):
        return

    assert getattr(ft, "Icons", None) is not None
    assert getattr(ft, "icons", None) is not None
    assert getattr(ft, "alignment", None) is not None
    assert getattr(ft, "Alignment", None) is not None
    assert getattr(ft, "Offset", None) is not None
    assert getattr(ft, "Scale", None) is not None
    assert getattr(ft, "Rotate", None) is not None


def test_flet_compat_import_tolerates_absent_internal_namespaces_in_matrix(monkeypatch) -> None:
    import importlib
    import sys

    fake_icons = getattr(ft, "Icons", None) or type("Icons", (), {"HOME": "home"})()
    fake_alignment = getattr(ft, "alignment", None) or type("alignment", (), {})()

    monkeypatch.setattr(ft, "Icons", fake_icons, raising=False)
    monkeypatch.setattr(ft, "icons", fake_icons, raising=False)
    monkeypatch.delattr(ft, "transform", raising=False)
    monkeypatch.setattr(ft, "alignment", fake_alignment, raising=False)

    real_import_module = importlib.import_module
    internal_imports: list[str] = []

    def _block_internal_import(name: str, package: str | None = None):
        if name.startswith("flet.controls."):
            internal_imports.append(name)
            raise ModuleNotFoundError(name)
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", _block_internal_import)
    sys.modules.pop("fletplus.utils.flet_compat", None)

    flet_compat = importlib.import_module("fletplus.utils.flet_compat")

    assert internal_imports == []
    assert flet_compat.get_flet_icons() is fake_icons
    assert hasattr(flet_compat.ft, "transform")
