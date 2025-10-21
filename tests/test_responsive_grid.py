import flet as ft
import pytest

from fletplus.components.responsive_grid import (
    HeaderHighlight,
    ResponsiveGrid,
    ResponsiveGridItem,
)
from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle
from fletplus.themes.theme_manager import ThemeManager


@pytest.fixture
def page_factory():
    class DummyPage:
        def __init__(self, width: int, height: int) -> None:
            self.width = width
            self.height = height
            self.platform = "web"
            self.on_resize = None
            self.update_calls = 0

        def update(self) -> None:
            self.update_calls += 1

    def factory(width: int = 800, height: int = 600) -> DummyPage:
        return DummyPage(width, height)

    return factory

def test_responsive_grid_builds_correctly():
    # Crear una lista de widgets dummy
    items = [
        ft.Text(f"Elemento {i}") for i in range(4)
    ]

    # Breakpoints definidos manualmente
    breakpoints = {
        0: 1,
        600: 2,
        900: 4
    }

    grid = ResponsiveGrid(children=items, breakpoints=breakpoints, spacing=5)

    # Simular un ancho de 900px (esperamos 4 columnas)
    layout = grid.build(page_width=900)

    # Validaciones
    assert isinstance(layout, ft.ResponsiveRow)
    assert len(layout.controls) == len(items)

    # Cada contenedor debe tener col=3 (12/4 columnas)
    for container in layout.controls:
        assert isinstance(container, ft.Container)
        assert container.col == 3


def test_responsive_grid_handles_none_width():
    grid = ResponsiveGrid(children=[ft.Text("Elemento")])

    layout = grid.build(page_width=None)

    assert isinstance(layout, ft.ResponsiveRow)
    assert all(isinstance(control, ft.Container) for control in layout.controls)


def test_responsive_grid_item_span_by_device():
    grid = ResponsiveGrid(
        items=[
            ResponsiveGridItem(
                ft.Text("Principal"),
                span_devices={"mobile": 12, "tablet": 6, "desktop": 3},
            ),
            ResponsiveGridItem(
                ft.Text("Secundario"),
                span_breakpoints={0: 12, 800: 6, 1100: 4},
            ),
        ]
    )

    mobile_row = grid.build(page_width=400)
    tablet_row = grid.build(page_width=800)
    desktop_row = grid.build(page_width=1200)

    assert [control.col for control in mobile_row.controls] == [12, 12]
    assert [control.col for control in tablet_row.controls] == [6, 6]
    assert [control.col for control in desktop_row.controls] == [3, 4]


def test_responsive_grid_registers_responsive_styles(page_factory):
    page = page_factory()
    style = ResponsiveStyle(width={0: Style(bgcolor="#fff"), 800: Style(bgcolor="#000")})
    grid = ResponsiveGrid(
        items=[ResponsiveGridItem(ft.Text("Item"), responsive_style=style)]
    )

    layout = grid.init_responsive(page)
    row = layout.content if isinstance(layout, ft.Container) else layout
    container = row.controls[0]

    registered_style = getattr(container, "_fletplus_responsive_style", None)
    assert isinstance(registered_style, ResponsiveStyle)


def test_responsive_grid_header_tags_and_highlights(page_factory):
    page = page_factory(width=1280, height=720)
    theme = ThemeManager(page=page)
    grid = ResponsiveGrid(
        header_title="Panel de control",
        header_tags=["Urgente", ("Beta", ft.Icons.FLUTTER_DASH)],
        header_highlights=[
            HeaderHighlight(label="Usuarios", value="1.2K", icon=ft.Icons.PEOPLE),
            {"label": "Satisfacción", "value": "97%", "description": "Últimos 7 días"},
        ],
        section_glass_background=True,
        section_border=ft.border.all(2, "#334155"),
        theme=theme,
        header_background="#0F172A",
        header_padding={"desktop": ft.Padding(28, 24, 28, 32)},
    )

    layout = grid.init_responsive(page)
    assert layout is not None

    tags_layout = grid._build_tags_layout("desktop")
    assert tags_layout is not None
    assert getattr(tags_layout, "wrap", False)

    highlights_layout = grid._build_highlight_layout("desktop")
    assert highlights_layout is not None
    assert any(isinstance(ctrl, ft.Container) for ctrl in highlights_layout.controls)

    grid._update_section_layout(page.width)
    assert grid._section_container is not None
    assert grid._section_container.border is not None
    assert grid._section_container.shadow is not None

    grid._update_section_header(page.width)
    assert grid._section_header_container is not None
    assert isinstance(grid._section_header_container.padding, ft.Padding)


def test_responsive_grid_item_visibility_across_devices():
    grid = ResponsiveGrid(
        items=[
            ResponsiveGridItem(
                ft.Text("Solo escritorio"),
                visible_devices=["desktop", "large_desktop"],
            ),
            ResponsiveGridItem(
                ft.Text("Oculto móvil"),
                hidden_devices="mobile",
            ),
            ResponsiveGridItem(
                ft.Text("Rango ancho"),
                min_width=700,
                max_width=1100,
            ),
        ]
    )

    mobile_row = grid.build(page_width=360)
    assert isinstance(mobile_row, ft.ResponsiveRow)
    assert len(mobile_row.controls) == 0

    tablet_row = grid.build(page_width=820)
    assert [
        container.content.value for container in tablet_row.controls
    ] == ["Oculto móvil", "Rango ancho"]

    desktop_row = grid.build(page_width=1200)
    assert [
        container.content.value for container in desktop_row.controls
    ] == ["Solo escritorio", "Oculto móvil"]


def test_responsive_grid_header_surface_customization(page_factory):
    page = page_factory(width=1024, height=720)
    theme = ThemeManager(page=page)
    header_gradient = ft.LinearGradient(
        colors=["#1F2937", "#3B82F6"],
        begin=ft.Alignment(-1.0, 0.0),
        end=ft.Alignment(1.0, 0.0),
    )
    grid = ResponsiveGrid(
        header_title="Resumen",
        header_gradient=header_gradient,
        header_border=ft.border.all(1, "#3B82F6"),
        header_shadow=ft.BoxShadow(
            blur_radius=16,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.18, "#1F2937"),
            offset=ft.Offset(0, 6),
        ),
        header_padding={"desktop": ft.Padding(32, 24, 32, 28), "mobile": ft.Padding(16, 12, 16, 16)},
        theme=theme,
    )

    layout = grid.init_responsive(page)
    assert layout is not None
    grid._update_section_header(page.width)
    header_container = grid._section_header_container
    assert header_container is not None
    assert header_container.gradient is header_gradient
    assert header_container.border is not None
    assert header_container.shadow is not None
    assert isinstance(header_container.padding, ft.Padding)
    assert header_container.padding.left == 32

    grid._update_section_header(420)
    assert grid._section_header_container.padding.left == 16


def test_responsive_grid_orientation_controls(page_factory):
    page = page_factory(width=900, height=1200)
    theme = ThemeManager(page=page)
    landscape_gradient = ft.LinearGradient(
        colors=["#0EA5E9", "#1D4ED8"],
        begin=ft.Alignment(-1.0, 0.0),
        end=ft.Alignment(1.0, 0.0),
    )
    grid = ResponsiveGrid(
        header_title="Reporte",
        items=[ResponsiveGridItem(ft.Text("Bloque"))],
        section_gap=18,
        section_gap_by_device={"mobile": 14, "tablet": 24, "desktop": 36},
        section_max_content_width_by_device={"tablet": 720, "desktop": 1280},
        section_orientation_backgrounds={"portrait": "#123456", "landscape": "#abcdef"},
        section_orientation_gradients={"landscape": landscape_gradient},
        theme=theme,
    )

    layout = grid.init_responsive(page)
    assert layout is not None

    grid._update_section_layout(page.width)
    assert grid.section_gap == 24
    assert grid._section_inner_container is not None
    assert grid._section_inner_container.width == 720
    assert grid._section_container.bgcolor == "#123456"

    # Simulate rotating the device to landscape desktop
    page.width = 1280
    page.height = 720
    grid._manager.orientation_callbacks["landscape"]("landscape")

    assert grid.section_gap == 36
    assert grid._section_inner_container.width == 1280
    assert grid._section_container.gradient is landscape_gradient
    assert grid._section_container.bgcolor is None
