"""Helpers de layout responsivo para {{ project_name }}."""

from __future__ import annotations

import flet as ft

from fletplus import FrontEndConfig
from fletplus.utils.viewport import viewport_info


def active_profile(page: ft.Page, frontend: FrontEndConfig):
    """Obtiene el perfil responsivo activo a partir del ancho actual."""
    return viewport_info(
        page,
        profiles=frontend.responsive_profiles,
        fallback_width=frontend.max_content_width,
        padding_base=frontend.page_padding,
    ).profile


def orientation(page: ft.Page, frontend: FrontEndConfig | None = None) -> str:
    """Devuelve `portrait` o `landscape` según las dimensiones de la página."""
    profiles = frontend.responsive_profiles if frontend is not None else None
    return viewport_info(page, profiles=profiles).orientation


def density(page: ft.Page, frontend: FrontEndConfig) -> str:
    """Devuelve la densidad visual sugerida para el viewport actual."""
    return viewport_info(page, profiles=frontend.responsive_profiles).density


def safe_padding(page: ft.Page, frontend: FrontEndConfig) -> ft.Padding:
    """Calcula padding seguro para móviles y ventanas compactas."""
    return viewport_info(
        page, profiles=frontend.responsive_profiles, padding_base=frontend.page_padding
    ).padding


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
    info = viewport_info(
        page,
        profiles=frontend.responsive_profiles,
        fallback_width=frontend.max_content_width,
        padding_base=frontend.page_padding,
    )
    header = ft.Text(
        f"Perfil: {info.profile.name} · {info.profile.columns} columnas · "
        f"{info.orientation} · densidad {info.density} · {info.width}×{info.height}",
        size=12,
    )
    return max_width_container(
        ft.Column(controls=[header, content], spacing=spacing(frontend)), page, frontend
    )
