"""Ejemplo de textos, navegación, badges y ayudas con roles tipográficos."""

from __future__ import annotations

import flet as ft

from examples._bootstrap import ensure_project_root
from fletplus import FrontEndConfig
from fletplus.frontend.config import FontDeclaration
from fletplus.utils.flet_compat import (
    get_flet_color,
    get_flet_icon,
    make_navigation_bar_destination,
)
from fletplus.utils.responsive_typography import ResponsiveTypography

ensure_project_root()

NAV_ITEM_ROLE = "nav_item"
BADGE_ROLE = "badge"
HELPER_ROLE = "helper"


def build_config() -> FrontEndConfig:
    """Configuración con familia personalizada, fallbacks y roles semánticos."""

    return FrontEndConfig(
        font=FontDeclaration(
            family="Inter",
            fallback_families=("Roboto", "Arial", "sans-serif"),
            weights=("w400", "w600", "w700"),
            styles=("normal", "italic"),
        ),
        typography_tokens={
            NAV_ITEM_ROLE: {
                "mobile": {"size": 12, "weight": "w600", "line_height": 1.3},
                "desktop": {"size": 14, "weight": "w600", "line_height": 1.3},
            },
            BADGE_ROLE: {
                "mobile": {"size": 10, "weight": "w700", "line_height": 1.2},
                "desktop": {"size": 12, "weight": "w700", "line_height": 1.2},
            },
            # Rol con valores planos: se interpreta como variante `mobile` y el
            # resto de perfiles degradan a ella automáticamente.
            HELPER_ROLE: {"size": 12, "weight": "w400", "line_height": 1.4},
        },
    )


def _role_text(
    typography: ResponsiveTypography, value: str, role: str
) -> ft.Text:
    text = ft.Text(value)
    typography.register_text(text, role=role)
    return text


def main(page: ft.Page) -> None:
    config = build_config()
    theme = config.apply_to_page(page)
    typography = ResponsiveTypography(page, theme=theme, config=config)

    width_label = ft.Text()
    samples = [
        ("display", "Display: hero principal"),
        ("headline", "Headline: sección destacada"),
        ("title", "Title: título de tarjeta"),
        ("body", "Body: párrafo legible y adaptable."),
        ("label", "Label: acción o metadato"),
        ("caption", "Caption: ayuda contextual"),
    ]
    sample_controls = [_role_text(typography, value, role) for role, value in samples]

    nav_items = [
        ft.Row(
            [
                ft.Icon(get_flet_icon("HOME_OUTLINED", None)),
                _role_text(typography, label, NAV_ITEM_ROLE),
            ],
            spacing=6,
        )
        for label in ("Inicio", "Informes", "Ajustes")
    ]

    badge_text = _role_text(typography, "Beta", BADGE_ROLE)
    badge = ft.Container(
        content=badge_text,
        padding=8,
        border_radius=10,
        bgcolor=get_flet_color("SECONDARY_CONTAINER", None),
    )

    help_control = ft.Icon(
        get_flet_icon("HELP_OUTLINE", None),
        tooltip="Atajos: pulsa Ctrl+K",
    )
    helper_text = _role_text(
        typography, "Los tamaños se adaptan al ancho de la ventana.", HELPER_ROLE
    )

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            make_navigation_bar_destination(
                icon=get_flet_icon("HOME_OUTLINED", None), label="Inicio"
            ),
            make_navigation_bar_destination(
                icon=get_flet_icon("INSIGHTS_OUTLINED", None), label="Informes"
            ),
            make_navigation_bar_destination(
                icon=get_flet_icon("SETTINGS_OUTLINED", None), label="Ajustes"
            ),
        ],
    )

    panel = ft.Container(
        padding=config.spacing,
        content=ft.Column(
            [
                ft.Row([badge], alignment=ft.MainAxisAlignment.END),
                *sample_controls,
                ft.Row(nav_items, spacing=config.spacing, wrap=True),
                ft.Row([help_control, helper_text], spacing=config.spacing),
                width_label,
            ],
            spacing=config.spacing,
        ),
    )
    typography.register_spacing_control(panel)

    def sync(_: ft.ControlEvent | None = None) -> None:
        width = int(page.width or 0)
        profile = config.resolve_device_profile(width).name
        width_label.value = f"Ancho: {width}px · perfil: {profile}"
        page.update()

    page.on_resize = sync
    page.add(config.build_content_shell(panel, page))
    sync()


if __name__ == "__main__":
    ft.app(target=main)
