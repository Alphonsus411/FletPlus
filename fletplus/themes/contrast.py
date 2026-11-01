"""Cálculos WCAG 2.1 para auditar el contraste de las paletas.

Expone utilidades puras de luminancia relativa y relación de contraste. Se
consumen desde la suite de tests para *reportar* (sin bloquear CI) los pares
de tokens que no alcanzan los umbrales AA. Este módulo no modifica ninguna
paleta ni altera el runtime de la aplicación.
"""

from __future__ import annotations

import re

_HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")

# Umbrales WCAG 2.1 AA.
WCAG_AA_TEXT = 4.5
WCAG_AA_LARGE_TEXT = 3.0
WCAG_AA_UI = 3.0


def parse_hex_color(color: str) -> tuple[int, int, int]:
    """Convierte ``#RRGGBB`` o ``#RRGGBBAA`` en una tupla de canales ``(r, g, b)``.

    El canal alfa, cuando existe, se ignora: WCAG evalúa el color opaco de
    referencia, no la composición sobre el fondo.
    """

    normalized = color.strip()
    if not _HEX_COLOR_PATTERN.match(normalized):
        raise ValueError(f"Color hexadecimal no soportado: {color!r}")
    digits = normalized[1:7]
    return (
        int(digits[0:2], 16),
        int(digits[2:4], 16),
        int(digits[4:6], 16),
    )


def _channel_luminance(channel: int) -> float:
    srgb = channel / 255
    if srgb <= 0.03928:
        return srgb / 12.92
    return ((srgb + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    """Luminancia relativa WCAG (``0.0`` negro puro, ``1.0`` blanco puro)."""

    red, green, blue = (
        _channel_luminance(value) for value in parse_hex_color(color)
    )
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(color_a: str, color_b: str) -> float:
    """Relación de contraste WCAG entre dos colores (rango ``1.0`` a ``21.0``)."""

    luminance_a = relative_luminance(color_a)
    luminance_b = relative_luminance(color_b)
    lighter = max(luminance_a, luminance_b)
    darker = min(luminance_a, luminance_b)
    return (lighter + 0.05) / (darker + 0.05)
