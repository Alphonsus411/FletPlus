"""Showcase frontend para escritorio con navegación lateral adaptable."""
from __future__ import annotations
import flet as ft
from examples.frontend_showcase_common import ShowcaseProfile, build_showcase

def main(page: ft.Page) -> None:
    build_showcase(page, ShowcaseProfile(title="FletPlus Desktop Showcase", eyebrow="desktop", description="Demo de escritorio con densidad cómoda, panel de métricas, tarjetas y estados reutilizables.", width=1180, platform_label="FletPlus Desktop"))

if __name__ == "__main__":
    ft.app(target=main, assets_dir="examples/assets")
