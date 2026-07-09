"""Showcase frontend para web con paleta, navegación y layout responsive."""
from __future__ import annotations
import flet as ft
from examples.frontend_showcase_common import ShowcaseProfile, build_showcase

def main(page: ft.Page) -> None:
    build_showcase(page, ShowcaseProfile(title="FletPlus Web Showcase", eyebrow="web", description="Demo optimizada para navegador: hero amplio, grilla fluida, assets SVG y navegación adaptable.", width=1280, platform_label="FletPlus Web"))

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, assets_dir="examples/assets")
