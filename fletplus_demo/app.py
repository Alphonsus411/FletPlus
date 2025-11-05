"""Aplicación de demostración basada en :class:`fletplus.FletPlusApp`."""
from __future__ import annotations

import flet as ft

from fletplus import FletPlusApp


def _build_view(title: str, description: str) -> ft.Control:
    """Crea una sección simple para las rutas de demostración."""
    return ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=18,
            controls=[
                ft.Icon(name=ft.Icons.DASHBOARD_OUTLINED, size=56, color=ft.Colors.PRIMARY),
                ft.Text(title, size=28, weight=ft.FontWeight.W_600),
                ft.Text(description, size=16, text_align=ft.TextAlign.CENTER),
            ],
        ),
    )


def main(page: ft.Page) -> None:
    """Punto de entrada para la app de ejemplo."""
    routes = {
        "/": lambda: _build_view("Inicio", "Bienvenido al panel principal de FletPlus."),
        "/dashboard": lambda: _build_view("Dashboard", "Explora las métricas más recientes de tu organización."),
        "/reportes": lambda: _build_view("Reportes", "Consulta indicadores clave y descárgalos en distintos formatos."),
        "/usuarios": lambda: _build_view("Usuarios", "Administra permisos, invita a colaboradores y revisa su actividad."),
        "/configuracion": lambda: _build_view("Configuración", "Ajusta la apariencia, idioma y preferencias globales."),
    }
    sidebar_items = [
        {"title": "Inicio", "icon": ft.Icons.HOME, "path": "/"},
        {"title": "Dashboard", "icon": ft.Icons.INSIGHTS, "path": "/dashboard"},
        {"title": "Reportes", "icon": ft.Icons.ANALYTICS, "path": "/reportes"},
        {"title": "Usuarios", "icon": ft.Icons.SUPERVISED_USER_CIRCLE, "path": "/usuarios"},
        {"title": "Configuración", "icon": ft.Icons.SETTINGS, "path": "/configuracion"},
    ]

    app = FletPlusApp(
        page,
        routes=routes,
        sidebar_items=sidebar_items,
        title="FletPlus Demo",
    )
    app.build()

    app.command_palette.commands = {
        "Ir a inicio": lambda: app.router.go("/"),
        "Explorar dashboard": lambda: app.router.go("/dashboard"),
        "Ver reportes": lambda: app.router.go("/reportes"),
        "Gestionar usuarios": lambda: app.router.go("/usuarios"),
        "Configuración general": lambda: app.router.go("/configuracion"),
    }
    app.command_palette.filtered = list(app.command_palette.commands.items())
    app.command_palette._refresh()


def run() -> None:
    """Ejecuta la aplicación con el *runtime* de Flet."""
    ft.app(target=main)
