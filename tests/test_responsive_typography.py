import flet as ft

from fletplus.themes.theme_manager import ThemeManager
from fletplus.utils.responsive_typography import (
    ResponsiveTypography,
    responsive_spacing,
    responsive_text,
)


class DummyPage:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.platform = "windows"
        self.on_resize = None
        self.theme = None
        self.theme_mode = None

    def resize(self, width: int | None = None, height: int | None = None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if self.on_resize:
            self.on_resize(None)

    def update(self):
        pass


def test_responsive_typography_updates_text_and_spacing():
    page = DummyPage(500, 800)
    theme = ThemeManager(page)
    typography = ResponsiveTypography(page, theme)

    txt = ft.Text("hola", style=ft.TextStyle(size=responsive_text(page)))
    typography.register_text(txt)
    box = ft.Container()
    typography.register_spacing_control(box)

    assert txt.style.size == 14
    assert responsive_spacing(page) == 8
    assert theme.tokens["spacing"]["default"] == 8

    page.resize(950)

    assert txt.style.size == 24
    assert responsive_spacing(page) == 16
    assert theme.tokens["spacing"]["default"] == 16

from fletplus.frontend.config import FrontEndConfig


def test_frontend_config_resolves_typography_by_width():
    config = FrontEndConfig(
        typography_tokens={
            "headline": {
                "mobile": {"size": 30, "weight": "w500", "line_height": 1.2},
                "desktop": {"size": 42, "weight": "w700", "line_height": 1.1},
                "pantalla_amplia": {"size": 54, "weight": "w700", "line_height": 1.05},
            }
        }
    )

    assert config.typography_size("headline", 390) == 30
    assert config.typography_weight("headline", 1280) == "w700"
    assert config.typography_line_height("headline", 1600) == 1.05


def test_responsive_typography_applies_role_styles():
    page = DummyPage(1280, 800)
    config = FrontEndConfig()
    typography = ResponsiveTypography(page, config=config)
    title = ft.Text("Título")

    typography.register_text(title, role="title")

    assert title.style.size == config.typography_size("title", 1280)
    assert title.style.weight == config.typography_weight("title", 1280)
    assert title.style.height == config.typography_line_height("title", 1280)
