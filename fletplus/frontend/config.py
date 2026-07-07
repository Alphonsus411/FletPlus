"""Configuración FrontEnd reutilizable para apps FletPlus."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    allow_min_width_overflow: bool = False
    spacing: int = 16
    responsive_profiles: Sequence[DeviceProfile] = DEFAULT_DEVICE_PROFILES
    layout_density: str = "comfortable"
    theme_tokens: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    follow_platform_theme: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "FrontEndConfig":
        """Crea configuración visual desde un mapping declarativo seguro.

        Acepta las claves usadas por ``[tool.fletplus.frontend]`` y descarta
        valores desconocidos para que las plantillas puedan crecer sin romper
        versiones anteriores de FletPlus.
        """

        allowed = {
            "palette",
            "mode",
            "font_family",
            "font_assets",
            "page_padding",
            "max_content_width",
            "min_content_width",
            "allow_min_width_overflow",
            "spacing",
            "layout_density",
            "theme_tokens",
            "follow_platform_theme",
        }
        normalized = {key: value for key, value in data.items() if key in allowed}
        return cls(**normalized)

    @classmethod
    def from_pyproject(cls, path: str | Path = "pyproject.toml") -> "FrontEndConfig":
        """Carga ``[tool.fletplus.frontend]`` desde un ``pyproject.toml``.

        Si el archivo no existe o no declara la sección, devuelve la
        configuración por defecto.
        """

        pyproject_path = Path(path)
        if not pyproject_path.exists():
            return cls()

        try:
            import tomllib
        except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
            import tomli as tomllib  # type: ignore

        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        tool_data = data.get("tool", {}) if isinstance(data, dict) else {}
        fletplus_data = (
            tool_data.get("fletplus", {}) if isinstance(tool_data, dict) else {}
        )
        frontend_data = (
            fletplus_data.get("frontend", {}) if isinstance(fletplus_data, dict) else {}
        )
        if not isinstance(frontend_data, Mapping):
            return cls()
        return cls.from_mapping(frontend_data)

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
        available_width = max(0, width - (self.page_padding * 2))
        content_width = min(available_width, self.max_content_width)
        if self.allow_min_width_overflow:
            return max(self.min_content_width, content_width)
        return content_width

    def apply_to_page(self, page: ft.Page) -> ThemeManager:
        """Aplica fuente, tema, modo visual y espaciado base sobre una página Flet."""

        if self.font_assets:
            page.fonts = {**getattr(page, "fonts", {}), **dict(self.font_assets)}
        if self.font_family:
            theme = page.theme or ft.Theme()
            try:
                theme.font_family = self.font_family
            except AttributeError:
                theme = ft.Theme(font_family=self.font_family)
            page.theme = theme

        theme = page.theme or ft.Theme()
        try:
            if getattr(theme, "visual_density", None) is None:
                theme.visual_density = self.layout_density
        except AttributeError:
            pass
        page.theme = theme
        page.padding = self.page_padding

        theme_manager = ThemeManager(
            page,
            palette=self.palette,
            palette_mode=self.mode,
            follow_platform_theme=self.follow_platform_theme,
        )
        for group, values in self.theme_tokens.items():
            for key, value in values.items():
                theme_manager.set_token(f"{group}.{key}", value)
        theme_manager.apply_theme(
            device=self.resolve_device_profile(
                int(getattr(page, "width", 0) or self.max_content_width)
            ).name,
            orientation=self.orientation_for_page(page),
            width=getattr(page, "width", None),
        )
        return theme_manager

    def orientation_for_page(self, page: ft.Page) -> str:
        """Devuelve ``portrait`` o ``landscape`` según dimensiones actuales."""

        width = int(getattr(page, "width", 0) or 0)
        height = int(getattr(page, "height", 0) or 0)
        return "portrait" if height >= width else "landscape"

    def build_content_shell(self, control: ft.Control, page: ft.Page) -> ft.Container:
        """Envuelve un control en un contenedor responsivo centrado."""

        return ft.Container(
            content=control,
            width=self.content_width_for_page(page),
            padding=self.page_padding,
            alignment=getattr(getattr(ft, "alignment", object()), "center", None),
        )
