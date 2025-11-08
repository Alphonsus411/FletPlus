"""Interfaz pública del subpaquete :mod:`fletplus.themes`."""

from fletplus.themes.theme_manager import (
    ThemeManager,
    load_palette_from_file,
    load_theme_from_json,
)
from fletplus.themes.adaptive_theme import AdaptiveThemeController
from fletplus.themes.palettes import (
    list_palettes,
    get_palette_tokens,
    has_palette,
    get_palette_definition,
)
from fletplus.themes.presets import (
    list_presets,
    has_preset,
    get_preset_definition,
)

__all__ = [
    "ThemeManager",
    "AdaptiveThemeController",
    "load_palette_from_file",
    "load_theme_from_json",
    "list_palettes",
    "get_palette_tokens",
    "has_palette",
    "get_palette_definition",
    "list_presets",
    "has_preset",
    "get_preset_definition",
]
