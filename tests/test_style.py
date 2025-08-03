import flet as ft

from fletplus.styles import Style


def test_apply_returns_container_with_styles():
    text_style = ft.TextStyle(color=ft.colors.WHITE)
    style = Style(
        margin=5,
        padding=10,
        bgcolor=ft.colors.RED,
        border_radius=4,
        border_color=ft.colors.BLUE,
        text_style=text_style,
    )
    control = ft.Text("hola")
    container = style.apply(control)

    assert isinstance(container, ft.Container)
    assert container.content is control
    assert container.margin == 5
    assert container.padding == 10
    assert container.bgcolor == ft.colors.RED
    assert container.border_radius == 4
    assert container.border.top.color == ft.colors.BLUE
    assert control.style == text_style


def test_apply_without_styles_returns_simple_container():
    style = Style()
    control = ft.Text("test")
    container = style.apply(control)

    assert isinstance(container, ft.Container)
    assert container.content is control
    assert container.margin is None
    assert container.padding is None
    assert container.bgcolor is None
    assert container.border is None
