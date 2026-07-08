"""Valores editables de frontend para {{ project_name }}."""

from __future__ import annotations

import ast
from pathlib import Path

PALETTE_NAME = "{{ palette_name }}"
PALETTE_MODE = "light"
FONT_FAMILY = "{{ font_family }}"
FONT_FALLBACK_FAMILIES = ("Arial", "sans-serif")
FONT_ASSETS = {
    # Registra fuentes locales incluidas en assets/fonts/.
    # "Inter": "assets/fonts/Inter-Regular.ttf",
}
FONT_WEIGHTS = ("w400", "w600", "w700")
FONT_STYLES = ("normal",)
TYPOGRAPHY_TOKENS = {
    "display": {
        "mobile": {"size": 40, "weight": "w700", "line_height": 1.1},
        "tablet": {"size": 48, "weight": "w700", "line_height": 1.08},
        "desktop": {"size": 56, "weight": "w700", "line_height": 1.05},
        "large_desktop": {"size": 64, "weight": "w700", "line_height": 1.03},
    },
    "headline": {
        "mobile": {"size": 28, "weight": "w600", "line_height": 1.18},
        "desktop": {"size": 36, "weight": "w600", "line_height": 1.14},
    },
    "title": {"mobile": {"size": 20, "weight": "w600", "line_height": 1.28}},
    "body": {"mobile": {"size": 14, "weight": "w400", "line_height": 1.55}},
    "label": {"mobile": {"size": 12, "weight": "w600", "line_height": 1.35}},
    "caption": {"mobile": {"size": 11, "weight": "w400", "line_height": 1.35}},
}

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
MAX_CONTENT_WIDTH = 1180
MIN_CONTENT_WIDTH = 320
SPACING = int("0{{ spacing }}".replace("0{{ spacing }}", "16"))
LAYOUT_DENSITY = "{{ layout_density }}"
ASSETS_DIR = Path("assets")
PLACEHOLDER_README = ASSETS_DIR / "README.md"
