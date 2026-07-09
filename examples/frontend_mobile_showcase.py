"""Showcase frontend para móvil con navegación inferior y tarjetas apiladas."""
from __future__ import annotations
import flet as ft
from examples.frontend_showcase_common import ShowcaseProfile, build_showcase

def main(page: ft.Page) -> None:
    build_showcase(page, ShowcaseProfile(title="FletPlus Mobile Showcase", eyebrow="mobile", description="Demo móvil con contenido apilado, navegación inferior, estados compactos y controles táctiles.", width=390, platform_label="FletPlus Mobile", asset_fit=ft.ImageFit.CONTAIN))

if __name__ == "__main__":
    ft.app(target=main, assets_dir="examples/assets")
