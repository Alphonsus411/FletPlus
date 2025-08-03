"""Ejemplos de uso de los contenedores responsivos."""

import flet as ft
from fletplus.components.layouts import ResponsiveContainer, FlexRow, FlexColumn
from fletplus.styles import Style


def desktop_demo(page: ft.Page) -> None:
    page.title = "Desktop responsive"
    container = ResponsiveContainer(
        ft.Text("Área de contenido"),
        breakpoints={
            0: Style(max_width=300, padding=10),
            800: Style(max_width=600, padding=30),
        },
    )
    row = FlexRow(
        [ft.Text("Uno"), ft.Text("Dos"), ft.Text("Tres")],
        breakpoints={
            0: {"spacing": 5, "alignment": ft.MainAxisAlignment.START, "wrap": True},
            800: {"spacing": 20, "alignment": ft.MainAxisAlignment.SPACE_BETWEEN, "wrap": False},
        },
    )
    page.add(container.init_responsive(page), row.init_responsive(page))


def web_demo(page: ft.Page) -> None:
    page.title = "Web responsive"
    column = FlexColumn(
        [ft.Text(f"Item {i}") for i in range(5)],
        breakpoints={
            0: {"spacing": 5, "alignment": ft.MainAxisAlignment.START},
            600: {"spacing": 15, "alignment": ft.MainAxisAlignment.CENTER},
        },
    )
    page.add(column.init_responsive(page))


def mobile_demo(page: ft.Page) -> None:
    page.title = "Mobile responsive"
    container = ResponsiveContainer(
        ft.Text("Móvil"),
        breakpoints={
            0: Style(max_width=200, padding=5),
            400: Style(max_width=300, padding=15),
        },
    )
    page.add(container.init_responsive(page))


# Para ejecutar:
#   Desktop: flet run examples/layouts_examples.py
#   Web:     flet run --view=web_browser examples/layouts_examples.py web_demo
#   Móvil:   flet run --view=flet_app examples/layouts_examples.py mobile_demo
if __name__ == "__main__":
    ft.app(target=desktop_demo)
