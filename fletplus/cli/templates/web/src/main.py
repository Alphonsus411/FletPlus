"""Punto de entrada principal para {{ project_name }}."""

from __future__ import annotations

import flet as ft

from fletplus import FrontEndConfig

frontend = FrontEndConfig(
    palette="material",
    mode="light",
    font_family="Roboto",
    page_padding=24,
    max_content_width=1100,
)


def build_home(page: ft.Page) -> ft.Control:
    """Construye la vista inicial con tema y layout responsivo."""

    profile = frontend.resolve_device_profile(int(page.width or 1024))
    hero = ft.Column(
        controls=[
            ft.Text(
                "¡Hola desde FletPlus!",
                style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                f"Plantilla web responsive activa: {profile.name} ({profile.columns} columnas)",
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Personaliza paletas, fuentes y layout desde `frontend`.",
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=frontend.spacing,
    )
    return frontend.build_content_shell(hero, page)


def main(page: ft.Page) -> None:
    """Crea el contenido inicial de la aplicación."""

    page.title = "{{ project_name }}"
    frontend.apply_to_page(page)
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(build_home(page))


if __name__ == "__main__":
    ft.app(target=main)
