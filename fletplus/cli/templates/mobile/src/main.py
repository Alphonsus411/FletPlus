"""Punto de entrada mobile para {{ project_name }}."""

from __future__ import annotations

import flet as ft
from fletplus import FrontEndConfig
from fletplus.utils.flet_compat import get_flet_icon, make_navigation_bar_destination

from layout import responsive_shell, spacing
from routes import render_initial_route
from theme import create_frontend_config

frontend: FrontEndConfig = create_frontend_config()  # layout_density="compact"


def build_mobile_body(page: ft.Page) -> ft.Control:
    profile = frontend.resolve_device_profile(int(page.width or 390))
    routed_view = render_initial_route("/")
    content = ft.Column(
        controls=[
            routed_view,
            ft.Text("{{ project_name }}", style=ft.TextThemeStyle.HEADLINE_SMALL),
            ft.Text(f"Perfil móvil: {profile.name} · {profile.columns} columna(s)"),
            ft.Container(
                content=ft.Text("Tarjeta optimizada para uso táctil y lectura rápida."),
                padding=16,
            ),
            ft.Container(content=ft.Text("Acción principal"), padding=16),
        ],
        spacing=spacing(frontend),
        tight=True,
    )
    safe_area = getattr(ft, "SafeArea", None)
    if safe_area is not None:
        return safe_area(content=responsive_shell(content, page, frontend))
    return ft.Container(content=responsive_shell(content, page, frontend), padding=12)


def build_navigation() -> ft.NavigationBar:
    return ft.NavigationBar(
        destinations=[
            make_navigation_bar_destination(
                icon=get_flet_icon("HOME", "home"), label="Inicio"
            ),
            make_navigation_bar_destination(
                icon=get_flet_icon("SEARCH", "search"), label="Buscar"
            ),
            make_navigation_bar_destination(
                icon=get_flet_icon("PERSON", "person"), label="Perfil"
            ),
        ],
        height=64,
    )


def main(page: ft.Page) -> None:
    page.title = "{{ project_name }}"
    page.scroll = ft.ScrollMode.AUTO
    frontend.apply_to_page(page)
    page.padding = 0
    page.navigation_bar = build_navigation()
    page.add(build_mobile_body(page))


if __name__ == "__main__":
    ft.app(target=main)
