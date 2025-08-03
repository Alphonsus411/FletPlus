import flet as ft

from fletplus.themes.theme_manager import ThemeManager
from fletplus.utils.responsive_typography import ResponsiveTypography, responsive_text, responsive_spacing


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
