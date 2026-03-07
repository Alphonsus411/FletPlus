"""Ejemplo de uso de ResponsiveContainer."""

from __future__ import annotations

import sys
from pathlib import Path

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

    container_host = ft.Column()
    container: ResponsiveContainer | None = None

    def render_container(_event: ft.ControlEvent | None = None) -> None:
        nonlocal container
        if container is not None:
            container.dispose()

        container = ResponsiveContainer(ft.Text("Contenido adaptable"), estilos)
        container_host.controls = [container.build(page)]
        page.update()

    def dispose_container(_event: ft.ControlEvent | None = None) -> None:
        nonlocal container
        if container is not None:
            container.dispose()
            container = None
        container_host.controls = [ft.Text("Contenedor desmontado")]
        page.update()

    page.add(
        ft.Row(
            [
                ft.Button("Reconstruir", on_click=render_container),
                ft.OutlinedButton("Desmontar", on_click=dispose_container),
            ]
        ),
        container_host,
    )

    render_container()


if __name__ == "__main__":
    ft.app(target=main)
