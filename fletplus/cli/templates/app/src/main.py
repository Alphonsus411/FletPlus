"""Punto de entrada principal para {{ project_name }}."""

from __future__ import annotations

import flet as ft


def main(page: ft.Page) -> None:
    page.title = "{{ project_name }}"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(
        ft.Column(
            controls=[
                ft.Text("¡Bienvenido a FletPlus!", style=ft.TextThemeStyle.TITLE_LARGE),
                ft.Text(
                    "Edita `src/main.py` y guarda el archivo para ver los cambios al instante.",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.ElevatedButton(
                    "Abrir documentación",
                    on_click=lambda _: page.launch_url("https://flet.dev/docs/"),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
