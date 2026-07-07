"""Punto de entrada web para {{ project_name }}."""

from __future__ import annotations

from pathlib import Path

import flet as ft
from frontend.layout import responsive_shell, spacing
from frontend.routes import render_initial_route
from frontend.theme import create_frontend_config

from fletplus import FrontEndConfig
from fletplus.web.pwa import generate_manifest, generate_service_worker, register_pwa

frontend: FrontEndConfig = create_frontend_config()
PWA_DIR = Path("web")
PWA_ASSETS = ["/", "manifest.json", "service_worker.js"]


def prepare_pwa_assets() -> None:
    generate_manifest(
        name="{{ project_name }}", icons=[], start_url="/", output_dir=PWA_DIR
    )
    generate_service_worker(PWA_ASSETS, PWA_DIR, cache_version="v1")


def build_home(page: ft.Page) -> ft.Control:
    profile = frontend.resolve_device_profile(int(page.width or 1280))
    routed_view = render_initial_route("/")
    hero = ft.Column(
        controls=[
            ft.Text(
                "{{ project_name }} para web",
                style=ft.TextThemeStyle.DISPLAY_SMALL,
                text_align=ft.TextAlign.CENTER,
            ),
            routed_view,
            ft.Text(
                f"Perfil activo: {profile.name} · {profile.columns} columnas",
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text("SEO/PWA listo"), padding=16, expand=True
                    ),
                    ft.Container(
                        content=ft.Text("Layout web centrado"), padding=16, expand=True
                    ),
                    ft.Container(
                        content=ft.Text("Deploy estático"), padding=16, expand=True
                    ),
                ],
                wrap=True,
                spacing=spacing(frontend),
                run_spacing=spacing(frontend),
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=spacing(frontend),
    )
    return responsive_shell(hero, page, frontend)


def main(page: ft.Page) -> None:
    page.title = "{{ project_name }}"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    frontend.apply_to_page(page)
    register_pwa(page, "manifest.json", "service_worker.js")
    page.add(build_home(page))


if __name__ == "__main__":
    prepare_pwa_assets()
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, assets_dir=str(PWA_DIR))
