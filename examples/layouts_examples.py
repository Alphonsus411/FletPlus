"""Ejemplos de uso de los contenedores responsivos."""

from __future__ import annotations

from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

from examples._bootstrap import ensure_project_root

ensure_project_root()

import flet as ft
from fletplus.components.layouts import (
    ResponsiveContainer,
    FlexRow,
    FlexColumn,
    Grid,
    GridItem,
    Wrap,
)
from fletplus.styles import Style
from fletplus.themes.theme_manager import ThemeManager
from fletplus.utils.responsive_typography import (
    ResponsiveTypography,
    responsive_text,
    responsive_spacing,
)


def desktop_demo(page: ft.Page) -> None:
    page.title = "Desktop responsive"
    container = ResponsiveContainer(
        ft.Text("Área de contenido"),
        breakpoints={
            "xs": Style(max_width=300, padding=10),
            "md": Style(max_width=600, padding=30),
        },
    )
    row = FlexRow(
        [ft.Text("Uno"), ft.Text("Dos"), ft.Text("Tres")],
        breakpoints={
            "xs": {"spacing": 5, "alignment": ft.MainAxisAlignment.START, "wrap": True},
            "md": {
                "spacing": 20,
                "alignment": ft.MainAxisAlignment.SPACE_BETWEEN,
                "wrap": False,
            },
        },
    )
    grid = Grid(
        items=[
            GridItem(ft.Container(ft.Text("Hero"), bgcolor=ft.Colors.BLUE_100), span_breakpoints={"xs": 12, "md": 6, "xl": 4}),
            GridItem(ft.Container(ft.Text("Detalle"), bgcolor=ft.Colors.AMBER_100), span=6),
        ],
        spacing_breakpoints={"md": 24},
    )
    page.add(container.init_responsive(page), row.init_responsive(page))
    page.add(grid.init_responsive(page))


def web_demo(page: ft.Page) -> None:
    page.title = "Web responsive"
    column = FlexColumn(
        [ft.Text(f"Item {i}") for i in range(5)],
        breakpoints={
            "xs": {"spacing": 5, "alignment": ft.MainAxisAlignment.START},
            "md": {"spacing": 15, "alignment": ft.MainAxisAlignment.CENTER},
        },
    )
    page.add(column.init_responsive(page))


def mobile_demo(page: ft.Page) -> None:
    page.title = "Mobile responsive"
    container = ResponsiveContainer(
        ft.Text("Móvil"),
        breakpoints={
            "xs": Style(max_width=200, padding=5),
            "md": Style(max_width=300, padding=15),
        },
    )
    actions = Wrap(
        [ft.ElevatedButton("Aceptar"), ft.OutlinedButton("Cancelar")],
        breakpoints={"xs": {"spacing": 4}, "md": {"spacing": 12, "run_spacing": 6}},
    )
    page.add(container.init_responsive(page), actions.init_responsive(page))


def typography_demo(page: ft.Page) -> None:
    """Ejemplo de tipografía y espaciado responsivo."""

    page.title = "Responsive typography"
    theme = ThemeManager(page)
    typography = ResponsiveTypography(page, theme)

    txt = ft.Text("Texto adaptable", style=ft.TextStyle(size=responsive_text(page)))
    typography.register_text(txt)

    box = ft.Container(bgcolor=ft.Colors.AMBER, padding=responsive_spacing(page))
    typography.register_spacing_control(box)

    page.add(txt, box)


# Para ejecutar:
#   Desktop: flet run examples/layouts_examples.py
#   Web:     flet run --view=web_browser examples/layouts_examples.py web_demo
#   Móvil:   flet run --view=flet_app examples/layouts_examples.py mobile_demo
if __name__ == "__main__":
    ft.app(target=desktop_demo)
