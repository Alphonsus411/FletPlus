import flet as ft

from fletplus.components.buttons import PrimaryButton, SecondaryButton, IconButton
from fletplus.styles import Style
from fletplus.themes.theme_manager import ThemeManager


class DummyPage:
    def update(self):
        pass


def test_primary_button_style_and_callback():
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {"primary": ft.colors.RED},
            "typography": {"button_size": 20},
        },
    )
    called: list[str] = []
    btn = PrimaryButton(
        "Enviar",
        icon=ft.icons.SEND,
        theme=theme,
        style=Style(bgcolor=ft.colors.YELLOW),
        on_click=lambda e: called.append("ok"),
    )
    container = btn.build()
    assert isinstance(container, ft.Container)
    assert container.bgcolor == ft.colors.YELLOW
    assert container.content.bgcolor == ft.colors.RED
    assert (
        btn.style.text_style[ft.ControlState.DEFAULT].size == 20
    )
    btn.on_click(None)
    assert called == ["ok"]


def test_secondary_button_style_and_callback():
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {"secondary": ft.colors.GREEN},
            "typography": {"button_size": 18},
        },
    )
    called: list[str] = []
    btn = SecondaryButton(
        "Cancelar",
        icon=ft.icons.CLOSE,
        theme=theme,
        style=Style(bgcolor=ft.colors.BLUE),
        on_click=lambda e: called.append("cancel"),
    )
    container = btn.build()
    assert isinstance(container, ft.Container)
    assert container.bgcolor == ft.colors.BLUE
    assert container.content.bgcolor == ft.colors.GREEN
    assert (
        btn.style.text_style[ft.ControlState.DEFAULT].size == 18
    )
    btn.on_click(None)
    assert called == ["cancel"]


def test_icon_button_style_and_callback():
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {"primary": ft.colors.BLUE},
            "typography": {"icon_size": 32},
        },
    )
    called: list[str] = []
    btn = IconButton(
        icon=ft.icons.INFO,
        label="Info",
        theme=theme,
        style=Style(bgcolor=ft.colors.ORANGE),
        on_click=lambda e: called.append("info"),
    )
    container = btn.build()
    assert isinstance(container, ft.Container)
    assert container.bgcolor == ft.colors.ORANGE
    assert container.content.icon_color == ft.colors.BLUE
    assert container.content.icon_size == 32
    btn.on_click(None)
    assert called == ["info"]
