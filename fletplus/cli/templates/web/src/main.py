"""Punto de entrada web para {{ project_name }}."""

from __future__ import annotations

from pathlib import Path

import flet as ft

from fletplus import FrontEndConfig
from fletplus.web.pwa import generate_manifest, generate_service_worker, register_pwa

frontend = FrontEndConfig(
    palette="material",
    mode="light",
    font_family="Roboto",
    page_padding=32,
    max_content_width=1180,
    layout_density="comfortable",
)

PWA_DIR = Path("web")
PWA_ASSETS = ["/", "manifest.json", "service_worker.js"]


def prepare_pwa_assets() -> None:
    """Genera archivos PWA iniciales para despliegues web estáticos."""

    generate_manifest(
        name="{{ project_name }}",
        icons=[],
        start_url="/",
        output_dir=PWA_DIR,
    )
    generate_service_worker(PWA_ASSETS, PWA_DIR, cache_version="v1")


def build_home(page: ft.Page) -> ft.Control:
    """Construye una landing inicial orientada a navegador."""

    profile = frontend.resolve_device_profile(int(page.width or 1280))
    hero = ft.Column(
        controls=[
            ft.Text(
                "{{ project_name }} para web",
                style=ft.TextThemeStyle.DISPLAY_SMALL,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                f"Perfil activo: {profile.name} · {profile.columns} columnas",
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Row(
                controls=[
                    ft.Container(content=ft.Text("SEO/PWA listo"), padding=16, expand=True),
                    ft.Container(content=ft.Text("Layout web centrado"), padding=16, expand=True),
                    ft.Container(content=ft.Text("Deploy estático"), padding=16, expand=True),
                ],
                wrap=True,
                spacing=frontend.spacing,
                run_spacing=frontend.spacing,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=frontend.spacing,
    )
    return frontend.build_content_shell(hero, page)


def main(page: ft.Page) -> None:
    """Configura la página para navegador y registra recursos PWA."""

    page.title = "{{ project_name }}"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    frontend.apply_to_page(page)
    register_pwa(page, "manifest.json", "service_worker.js")
    page.add(build_home(page))


if __name__ == "__main__":
    prepare_pwa_assets()
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, assets_dir=str(PWA_DIR))
