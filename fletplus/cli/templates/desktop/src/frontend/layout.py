"""Helpers de layout responsivo para {{ project_name }}."""

from __future__ import annotations

import flet as ft

from fletplus import FrontEndConfig
from fletplus.utils.viewport import (
    active_device_profile,
    safe_mobile_padding,
    safe_page_height,
    safe_page_width,
    viewport_orientation,
    visual_density_for_page,
)


def active_profile(page: ft.Page, frontend: FrontEndConfig):
    """Obtiene el perfil responsivo activo a partir del ancho actual."""
    return active_device_profile(
        page, frontend.responsive_profiles, fallback_width=frontend.max_content_width
    )


def orientation(page: ft.Page) -> str:
    """Devuelve `portrait` o `landscape` según las dimensiones de la página."""
    return viewport_orientation(page)


def density(page: ft.Page, frontend: FrontEndConfig) -> str:
    """Devuelve la densidad visual sugerida para el viewport actual."""
    return visual_density_for_page(page, profiles=frontend.responsive_profiles)


def safe_padding(page: ft.Page, frontend: FrontEndConfig) -> ft.Padding:
    """Calcula padding seguro para móviles y ventanas compactas."""
    return safe_mobile_padding(
        page, base=frontend.page_padding, profiles=frontend.responsive_profiles
    )


def spacing(frontend: FrontEndConfig, multiplier: float = 1.0) -> int:
    """Calcula spacing consistente para filas, columnas y tarjetas."""
    return max(0, round(frontend.spacing * multiplier))


def max_width_container(
    content: ft.Control, page: ft.Page, frontend: FrontEndConfig
) -> ft.Container:
    """Centra contenido y limita el ancho máximo usando FrontEndConfig."""
    container = frontend.build_content_shell(content, page)
    container.padding = safe_padding(page, frontend)
    return container


def responsive_shell(
    content: ft.Control, page: ft.Page, frontend: FrontEndConfig
) -> ft.Container:
    """Envuelve contenido con metadata útil para depurar breakpoints."""
    profile = active_profile(page, frontend)
    width = safe_page_width(page, fallback=frontend.max_content_width)
    height = safe_page_height(page)
    header = ft.Text(
        f"Perfil: {profile.name} · {profile.columns} columnas · "
        f"{orientation(page)} · densidad {density(page, frontend)} · {width}×{height}",
        size=12,
    )
    return max_width_container(
        ft.Column(controls=[header, content], spacing=spacing(frontend)), page, frontend
    )
