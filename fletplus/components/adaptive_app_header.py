"""Cabecera adaptable con gradientes y disposición responsiva.

Este módulo incorpora :class:`AdaptiveAppHeader`, un contenedor decorativo
pensado para encabezados de páginas o secciones principales. El componente
ajusta tipografías, distribución de acciones y metadatos en función del ancho
de la ventana, ofreciendo una experiencia coherente en web, escritorio y
smartphones. Además, aprovecha los *tokens* de :class:`~fletplus.themes.theme_manager.ThemeManager`
para aplicar fondos degradados y colores semánticos coherentes con la paleta
activa.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, MutableMapping, Sequence

import flet as ft

from fletplus.themes.theme_manager import ThemeManager
from fletplus.utils.responsive_manager import ResponsiveManager


DeviceName = str


def _device_from_width(width: int) -> DeviceName:
    if width < 640:
        return "mobile"
    if width < 960:
        return "tablet"
    return "desktop"


def _as_padding(value: object) -> ft.Padding | None:
    if value is None:
        return None
    if isinstance(value, ft.Padding):
        return value
    if isinstance(value, Mapping):
        try:
            return ft.Padding(
                float(value.get("left", 0)),
                float(value.get("top", 0)),
                float(value.get("right", 0)),
                float(value.get("bottom", 0)),
            )
        except (TypeError, ValueError):  # pragma: no cover - validación defensiva
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return ft.Padding(number, number, number, number)


def _clone_padding(padding: ft.Padding | None) -> ft.Padding | None:
    if padding is None:
        return None
    return ft.Padding(padding.left, padding.top, padding.right, padding.bottom)


@dataclass(slots=True)
class MetadataBadge:
    """Representa una insignia o *pill* mostrada bajo el título."""

    control: ft.Control
    tooltip: str | None = None


class AdaptiveAppHeader:
    """Cabecera visual adaptable para aplicaciones Flet."""

    def __init__(
        self,
        *,
        title: str,
        subtitle: str | None = None,
        supporting_text: str | None = None,
        hero: ft.Control | None = None,
        breadcrumbs: Sequence[ft.Control] | None = None,
        metadata: Sequence[MetadataBadge] | None = None,
        actions: Sequence[ft.Control] | None = None,
        theme: ThemeManager | None = None,
        gradient_token: str | None = "app_header",
        background_color: str | None = None,
        padding: ft.Padding
        | int
        | float
        | Mapping[str, float]
        | MutableMapping[str, float]
        | Dict[str, object]
        | None = None,
        corner_radius: float | ft.BorderRadius | None = 24,
        shadow: ft.BoxShadow | Sequence[ft.BoxShadow] | None = None,
        max_content_width: float | int | None = 1280,
    ) -> None:
        self.title = title
        self.subtitle = subtitle
        self.supporting_text = supporting_text
        self.hero = hero
        self.breadcrumbs = list(breadcrumbs or [])
        self.metadata = list(metadata or [])
        self.actions = list(actions or [])
        self.theme = theme
        self.gradient_token = gradient_token
        self.background_color = background_color
        self.corner_radius = corner_radius
        self.shadow = shadow
        self.max_content_width = max_content_width

        self._padding_config: Dict[DeviceName, ft.Padding | None]
        if isinstance(padding, dict):
            self._padding_config = {
                str(device): _as_padding(value)
                for device, value in padding.items()
            }
        else:
            shared_padding = _as_padding(padding) or ft.Padding(24, 24, 24, 24)
            self._padding_config = {
                "mobile": shared_padding,
                "tablet": shared_padding,
                "desktop": ft.Padding(
                    shared_padding.left * 1.5,
                    shared_padding.top * 1.5,
                    shared_padding.right * 1.5,
                    shared_padding.bottom * 1.5,
                ),
            }

        self._page: ft.Page | None = None
        self._manager: ResponsiveManager | None = None

        self._container = ft.Container()
        self._background = ft.Container()

        if max_content_width:
            inner_container = ft.Container(width=max_content_width)
            inner_container.content = ft.Column(spacing=16, tight=True)
            self._content_column = inner_container.content
            wrapper = ft.Column(
                controls=[inner_container],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            self._background.content = wrapper
        else:
            self._content_column = ft.Column(spacing=16, tight=True)
            self._background.content = self._content_column

        self._container.content = self._background

        # Controles reutilizables
        self._title_text = ft.Text(self.title, weight=ft.FontWeight.W_700)
        self._subtitle_text = (
            ft.Text(self.subtitle, weight=ft.FontWeight.W_500)
            if self.subtitle
            else None
        )
        self._supporting_text_control = (
            ft.Text(self.supporting_text, opacity=0.92)
            if self.supporting_text
            else None
        )
        self._breadcrumbs_row = (
            ft.Row(controls=list(self.breadcrumbs), spacing=12, wrap=True)
            if self.breadcrumbs
            else None
        )
        self._actions_row = (
            ft.Row(controls=list(self.actions), spacing=12, wrap=True)
            if self.actions
            else ft.Row(spacing=12, wrap=True)
        )
        self._metadata_row = ft.Row(
            controls=[self._wrap_badge(badge) for badge in self.metadata],
            spacing=12,
            run_spacing=8,
            wrap=True,
        )
        self._hero_host = ft.Container(content=self.hero) if self.hero else None

    # ------------------------------------------------------------------
    def build(self, page: ft.Page) -> ft.Control:
        self._page = page
        self._apply_theme()
        self._update_layout(page.width or 0)

        breakpoints = {0: self._update_layout, 640: self._update_layout, 960: self._update_layout}
        self._manager = ResponsiveManager(page, breakpoints)

        return self._container

    # ------------------------------------------------------------------
    def _wrap_badge(self, badge: MetadataBadge) -> ft.Control:
        control = badge.control
        if badge.tooltip:
            return ft.Tooltip(content=control, message=badge.tooltip)
        return control

    # ------------------------------------------------------------------
    def _resolve_padding(self, device: DeviceName) -> ft.Padding:
        padding = self._padding_config.get(device)
        if padding is None:
            padding = self._padding_config.get("mobile") or ft.Padding(24, 24, 24, 24)
        return _clone_padding(padding) or ft.Padding(24, 24, 24, 24)

    # ------------------------------------------------------------------
    def _apply_theme(self) -> None:
        if not self.theme:
            if self.background_color:
                self._background.bgcolor = self.background_color
            return

        gradient = None
        if self.gradient_token:
            gradient = self.theme.get_gradient(self.gradient_token)

        start_color = self.theme.get_color("gradient_app_header_start")
        end_color = self.theme.get_color("gradient_app_header_end")

        if gradient is None and start_color and end_color:
            gradient = ft.LinearGradient(
                colors=[start_color, end_color],
                begin=ft.alignment.Alignment(0, -1),
                end=ft.alignment.Alignment(0, 1),
            )

        background = (
            self.background_color
            or self.theme.get_color("surface_variant")
            or self.theme.get_color("surface")
            or self.theme.get_color("primary")
        )

        self._background.gradient = gradient
        self._background.bgcolor = None if gradient else background

        if isinstance(self.corner_radius, ft.BorderRadius):
            self._background.border_radius = self.corner_radius
        elif self.corner_radius is not None:
            self._background.border_radius = ft.border_radius.all(self.corner_radius)

        if self.shadow is None:
            self._background.shadow = ft.BoxShadow(
                blur_radius=24,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.14, "#000000"),
                offset=ft.Offset(0, 12),
            )
        else:
            self._background.shadow = self.shadow

    # ------------------------------------------------------------------
    def _update_layout(self, width: int) -> None:
        device = _device_from_width(width)

        padding = self._resolve_padding(device)
        self._background.padding = padding

        title_sizes = {"mobile": 26, "tablet": 30, "desktop": 36}
        subtitle_sizes = {"mobile": 16, "tablet": 18, "desktop": 20}

        self._title_text.size = title_sizes.get(device, 30)
        self._title_text.opacity = 0.98

        if self._subtitle_text:
            self._subtitle_text.size = subtitle_sizes.get(device, 18)
            self._subtitle_text.opacity = 0.92

        if self._supporting_text_control:
            self._supporting_text_control.size = 14 if device == "mobile" else 16
            self._supporting_text_control.opacity = 0.85

        controls: list[ft.Control] = []

        if self._breadcrumbs_row and self._breadcrumbs_row.controls:
            self._breadcrumbs_row.alignment = (
                ft.MainAxisAlignment.CENTER if device == "mobile" else ft.MainAxisAlignment.START
            )
            controls.append(self._breadcrumbs_row)

        title_block_controls: list[ft.Control] = [self._title_text]

        if self._subtitle_text:
            title_block_controls.append(self._subtitle_text)
        if self._supporting_text_control:
            title_block_controls.append(self._supporting_text_control)

        title_block = ft.Column(
            controls=title_block_controls,
            spacing=4,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        metadata_visible = [badge for badge in self._metadata_row.controls if badge is not None]
        if metadata_visible:
            self._metadata_row.alignment = (
                ft.MainAxisAlignment.CENTER if device == "mobile" else ft.MainAxisAlignment.START
            )
            self._metadata_row.spacing = 12 if device != "mobile" else 8
            controls.append(title_block)
            controls.append(self._metadata_row)
        else:
            controls.append(title_block)

        actions_present = bool(self._actions_row.controls)
        self._actions_row.alignment = (
            ft.MainAxisAlignment.CENTER if device == "mobile" else ft.MainAxisAlignment.END
        )

        if actions_present:
            if device == "desktop":
                header_layout = ft.Row(
                    controls=[
                        ft.Column(controls=controls, spacing=12, tight=True),
                        ft.Container(expand=1),
                        self._actions_row,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
                self._content_column.controls.clear()
                self._content_column.controls.append(header_layout)
            elif device == "tablet":
                header_layout = ft.Row(
                    controls=[
                        ft.Column(controls=controls, spacing=12, tight=True, expand=True),
                        ft.Container(width=16),
                        self._actions_row,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                )
                self._content_column.controls.clear()
                self._content_column.controls.append(header_layout)
            else:
                self._content_column.controls.clear()
                self._content_column.controls.append(
                    ft.Column(
                        controls=controls + [self._actions_row],
                        spacing=12,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )
        else:
            self._content_column.controls.clear()
            self._content_column.controls.append(
                ft.Column(controls=controls, spacing=12, tight=True)
            )

        if self._hero_host:
            hero_container = ft.Container(content=self._hero_host.content)
            hero_container.width = None
            hero_container.padding = ft.Padding(0, 12, 0, 0)
            if device == "mobile":
                hero_container.padding = ft.Padding(0, 16, 0, 0)
            self._content_column.controls.append(hero_container)

        if self._page is not None:
            self._page.update()

