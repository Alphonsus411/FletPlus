from __future__ import annotations

import flet as ft

from fletplus.frontend import FrontEndConfig


class DummyPage:
    def __init__(self) -> None:
        self.width = 900
        self.height = 600
        self.fonts = {}
        self.theme = None
        self.padding = None
        self.platform_brightness = "light"

    def update(self) -> None:
        return None


def test_frontend_config_resolves_profiles_and_columns() -> None:
    config = FrontEndConfig()

    assert config.resolve_device_profile(375).name == "mobile"
    assert config.columns_for_width(900) == 8


def test_frontend_config_applies_page_defaults() -> None:
    page = DummyPage()
    config = FrontEndConfig(
        font_family="Inter",
        font_assets={"Inter": "assets/fonts/Inter.ttf"},
        page_padding=32,
        palette="material",
        mode="light",
    )

    manager = config.apply_to_page(page)  # type: ignore[arg-type]

    assert page.fonts["Inter"] == "assets/fonts/Inter.ttf"
    assert page.padding == 32
    assert manager.page is page


def test_frontend_config_builds_content_shell_width() -> None:
    page = DummyPage()
    config = FrontEndConfig(page_padding=20, max_content_width=700)

    shell = config.build_content_shell(ft.Text("hola"), page)  # type: ignore[arg-type]

    assert isinstance(shell, ft.Container)
    assert shell.width == 700
