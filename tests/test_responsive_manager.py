import flet as ft
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.components.responsive_grid import ResponsiveGrid


class DummyPage:
    def __init__(self, width: int):
        self.width = width
        self.on_resize = None

    def resize(self, width: int):
        self.width = width
        if self.on_resize:
            self.on_resize(None)

    def update(self):
        pass


def test_responsive_manager_triggers_callbacks():
    page = DummyPage(500)
    calls: list[tuple[str, int]] = []

    ResponsiveManager(
        page,
        {
            0: lambda w: calls.append(("small", w)),
            600: lambda w: calls.append(("large", w)),
        },
    )

    page.resize(550)  # permanece en small
    page.resize(650)  # cambia a large

    assert calls == [("small", 500), ("large", 650)]


def test_responsive_grid_rebuilds_on_resize():
    page = DummyPage(500)
    items = [ft.Text(f"Item {i}") for i in range(2)]
    grid = ResponsiveGrid(children=items, breakpoints={0: 1, 600: 2})

    layout = grid.init_responsive(page)
    assert layout.controls[0].col == 12

    page.resize(650)
    assert layout.controls[0].col == 6
