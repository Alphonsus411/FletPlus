"""Ejemplos de estados semánticos de FletPlus."""

from __future__ import annotations

import flet as ft

from examples._bootstrap import ensure_repo_on_path

ensure_repo_on_path()

from fletplus.components import (  # noqa: E402
    EmptyState,
    ErrorState,
    LoadingState,
    MaintenanceState,
    PermissionState,
    SuccessState,
)
from fletplus.themes.theme_manager import ThemeManager  # noqa: E402


def main(page: ft.Page) -> None:
    page.title = "FletPlus state components"
    theme = ThemeManager(
        page,
        tokens={
            "colors": {
                "primary": ft.Colors.BLUE,
                "success": ft.Colors.GREEN,
                "warning": ft.Colors.ORANGE,
                "error": ft.Colors.RED,
                "info": ft.Colors.INDIGO,
                "surface_soft": ft.Colors.with_opacity(0.06, ft.Colors.PRIMARY),
            },
            "spacing": {"default": 14},
            "typography": {"state_icon_size": 48},
        },
    )

    states = [
        LoadingState(theme=theme),
        EmptyState(
            theme=theme,
            primary_action=ft.FilledButton("Crear elemento"),
            secondary_action=ft.OutlinedButton("Importar"),
        ),
        ErrorState(theme=theme, primary_action=ft.FilledButton("Reintentar")),
        SuccessState(theme=theme, primary_action=ft.FilledButton("Ver detalle")),
        PermissionState(
            theme=theme, primary_action=ft.FilledButton("Solicitar acceso")
        ),
        MaintenanceState(
            theme=theme, secondary_action=ft.TextButton("Ver estado del servicio")
        ),
    ]

    page.add(
        ft.ResponsiveRow(
            [
                ft.Container(
                    content=state.build(page), col={"xs": 12, "md": 6, "xl": 4}
                )
                for state in states
            ],
            spacing=16,
            run_spacing=16,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
