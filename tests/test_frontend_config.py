from __future__ import annotations

from pathlib import Path

import flet as ft
import pytest

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


def test_frontend_config_content_width_uses_available_width_for_small_pages() -> None:
    page = DummyPage()
    page.width = 320
    config = FrontEndConfig(page_padding=24, min_content_width=320)

    assert config.content_width_for_page(page) == 272  # type: ignore[arg-type]


def test_frontend_config_content_width_can_allow_min_width_overflow() -> None:
    page = DummyPage()
    page.width = 320
    config = FrontEndConfig(
        page_padding=24,
        min_content_width=320,
        allow_min_width_overflow=True,
    )

    assert config.content_width_for_page(page) == 320  # type: ignore[arg-type]


def test_frontend_config_content_width_never_goes_below_zero() -> None:
    page = DummyPage()
    page.width = 32
    config = FrontEndConfig(page_padding=24, min_content_width=320)

    assert config.content_width_for_page(page) == 0  # type: ignore[arg-type]


def test_frontend_config_builds_content_shell_with_very_reduced_width() -> None:
    page = DummyPage()
    page.width = 32
    config = FrontEndConfig(page_padding=24, min_content_width=320)

    shell = config.build_content_shell(ft.Text("hola"), page)  # type: ignore[arg-type]

    assert isinstance(shell, ft.Container)
    assert shell.width == 0
    assert shell.padding == 24


def test_frontend_config_preserves_existing_theme_properties() -> None:
    page = DummyPage()
    existing_theme = ft.Theme(
        scaffold_bgcolor=ft.Colors.AMBER, visual_density="compact"
    )
    page.theme = existing_theme
    config = FrontEndConfig(font_family="Inter", palette="material", mode="light")

    config.apply_to_page(page)  # type: ignore[arg-type]

    assert page.theme is existing_theme
    assert page.theme.font_family == "Inter"
    assert page.theme.scaffold_bgcolor == ft.Colors.AMBER
    assert page.theme.visual_density == "compact"


def test_frontend_config_theme_tokens_and_font_share_final_theme() -> None:
    page = DummyPage()
    existing_theme = ft.Theme(scaffold_bgcolor=ft.Colors.AMBER)
    page.theme = existing_theme
    config = FrontEndConfig(
        font_family="Inter",
        palette="material",
        mode="light",
        theme_tokens={"spacing": {"default": 12}, "radii": {"default": 6}},
    )

    config.apply_to_page(page)  # type: ignore[arg-type]

    assert page.theme is existing_theme
    assert page.theme.font_family == "Inter"
    assert page.theme.scaffold_bgcolor == ft.Colors.AMBER
    assert page.theme.spacing["default"] == 12
    assert page.theme.radii["default"] == 6


def test_frontend_config_can_load_from_pyproject(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.fletplus.frontend]
palette = 'ocean'
mode = 'dark'
font_family = 'Inter'
page_padding = 18
max_content_width = 960
spacing = 14
layout_density = 'compact'
unknown = 'ignored'
""",
        encoding="utf-8",
    )

    config = FrontEndConfig.from_pyproject(pyproject)

    assert config.palette == "ocean"
    assert config.mode == "dark"
    assert config.font_family == "Inter"
    assert config.page_padding == 18
    assert config.max_content_width == 960
    assert config.spacing == 14
    assert config.layout_density == "compact"


def test_frontend_config_loads_official_frontend_sections(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.fletplus.frontend]
palette = 'material'
mode = 'dark'
font_family = 'Inter'
page_padding = 20
max_content_width = 1000
min_content_width = 360
spacing = 18
layout_density = 'comfortable'
target = 'web'

[tool.fletplus.frontend.fonts]
Inter = 'assets/fonts/Inter.ttf'

[tool.fletplus.frontend.tokens.colors]
primary = '#2563EB'

[tool.fletplus.frontend.tokens.spacing]
page = 20
section = 32
""",
        encoding="utf-8",
    )

    config = FrontEndConfig.from_pyproject(pyproject)

    assert config.target == "web"
    assert config.font_assets == {"Inter": "assets/fonts/Inter.ttf"}
    assert config.theme_tokens["colors"]["primary"] == "#2563EB"
    assert config.theme_tokens["spacing"]["section"] == 32


def test_frontend_config_rejects_invalid_official_values(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.fletplus.frontend]
mode = 'sepia'
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="mode"):
        FrontEndConfig.from_pyproject(pyproject)


def test_frontend_config_from_pyproject_uses_defaults_when_missing(
    tmp_path: Path,
) -> None:
    config = FrontEndConfig.from_pyproject(tmp_path / "missing.toml")

    assert config.palette == "material"
    assert config.page_padding == 24


def test_frontend_config_applies_density_mode_and_responsive_metadata() -> None:
    page = DummyPage()
    page.width = 375
    page.height = 812
    config = FrontEndConfig(
        palette="material",
        mode="dark",
        layout_density="compact",
        follow_platform_theme=False,
    )

    manager = config.apply_to_page(page)  # type: ignore[arg-type]

    assert manager.dark_mode is True
    assert page.theme_mode == ft.ThemeMode.DARK
    assert page.theme.visual_density == "compact"
    assert manager._active_device == "mobile"
    assert manager._active_orientation == "portrait"


def test_frontend_config_can_read_follow_platform_theme(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.fletplus.frontend]
follow_platform_theme = true
""",
        encoding="utf-8",
    )

    config = FrontEndConfig.from_pyproject(pyproject)

    assert config.follow_platform_theme is True
