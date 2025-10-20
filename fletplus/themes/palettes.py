"""Paletas de color predefinidas para temas de FletPlus."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

PaletteTokens = Dict[str, Dict[str, object]]
PaletteDefinition = Dict[str, PaletteTokens]


_PRESET_PALETTES: Dict[str, Dict[str, object]] = {
    "aurora": {
        "description": "Gama fría inspirada en auroras boreales con acentos violetas.",
        "light": {
            "colors": {
                "primary": "#6750A4",
                "on_primary": "#FFFFFF",
                "background": "#F4F0FF",
                "on_background": "#1D1B20",
                "surface": "#FFFFFF",
                "on_surface": "#1D1B20",
                "surface_variant": "#E7E0EC",
                "on_surface_variant": "#4A4458",
                "outline": "#7A7289",
                "accent": "#B583F5",
                "muted": "#605866",
                "gradient_app_header_start": "#6750A4",
                "gradient_app_header_end": "#B583F5",
            },
            "radii": {"card": 20, "chip": 100},
            "spacing": {"page": 20, "section": 16},
            "gradients": {
                "app_header": {
                    "colors": ["#6750A4", "#7C66C7", "#B583F5"],
                    "begin": (0.0, -1.0),
                    "end": (0.0, 1.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#D0BCFF",
                "on_primary": "#381E72",
                "background": "#141218",
                "on_background": "#E7E0EC",
                "surface": "#1D1B20",
                "on_surface": "#E7E0EC",
                "surface_variant": "#49454F",
                "on_surface_variant": "#CAC4D0",
                "outline": "#938F99",
                "accent": "#9A82DB",
                "muted": "#A09AB2",
                "gradient_app_header_start": "#3D2B5B",
                "gradient_app_header_end": "#7F67BE",
            },
            "radii": {"card": 20, "chip": 100},
            "spacing": {"page": 18, "section": 14},
            "gradients": {
                "app_header": {
                    "colors": ["#3D2B5B", "#5B3F8C", "#7F67BE"],
                    "begin": (0.0, -1.0),
                    "end": (0.0, 1.0),
                }
            },
        },
    },
    "sunset": {
        "description": "Tonos cálidos inspirados en un atardecer urbano.",
        "light": {
            "colors": {
                "primary": "#FF7043",
                "on_primary": "#FFFFFF",
                "background": "#FFF3E0",
                "on_background": "#3E2723",
                "surface": "#FFFFFF",
                "on_surface": "#4E342E",
                "surface_variant": "#FFE0B2",
                "on_surface_variant": "#6D4C41",
                "outline": "#8D6E63",
                "accent": "#FFB74D",
                "muted": "#A1887F",
                "gradient_app_header_start": "#FF7043",
                "gradient_app_header_end": "#FFB74D",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#FF7043", "#FF8A65", "#FFB74D"],
                    "begin": (-1.0, 0.0),
                    "end": (1.0, 0.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#FFB59D",
                "on_primary": "#5D1905",
                "background": "#311207",
                "on_background": "#FFD7BA",
                "surface": "#3E1B0D",
                "on_surface": "#FFD7BA",
                "surface_variant": "#5B2B19",
                "on_surface_variant": "#FFBC9C",
                "outline": "#C37C61",
                "accent": "#FF9248",
                "muted": "#F8B69F",
                "gradient_app_header_start": "#5D1905",
                "gradient_app_header_end": "#FF8A65",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#5D1905", "#992E15", "#FF8A65"],
                    "begin": (-1.0, 0.0),
                    "end": (1.0, 0.0),
                }
            },
        },
    },
    "lagoon": {
        "description": "Paleta fresca con verdes y azules pensada para dashboards.",
        "light": {
            "colors": {
                "primary": "#00838F",
                "on_primary": "#FFFFFF",
                "background": "#E0F7FA",
                "on_background": "#004D40",
                "surface": "#FFFFFF",
                "on_surface": "#1A535C",
                "surface_variant": "#B2EBF2",
                "on_surface_variant": "#006064",
                "outline": "#4DD0E1",
                "accent": "#00BFA5",
                "muted": "#5DA3A7",
                "gradient_app_header_start": "#00838F",
                "gradient_app_header_end": "#00BFA5",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#006064", "#00838F", "#00BFA5"],
                    "begin": (0.0, -1.0),
                    "end": (1.0, 1.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#4DD0E1",
                "on_primary": "#00363A",
                "background": "#002024",
                "on_background": "#A6F2F5",
                "surface": "#00363A",
                "on_surface": "#A6F2F5",
                "surface_variant": "#004F55",
                "on_surface_variant": "#80CBC4",
                "outline": "#26A69A",
                "accent": "#1DE9B6",
                "muted": "#7BC9CC",
                "gradient_app_header_start": "#00363A",
                "gradient_app_header_end": "#26A69A",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#00363A", "#006064", "#26A69A"],
                    "begin": (0.0, -1.0),
                    "end": (1.0, 1.0),
                }
            },
        },
    },
    "midnight": {
        "description": "Contraste elegante con acentos cian para apps nocturnas.",
        "light": {
            "colors": {
                "primary": "#1E3A8A",
                "on_primary": "#FFFFFF",
                "background": "#F8FAFC",
                "on_background": "#0F172A",
                "surface": "#FFFFFF",
                "on_surface": "#111827",
                "surface_variant": "#E2E8F0",
                "on_surface_variant": "#1E293B",
                "outline": "#475569",
                "accent": "#06B6D4",
                "muted": "#64748B",
                "gradient_app_header_start": "#1E3A8A",
                "gradient_app_header_end": "#0F172A",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#1E3A8A", "#1D4ED8", "#0F172A"],
                    "begin": (-0.5, -1.0),
                    "end": (0.5, 1.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#93C5FD",
                "on_primary": "#0B1120",
                "background": "#020617",
                "on_background": "#E2E8F0",
                "surface": "#0F172A",
                "on_surface": "#E2E8F0",
                "surface_variant": "#1E293B",
                "on_surface_variant": "#CBD5F5",
                "outline": "#2563EB",
                "accent": "#38BDF8",
                "muted": "#64748B",
                "gradient_app_header_start": "#0B1120",
                "gradient_app_header_end": "#1D4ED8",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#0B1120", "#1E3A8A", "#1D4ED8"],
                    "begin": (-0.3, -1.0),
                    "end": (0.6, 1.0),
                }
            },
        },
    },
    "sakura": {
        "description": "Tonos pastel inspirados en cerezos para apps creativas.",
        "light": {
            "colors": {
                "primary": "#E91E63",
                "on_primary": "#FFFFFF",
                "background": "#FFF5F7",
                "on_background": "#4A001F",
                "surface": "#FFFFFF",
                "on_surface": "#4A001F",
                "surface_variant": "#FFD1DC",
                "on_surface_variant": "#7F1D40",
                "outline": "#F48FB1",
                "accent": "#F06292",
                "muted": "#B56576",
                "gradient_app_header_start": "#F48FB1",
                "gradient_app_header_end": "#FBCFE8",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#F48FB1", "#F06292", "#FBCFE8"],
                    "begin": (0.0, -1.0),
                    "end": (1.0, 1.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#FBCFE8",
                "on_primary": "#460018",
                "background": "#2D0A1A",
                "on_background": "#FFD7E8",
                "surface": "#3A0F23",
                "on_surface": "#FFD7E8",
                "surface_variant": "#571533",
                "on_surface_variant": "#FF9EC4",
                "outline": "#F48FB1",
                "accent": "#FF6F9F",
                "muted": "#C77A96",
                "gradient_app_header_start": "#460018",
                "gradient_app_header_end": "#F06292",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#460018", "#7F1D40", "#F06292"],
                    "begin": (0.0, -1.0),
                    "end": (1.0, 1.0),
                }
            },
        },
    },
}


def list_palettes() -> Iterable[Tuple[str, str]]:
    """Devuelve un iterable con pares ``(nombre, descripción)``."""

    return tuple((name, data.get("description", "")) for name, data in _PRESET_PALETTES.items())


def get_palette_definition(name: str) -> Dict[str, object] | None:
    """Obtiene la definición completa de una paleta."""

    return _PRESET_PALETTES.get(name)


def get_palette_tokens(name: str, mode: str = "light") -> PaletteTokens:
    """Obtiene los *tokens* de una paleta en el modo indicado."""

    definition = get_palette_definition(name)
    if not definition:
        raise KeyError(name)

    if mode not in definition:
        raise KeyError(mode)

    tokens: PaletteTokens = {}
    for group, values in definition[mode].items():
        if isinstance(values, dict):
            tokens[group] = dict(values)
    return tokens


def has_palette(name: str) -> bool:
    """Indica si existe una paleta con el nombre indicado."""

    return name in _PRESET_PALETTES
