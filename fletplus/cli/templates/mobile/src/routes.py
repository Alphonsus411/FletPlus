"""Rutas mínimas para {{ project_name }}."""

from __future__ import annotations

import flet as ft

from fletplus.router import Route, Router


def home_view(match) -> ft.Control:
    """Vista inicial usada por el router de ejemplo."""
    return ft.Column(
        controls=[
            ft.Text("{{ project_name }}", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Text(f"Ruta activa: {match.path}"),
        ],
        spacing=12,
    )


def about_view(match) -> ft.Control:
    """Vista secundaria mínima para validar navegación."""
    return ft.Column(
        controls=[
            ft.Text("Acerca de"),
            ft.Text("Edita src/routes.py para añadir pantallas."),
        ],
        spacing=12,
    )


def create_router() -> Router:
    """Crea un router FletPlus con rutas iniciales."""
    return Router(
        routes=[Route(path="/", view=home_view), Route(path="/about", view=about_view)]
    )


def render_initial_route(path: str = "/") -> ft.Control:
    """Renderiza una ruta mediante observers sin acoplar el ejemplo a APIs internas."""
    router = create_router()
    rendered: list[ft.Control] = []
    router.observe(lambda _match, view: rendered.append(view))
    router.go(path)
    return rendered[-1]
