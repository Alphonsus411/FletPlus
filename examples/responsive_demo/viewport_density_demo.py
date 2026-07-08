"""Demo de orientación, perfil activo y densidad visual con helpers de viewport."""

from __future__ import annotations

import flet as ft

from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.utils.viewport import viewport_info


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
        info = viewport_info(page, fallback_width=390, fallback_height=844)
        panel.padding = info.padding
        status.value = "Redimensiona la ventana o rota el dispositivo para actualizar los valores."
        metrics.controls = [
            _metric("Viewport", f"{info.width} × {info.height}"),
            _metric("Orientación", info.orientation),
            _metric("Perfil", f"{info.profile.name} · {info.profile.columns} columnas"),
            _metric("Densidad", info.density),
            _metric("Padding", str(info.padding)),
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
