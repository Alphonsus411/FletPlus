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
    "selva": {
        "description": "Verdes botánicos con acentos lima pensados para paneles ecológicos.",
        "light": {
            "colors": {
                "primary": "#2E7D32",
                "on_primary": "#FFFFFF",
                "background": "#F1F8E9",
                "on_background": "#1B4332",
                "surface": "#FFFFFF",
                "on_surface": "#2F4F4F",
                "surface_variant": "#E5F2D6",
                "on_surface_variant": "#3D6651",
                "outline": "#7BA882",
                "accent": "#A5D936",
                "muted": "#5C7E68",
                "gradient_app_header_start": "#2E7D32",
                "gradient_app_header_end": "#A5D936",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#1B5E20", "#2E7D32", "#A5D936"],
                    "begin": (-0.6, -1.0),
                    "end": (0.6, 1.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#81C784",
                "on_primary": "#0B2611",
                "background": "#0D1F15",
                "on_background": "#CDEACC",
                "surface": "#12281C",
                "on_surface": "#CDEACC",
                "surface_variant": "#1B3A28",
                "on_surface_variant": "#8FB399",
                "outline": "#4E7F5E",
                "accent": "#B2F369",
                "muted": "#7AA882",
                "gradient_app_header_start": "#0D2B18",
                "gradient_app_header_end": "#4CAF50",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#0D2B18", "#1B5E20", "#4CAF50"],
                    "begin": (-0.6, -1.0),
                    "end": (0.6, 1.0),
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
    "botanical": {
        "description": "Verdes orgánicos con acentos tierra para proyectos wellness.",
        "light": {
            "colors": {
                "primary": "#2F855A",
                "on_primary": "#FFFFFF",
                "background": "#F3FAF4",
                "on_background": "#1B4332",
                "surface": "#FFFFFF",
                "on_surface": "#1B4332",
                "surface_variant": "#D8F3DC",
                "on_surface_variant": "#2D6A4F",
                "outline": "#74C69D",
                "accent": "#FFB703",
                "muted": "#52796F",
                "gradient_app_header_start": "#2F855A",
                "gradient_app_header_end": "#74C69D",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#1B4332", "#2F855A", "#74C69D"],
                    "begin": (0.0, -1.0),
                    "end": (0.4, 1.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#95D5B2",
                "on_primary": "#003322",
                "background": "#0B1E16",
                "on_background": "#D8F3DC",
                "surface": "#123524",
                "on_surface": "#D8F3DC",
                "surface_variant": "#1E5234",
                "on_surface_variant": "#B7E4C7",
                "outline": "#52B788",
                "accent": "#F4A259",
                "muted": "#6C8E81",
                "gradient_app_header_start": "#0B1E16",
                "gradient_app_header_end": "#2D6A4F",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#0B1E16", "#1E5234", "#2D6A4F"],
                    "begin": (0.0, -1.0),
                    "end": (0.5, 1.0),
                }
            },
        },
    },
    "cyberwave": {
        "description": "Neones futuristas pensados para dashboards nocturnos.",
        "light": {
            "colors": {
                "primary": "#7C3AED",
                "on_primary": "#FFFFFF",
                "background": "#F5F3FF",
                "on_background": "#1E1B4B",
                "surface": "#FFFFFF",
                "on_surface": "#1E1B4B",
                "surface_variant": "#DDD6FE",
                "on_surface_variant": "#4C1D95",
                "outline": "#A855F7",
                "accent": "#22D3EE",
                "muted": "#6B7280",
                "gradient_app_header_start": "#7C3AED",
                "gradient_app_header_end": "#22D3EE",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#4C1D95", "#7C3AED", "#22D3EE"],
                    "begin": (-0.4, -1.0),
                    "end": (0.6, 1.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#C4B5FD",
                "on_primary": "#1E1B4B",
                "background": "#09021C",
                "on_background": "#E0E7FF",
                "surface": "#120A2A",
                "on_surface": "#E0E7FF",
                "surface_variant": "#1E1B4B",
                "on_surface_variant": "#C4B5FD",
                "outline": "#8B5CF6",
                "accent": "#67E8F9",
                "muted": "#94A3B8",
                "gradient_app_header_start": "#120A2A",
                "gradient_app_header_end": "#3B82F6",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#120A2A", "#4338CA", "#3B82F6"],
                    "begin": (-0.2, -1.0),
                    "end": (0.7, 1.0),
                }
            },
        },
    },
    "zenith": {
        "description": "Azules profundos con dorados suaves para portales corporativos.",
        "light": {
            "colors": {
                "primary": "#1D4E89",
                "on_primary": "#FFFFFF",
                "background": "#F2F6FC",
                "on_background": "#0F172A",
                "surface": "#FFFFFF",
                "on_surface": "#102A43",
                "surface_variant": "#E1E8F5",
                "on_surface_variant": "#1D3A64",
                "outline": "#8091B2",
                "accent": "#F59E0B",
                "muted": "#6B7280",
                "gradient_app_header_start": "#1D4E89",
                "gradient_app_header_end": "#F59E0B",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#102A43", "#1D4E89", "#F59E0B"],
                    "begin": (-0.3, -1.0),
                    "end": (0.8, 1.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#60A5FA",
                "on_primary": "#0B1120",
                "background": "#0A1224",
                "on_background": "#CBD5F5",
                "surface": "#111C33",
                "on_surface": "#CBD5F5",
                "surface_variant": "#1E2F4F",
                "on_surface_variant": "#9CB7E0",
                "outline": "#3B82F6",
                "accent": "#FBBF24",
                "muted": "#8193B2",
                "gradient_app_header_start": "#0B1120",
                "gradient_app_header_end": "#2563EB",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#0B1120", "#1D4E89", "#2563EB"],
                    "begin": (-0.2, -1.0),
                    "end": (0.6, 1.0),
                }
            },
        },
    },
    "terracotta": {
        "description": "Paleta cálida de arcilla con acentos turquesa para sitios editoriales.",
        "light": {
            "colors": {
                "primary": "#BF6C43",
                "on_primary": "#FFFFFF",
                "background": "#FBF3EF",
                "on_background": "#43281C",
                "surface": "#FFFFFF",
                "on_surface": "#4E342E",
                "surface_variant": "#F0D6CB",
                "on_surface_variant": "#6E4B3C",
                "outline": "#C49A7E",
                "accent": "#1BA39C",
                "muted": "#8B6F60",
                "gradient_app_header_start": "#BF6C43",
                "gradient_app_header_end": "#1BA39C",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#8C4A2F", "#BF6C43", "#1BA39C"],
                    "begin": (-0.5, -1.0),
                    "end": (0.5, 1.0),
                }
            },
        },
        "dark": {
            "colors": {
                "primary": "#F2A97D",
                "on_primary": "#3A1C12",
                "background": "#22130E",
                "on_background": "#FFE1D2",
                "surface": "#2F1C14",
                "on_surface": "#FFE1D2",
                "surface_variant": "#4B2C1F",
                "on_surface_variant": "#FFC7AA",
                "outline": "#D28B68",
                "accent": "#30CBC1",
                "muted": "#B08774",
                "gradient_app_header_start": "#22130E",
                "gradient_app_header_end": "#30CBC1",
            },
            "gradients": {
                "app_header": {
                    "colors": ["#22130E", "#BF6C43", "#30CBC1"],
                    "begin": (-0.4, -1.0),
                    "end": (0.7, 1.0),
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
