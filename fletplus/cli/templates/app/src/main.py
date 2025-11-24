"""Punto de entrada principal para {{ project_name }}."""

from __future__ import annotations

import flet as ft


def main(page: ft.Page) -> None:
    """Crea el contenido inicial de la aplicación."""

    page.title = "{{ project_name }}"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(
        ft.Column(
            controls=[
                ft.Text(
                    "¡Hola desde FletPlus!",
                    style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Edita `src/main.py` para personalizar tu aplicación.",
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
