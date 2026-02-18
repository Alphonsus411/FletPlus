"""Tests de contrato para APIs críticas de Flet usadas por FletPlus."""

from __future__ import annotations

import flet as ft


def _require_attr(obj: object, attr_name: str) -> object:
    assert hasattr(obj, attr_name), f"Falta atributo requerido: {attr_name}"
    return getattr(obj, attr_name)


def test_theme_initialization_contract() -> None:
    theme = ft.Theme()

    _require_attr(theme, "color_scheme")
    _require_attr(theme, "page_transitions")


def test_color_scheme_assignment_contract() -> None:
    theme = ft.Theme()
    scheme = ft.ColorScheme(
        primary=ft.Colors.BLUE,
        on_primary=ft.Colors.WHITE,
        secondary=ft.Colors.GREEN,
        on_secondary=ft.Colors.WHITE,
        surface=ft.Colors.WHITE,
        on_surface=ft.Colors.BLACK,
    )

    theme.color_scheme = scheme

    assert theme.color_scheme is scheme
    assert theme.color_scheme.primary == ft.Colors.BLUE


def test_page_transition_theme_contract() -> None:
    transitions_theme_cls = _require_attr(ft, "PageTransitionsTheme")
    transition_enum = _require_attr(ft, "PageTransitionTheme")
    none_transition = _require_attr(transition_enum, "NONE")

    transitions = transitions_theme_cls(
        android=none_transition,
        ios=none_transition,
        linux=none_transition,
        macos=none_transition,
        windows=none_transition,
    )

    assert transitions.android == none_transition
    assert transitions.ios == none_transition


def test_navigation_drawer_contract() -> None:
    destination = ft.NavigationDrawerDestination(
        icon=ft.Icons.HOME,
        label="Inicio",
    )
    drawer = ft.NavigationDrawer(
        controls=[destination],
        selected_index=0,
    )

    assert len(drawer.controls) == 1
    assert drawer.selected_index == 0


def test_page_window_contract() -> None:
    window_attr = _require_attr(ft.Page, "window")
    assert isinstance(window_attr, property)


def test_page_update_contract_methods_exist() -> None:
    update_method = _require_attr(ft.Page, "update")
    update_async_method = getattr(ft.Page, "update_async", None)

    assert callable(update_method)
    if update_async_method is not None:
        assert callable(update_async_method)


def test_page_transition_theme_enum_contract() -> None:
    transition_enum = _require_attr(ft, "PageTransitionTheme")
    _require_attr(transition_enum, "NONE")


def test_navigation_rail_destination_contract() -> None:
    destination = ft.NavigationRailDestination(
        icon=ft.Icons.HOME,
        selected_icon=ft.Icons.HOME_FILLED,
        label="Inicio",
    )

    assert destination.icon == ft.Icons.HOME
    assert destination.selected_icon == ft.Icons.HOME_FILLED
    assert destination.label == "Inicio"


def test_navigation_bar_contract() -> None:
    destination = ft.NavigationBarDestination(
        icon=ft.Icons.HOME,
        selected_icon=ft.Icons.HOME_FILLED,
        label="Inicio",
    )

    nav_bar = ft.NavigationBar(
        destinations=[destination],
        selected_index=0,
        label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
    )

    assert len(nav_bar.destinations) == 1
    assert nav_bar.selected_index == 0
