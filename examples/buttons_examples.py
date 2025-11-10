"""Ejemplos de los nuevos tipos de botones de FletPlus."""

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
        OutlinedButton("Editar", icon=ft.Icons.EDIT, theme=theme),
        TextButton(
            "Continuar", icon=ft.Icons.ARROW_FORWARD, icon_position="end", theme=theme
        ),
        FloatingActionButton(icon=ft.Icons.ADD, theme=theme),
    )


if __name__ == "__main__":
    ft.app(main)
