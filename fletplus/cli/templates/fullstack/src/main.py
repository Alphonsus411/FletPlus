"""Punto de entrada principal para {{ project_name }}."""

from __future__ import annotations

import flet as ft
from backend.services import get_project_status
from frontend.layout import responsive_shell, spacing
from frontend.routes import render_initial_route
from frontend.theme import create_frontend_config

from fletplus import FrontEndConfig

frontend: FrontEndConfig = create_frontend_config()


def build_home(page: ft.Page) -> ft.Control:
    """Construye la vista inicial con tema y layout responsivo."""
    routed_view = render_initial_route("/")
    profile = frontend.resolve_device_profile(int(page.width or 1024))
    status = get_project_status()
    hero = ft.Column(
        controls=[
            routed_view,
            ft.Text(
                f"Plantilla responsive activa: {profile.name} ({profile.columns} columnas)",
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                f"Backend local: {status.name} · listo={status.ready}",
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Personaliza frontend, backend, shared, docs y deploy desde sus carpetas dedicadas.",
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=spacing(frontend),
    )
    return responsive_shell(hero, page, frontend)


def main(page: ft.Page) -> None:
    page.title = "{{ project_name }}"
    frontend.apply_to_page(page)
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(build_home(page))


if __name__ == "__main__":
    ft.app(target=main)
