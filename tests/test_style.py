import flet as ft

from fletplus.styles import Style


def test_apply_returns_container_with_styles():
    text_style = ft.TextStyle(color=ft.colors.WHITE)
    shadow = ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK)
    gradient = ft.LinearGradient(colors=[ft.colors.RED, ft.colors.BLUE])
    transform = {"scale": ft.transform.Scale(0.5)}
    transition = ft.Animation(500, "easeInOut")
    style = Style(
        margin=5,
        padding=10,
        bgcolor=ft.colors.RED,
        border_radius=4,
        border_color=ft.colors.BLUE,
        text_style=text_style,
        width=100,
        height=200,
        min_width=50,
        max_width=150,
        min_height=100,
        max_height=250,
        shadow=shadow,
        gradient=gradient,
        alignment=ft.alignment.center,
        opacity=0.5,
        transform=transform,
        transition=transition,
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
    assert container.width == 100
    assert container.height == 200
    assert container.min_width == 50
    assert container.max_width == 150
    assert container.min_height == 100
    assert container.max_height == 250
    assert container.shadow == shadow
    assert container.gradient == gradient
    assert container.alignment == ft.alignment.center
    assert container.opacity == 0.5
    assert container.animate == transition
    assert container.scale == transform["scale"]


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
    assert container.width is None
    assert container.height is None
    assert not hasattr(container, "min_width")
    assert not hasattr(container, "max_width")
    assert not hasattr(container, "min_height")
    assert not hasattr(container, "max_height")
    assert container.shadow == []
    assert container.gradient is None
    assert container.alignment is None
    assert container.opacity == 1.0
    assert container.animate is None
    assert container.scale is None and container.rotate is None and container.offset is None
