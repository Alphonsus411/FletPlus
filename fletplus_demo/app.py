"""Aplicación de demostración basada en :class:`fletplus.FletPlusApp`."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import flet as ft

from fletplus import FletPlusApp

@dataclass(frozen=True, slots=True)
class DemoRoute:
    """Describe una sección navegable de la demostración."""

    path: str
    title: str
    description: str
    icon: str
    command_label: str
    slug: str


DEMO_ROUTES: tuple[DemoRoute, ...] = (
    DemoRoute(
        path="/",
        title="Inicio",
        description="Bienvenido al panel principal de FletPlus.",
        icon=ft.Icons.HOME,
        command_label="Ir a inicio",
        slug="inicio",
    ),
    DemoRoute(
        path="/dashboard",
        title="Dashboard",
        description="Explora las métricas más recientes de tu organización.",
        icon=ft.Icons.INSIGHTS,
        command_label="Explorar dashboard",
        slug="dashboard",
    ),
    DemoRoute(
        path="/reportes",
        title="Reportes",
        description="Consulta indicadores clave y descárgalos en distintos formatos.",
        icon=ft.Icons.ANALYTICS,
        command_label="Ver reportes",
        slug="reportes",
    ),
    DemoRoute(
        path="/usuarios",
        title="Usuarios",
        description="Administra permisos, invita a colaboradores y revisa su actividad.",
        icon=ft.Icons.SUPERVISED_USER_CIRCLE,
        command_label="Gestionar usuarios",
        slug="usuarios",
    ),
    DemoRoute(
        path="/configuracion",
        title="Configuración",
        description="Ajusta la apariencia, idioma y preferencias globales.",
        icon=ft.Icons.SETTINGS,
        command_label="Configuración general",
        slug="configuracion",
    ),
)


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


def _build_routes() -> dict[str, Callable[[], ft.Control]]:
    def make_builder(route: DemoRoute) -> Callable[[], ft.Control]:
        return lambda route=route: _build_view(route.title, route.description)

    return {route.path: make_builder(route) for route in DEMO_ROUTES}


def _sidebar_items() -> list[dict[str, object]]:
    return [
        {"title": route.title, "icon": route.icon, "path": route.path}
        for route in DEMO_ROUTES
    ]


def _command_palette_entries(app: FletPlusApp) -> dict[str, Callable[[], None]]:
    return {
        route.command_label: (lambda r=route: app.router.go(r.path))
        for route in DEMO_ROUTES
    }


def create_app(page: ft.Page) -> FletPlusApp:
    """Construye la aplicación de demostración sobre ``page`` y la devuelve."""

    app = FletPlusApp(
        page,
        routes=_build_routes(),
        sidebar_items=_sidebar_items(),
        title="FletPlus Demo",
    )
    app.build()
    app.command_palette.commands = _command_palette_entries(app)
    app.command_palette.refresh()
    return app


def main(page: ft.Page) -> None:
    """Punto de entrada para la app de ejemplo."""

    create_app(page)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta la demo de FletPlus.")
    parser.add_argument(
        "--capture",
        metavar="DIR",
        help="Genera capturas PNG de cada vista en la carpeta indicada.",
    )
    parser.add_argument(
        "--record",
        metavar="DIR",
        help="Genera clips MP4 a partir de las capturas en la carpeta indicada.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Ancho del viewport usado para generar los activos (por defecto 1280).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Alto del viewport usado para generar los activos (por defecto 720).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.8,
        help="Segundos de espera tras navegar antes de capturar (por defecto 0.8).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=3.0,
        help="Duración en segundos de cada clip generado con --record (por defecto 3).",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Cuadros por segundo para los clips de --record (por defecto 30).",
    )
    parser.add_argument(
        "--launch",
        action="store_true",
        help="Lanza la UI interactiva tras generar activos (--capture/--record).",
    )
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> None:
    """Ejecuta la aplicación con el *runtime* de Flet o genera activos."""

    args = _parse_args(argv)
    requested_assets = bool(args.capture or args.record)
    if requested_assets:
        from .capture import capture_assets

        capture_assets(
            screenshot_dir=Path(args.capture) if args.capture else None,
            recording_dir=Path(args.record) if args.record else None,
            viewport=(args.width, args.height),
            delay=args.delay,
            record_duration=args.duration,
            record_fps=args.fps,
        )
        if not args.launch:
            return

    ft.app(target=main)


__all__ = ["create_app", "DEMO_ROUTES", "main", "run"]
