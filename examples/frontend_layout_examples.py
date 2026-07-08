"""Ejemplo de layouts frontend responsive de FletPlus."""

from __future__ import annotations

import flet as ft

from fletplus import FrontEndConfig
from fletplus.components import (
    CardGrid,
    FooterSection,
    HeroSection,
    PageShell,
    Section,
    ToolbarSection,
)


def _metric_card(title: str, value: str, icon: str) -> ft.Container:
    return ft.Container(
        padding=18,
        border_radius=18,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.BLUE),
        content=ft.Column(
            [
                ft.Icon(icon, color=ft.Colors.BLUE),
                ft.Text(value, size=26, weight=ft.FontWeight.BOLD),
                ft.Text(title),
            ],
            spacing=8,
        ),
    )


def main(page: ft.Page) -> None:
    page.title = "FletPlus frontend layouts"
    page.width = page.width or 1180

    frontend = FrontEndConfig(
        page_padding=20,
        spacing=18,
        max_content_width=1180,
        theme_tokens={"spacing": {"default": 18}},
    )
    theme = frontend.apply_to_page(page)

    hero = HeroSection(
        headline="Construye pantallas responsive con tokens",
        description="PageShell, Section, CardGrid y las secciones auxiliares leen FrontEndConfig y ThemeManager.",
        eyebrow="Nuevo layout kit",
        primary_action=ft.FilledButton("Empezar"),
        secondary_action=ft.OutlinedButton("Ver documentación"),
        config=frontend,
        theme=theme,
        bgcolor_token="surface_soft",
        border_radius=24,
        padding_by_device={"mobile": 16, "tablet": 24, "desktop": 32},
    )

    toolbar = ToolbarSection(
        leading=ft.Text("Panel comercial", weight=ft.FontWeight.W_600),
        trailing=[ft.TextButton("Exportar"), ft.FilledButton("Crear informe")],
        config=frontend,
        theme=theme,
        padding_by_device={"mobile": 8, "desktop": 12},
    )

    grid = Section(
        title="Métricas clave",
        subtitle="El número de columnas se deriva del perfil activo.",
        content=CardGrid(
            cards=[
                _metric_card("Ingresos", "$128K", ft.Icons.TRENDING_UP),
                _metric_card("Usuarios", "24K", ft.Icons.GROUP),
                _metric_card("Conversión", "8.4%", ft.Icons.INSIGHTS),
                _metric_card("Tickets", "312", ft.Icons.SUPPORT_AGENT),
            ],
            config=frontend,
            theme=theme,
            padding=0,
            columns_by_device={"mobile": 1, "tablet": 2, "desktop": 4},
        ).build(page),
        config=frontend,
        theme=theme,
        padding=0,
    )

    footer = FooterSection(
        content=ft.Text("© 2026 FletPlus"),
        links=[ft.TextButton("Privacidad"), ft.TextButton("Soporte")],
        config=frontend,
        theme=theme,
        padding_by_device={"mobile": 12, "desktop": 20},
    )

    page.add(
        PageShell(
            sections=[hero, toolbar, grid, footer],
            config=frontend,
            theme=theme,
            spacing_by_device={"mobile": 14, "tablet": 18, "desktop": 24},
            padding_by_device={"mobile": 12, "tablet": 18, "desktop": 24},
        ).build(page)
    )


if __name__ == "__main__":
    ft.app(target=main)
