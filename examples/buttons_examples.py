"""Ejemplos de los nuevos tipos de botones de FletPlus."""

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
