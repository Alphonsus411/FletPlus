import flet as ft
from fletplus.styles import Style
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.utils.responsive_style import ResponsiveStyle
from fletplus.components.responsive_grid import ResponsiveGrid


class DummyPage:
    def __init__(self, width: int, height: int, platform: str = "windows"):
        self.width = width
        self.height = height
        self.platform = platform
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


def test_responsive_manager_device_callbacks():
    page = DummyPage(480, 800)
    calls: list[tuple[str, str]] = []

    ResponsiveManager(
        page,
        device_callbacks={
            "mobile": lambda name: calls.append(("initial", name)),
            "desktop": lambda name: calls.append(("switch", name)),
        },
    )

    assert calls[0] == ("initial", "mobile")

    page.resize(width=1200)
    assert ("switch", "desktop") in calls


def test_responsive_style_by_width():
    page = DummyPage(500, 800)
    text = ft.Text("hola")
    styles = ResponsiveStyle(
        width={
            0: Style(text_style=ft.TextStyle(size=10)),
            600: Style(text_style=ft.TextStyle(size=20)),
        }
    )

    manager = ResponsiveManager(page)
    manager.register_styles(text, styles)

    assert text.style.size == 10

    page.resize(650)
    assert text.style.size == 20


def test_responsive_style_by_height():
    page = DummyPage(500, 400)
    text = ft.Text("hola")
    styles = ResponsiveStyle(
        height={
            0: Style(text_style=ft.TextStyle(size=10)),
            600: Style(text_style=ft.TextStyle(size=20)),
        }
    )

    manager = ResponsiveManager(page)
    manager.register_styles(text, styles)

    assert text.style.size == 10

    page.resize(height=650)
    assert text.style.size == 20


def test_responsive_style_by_orientation_and_device():
    page = DummyPage(500, 800, platform="android")
    text = ft.Text("hola")
    styles = ResponsiveStyle(
        orientation={
            "landscape": Style(text_style=ft.TextStyle(size=20)),
        },
        device={
            "desktop": Style(text_style=ft.TextStyle(size=30)),
            "mobile": Style(text_style=ft.TextStyle(size=40)),
        },
    )

    manager = ResponsiveManager(page)
    manager.register_styles(text, styles)

    # Inicialmente aplica estilo del dispositivo móvil
    assert text.style.size == 40

    # Cambia a landscape, debe usar estilo de orientación
    page.resize(width=900, height=600)
    assert text.style.size == 20

    # Cambia de plataforma a escritorio y fuerza actualización
    page.platform = "windows"
    page.resize(900)  # disparar resize
    assert text.style.size == 20


def test_responsive_style_updates_container_properties():
    page = DummyPage(500, 800)
    box = ft.Container(bgcolor="base", padding=ft.padding.all(5), width=120)
    styles = ResponsiveStyle(
        width={
            0: Style(bgcolor="red", padding=10, width=200),
            600: Style(bgcolor="blue"),
        }
    )

    manager = ResponsiveManager(page)
    manager.register_styles(box, styles)

    assert box.bgcolor == "red"
    assert box.padding == 10
    assert box.width == 200

    page.resize(650)
    assert box.bgcolor == "blue"
    assert isinstance(box.padding, ft.padding.Padding)
    assert box.padding.left == 5
    assert box.width == 120

    page.resize(400)
    assert box.bgcolor == "red"
    assert box.padding == 10
    assert box.width == 200


def test_responsive_manager_preserves_existing_resize_handler():
    page = DummyPage(500, 800)
    calls: list[str] = []

    def previous_handler(event):
        calls.append("previous")

    page.on_resize = previous_handler

    ResponsiveManager(page, {0: lambda _w: calls.append("manager")})

    page.resize(600)

    assert calls == ["manager", "previous"]
