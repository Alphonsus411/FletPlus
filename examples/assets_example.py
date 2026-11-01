"""Ejemplo funcional de carga de assets desde ``assets/``.

Reproduce la convención de las plantillas CLI: centralizar las rutas de recursos
en un módulo único (``assets.py``), apuntar ``page.assets_dir`` al directorio de
assets y referenciar las ``src`` de los controles de forma relativa a ese
directorio.
"""

from __future__ import annotations

from pathlib import Path

import flet as ft

# En un proyecto generado esto vive en `src/frontend/assets.py`.
ASSETS_DIR = Path("examples/assets")
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"

# Recurso real versionado en el repositorio para que el ejemplo sea ejecutable.
LOGO = ASSETS_DIR / "fletplus_showcase.svg"


def build_asset_card() -> ft.Control:
    """Tarjeta que carga un logo servido desde ``page.assets_dir``."""

    logo_src = LOGO.relative_to(ASSETS_DIR).as_posix()
    return ft.Container(
        padding=18,
        border_radius=18,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.BLUE),
        content=ft.Column(
            [
                ft.Image(src=logo_src, height=160, fit=ft.ImageFit.CONTAIN),
                ft.Text("Logo cargado desde assets/", weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Sirve los recursos con page.assets_dir y usa rutas "
                    "relativas centralizadas en assets.py.",
                    opacity=0.75,
                ),
            ],
            spacing=10,
        ),
    )


def main(page: ft.Page) -> None:
    page.title = "FletPlus · Assets"
    page.assets_dir = str(ASSETS_DIR)
    page.padding = 24

    # Si añades `assets/fonts/Inter-Regular.ttf`, se registra como familia local.
    local_font = FONTS_DIR / "Inter-Regular.ttf"
    if local_font.is_file():
        page.fonts = {**(page.fonts or {}), "Inter": str(local_font)}

    page.add(
        ft.Column(
            [
                ft.Text("Assets e iconografía", size=26, weight=ft.FontWeight.BOLD),
                build_asset_card(),
                ft.Text(
                    "Estructura: fonts/, icons/ e images/ con su README.md en cada "
                    "subdirectorio (ver docs/frontend-projects.md).",
                    opacity=0.7,
                ),
            ],
            spacing=16,
        )
    )


if __name__ == "__main__":
    ft.app(target=main, assets_dir=str(ASSETS_DIR))
