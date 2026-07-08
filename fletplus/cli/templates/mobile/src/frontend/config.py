"""Valores editables de frontend para {{ project_name }}."""

from __future__ import annotations

from pathlib import Path

PALETTE_NAME = "material"
PALETTE_MODE = "light"
FONT_FAMILY = "Roboto"
FONT_FALLBACK_FAMILIES = ("Arial", "sans-serif")
FONT_ASSETS = {
    # Registra fuentes locales incluidas en assets/fonts/.
    # "Inter": "assets/fonts/Inter-Regular.ttf",
}
FONT_WEIGHTS = ("w400", "w600", "w700")
FONT_STYLES = ("normal",)
CUSTOM_TOKENS = {
    "colors": {
        "brand": "#2563EB",
        "brand_container": "#DBEAFE",
        "surface_soft": "#F8FAFC",
    },
    "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
    "radius": {"card": 18, "pill": 999},
}
PAGE_PADDING = 12
MAX_CONTENT_WIDTH = 480
MIN_CONTENT_WIDTH = 280
SPACING = 12
LAYOUT_DENSITY = "compact"
ASSETS_DIR = Path("assets")
PLACEHOLDER_README = ASSETS_DIR / "README.md"
