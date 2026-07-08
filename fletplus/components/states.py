"""Componentes semánticos para representar estados de interfaz.

Los estados comparten una base visual centrada y consumen tokens de
``ThemeManager``/``FrontEndConfig`` para mantener colores, spacing y tipografía
alineados con el resto de FletPlus.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

import flet as ft

from fletplus.frontend.config import FrontEndConfig
from fletplus.utils.flet_compat import get_page_width

if TYPE_CHECKING:
    from fletplus.themes.theme_manager import ThemeManager

SpacingValue = int | float | ft.Padding | Mapping[str, int | float] | None


def _token(
    theme: "ThemeManager | None",
    group: str,
    name: str,
    default: object = None,
) -> object:
    if theme is None:
        return default
    tokens = getattr(theme, "tokens", {})
    effective = getattr(theme, "_effective_tokens", tokens)
    if isinstance(effective, Mapping):
        group_tokens = effective.get(group, {})
        if isinstance(group_tokens, Mapping) and name in group_tokens:
            return group_tokens[name]
    if isinstance(tokens, Mapping):
        group_tokens = tokens.get(group, {})
        if isinstance(group_tokens, Mapping):
            return group_tokens.get(name, default)
    return default


def _color(
    theme: "ThemeManager | None",
    token: str | None,
    default: str | None = None,
) -> str | None:
    if not token:
        return default
    if theme is not None:
        value = theme.get_color(token, None)
        if isinstance(value, str):
            return value
    return default if default is not None else token


def _number(value: object, default: int | float) -> int | float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _padding(value: SpacingValue, fallback: int | float) -> ft.Padding:
    if isinstance(value, ft.Padding):
        return value
    if isinstance(value, Mapping):
        return ft.Padding(
            _number(value.get("left"), fallback),
            _number(value.get("top"), fallback),
            _number(value.get("right"), fallback),
            _number(value.get("bottom"), fallback),
        )
    amount = _number(value, fallback) if value is not None else fallback
    return ft.Padding(amount, amount, amount, amount)


@dataclass(slots=True)
class StateComponent:
    """Base reusable para mensajes de estado con acciones opcionales."""

    title: str
    description: str | None = None
    icon: str | None = None
    primary_action: ft.Control | None = None
    secondary_action: ft.Control | None = None
    config: FrontEndConfig | None = None
    theme: "ThemeManager | None" = None
    color_token: str | None = None
    icon_color: str | None = None
    bgcolor_token: str | None = "surface_soft"
    bgcolor: str | None = None
    spacing: int | None = None
    padding: SpacingValue = None
    max_width: int | None = 520
    icon_size: int | float | None = None
    border_radius: int | float | ft.BorderRadius | None = 24

    default_icon: str = ft.Icons.INFO_OUTLINE
    default_color_token: str = "info"

    def build(self, page: ft.Page) -> ft.Container:
        """Construye el control Flet usando tokens de diseño disponibles."""
        cfg = self.config or FrontEndConfig()
        width = get_page_width(page)
        theme_spacing = _token(self.theme, "spacing", "default", cfg.spacing)
        resolved_spacing = int(
            self.spacing
            if self.spacing is not None
            else _number(theme_spacing, cfg.spacing)
        )
        resolved_padding = _padding(
            self.padding, max(resolved_spacing * 2, cfg.page_padding)
        )
        color_token = self.color_token or self.default_color_token
        accent_color = _color(self.theme, color_token, self.icon_color)
        icon_color = self.icon_color or accent_color
        bg = _color(self.theme, self.bgcolor_token, self.bgcolor)
        title_style = cfg.text_style("title", width)
        body_style = cfg.text_style("body", width)
        icon_size = self.icon_size or _number(
            _token(self.theme, "typography", "state_icon_size", 56), 56
        )

        controls: list[ft.Control] = [
            ft.Icon(self.icon or self.default_icon, size=icon_size, color=icon_color),
            ft.Text(self.title, style=title_style, text_align=ft.TextAlign.CENTER),
        ]
        if self.description:
            controls.append(
                ft.Text(
                    self.description, style=body_style, text_align=ft.TextAlign.CENTER
                )
            )

        actions = [
            control
            for control in (self.primary_action, self.secondary_action)
            if control is not None
        ]
        if actions:
            controls.append(
                ft.Row(
                    actions,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=max(8, resolved_spacing),
                    wrap=True,
                )
            )

        return ft.Container(
            width=self.max_width,
            padding=resolved_padding,
            bgcolor=bg,
            border_radius=self.border_radius,
            alignment=ft.alignment.center,
            content=ft.Column(
                controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=resolved_spacing,
                tight=True,
            ),
        )


@dataclass(slots=True)
class LoadingState(StateComponent):
    """Estado de carga para procesos en curso."""

    title: str = "Cargando"
    description: str | None = "Estamos preparando el contenido."
    default_icon: str = ft.Icons.HOURGLASS_EMPTY
    default_color_token: str = "primary"


@dataclass(slots=True)
class EmptyState(StateComponent):
    """Estado vacío para colecciones sin datos."""

    title: str = "Sin resultados"
    description: str | None = "No hay elementos para mostrar todavía."
    default_icon: str = ft.Icons.INBOX_OUTLINED
    default_color_token: str = "info"


@dataclass(slots=True)
class ErrorState(StateComponent):
    """Estado de error con acción de recuperación opcional."""

    title: str = "Algo salió mal"
    description: str | None = (
        "Intenta nuevamente o contacta con soporte si el problema continúa."
    )
    default_icon: str = ft.Icons.ERROR_OUTLINE
    default_color_token: str = "error"


@dataclass(slots=True)
class SuccessState(StateComponent):
    """Estado de confirmación para operaciones completadas."""

    title: str = "Operación completada"
    description: str | None = "Los cambios se guardaron correctamente."
    default_icon: str = ft.Icons.CHECK_CIRCLE_OUTLINE
    default_color_token: str = "success"


@dataclass(slots=True)
class PermissionState(StateComponent):
    """Estado para accesos restringidos o permisos insuficientes."""

    title: str = "Permiso requerido"
    description: str | None = "Necesitas autorización para acceder a esta sección."
    default_icon: str = ft.Icons.LOCK_OUTLINE
    default_color_token: str = "warning"


@dataclass(slots=True)
class MaintenanceState(StateComponent):
    """Estado para pantallas temporalmente no disponibles."""

    title: str = "Mantenimiento programado"
    description: str | None = "Volveremos pronto con mejoras para la experiencia."
    default_icon: str = ft.Icons.CONSTRUCTION_OUTLINED
    default_color_token: str = "warning"


__all__ = [
    "StateComponent",
    "LoadingState",
    "EmptyState",
    "ErrorState",
    "SuccessState",
    "PermissionState",
    "MaintenanceState",
]
