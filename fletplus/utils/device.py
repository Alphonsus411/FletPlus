"""Utilidades para detectar el tipo de dispositivo basado en ``page.platform``."""

from __future__ import annotations

import flet as ft


# -----------------------------------------------------------------------------
def is_mobile(page: ft.Page) -> bool:
    """Retorna ``True`` si la plataforma corresponde a un dispositivo móvil."""

    return page.platform in ("android", "ios")


# -----------------------------------------------------------------------------
def is_web(page: ft.Page) -> bool:
    """Retorna ``True`` si la plataforma es web."""

    return page.platform == "web"


# -----------------------------------------------------------------------------
def is_desktop(page: ft.Page) -> bool:
    """Retorna ``True`` si la plataforma es de escritorio."""

    return page.platform in ("windows", "macos", "linux")
