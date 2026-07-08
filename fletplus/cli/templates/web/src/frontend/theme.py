"""Tema inicial para {{ project_name }}."""

from __future__ import annotations

from pathlib import Path

from fletplus import FontDeclaration, FrontEndConfig

from .config import (
    CUSTOM_TOKENS,
    FONT_ASSETS,
    FONT_FALLBACK_FAMILIES,
    FONT_FAMILY,
    FONT_STYLES,
    FONT_WEIGHTS,
    LAYOUT_DENSITY,
    MAX_CONTENT_WIDTH,
    MIN_CONTENT_WIDTH,
    PAGE_PADDING,
    PALETTE_MODE,
    PALETTE_NAME,
    SPACING,
    TYPOGRAPHY_TOKENS,
)


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
            font=FontDeclaration(
                family=FONT_FAMILY,
                fallback_families=FONT_FALLBACK_FAMILIES,
                assets=FONT_ASSETS,
                weights=FONT_WEIGHTS,
                styles=FONT_STYLES,
            ),
            page_padding=PAGE_PADDING,
            max_content_width=MAX_CONTENT_WIDTH,
            min_content_width=MIN_CONTENT_WIDTH,
            spacing=SPACING,
            layout_density=LAYOUT_DENSITY,
            typography_tokens=TYPOGRAPHY_TOKENS,
        )
    config.font_assets = {**FONT_ASSETS, **dict(config.font_assets)}
    config.font = FontDeclaration(
        family=config.font.family or config.font_family or FONT_FAMILY,
        fallback_families=config.font.fallback_families or FONT_FALLBACK_FAMILIES,
        assets={**FONT_ASSETS, **dict(config.font.assets)},
        weights=config.font.weights or FONT_WEIGHTS,
        styles=config.font.styles or FONT_STYLES,
    )
    config.theme_tokens = {**CUSTOM_TOKENS, **dict(config.theme_tokens)}
    config.typography_tokens = {**TYPOGRAPHY_TOKENS, **dict(config.typography_tokens)}
    return config


def _find_pyproject() -> Path:
    """Localiza ``pyproject.toml`` tanto desde ``fletplus run`` como desde ``python src/main.py``."""
    for candidate in (Path("pyproject.toml"), Path("..") / "pyproject.toml"):
        if candidate.exists():
            return candidate
    return Path("pyproject.toml")
