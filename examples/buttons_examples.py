"""Ejemplos de los nuevos tipos de botones de FletPlus."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType


def _ensure_bootstrap_imported() -> None:
    """Permite cargar ``examples._bootstrap`` sin depender del modo de ejecución."""

    module_name = "examples._bootstrap"
    bootstrap_path = Path(__file__).resolve().parent / "_bootstrap.py"

    if __package__ in (None, ""):
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

from fletplus.components import (
    OutlinedButton,
    TextButton,
    FloatingActionButton,
)
from fletplus.themes.theme_manager import ThemeManager


def main(page: ft.Page):
    theme = ThemeManager(
        page=page,
        tokens={
            "colors": {
                "primary": ft.Colors.BLUE,
                "primary_hover": ft.Colors.BLUE_200,
                "primary_focus": ft.Colors.BLUE_300,
                "primary_pressed": ft.Colors.BLUE_400,
            },
            "typography": {"button_size": 16, "icon_size": 20},
        },
    )

    page.add(
        OutlinedButton("Editar", icon=ft.icons.EDIT, theme=theme),
        TextButton(
            "Continuar", icon=ft.icons.ARROW_FORWARD, icon_position="end", theme=theme
        ),
        FloatingActionButton(icon=ft.icons.ADD, theme=theme),
    )


if __name__ == "__main__":
    ft.app(main)
