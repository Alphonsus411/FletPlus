"""Tests de contrato para APIs críticas de Flet usadas por FletPlus."""

from __future__ import annotations

import flet as ft

from fletplus.components.adaptive_layout import (
    AdaptiveDestination,
    AdaptiveNavigationLayout,
)
from fletplus.components.responsive_container import ResponsiveContainer
from fletplus.components.responsive_grid import ResponsiveGrid, ResponsiveGridItem
from fletplus.components.smart_table import SmartTable, SmartTableColumn
from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle


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


def test_page_window_dimension_contract() -> None:
    window_attr = _require_attr(ft.Page, "window")
    page_width_attr = getattr(ft.Page, "window_width", None)
    page_height_attr = getattr(ft.Page, "window_height", None)
    width_attr = getattr(ft.Page, "width", None)
    height_attr = getattr(ft.Page, "height", None)
    window = ft.Window()
    has_window_width = hasattr(window, "width")
    has_window_height = hasattr(window, "height")

    assert isinstance(window_attr, property)
    assert page_width_attr is not None or width_attr is not None or has_window_width
    assert page_height_attr is not None or height_attr is not None or has_window_height


def test_page_update_contract_methods_exist() -> None:
    update_method = _require_attr(ft.Page, "update")
    update_async_method = getattr(ft.Page, "update_async", None)

    assert callable(update_method)
    if update_async_method is not None:
        assert callable(update_async_method)


def test_page_drawer_contract_methods_optional_but_consistent() -> None:
    open_drawer = getattr(ft.Page, "open_drawer", None)
    close_drawer = getattr(ft.Page, "close_drawer", None)

    if open_drawer is not None:
        assert callable(open_drawer)
    if close_drawer is not None:
        assert callable(close_drawer)


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


def test_sensitive_flet_namespaces_contract() -> None:
    icons_namespace = getattr(ft, "Icons", None) or getattr(ft, "icons", None)
    colors_namespace = getattr(ft, "Colors", None) or getattr(ft, "colors", None)

    assert icons_namespace is not None
    assert colors_namespace is not None
    assert getattr(colors_namespace, "with_opacity", None) is not None
    assert callable(colors_namespace.with_opacity)


def test_sensitive_page_runtime_methods_contract() -> None:
    run_task_method = _require_attr(ft.Page, "run_task")
    assert callable(run_task_method)


def test_sensitive_layout_controls_contract() -> None:
    for symbol in (
        "Container",
        "Column",
        "Row",
        "NavigationBar",
        "NavigationRail",
        "DataTable",
    ):
        cls = _require_attr(ft, symbol)
        assert isinstance(cls, type)


class _ContractPageNoOptionalApi:
    def __init__(self, width: int) -> None:
        self.width = width
        self.height = 720
        self.on_resize = None
        self.platform = "web"
        self.theme = ft.Theme()
        self.locale = None
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1


def test_adaptive_layout_tolerates_missing_optional_page_apis() -> None:
    page = _ContractPageNoOptionalApi(width=420)
    layout = AdaptiveNavigationLayout(
        [AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED)],
        lambda idx, device: ft.Text(f"{idx}-{device}"),
        drawer=ft.NavigationDrawer(controls=[ft.Text("Menú")]),
    )

    root = layout.build(page)
    layout._open_drawer(None)
    layout._focus_content(None)

    assert isinstance(root, ft.Column)
    assert page.drawer is not None


def test_responsive_components_tolerate_minimal_page_contract() -> None:
    class _MinimalResponsivePage:
        def __init__(self) -> None:
            self.width = 900
            self.height = 700
            self.on_resize = None
            self.update_calls = 0

        def update(self) -> None:
            self.update_calls += 1

    page = _MinimalResponsivePage()

    container = ResponsiveContainer(
        content=ft.Text("contenido"),
        styles=ResponsiveStyle(width={0: Style(width=320), 600: Style(width=640)}),
    )
    built_container = container.build(page)

    grid = ResponsiveGrid(
        items=[ResponsiveGridItem(control=ft.Text("item"), span=12)],
        columns=12,
    )
    built_grid = grid.build(page.width)

    assert isinstance(built_container, ft.Container)
    assert isinstance(built_grid, ft.Control)


def test_smart_table_refresh_and_build_without_gui_runtime() -> None:
    table = SmartTable(
        columns=[SmartTableColumn(key="name", label="Nombre", sortable=True, filterable=True)],
        rows=[{"name": "Ada"}, {"name": "Linus"}],
    )

    control = table.build()
    table.set_filter("name", "a")
    table.toggle_sort("name")
    table.refresh()

    assert isinstance(control, ft.Control)


def test_icons_namespace_contract_supports_pascal_or_snake_case() -> None:
    icons_namespace = getattr(ft, "Icons", None) or getattr(ft, "icons", None)

    assert icons_namespace is not None
    home_icon = getattr(icons_namespace, "HOME", None) or getattr(icons_namespace, "home", None)
    assert home_icon is not None


def test_colors_namespace_contract_supports_pascal_or_snake_case() -> None:
    colors_namespace = getattr(ft, "Colors", None) or getattr(ft, "colors", None)

    assert colors_namespace is not None
    opacity_method = getattr(colors_namespace, "with_opacity", None)
    assert callable(opacity_method)


def test_page_update_contract_supports_sync_or_async_paths() -> None:
    update = getattr(ft.Page, "update", None)
    update_async = getattr(ft.Page, "update_async", None)

    assert callable(update)
    if update_async is not None:
        assert callable(update_async)


def test_page_window_dimensions_contract_has_modern_or_legacy_attributes() -> None:
    assert hasattr(ft.Page, "window")
    has_width = hasattr(ft.Page, "window_width") or hasattr(ft.Page, "width")
    has_height = hasattr(ft.Page, "window_height") or hasattr(ft.Page, "height")

    assert has_width is True
    assert has_height is True
