"""Valores editables de frontend para {{ project_name }}."""

from __future__ import annotations

import ast
from pathlib import Path

PALETTE_NAME = "{{ palette_name }}"
PALETTE_MODE = "{{ theme_mode }}"
FONT_FAMILY = "{{ font_family }}"
_FONT_FALLBACK_SOURCE = """{{ font_fallback_families }}"""
FONT_FALLBACK_FAMILIES = (
    ("Arial", "sans-serif")
    if _FONT_FALLBACK_SOURCE.strip().startswith("{{")
    else ast.literal_eval(_FONT_FALLBACK_SOURCE)
)
FONT_ASSETS = {
    # Registra fuentes locales incluidas en assets/fonts/.
    # "Inter": "assets/fonts/Inter-Regular.ttf",
}
FONT_WEIGHTS = ("w400", "w600", "w700")
FONT_STYLES = ("normal",)
DEFAULT_CUSTOM_TOKENS = {
    "colors": {"brand": "#2563EB", "surface_soft": "#F8FAFC"},
    "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
    "radii": {"card": 18, "pill": 999},
}
_CUSTOM_TOKENS_SOURCE = """{{ custom_tokens_repr }}"""
CUSTOM_TOKENS = (
    DEFAULT_CUSTOM_TOKENS
    if _CUSTOM_TOKENS_SOURCE.strip().startswith("{{")
    else ast.literal_eval(_CUSTOM_TOKENS_SOURCE)
)
PAGE_PADDING = int("0{{ page_padding }}".replace("0{{ page_padding }}", "24"))
MAX_CONTENT_WIDTH = int(
    "0{{ max_content_width }}".replace("0{{ max_content_width }}", "1200")
)
MIN_CONTENT_WIDTH = 280
SPACING = int("0{{ spacing }}".replace("0{{ spacing }}", "16"))
LAYOUT_DENSITY = "{{ layout_density }}"
TARGET_NAME = "{{ target_name }}"
PRESET_NAME = "{{ preset_name }}"
ASSETS_DIR = Path("assets")
PLACEHOLDER_README = ASSETS_DIR / "README.md"
