"""Tema inicial para {{ project_name }}."""

from __future__ import annotations

from fletplus import FrontEndConfig

PALETTE_NAME = "material"
PALETTE_MODE = "light"
FONT_FAMILY = "Roboto"
FONT_ASSETS = {
    # "Inter": "assets/fonts/Inter-Regular.ttf",
}
CUSTOM_TOKENS = {
    "colors": {
        "brand": "#2563EB",
        "brand_container": "#DBEAFE",
        "surface_soft": "#F8FAFC",
    },
    "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
    "radius": {"card": 18, "pill": 999},
}


def create_frontend_config() -> FrontEndConfig:
    """Devuelve la configuración visual base editable del proyecto."""
    return FrontEndConfig(
        palette=PALETTE_NAME,
        mode=PALETTE_MODE,
        font_family=FONT_FAMILY,
        font_assets=FONT_ASSETS,
        page_padding=24,
        max_content_width=1100,
        min_content_width=320,
        spacing=16,
        layout_density='comfortable',
        theme_tokens=CUSTOM_TOKENS,
    )
