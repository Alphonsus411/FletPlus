import flet as ft
import pytest

from fletplus.components.buttons import (
    PrimaryButton,
    SecondaryButton,
    SuccessButton,
    WarningButton,
    DangerButton,
    InfoButton,
    IconButton,
    OutlinedButton,
    TextButton,
    FloatingActionButton,
)
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
            "colors": {
                "primary": ft.colors.RED,
                "primary_hover": ft.colors.ORANGE,
                "primary_focus": ft.colors.PINK,
                "primary_pressed": ft.colors.PURPLE,
            },
            "typography": {"button_size": 20, "icon_size": 24},
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
    assert (
        container.content.style.bgcolor[ft.ControlState.DEFAULT] == ft.colors.RED
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.HOVERED] == ft.colors.ORANGE
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.FOCUSED] == ft.colors.PINK
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.PRESSED] == ft.colors.PURPLE
    )
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
            "colors": {
                "secondary": ft.colors.GREEN,
                "secondary_hover": ft.colors.GREEN_ACCENT,
                "secondary_focus": ft.colors.LIME,
                "secondary_pressed": ft.colors.TEAL,
            },
            "typography": {"button_size": 18, "icon_size": 22},
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
    assert (
        container.content.style.bgcolor[ft.ControlState.DEFAULT] == ft.colors.GREEN
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.HOVERED]
        == ft.colors.GREEN_ACCENT
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.FOCUSED] == ft.colors.LIME
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.PRESSED] == ft.colors.TEAL
    )
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
            "colors": {
                "primary": ft.colors.BLUE,
                "primary_hover": ft.colors.BLUE_200,
                "primary_focus": ft.colors.BLUE_300,
                "primary_pressed": ft.colors.BLUE_400,
            },
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
    assert (
        container.content.style.icon_color[ft.ControlState.DEFAULT] == ft.colors.BLUE
    )
    assert (
        container.content.style.icon_color[ft.ControlState.HOVERED]
        == ft.colors.BLUE_200
    )
    assert (
        container.content.style.icon_color[ft.ControlState.FOCUSED]
        == ft.colors.BLUE_300
    )
    assert (
        container.content.style.icon_color[ft.ControlState.PRESSED]
        == ft.colors.BLUE_400
    )
    assert container.content.style.icon_size[ft.ControlState.DEFAULT] == 32
    btn.on_click(None)
    assert called == ["info"]


def test_outlined_button_states_and_icon_position():
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {
                "primary": ft.colors.BLUE,
                "primary_hover": ft.colors.BLUE_100,
                "primary_focus": ft.colors.BLUE_200,
                "primary_pressed": ft.colors.BLUE_300,
            },
            "typography": {"button_size": 14, "icon_size": 18},
        },
    )
    btn = OutlinedButton(
        "Editar",
        icon=ft.icons.EDIT,
        icon_position="end",
        theme=theme,
        style=Style(bgcolor=ft.colors.WHITE),
    )
    container = btn.build()
    assert isinstance(container, ft.Container)
    assert container.bgcolor == ft.colors.WHITE
    row = container.content.content
    assert isinstance(row.controls[0], ft.Text)
    assert isinstance(row.controls[1], ft.Icon)
    assert row.controls[0].size == 14
    assert row.controls[1].size == 18
    style = container.content.style
    assert style.side[ft.ControlState.DEFAULT].color == ft.colors.BLUE
    assert style.bgcolor[ft.ControlState.HOVERED] == ft.colors.BLUE_100
    assert style.bgcolor[ft.ControlState.FOCUSED] == ft.colors.BLUE_200
    assert style.bgcolor[ft.ControlState.PRESSED] == ft.colors.BLUE_300


def test_text_button_states():
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {
                "primary": ft.colors.BLACK,
                "primary_hover": ft.colors.GREY_400,
                "primary_focus": ft.colors.GREY_500,
                "primary_pressed": ft.colors.GREY_600,
            },
            "typography": {"button_size": 12, "icon_size": 16},
        },
    )
    btn = TextButton("Seguir", icon=ft.icons.NAVIGATE_NEXT, theme=theme)
    control = btn.build()
    style = control.style
    assert style.text_style[ft.ControlState.DEFAULT].size == 12
    assert style.icon_size[ft.ControlState.DEFAULT] == 16
    assert style.color[ft.ControlState.DEFAULT] == ft.colors.BLACK
    assert style.bgcolor[ft.ControlState.HOVERED] == ft.colors.GREY_400


def test_fab_states_and_shape():
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {
                "primary": ft.colors.RED,
                "primary_hover": ft.colors.RED_200,
                "primary_focus": ft.colors.RED_300,
                "primary_pressed": ft.colors.RED_400,
            },
            "typography": {"button_size": 14, "icon_size": 24},
        },
    )
    btn = FloatingActionButton(
        icon=ft.icons.ADD,
        theme=theme,
        style=Style(bgcolor=ft.colors.YELLOW),
    )
    container = btn.build()
    assert container.bgcolor == ft.colors.YELLOW
    style = container.content.style
    assert isinstance(style.shape[ft.ControlState.DEFAULT], ft.CircleBorder)
    assert style.bgcolor[ft.ControlState.HOVERED] == ft.colors.RED_200
    assert style.bgcolor[ft.ControlState.FOCUSED] == ft.colors.RED_300
    assert style.bgcolor[ft.ControlState.PRESSED] == ft.colors.RED_400
    assert style.icon_size[ft.ControlState.DEFAULT] == 24


@pytest.mark.parametrize(
    "cls,color_key,colors",
    [
        (
            SuccessButton,
            "success",
            (
                ft.colors.GREEN,
                ft.colors.GREEN_200,
                ft.colors.GREEN_300,
                ft.colors.GREEN_400,
            ),
        ),
        (
            WarningButton,
            "warning",
            (
                ft.colors.AMBER,
                ft.colors.AMBER_200,
                ft.colors.AMBER_300,
                ft.colors.AMBER_400,
            ),
        ),
        (
            DangerButton,
            "error",
            (
                ft.colors.RED,
                ft.colors.RED_200,
                ft.colors.RED_300,
                ft.colors.RED_400,
            ),
        ),
        (
            InfoButton,
            "info",
            (
                ft.colors.BLUE,
                ft.colors.BLUE_200,
                ft.colors.BLUE_300,
                ft.colors.BLUE_400,
            ),
        ),
    ],
)
def test_status_buttons(cls, color_key, colors):
    page = DummyPage()
    base, hover, focus, pressed = colors
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {
                color_key: base,
                f"{color_key}_hover": hover,
                f"{color_key}_focus": focus,
                f"{color_key}_pressed": pressed,
            },
            "typography": {"button_size": 15, "icon_size": 25},
        },
    )
    btn = cls(
        "Aceptar",
        icon=ft.icons.CHECK,
        theme=theme,
        style=Style(bgcolor=ft.colors.BLACK),
    )
    container = btn.build()
    assert container.bgcolor == ft.colors.BLACK
    style = container.content.style
    assert style.bgcolor[ft.ControlState.DEFAULT] == base
    assert style.bgcolor[ft.ControlState.HOVERED] == hover
    assert style.bgcolor[ft.ControlState.FOCUSED] == focus
    assert style.bgcolor[ft.ControlState.PRESSED] == pressed
    assert btn.style.text_style[ft.ControlState.DEFAULT].size == 15
    assert btn.style.icon_size[ft.ControlState.DEFAULT] == 25
