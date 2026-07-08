"""Presets de tokens de diseño para distintas guías visuales."""

from __future__ import annotations

from copy import deepcopy
from typing import Iterator

PresetDefinition = dict[str, dict[str, dict[str, object]] | str]

_MATERIAL3: PresetDefinition = {
    "description": "Tokens inspirados en Material Design 3.",
    "light": {
        "colors": {
            "primary": "#6750A4",
            "on_primary": "#FFFFFF",
            "primary_container": "#EADDFF",
            "on_primary_container": "#21005D",
            "secondary": "#625B71",
            "background": "#FFFBFE",
            "surface": "#FFFBFE",
            "surface_variant": "#E7E0EC",
            "outline": "#79747E",
        },
        "typography": {
            "font_family": "Roboto",
            "display_large": {"size": 57, "weight": 400},
            "headline_medium": {"size": 28, "weight": 400},
            "body_medium": {"size": 16, "weight": 400},
        },
        "radii": {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 28},
        "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
        "borders": {"thin": 1, "regular": 2},
        "shadows": {"default": "md", "raised": "lg"},
    },
    "dark": {
        "colors": {
            "primary": "#D0BCFF",
            "on_primary": "#381E72",
            "primary_container": "#4F378B",
            "on_primary_container": "#EADDFF",
            "secondary": "#CCC2DC",
            "background": "#1C1B1F",
            "surface": "#1C1B1F",
            "surface_variant": "#49454F",
            "outline": "#938F99",
        },
        "typography": {
            "font_family": "Roboto",
            "display_large": {"size": 57, "weight": 400},
            "headline_medium": {"size": 28, "weight": 400},
            "body_medium": {"size": 16, "weight": 400},
        },
        "radii": {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 28},
        "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
        "borders": {"thin": 1, "regular": 2},
        "shadows": {"default": "md", "raised": "lg"},
    },
}

_FLUENT: PresetDefinition = {
    "description": "Tokens basados en Fluent Design System.",
    "light": {
        "colors": {
            "primary": "#0078D4",
            "on_primary": "#FFFFFF",
            "secondary": "#107C10",
            "background": "#FFFFFF",
            "surface": "#F3F2F1",
            "outline": "#C8C6C4",
            "accent": "#005A9E",
        },
        "typography": {
            "font_family": "Segoe UI",
            "title_large": {"size": 32, "weight": 600},
            "title_medium": {"size": 24, "weight": 600},
            "body_medium": {"size": 14, "weight": 400},
        },
        "radii": {"xs": 2, "sm": 4, "md": 6, "lg": 8, "xl": 12},
        "spacing": {"xs": 4, "sm": 8, "md": 12, "lg": 20, "xl": 28},
        "borders": {"thin": 1, "regular": 2},
        "shadows": {"default": "level1", "card": "level2"},
    },
    "dark": {
        "colors": {
            "primary": "#58A6FF",
            "on_primary": "#003A6D",
            "secondary": "#6BB700",
            "background": "#201F1E",
            "surface": "#252423",
            "outline": "#3B3A39",
            "accent": "#3B78FF",
        },
        "typography": {
            "font_family": "Segoe UI",
            "title_large": {"size": 32, "weight": 600},
            "title_medium": {"size": 24, "weight": 600},
            "body_medium": {"size": 14, "weight": 400},
        },
        "radii": {"xs": 2, "sm": 4, "md": 6, "lg": 8, "xl": 12},
        "spacing": {"xs": 4, "sm": 8, "md": 12, "lg": 20, "xl": 28},
        "borders": {"thin": 1, "regular": 2},
        "shadows": {"default": "level1", "card": "level2"},
    },
}

_CUPERTINO: PresetDefinition = {
    "description": "Tokens inspirados en el estilo Cupertino.",
    "light": {
        "colors": {
            "primary": "#0A84FF",
            "on_primary": "#FFFFFF",
            "secondary": "#5E5CE6",
            "background": "#FFFFFF",
            "surface": "#F2F2F7",
            "outline": "#D1D1D6",
            "accent": "#FF9500",
        },
        "typography": {
            "font_family": "SF Pro Text",
            "title_large": {"size": 34, "weight": 600},
            "title_medium": {"size": 28, "weight": 600},
            "body_medium": {"size": 17, "weight": 400},
        },
        "radii": {"xs": 8, "sm": 12, "md": 16, "lg": 24, "xl": 32},
        "spacing": {"xs": 4, "sm": 10, "md": 16, "lg": 24, "xl": 32},
        "borders": {"thin": 1, "regular": 2},
        "shadows": {"default": "soft", "card": "medium"},
    },
    "dark": {
        "colors": {
            "primary": "#409CFF",
            "on_primary": "#003A75",
            "secondary": "#8E8CF1",
            "background": "#1C1C1E",
            "surface": "#2C2C2E",
            "outline": "#3A3A3C",
            "accent": "#FF9F0A",
        },
        "typography": {
            "font_family": "SF Pro Text",
            "title_large": {"size": 34, "weight": 600},
            "title_medium": {"size": 28, "weight": 600},
            "body_medium": {"size": 17, "weight": 400},
        },
        "radii": {"xs": 8, "sm": 12, "md": 16, "lg": 24, "xl": 32},
        "spacing": {"xs": 4, "sm": 10, "md": 16, "lg": 24, "xl": 32},
        "borders": {"thin": 1, "regular": 2},
        "shadows": {"default": "soft", "card": "medium"},
    },
}


def _product_preset(
    description: str,
    palette: str,
    spacing: dict[str, int],
    radii: dict[str, int],
    shadows: dict[str, str],
    typography: dict[str, object],
    density: str,
) -> PresetDefinition:
    tokens = {
        "colors": {"palette_base": palette},
        "spacing": spacing,
        "radii": radii,
        "shadows": shadows,
        "typography": typography,
        "meta": {"palette": palette, "density": density},
    }
    return {
        "description": description,
        "palette": palette,
        "density": density,
        "light": deepcopy(tokens),
        "dark": deepcopy(tokens),
    }


_DASHBOARD = _product_preset(
    "Preset analítico para KPIs, tarjetas densas y vistas de datos.",
    "fjord",
    {"xs": 4, "sm": 8, "md": 12, "lg": 20, "xl": 28, "page": 28, "section": 20},
    {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "card": 16},
    {"default": "sm", "card": "md", "overlay": "lg"},
    {"font_family": "Inter", "heading_weight": 700, "body_size": 14},
    "compact",
)

_LANDING = _product_preset(
    "Preset expresivo para páginas de marketing, hero sections y conversiones.",
    "solstice",
    {"xs": 6, "sm": 12, "md": 20, "lg": 32, "xl": 48, "page": 40, "section": 64},
    {"xs": 8, "sm": 14, "md": 22, "lg": 32, "xl": 40, "card": 28},
    {"default": "soft", "card": "xl", "hero": "glow"},
    {"font_family": "Inter", "heading_weight": 800, "body_size": 16},
    "spacious",
)

_ADMIN = _product_preset(
    "Preset sobrio para backoffices, CRUDs, tablas y navegación lateral.",
    "metropolis",
    {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "page": 24, "section": 16},
    {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16, "card": 12},
    {"default": "xs", "card": "sm", "drawer": "md"},
    {"font_family": "Inter", "heading_weight": 650, "body_size": 14},
    "compact",
)

_MOBILE_APP = _product_preset(
    "Preset táctil para aplicaciones móviles con controles amplios y lectura rápida.",
    "aurora",
    {"xs": 4, "sm": 10, "md": 16, "lg": 24, "xl": 32, "page": 16, "section": 20},
    {"xs": 10, "sm": 14, "md": 20, "lg": 28, "xl": 36, "card": 24},
    {"default": "soft", "card": "medium", "bottom_sheet": "xl"},
    {"font_family": "Roboto", "heading_weight": 700, "body_size": 16},
    "comfortable",
)

_SAAS = _product_preset(
    "Preset equilibrado para productos SaaS, onboarding y áreas de cuenta.",
    "zenith",
    {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 36, "page": 32, "section": 32},
    {"xs": 6, "sm": 10, "md": 16, "lg": 22, "xl": 30, "card": 20},
    {"default": "sm", "card": "lg", "modal": "xl"},
    {"font_family": "Inter", "heading_weight": 750, "body_size": 15},
    "comfortable",
)

_ECOMMERCE = _product_preset(
    "Preset comercial para catálogos, fichas de producto y flujos de checkout.",
    "citrus",
    {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 40, "page": 24, "section": 36},
    {"xs": 4, "sm": 8, "md": 14, "lg": 20, "xl": 28, "card": 18},
    {"default": "sm", "product_card": "md", "checkout": "lg"},
    {"font_family": "Inter", "heading_weight": 700, "body_size": 15},
    "comfortable",
)

_PRESETS: dict[str, PresetDefinition] = {
    "material3": _MATERIAL3,
    "fluent": _FLUENT,
    "cupertino": _CUPERTINO,
    "dashboard": _DASHBOARD,
    "landing": _LANDING,
    "admin": _ADMIN,
    "mobile_app": _MOBILE_APP,
    "saas": _SAAS,
    "ecommerce": _ECOMMERCE,
}


def list_presets() -> Iterator[tuple[str, str]]:
    """Devuelve un iterador con ``(nombre, descripción)`` de los presets."""

    for name, definition in _PRESETS.items():
        description = definition.get("description", "")
        yield name, description


def has_preset(name: str) -> bool:
    """Indica si ``name`` corresponde a un preset registrado."""

    return name.lower() in _PRESETS


def get_preset_metadata(name: str) -> dict[str, object]:
    """Obtiene metadatos de un preset como paleta base y densidad."""

    normalized = name.lower()
    if normalized not in _PRESETS:
        raise ValueError(f"Preset '{name}' is not registered")
    definition = _PRESETS[normalized]
    return {
        key: deepcopy(value)
        for key, value in definition.items()
        if key not in {"description", "light", "dark"}
    }


def get_preset_definition(name: str) -> dict[str, dict[str, dict[str, object]]]:
    """Obtiene una copia profunda de la definición del preset solicitado."""

    normalized = name.lower()
    if normalized not in _PRESETS:
        raise ValueError(f"Preset '{name}' is not registered")
    definition = _PRESETS[normalized]
    result: dict[str, dict[str, dict[str, object]]] = {}
    for key, value in definition.items():
        if key == "description":
            continue
        if isinstance(value, dict):
            result[key] = deepcopy(value)
    return result


__all__ = [
    "list_presets",
    "has_preset",
    "get_preset_metadata",
    "get_preset_definition",
]
