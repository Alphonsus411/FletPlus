import flet as ft

from fletplus.components.responsive_container import ResponsiveContainer
from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle


class DummyPage:
    def __init__(self, width: int = 300, height: int = 600) -> None:
        self.width = width
        self.height = height
        self.on_resize = None

    def update(self) -> None:  # pragma: no cover - solo para compatibilidad
        pass


def _trigger_resize(page: DummyPage) -> None:
    if page.on_resize:
        page.on_resize(None)


def test_responsive_container_restores_base_attributes():
    page = DummyPage(width=320, height=640)
    inner = ft.Container(padding=ft.padding.all(42))

    styles = ResponsiveStyle(
        width={
            0: Style(padding=5, bgcolor="red"),
            600: Style(bgcolor="green"),
        }
    )

    container = ResponsiveContainer(inner, styles)
    target = container.build(page)

    assert target.padding == 5
    assert target.bgcolor == "red"

    page.width = 700
    _trigger_resize(page)

    assert isinstance(target.padding, ft.padding.Padding)
    assert target.padding.left == 42
    assert target.bgcolor == "green"

    page.width = 400
    _trigger_resize(page)

    assert target.padding == 5
    assert target.bgcolor == "red"


def test_responsive_container_rebuild_disposes_previous_manager():
    page = DummyPage(width=500, height=700)
    calls: list[int] = []

    styles = ResponsiveStyle(width={0: Style(padding=5), 800: Style(padding=10)})

    def on_width(width: int) -> None:
        calls.append(width)

    container = ResponsiveContainer(
        ft.Container(content=ft.Text("Contenido")),
        styles,
        breakpoints={0: on_width, 800: on_width},
    )

    container.build(page)
    container.build(page)
    calls_before_resize = len(calls)

    page.width = 900
    _trigger_resize(page)

    assert len(calls) == calls_before_resize + 1

    container.dispose()
    assert page.on_resize is None
