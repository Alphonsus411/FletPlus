"""Tests for token handling in :mod:`fletplus.themes.theme_manager`."""

import flet as ft

from fletplus.themes.theme_manager import ThemeManager


class DummyPage:
    """Simple stand-in for ``ft.Page`` used in tests."""

    def __init__(self) -> None:
        self.theme = None
        self.theme_mode = None
        self.updated = False

    def update(self) -> None:
        self.updated = True


def test_get_and_set_tokens_updates_theme():
    """Tokens can be queried and updated live on the page."""

    page = DummyPage()
    tokens = {
        "colors": {"primary": ft.colors.RED},
        "typography": {"font_family": "Roboto"},
        "radii": {"default": 6},
    }

    manager = ThemeManager(page=page, tokens=tokens)
    manager.apply_theme()

    assert page.theme.color_scheme_seed == ft.colors.RED
    assert page.theme.font_family == "Roboto"
    assert page.theme.radii["default"] == 6

    # get_token
    assert manager.get_token("colors.primary") == ft.colors.RED

    # set_token should update internal token and page theme
    manager.set_token("colors.primary", ft.colors.GREEN)
    assert manager.get_token("colors.primary") == ft.colors.GREEN
    assert page.theme.color_scheme_seed == ft.colors.GREEN

    manager.set_token("typography.font_family", "Arial")
    assert page.theme.font_family == "Arial"

    manager.set_token("radii.default", 12)
    assert page.theme.radii["default"] == 12
    assert manager.get_token("radii.default") == 12

