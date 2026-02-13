"""Utilidades para detectar el tipo de dispositivo basado en ``page.platform``.

Las funciones de este módulo son tolerantes con tipos no string:

- Si el valor expone ``.value`` (por ejemplo, enums), se usa ese valor.
- Luego se normaliza con ``str(...).lower()`` para soportar variaciones de mayúsculas.
"""

from __future__ import annotations

import flet as ft


# -----------------------------------------------------------------------------
def _platform_name(platform: object) -> str:
    """Normaliza el nombre de plataforma a un string estable en minúsculas."""

    value = getattr(platform, "value", platform)
    return str(value).lower()


# -----------------------------------------------------------------------------
def is_mobile(page: ft.Page) -> bool:
    """Retorna ``True`` si la plataforma corresponde a un dispositivo móvil."""

    platform = _platform_name(page.platform)
    return platform in ("android", "ios")


# -----------------------------------------------------------------------------
def is_web(page: ft.Page) -> bool:
    """Retorna ``True`` si la plataforma es web."""

    return _platform_name(page.platform) == "web"


# -----------------------------------------------------------------------------
def is_desktop(page: ft.Page) -> bool:
    """Retorna ``True`` si la plataforma es de escritorio."""

    platform = _platform_name(page.platform)
    return platform in ("windows", "macos", "linux")
