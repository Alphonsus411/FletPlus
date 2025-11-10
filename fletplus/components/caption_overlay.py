"""Superposición de subtítulos accesibles para cualquier plataforma."""

from __future__ import annotations

from typing import Literal

import flet as ft


CaptionTone = Literal["info", "success", "warning", "error"]

_TONE_COLORS: dict[CaptionTone, str] = {
    "info": ft.Colors.with_opacity(0.95, ft.Colors.BLUE_GREY_900),
    "success": ft.Colors.with_opacity(0.95, ft.Colors.GREEN_900),
    "warning": ft.Colors.with_opacity(0.95, ft.Colors.AMBER_900),
    "error": ft.Colors.with_opacity(0.95, ft.Colors.RED_900),
}

_TONE_ICONS: dict[CaptionTone, str] = {
    "info": ft.Icons.CLOSED_CAPTION,
    "success": ft.Icons.VERIFIED_OUTLINED,
    "warning": ft.Icons.WARNING_AMBER_OUTLINED,
    "error": ft.Icons.ERROR_OUTLINE,
}


class CaptionOverlay:
    """Presenta mensajes accesibles compatibles con lectores de pantalla."""

    def __init__(
        self,
        *,
        max_messages: int = 2,
        text_color: str = ft.Colors.WHITE,
        semantics_label: str = "Mensajes accesibles",
    ) -> None:
        if max_messages <= 0:
            raise ValueError("max_messages debe ser mayor que cero")

        self.max_messages = max_messages
        self.text_color = text_color
        self.semantics_label = semantics_label

        self._page: ft.Page | None = None
        self._messages = ft.Column(spacing=6, tight=True)
        self._panel = ft.Container(
            content=self._messages,
            bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.BLACK),
            border_radius=12,
            padding=ft.Padding(16, 12, 16, 12),
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.with_opacity(0.35, ft.Colors.BLACK)),
            opacity=0.98,
        )
        self._host = ft.Container(
            alignment=ft.alignment.bottom_center,
            padding=ft.Padding(12, 12, 12, 24),
            visible=False,
            data="caption-overlay",
        )
        self._host.content = ft.Semantics(
            label=self.semantics_label,
            focusable=False,
            container=True,
            content=self._panel,
        )
        self._enabled = True

    @property
    def control(self) -> ft.Container:
        """Control raíz que debe añadirse a un ``Stack``."""

        return self._host

    def build(self, page: ft.Page) -> ft.Control:
        """Asocia la superposición a ``page`` y devuelve el control raíz."""

        self._page = page
        return self.control

    def set_enabled(self, enabled: bool) -> None:
        """Activa o desactiva la visualización de mensajes."""

        self._enabled = bool(enabled)
        if not self._enabled:
            self.clear()

    def announce(self, message: str, *, tone: CaptionTone = "info") -> None:
        """Muestra ``message`` en la superposición y lo vuelve legible."""

        if not message:
            return
        tone = tone if tone in _TONE_COLORS else "info"
        if not self._enabled:
            return

        indicator = ft.Container(
            width=6,
            bgcolor=_TONE_COLORS[tone],
            border_radius=6,
        )
        icon = ft.Icon(_TONE_ICONS[tone], color=self.text_color, size=18)
        text = ft.Text(message, color=self.text_color, selectable=True, no_wrap=False)
        row = ft.Row(
            controls=[
                indicator,
                ft.Container(width=8),
                icon,
                ft.Container(width=8),
                ft.Container(content=text, expand=True),
            ],
            tight=True,
        )

        self._messages.controls.insert(0, row)
        if len(self._messages.controls) > self.max_messages:
            self._messages.controls = self._messages.controls[: self.max_messages]

        self._host.visible = True
        if self._page:
            self._page.update()

    def clear(self) -> None:
        """Elimina todos los mensajes visibles."""

        self._messages.controls.clear()
        self._host.visible = False
        if self._page:
            self._page.update()
