import flet as ft
import pytest

from fletplus.components.responsive_grid import ResponsiveGrid, ResponsiveGridItem
from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle


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
