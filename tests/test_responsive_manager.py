import flet as ft
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.components.responsive_grid import ResponsiveGrid


class DummyPage:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.on_resize = None

    def resize(self, width: int | None = None, height: int | None = None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if self.on_resize:
            self.on_resize(None)

    def update(self):
        pass


def test_responsive_manager_triggers_callbacks():
    page = DummyPage(500, 800)
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
    page = DummyPage(500, 800)
    items = [ft.Text(f"Item {i}") for i in range(2)]
    grid = ResponsiveGrid(children=items, breakpoints={0: 1, 600: 2})

    layout = grid.init_responsive(page)
    assert layout.controls[0].col == 12

    page.resize(650)
    assert layout.controls[0].col == 6


def test_responsive_manager_height_callbacks():
    page = DummyPage(500, 400)
    calls: list[tuple[str, int]] = []

    ResponsiveManager(
        page,
        breakpoints={},
        height_breakpoints={
            0: lambda h: calls.append(("short", h)),
            600: lambda h: calls.append(("tall", h)),
        },
    )

    page.resize(height=550)  # permanece en short
    page.resize(height=650)  # cambia a tall

    assert calls == [("short", 400), ("tall", 650)]


def test_responsive_manager_orientation_callbacks():
    page = DummyPage(500, 800)
    calls: list[str] = []

    ResponsiveManager(
        page,
        breakpoints={},
        height_breakpoints={},
        orientation_callbacks={
            "portrait": lambda o: calls.append(o),
            "landscape": lambda o: calls.append(o),
        },
    )

    page.resize(width=900, height=600)  # cambia a landscape

    assert calls == ["portrait", "landscape"]
