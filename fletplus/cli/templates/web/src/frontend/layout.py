"""Helpers de layout responsivo para {{ project_name }}."""

from __future__ import annotations

import flet as ft

from fletplus import FrontEndConfig


def active_profile(page: ft.Page, frontend: FrontEndConfig):
    """Obtiene el perfil responsivo activo a partir del ancho actual."""
    return frontend.resolve_device_profile(
        int(page.width or frontend.max_content_width)
    )


def orientation(page: ft.Page) -> str:
    """Devuelve `portrait` o `landscape` según las dimensiones de la página."""
    width = int(page.width or 0)
    height = int(page.height or 0)
    return "portrait" if height >= width else "landscape"


def spacing(frontend: FrontEndConfig, multiplier: float = 1.0) -> int:
    """Calcula spacing consistente para filas, columnas y tarjetas."""
    return max(0, round(frontend.spacing * multiplier))


def max_width_container(
    content: ft.Control, page: ft.Page, frontend: FrontEndConfig
) -> ft.Container:
    """Centra contenido y limita el ancho máximo usando FrontEndConfig."""
    return frontend.build_content_shell(content, page)


def responsive_shell(
    content: ft.Control, page: ft.Page, frontend: FrontEndConfig
) -> ft.Container:
    """Envuelve contenido con metadata útil para depurar breakpoints."""
    profile = active_profile(page, frontend)
    header = ft.Text(
        f"Perfil: {profile.name} · {profile.columns} columnas · {orientation(page)}",
        size=12,
    )
    return max_width_container(
        ft.Column(controls=[header, content], spacing=spacing(frontend)), page, frontend
    )
