"""Demo de orientación, perfil activo y densidad visual con helpers de viewport."""

from __future__ import annotations

import flet as ft

from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.utils.viewport import (
    active_device_profile,
    safe_mobile_padding,
    safe_page_height,
    safe_page_width,
    viewport_orientation,
    visual_density_for_page,
)


def _metric(label: str, value: str) -> ft.Control:
    return ft.Container(
        padding=12,
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.PRIMARY),
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text(label, size=12, weight=ft.FontWeight.W_600),
                ft.Text(value, size=18),
            ],
        ),
    )


def main(page: ft.Page) -> None:
    page.title = "FletPlus viewport responsive demo"
    status = ft.Text(size=14)
    metrics = ft.Row(wrap=True, spacing=12, run_spacing=12)
    panel = ft.Container(border_radius=18, content=metrics)

    def sync(_: object | None = None) -> None:
        width = safe_page_width(page, fallback=390)
        height = safe_page_height(page, fallback=844)
        profile = active_device_profile(page)
        orientation = viewport_orientation(page)
        density = visual_density_for_page(page)
        panel.padding = safe_mobile_padding(page)
        status.value = "Redimensiona la ventana o rota el dispositivo para actualizar los valores."
        metrics.controls = [
            _metric("Viewport", f"{width} × {height}"),
            _metric("Orientación", orientation),
            _metric("Perfil", f"{profile.name} · {profile.columns} columnas"),
            _metric("Densidad", density),
            _metric("Padding", str(panel.padding)),
        ]
        page.update()

    ResponsiveManager(
        page,
        orientation_callbacks={"portrait": sync, "landscape": sync},
        device_callbacks={"mobile": sync, "tablet": sync, "desktop": sync},
    )
    page.add(
        ft.Text("Viewport helpers", size=28, weight=ft.FontWeight.W_700),
        status,
        panel,
    )
    sync()


if __name__ == "__main__":
    ft.app(target=main)
