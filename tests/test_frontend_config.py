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
        palette="aurora",
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
    config = FrontEndConfig(font_family="Inter", palette="aurora", mode="light")

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
        palette="aurora",
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
        palette="aurora",
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


def test_frontend_config_can_load_common_font_declaration(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    font_file = tmp_path / "assets" / "fonts" / "Inter-Regular.ttf"
    font_file.parent.mkdir(parents=True)
    font_file.write_text("placeholder", encoding="utf-8")
    pyproject.write_text(
        """[tool.fletplus.frontend.font]
family = 'Inter'
fallback_families = ['Roboto', 'Arial', 'sans-serif']
weights = ['w400', 'w700']
styles = ['normal', 'italic']

[tool.fletplus.frontend.font.assets]
Inter = 'assets/fonts/Inter-Regular.ttf'
""",
        encoding="utf-8",
    )

    config = FrontEndConfig.from_pyproject(pyproject)
    page = DummyPage()

    config.apply_to_page(page)  # type: ignore[arg-type]

    assert config.font.family == "Inter"
    assert config.font.fallback_families == ("Roboto", "Arial", "sans-serif")
    assert config.font.weights == ("w400", "w700")
    assert config.font.styles == ("normal", "italic")
    assert page.fonts["Inter"] == "assets/fonts/Inter-Regular.ttf"
    assert page.theme.font_family == "Inter, Roboto, Arial, sans-serif"


def test_frontend_config_warns_about_missing_local_font_assets() -> None:
    page = DummyPage()
    config = FrontEndConfig(
        font_family="Inter",
        font_assets={"Inter": "assets/fonts/Missing.ttf"},
    )

    with pytest.warns(UserWarning, match="Fuente local no encontrada.*Inter"):
        config.apply_to_page(page)  # type: ignore[arg-type]

    assert page.fonts["Inter"] == "assets/fonts/Missing.ttf"


def test_frontend_config_applies_target_presets_without_mutating_original() -> None:
    config = FrontEndConfig(target="mobile", page_padding=24, max_content_width=1200)

    mobile = config.configured_for_target()

    assert config.page_padding == 24
    assert config.max_content_width == 1200
    assert mobile.page_padding == 16
    assert mobile.max_content_width == 480
    assert mobile.spacing == 12
    assert mobile.layout_density == "compact"


def test_frontend_config_derives_registered_landing_preset_for_web() -> None:
    config = FrontEndConfig.from_mapping({"preset": "landing", "target": "web"})

    assert config.preset == "landing"
    assert config.palette == "solstice"
    assert config.layout_density == "spacious"
    assert config.page_padding == 40
    assert config.spacing == 20
    assert config.max_content_width == 1280
    assert config.font_family == "Inter"
    assert config.theme_tokens["spacing"]["section"] == 64
    assert config.typography_tokens["heading_weight"] == 800


def test_frontend_config_derives_registered_admin_preset_for_desktop() -> None:
    config = FrontEndConfig.from_mapping({"preset": "admin", "target": "desktop"})

    assert config.preset == "admin"
    assert config.palette == "metropolis"
    assert config.layout_density == "compact"
    assert config.page_padding == 24
    assert config.spacing == 12
    assert config.max_content_width == 1180
    assert config.theme_tokens["radii"]["card"] == 12
    assert config.typography_tokens["body_size"] == 14


def test_frontend_config_explicit_values_override_registered_preset() -> None:
    config = FrontEndConfig.from_mapping(
        {
            "preset": "landing",
            "target": "web",
            "palette": "aurora",
            "layout_density": "compact",
            "page_padding": 12,
            "max_content_width": 960,
            "spacing": 10,
            "typography_tokens": {"body": {"mobile": {"size": 18}}},
            "theme_tokens": {"colors": {"brand": "#111111"}},
        }
    )

    assert config.palette == "aurora"
    assert config.layout_density == "compact"
    assert config.page_padding == 12
    assert config.max_content_width == 960
    assert config.spacing == 10
    assert config.typography_tokens == {"body": {"mobile": {"size": 18}}}
    assert config.theme_tokens == {"colors": {"brand": "#111111"}}


def test_frontend_config_from_preset_keeps_explicit_override_precedence() -> None:
    config = FrontEndConfig.from_preset(
        "admin",
        target="desktop",
        palette="slate",
        layout_density="comfortable",
        spacing=18,
    )

    assert config.preset == "admin"
    assert config.target == "desktop"
    assert config.palette == "slate"
    assert config.layout_density == "comfortable"
    assert config.spacing == 18
    assert config.page_padding == 24
    assert config.max_content_width == 1180
    assert config.theme_tokens["radii"]["card"] == 12


def test_frontend_config_palette_for_web_merges_base_tokens() -> None:
    config = FrontEndConfig(
        palette="aurora",
        mode="light",
        platform_palettes={
            "web": {
                "primary": "#2563EB",
                "secondary": "#14B8A6",
                "background": "#F8FAFC",
                "surface": "#FFFFFF",
            }
        },
    )

    base_tokens = config.palette_tokens()
    palette = config.palette_for_target("web")

    assert palette["primary"] == "#2563EB"
    assert palette["secondary"] == "#14B8A6"
    assert palette["background"] == "#F8FAFC"
    assert palette["surface"] == "#FFFFFF"
    assert palette["on_primary"] == base_tokens["colors"]["on_primary"]
    assert palette["error"] == base_tokens["colors"]["error"]
    assert set(base_tokens["colors"]).issubset(palette)


def test_frontend_config_palette_for_desktop_merges_base_tokens() -> None:
    config = FrontEndConfig(
        palette="aurora",
        mode="light",
        platform_palettes={
            "desktop": {
                "primary": "#4F46E5",
                "secondary": "#0EA5E9",
                "background": "#EEF2FF",
                "surface": "#FFFFFF",
            }
        },
    )

    base_tokens = config.palette_tokens()
    palette = config.palette_for_target("desktop")

    assert palette["primary"] == "#4F46E5"
    assert palette["secondary"] == "#0EA5E9"
    assert palette["background"] == "#EEF2FF"
    assert palette["surface"] == "#FFFFFF"
    assert palette["on_surface"] == base_tokens["colors"]["on_surface"]
    assert palette["success"] == base_tokens["colors"]["success"]
    assert set(base_tokens["colors"]).issubset(palette)


def test_frontend_config_palette_for_mobile_merges_base_tokens() -> None:
    config = FrontEndConfig(
        palette="aurora",
        mode="light",
        platform_palettes={
            "mobile": {
                "primary": "#7C3AED",
                "secondary": "#EC4899",
                "background": "#FAF5FF",
                "surface": "#FFFFFF",
            }
        },
    )

    base_tokens = config.palette_tokens()
    palette = config.palette_for_target("mobile")

    assert palette["primary"] == "#7C3AED"
    assert palette["secondary"] == "#EC4899"
    assert palette["background"] == "#FAF5FF"
    assert palette["surface"] == "#FFFFFF"
    assert palette["focus_ring"] == base_tokens["colors"]["focus_ring"]
    assert palette["warning"] == base_tokens["colors"]["warning"]
    assert set(base_tokens["colors"]).issubset(palette)


def test_frontend_config_resolves_platform_palette_and_screen_tokens() -> None:
    page = DummyPage()
    page.width = 390
    page.height = 844
    config = FrontEndConfig(
        palette="aurora",
        target="mobile",
        platform_palettes={"mobile": {"primary": "#123456", "accent": "#ABCDEF"}},
        screen_tokens={"mobile": {"touch_target": 48}, "portrait": {"safe_area": True}},
    )

    palette = config.palette_for_target()
    tokens = config.screen_tokens_for_page(page)  # type: ignore[arg-type]

    assert palette["primary"] == "#123456"
    assert palette["accent"] == "#ABCDEF"
    assert tokens["device"] == "mobile"
    assert tokens["orientation"] == "portrait"
    assert tokens["columns"] == 4
    assert tokens["touch_target"] == 48
    assert tokens["safe_area"] is True


def test_frontend_config_exposes_structured_implementation_tasks() -> None:
    config = FrontEndConfig(target="web", font_family="Inter")

    tasks = config.implementation_tasks()

    assert [task.name for task in tasks] == ["paleta", "pantalla", "diseño", "fuentes"]
    assert tasks[0].target == "web"
    assert "palette_for_target" in tasks[0].functions
    assert tasks[1].tokens["max_content_width"] == 1280
    assert tasks[3].tokens["font_family"] == "Inter"


def test_frontend_config_resolves_custom_typography_roles_by_device_width() -> None:
    config = FrontEndConfig(
        typography_tokens={
            "badge": {
                "mobile": {"size": 10, "weight": "w500", "line_height": 1.1},
                "tablet": {"size": 12, "weight": "w600", "line_height": 1.2},
                "desktop": {"size": 14, "weight": "w700", "line_height": 1.3},
                "large_desktop": {"size": 16, "weight": "w800", "line_height": 1.4},
            }
        }
    )

    assert config.resolve_typography("badge", 375) == {
        "size": 10,
        "weight": "w500",
        "line_height": 1.1,
    }
    assert config.resolve_typography("badge", 768) == {
        "size": 12,
        "weight": "w600",
        "line_height": 1.2,
    }
    assert config.resolve_typography("badge", 1024) == {
        "size": 14,
        "weight": "w700",
        "line_height": 1.3,
    }
    assert config.resolve_typography("badge", 1440) == {
        "size": 16,
        "weight": "w800",
        "line_height": 1.4,
    }


def test_frontend_config_loads_custom_typography_roles_from_pyproject(
    tmp_path: Path,
) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.fletplus.frontend.typography_tokens.badge.mobile]
size = 10
weight = 'w500'
line_height = 1.1

[tool.fletplus.frontend.typography_tokens.badge.tablet]
size = 12
weight = 'w600'
line_height = 1.2

[tool.fletplus.frontend.typography_tokens.badge.desktop]
size = 14
weight = 'w700'
line_height = 1.3

[tool.fletplus.frontend.typography_tokens.badge.large_desktop]
size = 16
weight = 'w800'
line_height = 1.4
""",
        encoding="utf-8",
    )

    config = FrontEndConfig.from_pyproject(pyproject)
    tokens = config.resolved_typography_tokens()

    assert tokens["badge"]["mobile"]["size"] == 10
    assert config.text_style("badge", 375).size == 10
    assert config.text_style("badge", 768).size == 12
    assert config.text_style("badge", 1024).size == 14
    assert config.text_style("badge", 1440).size == 16
