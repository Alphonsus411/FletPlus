"""Ejemplos de uso de los contenedores responsivos."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType


def _ensure_bootstrap_imported() -> None:
    """Carga ``examples._bootstrap`` evitando fallos por importaciones relativas."""

    module_name = "examples._bootstrap"
    bootstrap_path = Path(__file__).resolve().parent / "_bootstrap.py"

    project_root = bootstrap_path.parents[1]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

    try:
        bootstrap = importlib.import_module(module_name)
    except ModuleNotFoundError:
        spec = importlib.util.spec_from_file_location(module_name, bootstrap_path)
        if spec is None or spec.loader is None:
            raise ImportError(
                f"No se pudo cargar {module_name} desde {bootstrap_path}."
            ) from None

        if "examples" not in sys.modules:
            package = ModuleType("examples")
            package.__path__ = [str(bootstrap_path.parent)]
            sys.modules["examples"] = package

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        bootstrap = module

    bootstrap.ensure_project_root()


_ensure_bootstrap_imported()

import flet as ft
from fletplus.components.layouts import ResponsiveContainer, FlexRow, FlexColumn
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
