"""Configuración FrontEnd reutilizable para apps FletPlus."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import flet as ft

from fletplus.themes import ThemeManager, get_palette_tokens, has_palette
from fletplus.utils.device_profiles import (
    DEFAULT_DEVICE_PROFILES,
    DeviceProfile,
    columns_for_width,
    get_device_profile,
)


@dataclass(slots=True)
class FrontEndConfig:
    """Agrupa decisiones visuales habituales para una aplicación FletPlus.

    La configuración concentra paleta, fuentes, breakpoints, dimensiones y
    densidad de layout para que las plantillas web, desktop y mobile partan de
    una misma metodología visual.
    """

    palette: str = "material"
    mode: str = "light"
    font_family: str | None = None
    font_assets: Mapping[str, str] = field(default_factory=dict)
    page_padding: int = 24
    max_content_width: int = 1200
    min_content_width: int = 320
    spacing: int = 16
    responsive_profiles: Sequence[DeviceProfile] = DEFAULT_DEVICE_PROFILES
    layout_density: str = "comfortable"
    theme_tokens: Mapping[str, Mapping[str, object]] = field(default_factory=dict)

    def palette_tokens(self) -> dict[str, object]:
        """Devuelve tokens de paleta si la paleta existe; si no, un dict vacío."""

        if has_palette(self.palette):
            return dict(get_palette_tokens(self.palette, self.mode))
        return {}

    def resolve_device_profile(self, width: int) -> DeviceProfile:
        """Selecciona el perfil de dispositivo activo para un ancho dado."""

        return get_device_profile(width, self.responsive_profiles)

    def columns_for_width(self, width: int) -> int:
        """Devuelve columnas sugeridas para un ancho de pantalla."""

        return columns_for_width(width, self.responsive_profiles)

    def content_width_for_page(self, page: ft.Page) -> int:
        """Calcula el ancho máximo seguro del contenido principal."""

        width = int(page.width or self.max_content_width)
        return max(
            self.min_content_width,
            min(width - (self.page_padding * 2), self.max_content_width),
        )

    def apply_to_page(self, page: ft.Page) -> ThemeManager:
        """Aplica fuente, tema y espaciado base sobre una página Flet."""

        if self.font_assets:
            page.fonts = {**getattr(page, "fonts", {}), **dict(self.font_assets)}
        if self.font_family:
            page.theme = ft.Theme(font_family=self.font_family)

        page.padding = self.page_padding
        theme_manager = ThemeManager(page, palette=self.palette, palette_mode=self.mode)
        for group, values in self.theme_tokens.items():
            for key, value in values.items():
                theme_manager.set_token(group, key, value)
        theme_manager.apply_theme()
        return theme_manager

    def build_content_shell(self, control: ft.Control, page: ft.Page) -> ft.Container:
        """Envuelve un control en un contenedor responsivo centrado."""

        return ft.Container(
            content=control,
            width=self.content_width_for_page(page),
            padding=self.page_padding,
            alignment=getattr(getattr(ft, "alignment", object()), "center", None),
        )
