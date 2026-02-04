"""Interfaz pública del subpaquete :mod:`fletplus.themes`."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

LAZY_IMPORTS = {
    "ThemeManager": "fletplus.themes.theme_manager",
    "load_palette_from_file": "fletplus.themes.theme_manager",
    "load_theme_from_json": "fletplus.themes.theme_manager",
    "AdaptiveThemeController": "fletplus.themes.adaptive_theme",
    "list_palettes": "fletplus.themes.palettes",
    "get_palette_tokens": "fletplus.themes.palettes",
    "has_palette": "fletplus.themes.palettes",
    "get_palette_definition": "fletplus.themes.palettes",
    "list_presets": "fletplus.themes.presets",
    "has_preset": "fletplus.themes.presets",
    "get_preset_definition": "fletplus.themes.presets",
}

if TYPE_CHECKING:
    from fletplus.themes.adaptive_theme import AdaptiveThemeController
    from fletplus.themes.palettes import (
        get_palette_definition,
        get_palette_tokens,
        has_palette,
        list_palettes,
    )
    from fletplus.themes.presets import (
        get_preset_definition,
        has_preset,
        list_presets,
    )
    from fletplus.themes.theme_manager import (
        ThemeManager,
        load_palette_from_file,
        load_theme_from_json,
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


def __getattr__(name: str) -> Any:
    if name in LAZY_IMPORTS:
        module = importlib.import_module(LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(set(__all__))
