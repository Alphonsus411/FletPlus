"""Ejemplo de uso de ResponsiveContainer."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType


def _ensure_bootstrap_imported() -> None:
    """Carga ``examples._bootstrap`` sin depender del contexto de ejecución."""

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
