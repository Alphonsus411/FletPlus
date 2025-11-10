"""Ejemplo de uso de ResponsiveContainer."""

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
