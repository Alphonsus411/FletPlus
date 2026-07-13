"""Punto de entrada desktop para {{ project_name }}."""

from __future__ import annotations

import flet as ft
from frontend.layout import responsive_shell, spacing
from frontend.routes import render_initial_route
from frontend.theme import create_frontend_config

from fletplus import FrontEndConfig
from fletplus.cli.catalog import get_cli_command_catalog
from fletplus.components import CommandPalette
from fletplus.utils.flet_compat import safe_set_window_attr

frontend: FrontEndConfig = create_frontend_config()

ROUTES = {
    "dashboard": {"label": "Dashboard", "path": "/"},
    "informes": {"label": "Informes", "path": "/about"},
    "ajustes": {"label": "Ajustes", "path": "/about"},
}


def configure_window(page: ft.Page) -> None:
    safe_set_window_attr(page, "width", 1280)
    safe_set_window_attr(page, "height", 820)
    safe_set_window_attr(page, "min_width", 960)
    safe_set_window_attr(page, "min_height", 640)
    safe_set_window_attr(page, "resizable", True)
    safe_set_window_attr(page, "center", True)


def _command_catalog_view() -> ft.Control:
    return ft.Column(
        controls=[
            ft.Text("CLI de FletPlus", style=ft.TextThemeStyle.HEADLINE_SMALL),
            ft.Text("Comandos disponibles para ejecutar desde tu terminal:"),
            *[
                ft.ListTile(
                    title=ft.Text(command.command),
                    subtitle=ft.Text(command.description),
                    leading=ft.Icon(ft.Icons.TERMINAL),
                )
                for command in get_cli_command_catalog()
            ],
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )


def build_home(page: ft.Page) -> ft.Control:
    profile = frontend.resolve_device_profile(int(page.width or 1280))
    selected_route = {"key": "dashboard"}
    content_host = ft.Container(expand=True)

    def render_route(route_key: str) -> ft.Control:
        route_info = ROUTES[route_key]
        routed_view = render_initial_route(str(route_info["path"]))
        return ft.Column(
            controls=[
                routed_view,
                ft.Text("Plantilla desktop", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ft.Text(
                    f"Perfil responsive: {profile.name} ({profile.columns} columnas)"
                ),
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text("Panel principal"), padding=24, expand=2
                        ),
                        ft.Container(
                            content=ft.Text("Actividad reciente"), padding=24, expand=1
                        ),
                    ],
                    spacing=spacing(frontend),
                    expand=True,
                ),
            ],
            spacing=spacing(frontend),
            expand=True,
        )

    def show_route(route_key: str) -> None:
        selected_route["key"] = route_key
        content_host.content = render_route(route_key)
        if getattr(content_host, "page", None):
            content_host.update()

    def show_cli_catalog() -> None:
        content_host.content = _command_catalog_view()
        if getattr(content_host, "page", None):
            content_host.update()

    palette_commands = {
        "Abrir Dashboard": lambda: show_route("dashboard"),
        "Abrir Informes": lambda: show_route("informes"),
        "Abrir Ajustes": lambda: show_route("ajustes"),
        "Mostrar CLI de FletPlus": show_cli_catalog,
    }
    palette_commands.update(
        {
            f"CLI: {command.name}": (lambda command=command: show_cli_catalog())
            for command in get_cli_command_catalog()
        }
    )
    command_palette = CommandPalette(palette_commands)

    def open_commands(_event=None) -> None:
        command_palette.open(page)

    def nav_tile(route_key: str) -> ft.Control:
        route_info = ROUTES[route_key]
        return ft.ListTile(
            title=ft.Text(str(route_info["label"])),
            leading=ft.Icon(ft.Icons.CHEVRON_RIGHT),
            selected=selected_route["key"] == route_key,
            on_click=lambda _event, key=route_key: show_route(key),
        )

    sidebar = ft.Container(
        width=280,
        padding=20,
        content=ft.Column(
            controls=[
                ft.Text("{{ project_name }}", style=ft.TextThemeStyle.TITLE_LARGE),
                ft.Text("Escritorio Linux friendly"),
                nav_tile("dashboard"),
                nav_tile("informes"),
                nav_tile("ajustes"),
                ft.Divider(),
                ft.FilledButton(
                    "Comandos",
                    icon=ft.Icons.TERMINAL,
                    tooltip="Abrir paleta de comandos y catálogo CLI",
                    on_click=open_commands,
                ),
                ft.Text("Tip: usa el botón Comandos para consultar la CLI."),
            ],
            spacing=10,
        ),
    )
    content_host.content = render_route("dashboard")
    return responsive_shell(
        ft.Row(
            controls=[sidebar, content_host], spacing=spacing(frontend), expand=True
        ),
        page,
        frontend,
    )


def main(page: ft.Page) -> None:
    page.title = "{{ project_name }}"
    configure_window(page)
    frontend.apply_to_page(page)
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.add(build_home(page))


if __name__ == "__main__":
    ft.app(target=main)
