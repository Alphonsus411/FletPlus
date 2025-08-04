"""Ejemplo de uso de ResponsiveContainer."""

import flet as ft
from fletplus.components.responsive_container import ResponsiveContainer
from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle


def main(page: ft.Page) -> None:
    page.title = "ResponsiveContainer"

    estilos = ResponsiveStyle(
        width={
            0: Style(padding=10, bgcolor=ft.Colors.BLUE_100),
            600: Style(padding=30, bgcolor=ft.Colors.GREEN_100),
        },
        base=Style(border_radius=10),
    )

    container = ResponsiveContainer(ft.Text("Contenido adaptable"), estilos)
    page.add(container.build(page))


if __name__ == "__main__":
    ft.app(target=main)
