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
                "primary": ft.Colors.RED,
                "primary_hover": ft.Colors.ORANGE,
                "primary_focus": ft.Colors.PINK,
                "primary_pressed": ft.Colors.PURPLE,
            },
            "typography": {"button_size": 20, "icon_size": 24},
        },
    )
    called: list[str] = []
    btn = PrimaryButton(
        "Enviar",
        icon=ft.icons.SEND,
        theme=theme,
        style=Style(bgcolor=ft.Colors.YELLOW),
        on_click=lambda e: called.append("ok"),
    )
    container = btn.build()
    assert isinstance(container, ft.Container)
    assert container.bgcolor == ft.Colors.YELLOW
    assert (
        container.content.style.bgcolor[ft.ControlState.DEFAULT] == ft.Colors.RED
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.HOVERED] == ft.Colors.ORANGE
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.FOCUSED] == ft.Colors.PINK
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.PRESSED] == ft.Colors.PURPLE
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
                "secondary": ft.Colors.GREEN,
                "secondary_hover": ft.Colors.GREEN_ACCENT,
                "secondary_focus": ft.Colors.LIME,
                "secondary_pressed": ft.Colors.TEAL,
            },
            "typography": {"button_size": 18, "icon_size": 22},
        },
    )
    called: list[str] = []
    btn = SecondaryButton(
        "Cancelar",
        icon=ft.icons.CLOSE,
        theme=theme,
        style=Style(bgcolor=ft.Colors.BLUE),
        on_click=lambda e: called.append("cancel"),
    )
    container = btn.build()
    assert isinstance(container, ft.Container)
    assert container.bgcolor == ft.Colors.BLUE
    assert (
        container.content.style.bgcolor[ft.ControlState.DEFAULT] == ft.Colors.GREEN
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.HOVERED]
        == ft.Colors.GREEN_ACCENT
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.FOCUSED] == ft.Colors.LIME
    )
    assert (
        container.content.style.bgcolor[ft.ControlState.PRESSED] == ft.Colors.TEAL
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
                "primary": ft.Colors.BLUE,
                "primary_hover": ft.Colors.BLUE_200,
                "primary_focus": ft.Colors.BLUE_300,
                "primary_pressed": ft.Colors.BLUE_400,
            },
            "typography": {"icon_size": 32},
        },
    )
    called: list[str] = []
    btn = IconButton(
        icon=ft.icons.INFO,
        label="Info",
        theme=theme,
        style=Style(bgcolor=ft.Colors.ORANGE),
        on_click=lambda e: called.append("info"),
    )
    container = btn.build()
    assert isinstance(container, ft.Container)
    assert container.bgcolor == ft.Colors.ORANGE
    assert (
        container.content.style.icon_color[ft.ControlState.DEFAULT] == ft.Colors.BLUE
    )
    assert (
        container.content.style.icon_color[ft.ControlState.HOVERED]
        == ft.Colors.BLUE_200
    )
    assert (
        container.content.style.icon_color[ft.ControlState.FOCUSED]
        == ft.Colors.BLUE_300
    )
    assert (
        container.content.style.icon_color[ft.ControlState.PRESSED]
        == ft.Colors.BLUE_400
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
                "primary": ft.Colors.BLUE,
                "primary_hover": ft.Colors.BLUE_100,
                "primary_focus": ft.Colors.BLUE_200,
                "primary_pressed": ft.Colors.BLUE_300,
            },
            "typography": {"button_size": 14, "icon_size": 18},
        },
    )
    btn = OutlinedButton(
        "Editar",
        icon=ft.icons.EDIT,
        icon_position="end",
        theme=theme,
        style=Style(bgcolor=ft.Colors.WHITE),
    )
    container = btn.build()
    assert isinstance(container, ft.Container)
    assert container.bgcolor == ft.Colors.WHITE
    row = container.content.content
    assert isinstance(row.controls[0], ft.Text)
    assert isinstance(row.controls[1], ft.Icon)
    assert row.controls[0].size == 14
    assert row.controls[1].size == 18
    style = container.content.style
    assert style.side[ft.ControlState.DEFAULT].color == ft.Colors.BLUE
    assert style.bgcolor[ft.ControlState.HOVERED] == ft.Colors.BLUE_100
    assert style.bgcolor[ft.ControlState.FOCUSED] == ft.Colors.BLUE_200
    assert style.bgcolor[ft.ControlState.PRESSED] == ft.Colors.BLUE_300


def test_text_button_states():
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {
                "primary": ft.Colors.BLACK,
                "primary_hover": ft.Colors.GREY_400,
                "primary_focus": ft.Colors.GREY_500,
                "primary_pressed": ft.Colors.GREY_600,
            },
            "typography": {"button_size": 12, "icon_size": 16},
        },
    )
    btn = TextButton("Seguir", icon=ft.icons.NAVIGATE_NEXT, theme=theme)
    control = btn.build()
    style = control.style
    assert style.text_style[ft.ControlState.DEFAULT].size == 12
    assert style.icon_size[ft.ControlState.DEFAULT] == 16
    assert style.color[ft.ControlState.DEFAULT] == ft.Colors.BLACK
    assert style.bgcolor[ft.ControlState.HOVERED] == ft.Colors.GREY_400


def test_fab_states_and_shape():
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {
                "primary": ft.Colors.RED,
                "primary_hover": ft.Colors.RED_200,
                "primary_focus": ft.Colors.RED_300,
                "primary_pressed": ft.Colors.RED_400,
            },
            "typography": {"button_size": 14, "icon_size": 24},
        },
    )
    btn = FloatingActionButton(
        icon=ft.icons.ADD,
        theme=theme,
        style=Style(bgcolor=ft.Colors.YELLOW),
    )
    container = btn.build()
    assert container.bgcolor == ft.Colors.YELLOW
    style = container.content.style
    assert isinstance(style.shape[ft.ControlState.DEFAULT], ft.CircleBorder)
    assert style.bgcolor[ft.ControlState.HOVERED] == ft.Colors.RED_200
    assert style.bgcolor[ft.ControlState.FOCUSED] == ft.Colors.RED_300
    assert style.bgcolor[ft.ControlState.PRESSED] == ft.Colors.RED_400
    assert style.icon_size[ft.ControlState.DEFAULT] == 24


@pytest.mark.parametrize(
    "cls,color_key,colors",
    [
        (
            SuccessButton,
            "success",
            (
                ft.Colors.GREEN,
                ft.Colors.GREEN_200,
                ft.Colors.GREEN_300,
                ft.Colors.GREEN_400,
            ),
        ),
        (
            WarningButton,
            "warning",
            (
                ft.Colors.AMBER,
                ft.Colors.AMBER_200,
                ft.Colors.AMBER_300,
                ft.Colors.AMBER_400,
            ),
        ),
        (
            DangerButton,
            "error",
            (
                ft.Colors.RED,
                ft.Colors.RED_200,
                ft.Colors.RED_300,
                ft.Colors.RED_400,
            ),
        ),
        (
            InfoButton,
            "info",
            (
                ft.Colors.BLUE,
                ft.Colors.BLUE_200,
                ft.Colors.BLUE_300,
                ft.Colors.BLUE_400,
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
        style=Style(bgcolor=ft.Colors.BLACK),
    )
    container = btn.build()
    assert container.bgcolor == ft.Colors.BLACK
    style = container.content.style
    assert style.bgcolor[ft.ControlState.DEFAULT] == base
    assert style.bgcolor[ft.ControlState.HOVERED] == hover
    assert style.bgcolor[ft.ControlState.FOCUSED] == focus
    assert style.bgcolor[ft.ControlState.PRESSED] == pressed
    assert btn.style.text_style[ft.ControlState.DEFAULT].size == 15
    assert btn.style.icon_size[ft.ControlState.DEFAULT] == 25


@pytest.mark.parametrize(
    "cls,color_key,color",
    [
        (SuccessButton, "success", ft.Colors.GREEN),
        (WarningButton, "warning", ft.Colors.AMBER),
        (DangerButton, "error", ft.Colors.RED),
        (InfoButton, "info", ft.Colors.BLUE),
    ],
)
def test_status_buttons_icon_end(cls, color_key, color):
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {color_key: color},
            "typography": {"button_size": 10, "icon_size": 20},
        },
    )
    btn = cls(
        "Acción",
        icon=ft.icons.CHECK,
        icon_position="end",
        theme=theme,
        style=Style(bgcolor=ft.Colors.WHITE),
    )
    container = btn.build()
    assert container.bgcolor == ft.Colors.WHITE
    row = container.content.content
    assert isinstance(row.controls[0], ft.Text)
    assert isinstance(row.controls[1], ft.Icon)
    assert row.controls[0].size == 10
    assert row.controls[1].size == 20
    style = container.content.style
    assert style.bgcolor[ft.ControlState.DEFAULT] == color
