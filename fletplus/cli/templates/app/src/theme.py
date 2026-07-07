"""Tema inicial para {{ project_name }}."""

from __future__ import annotations

from pathlib import Path

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
    """Devuelve la configuración visual base editable del proyecto.

    Primero carga ``[tool.fletplus.frontend]`` desde ``pyproject.toml`` y
    después aplica los valores editables de esta plantilla como fallback. Así
    las opciones declaradas por la CLI no quedan desconectadas del runtime.
    """
    pyproject_path = _find_pyproject()
    if pyproject_path.exists():
        config = FrontEndConfig.from_pyproject(pyproject_path)
    else:
        config = FrontEndConfig(
            palette=PALETTE_NAME,
            mode=PALETTE_MODE,
            font_family=FONT_FAMILY,
            font_assets=FONT_ASSETS,
            page_padding=24,
            max_content_width=1100,
            min_content_width=320,
            spacing=16,
            layout_density='comfortable',
        )
    config.font_assets = {**FONT_ASSETS, **dict(config.font_assets)}
    config.theme_tokens = {**CUSTOM_TOKENS, **dict(config.theme_tokens)}
    return config


def _find_pyproject() -> Path:
    """Localiza ``pyproject.toml`` tanto desde ``fletplus run`` como desde ``python src/main.py``."""
    for candidate in (Path("pyproject.toml"), Path("..") / "pyproject.toml"):
        if candidate.exists():
            return candidate
    return Path("pyproject.toml")
