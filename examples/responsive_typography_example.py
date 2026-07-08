"""Ejemplo de textos que cambian de tamaño según el ancho de la ventana."""

from __future__ import annotations

import flet as ft

from examples._bootstrap import bootstrap
from fletplus import FrontEndConfig
from fletplus.utils.responsive_typography import ResponsiveTypography

bootstrap()


def main(page: ft.Page) -> None:
    config = FrontEndConfig()
    theme = config.apply_to_page(page)
    typography = ResponsiveTypography(page, theme=theme, config=config)

    width_label = ft.Text()
    samples = [
        ("display", "Display: hero principal"),
        ("headline", "Headline: sección destacada"),
        ("title", "Title: título de tarjeta"),
        ("body", "Body: párrafo legible y adaptable."),
        ("label", "Label: acción o metadato"),
        ("caption", "Caption: ayuda contextual"),
    ]
    controls: list[ft.Text] = []
    for role, value in samples:
        text = ft.Text(value)
        typography.register_text(text, role=role)
        controls.append(text)

    panel = ft.Container(
        padding=config.spacing,
        content=ft.Column([width_label, *controls], spacing=config.spacing),
    )
    typography.register_spacing_control(panel)

    def sync(_: ft.ControlEvent | None = None) -> None:
        width = int(page.width or 0)
        profile = config.resolve_device_profile(width).name
        width_label.value = f"Ancho: {width}px · perfil: {profile}"
        page.update()

    page.on_resize = sync
    page.add(config.build_content_shell(panel, page))
    sync()


if __name__ == "__main__":
    ft.app(target=main)
