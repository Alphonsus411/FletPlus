import json
import flet as ft
import pytest
from fletplus.themes.theme_manager import (
    ThemeManager,
    load_palette_from_file,
    load_theme_from_json as load_theme_definition,
)

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
        primary_color=ft.Colors.RED
    )

    theme.apply_theme()
    assert page.theme.color_scheme_seed == ft.Colors.RED
    assert page.theme_mode == ft.ThemeMode.LIGHT
    assert page.updated

    page.updated = False
    theme.toggle_dark_mode()
    assert page.theme_mode == ft.ThemeMode.DARK
    assert page.updated

    page.updated = False
    theme.set_primary_color(ft.Colors.GREEN)
    assert page.theme.color_scheme_seed == ft.Colors.GREEN
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


def test_load_palette_from_missing_file(caplog):
    with caplog.at_level("ERROR"):
        assert load_palette_from_file("/no/such/file.json") == {}
    assert "not found" in caplog.text


def test_load_palette_from_file_requires_object_root(tmp_path, caplog):
    file_path = tmp_path / "palette.json"
    file_path.write_text(json.dumps(["not", "an", "object"]))

    with caplog.at_level("ERROR"):
        assert load_palette_from_file(str(file_path), "light") == {}

    assert "must contain a JSON object" in caplog.text


def test_load_palette_from_file_requires_object_mode(tmp_path, caplog):
    file_path = tmp_path / "palette.json"
    file_path.write_text(json.dumps({"light": "not-an-object"}))

    with caplog.at_level("ERROR"):
        assert load_palette_from_file(str(file_path), "light") == {}

    assert "must be a JSON object" in caplog.text


def test_apply_material3_preset_updates_tokens():
    page = DummyPage()
    theme = ThemeManager(page=page)

    theme.apply_material3()

    assert theme.get_token("typography.font_family") == "Roboto"
    assert theme.get_token("colors.primary") == "#6750A4"
    assert page.theme.font_family == "Roboto"
    assert page.theme.spacing["lg"] == 24

    theme.set_dark_mode(True)
    assert theme.get_token("colors.primary") == "#D0BCFF"


def test_apply_fluent_preset_updates_tokens():
    page = DummyPage()
    theme = ThemeManager(page=page)

    theme.apply_fluent(mode="dark")

    assert theme.dark_mode is True
    assert theme.get_token("colors.primary") == "#58A6FF"
    assert theme.get_token("typography.font_family") == "Segoe UI"
    assert page.theme.spacing["md"] == 12


def test_apply_cupertino_preset_updates_tokens():
    page = DummyPage()
    theme = ThemeManager(page=page)

    theme.apply_cupertino(refresh=False)

    assert theme.get_token("colors.primary") == "#0A84FF"
    assert theme.get_token("spacing.lg") == 24
    assert theme.get_token("typography.font_family") == "SF Pro Text"


def test_load_theme_from_json_with_overrides(tmp_path):
    data = {
        "preset": "material3",
        "mode": "dark",
        "tokens": {"spacing": {"md": 20}},
        "light": {"colors": {"primary": "#123456"}},
        "dark": {"colors": {"primary": "#654321"}},
    }
    file_path = tmp_path / "theme.json"
    file_path.write_text(json.dumps(data))

    page = DummyPage()
    theme = ThemeManager(page=page)

    theme.load_theme_from_json(str(file_path))

    assert theme.dark_mode is True
    assert theme.get_token("colors.primary") == "#654321"
    assert theme.get_token("spacing.md") == 20
    assert page.theme.color_scheme_seed == "#654321"


def test_load_theme_from_json_helper_returns_definition(tmp_path):
    data = {
        "preset": "fluent",
        "mode": "light",
        "light": {"colors": {"primary": "#101010"}},
    }
    file_path = tmp_path / "preset.json"
    file_path.write_text(json.dumps(data))

    payload = load_theme_definition(str(file_path))

    assert payload["preset"] == "fluent"
    assert payload["mode"] == "light"
    assert payload["variants"]["light"]["colors"]["primary"] == "#101010"
