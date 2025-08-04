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
        "colors": {"primary": ft.Colors.RED},
        "typography": {"font_family": "Roboto"},
        "radii": {"default": 6},
    }

    manager = ThemeManager(page=page, tokens=tokens)
    manager.apply_theme()

    assert page.theme.color_scheme_seed == ft.Colors.RED
    assert page.theme.font_family == "Roboto"
    assert page.theme.radii["default"] == 6

    # get_token
    assert manager.get_token("colors.primary") == ft.Colors.RED

    # set_token should update internal token and page theme
    manager.set_token("colors.primary", ft.Colors.GREEN)
    assert manager.get_token("colors.primary") == ft.Colors.GREEN
    assert page.theme.color_scheme_seed == ft.Colors.GREEN

    manager.set_token("typography.font_family", "Arial")
    assert page.theme.font_family == "Arial"

    manager.set_token("radii.default", 12)
    assert page.theme.radii["default"] == 12
    assert manager.get_token("radii.default") == 12

    manager.set_token("colors.info_100", "#BBDEFB")
    assert manager.get_token("colors.info_100") == "#BBDEFB"

    # set_token should also handle semantic color tokens with underscores
    manager.set_token("colors.warning_500", ft.Colors.RED_500)
    assert manager.get_token("colors.warning_500") == ft.Colors.RED_500


def test_default_color_tokens():
    """Default semantic color tokens are retrievable via get_token."""

    page = DummyPage()
    manager = ThemeManager(page=page)

    color_map = {
        "secondary": "PURPLE",
        "tertiary": "TEAL",
        "info": "BLUE",
        "success": "GREEN",
        "warning": "AMBER",
        "error": "RED",
        "info": "BLUE",
    }

    for prefix, base in color_map.items():
        for shade in range(100, 1000, 100):
            token = f"colors.{prefix}_{shade}"
            expected = getattr(ft.Colors, f"{base}_{shade}")
            assert manager.get_token(token) == expected


def test_semantic_color_token_access_and_update():
    """Semantic color tokens are retrievable and mutable."""

    page = DummyPage()
    manager = ThemeManager(page=page)

    defaults = {
        "info_100": ft.Colors.BLUE_100,
        "success_200": ft.Colors.GREEN_200,
        "warning_500": ft.Colors.AMBER_500,
        "error_900": ft.Colors.RED_900,
    }
    updates = {
        "info_100": "#001122",
        "success_200": "#334455",
        "warning_500": "#667788",
        "error_900": "#99aabb",
    }

    for name, expected in defaults.items():
        token = f"colors.{name}"
        assert manager.get_token(token) == expected
        manager.set_token(token, updates[name])
        assert manager.get_token(token) == updates[name]

