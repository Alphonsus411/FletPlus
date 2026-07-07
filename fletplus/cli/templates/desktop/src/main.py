"""Punto de entrada desktop para {{ project_name }}."""

from __future__ import annotations

import flet as ft

from fletplus import FrontEndConfig
from fletplus.utils.flet_compat import safe_set_window_attr

frontend = FrontEndConfig(
    palette="material",
    mode="light",
    font_family="Roboto",
    page_padding=28,
    max_content_width=1320,
    layout_density="spacious",
)


def configure_window(page: ft.Page) -> None:
    """Aplica preferencias de ventana usando helpers compatibles de FletPlus."""

    safe_set_window_attr(page, "width", 1280)
    safe_set_window_attr(page, "height", 820)
    safe_set_window_attr(page, "min_width", 960)
    safe_set_window_attr(page, "min_height", 640)
    safe_set_window_attr(page, "resizable", True)
    safe_set_window_attr(page, "center", True)


def build_home(page: ft.Page) -> ft.Control:
    """Construye un layout amplio con navegación lateral para escritorio."""

    profile = frontend.resolve_device_profile(int(page.width or 1280))
    sidebar = ft.Container(
        width=260,
        padding=20,
        content=ft.Column(
            controls=[
                ft.Text("{{ project_name }}", style=ft.TextThemeStyle.TITLE_LARGE),
                ft.Text("Dashboard"),
                ft.Text("Informes"),
                ft.Text("Ajustes"),
            ],
            spacing=14,
        ),
    )
    workspace = ft.Column(
        controls=[
            ft.Text("Plantilla desktop", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Text(f"Perfil responsive: {profile.name} ({profile.columns} columnas)"),
            ft.Row(
                controls=[
                    ft.Container(content=ft.Text("Panel principal"), padding=24, expand=2),
                    ft.Container(content=ft.Text("Actividad reciente"), padding=24, expand=1),
                ],
                spacing=frontend.spacing,
                expand=True,
            ),
        ],
        spacing=frontend.spacing,
        expand=True,
    )
    return frontend.build_content_shell(
        ft.Row(controls=[sidebar, workspace], spacing=frontend.spacing, expand=True), page
    )


def main(page: ft.Page) -> None:
    """Crea el contenido inicial de la aplicación desktop."""

    page.title = "{{ project_name }}"
    configure_window(page)
    frontend.apply_to_page(page)
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.add(build_home(page))


if __name__ == "__main__":
    ft.app(target=main)
