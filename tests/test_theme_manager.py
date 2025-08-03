import json
import flet as ft
import pytest
from fletplus.themes.theme_manager import ThemeManager, load_palette_from_file

class DummyPage:
    def __init__(self):
        self.theme = None
        self.theme_mode = None
        self.updated = False

    def update(self):
        self.updated = True

def test_theme_manager_initialization_and_toggle():
    page = DummyPage()
    theme = ThemeManager(
        page=page,
        primary_color=ft.colors.RED
    )

    theme.apply_theme()
    assert page.theme.color_scheme_seed == ft.colors.RED
    assert page.theme_mode == ft.ThemeMode.LIGHT
    assert page.updated

    page.updated = False
    theme.toggle_dark_mode()
    assert page.theme_mode == ft.ThemeMode.DARK
    assert page.updated

    page.updated = False
    theme.set_primary_color(ft.colors.GREEN)
    assert page.theme.color_scheme_seed == ft.colors.GREEN
    assert page.updated


def test_spacing_border_shadow_tokens():
    page = DummyPage()
    theme = ThemeManager(page=page)

    theme.apply_theme()

    # Defaults are exposed
    assert theme.get_token("spacing.default") == 8
    assert page.theme.spacing["default"] == 8

    assert theme.get_token("borders.default") == 1
    assert page.theme.borders["default"] == 1

    assert theme.get_token("shadows.default") == "none"
    assert page.theme.shadows["default"] == "none"

    # Values can be updated
    theme.set_token("spacing.default", 20)
    assert theme.get_token("spacing.default") == 20
    assert page.theme.spacing["default"] == 20

    theme.set_token("borders.default", 2)
    assert theme.get_token("borders.default") == 2
    assert page.theme.borders["default"] == 2

    theme.set_token("shadows.default", "small")
    assert theme.get_token("shadows.default") == "small"
    assert page.theme.shadows["default"] == "small"


def test_load_palette_from_file_mode_validation(tmp_path):
    palette = {"light": {"primary": "#fff"}, "dark": {"primary": "#000"}}
    file_path = tmp_path / "palette.json"
    file_path.write_text(json.dumps(palette))

    assert load_palette_from_file(str(file_path), "light") == palette["light"]
    assert load_palette_from_file(str(file_path), "dark") == palette["dark"]

    with pytest.raises(ValueError):
        load_palette_from_file(str(file_path), "midnight")
