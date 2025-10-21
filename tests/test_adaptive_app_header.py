import flet as ft
import pytest

from fletplus.components.adaptive_app_header import AdaptiveAppHeader
from fletplus.themes.theme_manager import ThemeManager


class DummyPage:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.platform = "web"
        self.on_resize = None
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1


@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
def test_adaptive_app_header_orientation_switch(orientation: str) -> None:
    width, height = (1200, 720) if orientation == "landscape" else (480, 900)
    page = DummyPage(width, height)
    theme = ThemeManager(page)

    header = AdaptiveAppHeader(
        title="Dashboard semanal",
        subtitle="Resumen de KPIs",
        supporting_text="Datos frescos cada hora",
        actions=[ft.TextButton(text="Actualizar")],
        hero=ft.Container(width=220, height=140, bgcolor=ft.Colors.BLUE_200),
        theme=theme,
        layout_by_orientation={"portrait": "stacked", "landscape": "split"},
        hero_max_height_by_device={"desktop": 300, "mobile": 160},
        hero_aspect_ratio=1.6,
    )

    container = header.build(page)
    assert isinstance(container, ft.Container)

    # For landscape we expect an inline hero and for portrait a stacked layout.
    first_control = header._content_column.controls[0]
    hero_container = header._hero_container
    assert hero_container is not None
    assert hero_container.max_height == (300 if orientation == "landscape" else 160)
    if orientation == "landscape":
        assert isinstance(first_control, ft.Row)
        assert any(
            isinstance(ctrl, ft.Container) and ctrl.content is header._hero_host.content
            for ctrl in first_control.controls
        )
    else:
        assert isinstance(first_control, ft.Column)
        assert header._content_column.controls[-1] is hero_container

    # Trigger an explicit orientation change and ensure the layout recalculates.
    target_orientation = "portrait" if orientation == "landscape" else "landscape"
    if target_orientation == "landscape":
        page.width, page.height = 1280, 720
    else:
        page.width, page.height = 480, 900
    header._handle_orientation_change(target_orientation)
    assert page.update_calls >= 1
    if target_orientation == "landscape":
        assert isinstance(header._content_column.controls[0], ft.Row)
    else:
        assert isinstance(header._content_column.controls[0], ft.Column)
