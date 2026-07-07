"""Punto de entrada principal para {{ project_name }}."""

from __future__ import annotations

import flet as ft
from layout import responsive_shell, spacing
from routes import render_initial_route
from theme import create_frontend_config

from fletplus import FrontEndConfig

frontend: FrontEndConfig = create_frontend_config()


def build_home(page: ft.Page) -> ft.Control:
    """Construye la vista inicial con tema y layout responsivo."""
    routed_view = render_initial_route("/")
    profile = frontend.resolve_device_profile(int(page.width or 1024))
    hero = ft.Column(
        controls=[
            routed_view,
            ft.Text(
                f"Plantilla responsive activa: {profile.name} ({profile.columns} columnas)",
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Personaliza paletas, fuentes, tokens y layout desde src/theme.py y src/layout.py.",
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
