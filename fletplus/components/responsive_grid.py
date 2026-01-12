"""Grid responsiva con soporte para span adaptable y estilos por dispositivo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence

import flet as ft

from fletplus.components.responsive_grid_rs import (
    plan_items as _plan_grid_items_native,
    plan_items_from_objects as _plan_grid_items_native_from_objects,
)
from fletplus.styles import Style
from fletplus.themes.theme_manager import ThemeManager
from fletplus.utils.responsive_breakpoints import BreakpointRegistry
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.utils.responsive_style import ResponsiveStyle
from fletplus.utils.device_profiles import (
    DeviceProfile,
    EXTENDED_DEVICE_PROFILES,
    get_device_profile,
    iter_device_profiles,
)


DeviceName = str


_GRADIENT_TYPES: tuple[type, ...] = tuple(
    cls
    for cls in (
        getattr(ft, "Gradient", None),
        getattr(ft, "LinearGradient", None),
        getattr(ft, "RadialGradient", None),
    )
    if isinstance(cls, type)
)


def _as_padding(value: object) -> ft.Padding | None:
    if value is None:
        return None
    if isinstance(value, ft.Padding):
        return value
    if isinstance(value, dict):
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


def _as_margin(value: object) -> ft.Margin | None:
    if value is None:
        return None
    if isinstance(value, ft.Margin):
        return value
    if isinstance(value, dict):
        try:
            return ft.Margin(
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
    return ft.Margin(number, number, number, number)


def _clone_padding(padding: ft.Padding | None) -> ft.Padding | None:
    if padding is None:
        return None
    return ft.Padding(padding.left, padding.top, padding.right, padding.bottom)


def _clone_margin(margin: ft.Margin | None) -> ft.Margin | None:
    if margin is None:
        return None
    return ft.Margin(margin.left, margin.top, margin.right, margin.bottom)


def _parse_main_axis_alignment(
    value: ft.MainAxisAlignment | str | None,
) -> ft.MainAxisAlignment | None:
    if value is None:
        return None
    if isinstance(value, ft.MainAxisAlignment):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        mapping = {
            "start": ft.MainAxisAlignment.START,
            "end": ft.MainAxisAlignment.END,
            "center": ft.MainAxisAlignment.CENTER,
            "spacebetween": ft.MainAxisAlignment.SPACE_BETWEEN,
            "space_between": ft.MainAxisAlignment.SPACE_BETWEEN,
            "spacearound": ft.MainAxisAlignment.SPACE_AROUND,
            "space_around": ft.MainAxisAlignment.SPACE_AROUND,
            "spaceevenly": ft.MainAxisAlignment.SPACE_EVENLY,
            "space_evenly": ft.MainAxisAlignment.SPACE_EVENLY,
        }
        return mapping.get(normalized)
    return None


def _normalize_device_name(value: DeviceName | None) -> DeviceName | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


@dataclass
class ResponsiveGridItem:
    """Describe un elemento con span adaptable dentro del grid.

    Parameters
    ----------
    control:
        Control a renderizar.
    span:
        Columna base en un sistema de 12 columnas. Si no se indica se ajusta
        automáticamente según ``columns``.
    span_breakpoints:
        Diccionario ``{ancho_minimo: span}`` para ajustar la distribución en
        función del tamaño de pantalla.
    span_devices:
        Diccionario ``{"mobile"|"tablet"|"desktop"|"large_desktop": span}`` que permite
        personalizar aún más cada dispositivo.
    style:
        Estilo opcional aplicado al contenedor del item.
    responsive_style:
        Instancia de :class:`ResponsiveStyle` aplicada automáticamente cuando el
        grid se registra mediante :meth:`ResponsiveGrid.init_responsive`.
    visible_devices:
        Lista de dispositivos donde el item debe mostrarse. Si se define tiene
        prioridad sobre ``hidden_devices``.
    hidden_devices:
        Lista de dispositivos donde el item no debe renderizarse.
    min_width / max_width:
        Límites de ancho (en px) para mostrar el item independientemente del
        dispositivo detectado.
    """

    control: ft.Control
    span: int | None = None
    span_breakpoints: Mapping[int | str, int] | None = None
    span_devices: Dict[DeviceName, int] | None = None
    style: Style | None = None
    responsive_style: ResponsiveStyle | Dict[int, Style] | None = None
    visible_devices: Sequence[DeviceName] | DeviceName | None = None
    hidden_devices: Sequence[DeviceName] | DeviceName | None = None
    min_width: int | None = None
    max_width: int | None = None

    def __post_init__(self) -> None:
        self.visible_devices = self._normalize_device_sequence(self.visible_devices)
        self.hidden_devices = self._normalize_device_sequence(self.hidden_devices)
        self.min_width = self._sanitize_dimension(self.min_width)
        self.max_width = self._sanitize_dimension(self.max_width)
        if self.span_breakpoints:
            normalized = BreakpointRegistry.normalize(self.span_breakpoints)
            self.span_breakpoints = {
                bp: self._sanitize_span(value) for bp, value in normalized.items()
            }

    def resolve_span(
        self, width: int, columns: int, device: DeviceName | None = None
    ) -> int:
        """Determina el span considerando un dispositivo normalizado.

        Si no se proporciona ``device``, se deriva a partir de ``width`` usando
        :func:`get_device_profile`, que toma como referencia los perfiles por
        defecto. El nombre se normaliza en minúsculas para facilitar coincidencias
        con ``span_devices``.
        """

        normalized_device = _normalize_device_name(device)
        if normalized_device is None:
            normalized_device = get_device_profile(width).name
        if self.span_devices and normalized_device in self.span_devices:
            return self._sanitize_span(self.span_devices[normalized_device])

        if self.span_breakpoints:
            bp = max((bp for bp in self.span_breakpoints if width >= bp), default=None)
            if bp is not None:
                return self._sanitize_span(self.span_breakpoints[bp])

        if self.span is not None:
            return self._sanitize_span(self.span)

        return max(1, int(12 / max(1, columns)))

    @staticmethod
    def _sanitize_span(value: int) -> int:
        try:
            value = int(value)
        except (TypeError, ValueError):  # pragma: no cover - validación defensiva
            value = 12
        return max(1, min(12, value))

    @staticmethod
    def _sanitize_dimension(value: object | None) -> int | None:
        if value is None:
            return None
        try:
            number = int(value)
        except (TypeError, ValueError):  # pragma: no cover - validación defensiva
            return None
        return max(0, number)

    @staticmethod
    def _normalize_device_sequence(
        value: Sequence[DeviceName] | DeviceName | None,
    ) -> tuple[DeviceName, ...] | None:
        if value is None:
            return None
        if isinstance(value, str):
            items: Sequence[DeviceName] = [value]
        else:
            items = value
        normalized: list[DeviceName] = []
        for item in items:
            if item is None:
                continue
            text = str(item).strip().lower()
            if not text:
                continue
            if text not in normalized:
                normalized.append(text)
        return tuple(normalized) if normalized else None

    def is_visible(self, width: int, device: DeviceName) -> bool:
        if self.min_width is not None and width < self.min_width:
            return False
        if self.max_width is not None and width > self.max_width:
            return False
        normalized_device = device.lower()
        if self.visible_devices is not None:
            return normalized_device in self.visible_devices
        if self.hidden_devices is not None and normalized_device in self.hidden_devices:
            return False
        return True


@dataclass
class HeaderHighlight:
    """Pequeño bloque de métricas destacado en el encabezado."""

    label: str
    value: str
    icon: str | ft.Control | None = None
    description: str | None = None

    def build_control(
        self,
        theme: ThemeManager | None,
        accent: str,
        device: DeviceName,
    ) -> ft.Control:
        on_surface = None
        muted = None
        if theme:
            on_surface = theme.get_color("on_surface") or theme.get_color("on_background")
            muted = theme.get_color("muted") or theme.get_color("on_surface_variant")
        if not isinstance(on_surface, str):
            on_surface = ft.Colors.BLACK
        if not isinstance(muted, str):
            muted = ft.Colors.GREY_600

        value_size = 22 if device in {"desktop", "large_desktop"} else 18
        label_size = 12
        description_size = 12

        icon_control: ft.Control | None = None
        if isinstance(self.icon, ft.Control):
            icon_control = self.icon
        elif isinstance(self.icon, str) and self.icon:
            icon_control = ft.Icon(
                self.icon,
                size=20 if device != "mobile" else 18,
                color=accent,
            )

        value_text = ft.Text(
            self.value,
            weight=ft.FontWeight.W_600,
            size=value_size,
            color=on_surface,
        )
        label_text = ft.Text(self.label, size=label_size, color=muted)

        body_controls: list[ft.Control] = [value_text, label_text]
        if self.description:
            body_controls.append(
                ft.Text(self.description, size=description_size, color=muted, opacity=0.9)
            )

        column = ft.Column(body_controls, spacing=2, tight=True)
        row_children: list[ft.Control] = [column]
        if icon_control is not None:
            row_children.insert(0, icon_control)

        content_row = ft.Row(
            controls=row_children,
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            wrap=False,
        )

        padding = ft.Padding(18, 16, 18, 16) if device != "mobile" else ft.Padding(14, 12, 14, 12)
        radius = 18 if device != "mobile" else 14

        container = ft.Container(
            content=content_row,
            padding=padding,
            bgcolor=ft.Colors.with_opacity(0.12, accent),
            border_radius=ft.border_radius.all(radius),
            border=ft.border.all(1, ft.Colors.with_opacity(0.28, accent)),
            expand=device in {"desktop", "large_desktop"},
        )
        return container


class ResponsiveGrid:
    def __init__(
        self,
        children: Sequence[ft.Control] | None = None,
        columns: int | None = None,
        breakpoints: Mapping[int | str, int] | None = None,
        spacing: int = 10,
        style: Style | None = None,
        *,
        items: Sequence[ResponsiveGridItem] | None = None,
        run_spacing: int | None = None,
        alignment: ft.MainAxisAlignment | None = None,
        header_title: str | None = None,
        header_subtitle: str | None = None,
        header_description: str | None = None,
        header_icon: str | ft.Control | None = None,
        header_actions: Sequence[ft.Control] | None = None,
        header_metadata: Sequence[ft.Control] | None = None,
        header_tags: Sequence[
            str
            | ft.Control
            | Mapping[str, object]
            | Sequence[object]
        ]
        | None = None,
        header_tag_style: Style | None = None,
        header_tag_spacing: int = 10,
        header_highlights: Sequence[
            HeaderHighlight
            | Mapping[str, object]
            | Sequence[object]
        ]
        | None = None,
        section_padding: Dict[str, object] | ft.Padding | int | float | None = None,
        section_margin: Dict[str, object] | ft.Margin | int | float | None = None,
        section_margin_by_orientation: Dict[str, object] | None = None,
        section_gap: int = 18,
        section_background: str | None = None,
        section_gradient_token: str | None = None,
        section_gradient: ft.Gradient | None = None,
        section_border_radius: ft.BorderRadius | float | None = None,
        section_shadow: ft.BoxShadow | Sequence[ft.BoxShadow] | None = None,
        section_max_content_width: int | None = None,
        section_max_content_width_by_device: Dict[str, float | int | None] | None = None,
        theme: ThemeManager | None = None,
        device_profiles: Sequence[DeviceProfile] | None = None,
        device_columns: Dict[str, int] | None = None,
        adaptive_spacing: bool = False,
        spacing_scale: Dict[str, float] | None = None,
        section_background_image: str | None = None,
        section_background_image_fit: ft.ImageFit | None = None,
        section_overlay_color: str | None = None,
        header_layout: str = "auto",
        header_layout_by_device: Dict[str, str] | None = None,
        header_layout_by_orientation: Dict[str, str] | None = None,
        section_device_backgrounds: Dict[str, str] | None = None,
        section_device_gradient_tokens: Dict[str, str] | None = None,
        section_device_gradients: Dict[str, ft.Gradient] | None = None,
        section_overlay_color_by_device: Dict[str, str] | None = None,
        section_border: ft.Border | None = None,
        section_glass_background: bool = False,
        section_gap_by_device: Dict[str, int] | None = None,
        section_orientation_backgrounds: Dict[str, str] | None = None,
        section_orientation_gradient_tokens: Dict[str, str] | None = None,
        section_orientation_gradients: Dict[str, ft.Gradient] | None = None,
        header_badge: str | ft.Control | None = None,
        header_badge_icon: str | None = None,
        header_badge_style: Style | None = None,
        header_padding: Dict[str, object] | ft.Padding | int | float | None = None,
        header_background: str | None = None,
        header_background_by_device: Dict[str, str] | None = None,
        header_background_by_orientation: Dict[str, str] | None = None,
        header_gradient_token: str | None = None,
        header_gradient: ft.Gradient | None = None,
        header_gradient_by_device: Dict[str, ft.Gradient] | None = None,
        header_gradient_by_orientation: Dict[str, ft.Gradient] | None = None,
        header_gradient_tokens_by_device: Mapping[str, Sequence[str] | tuple[str, str]]
        | None = None,
        header_border: ft.Border | None = None,
        header_border_radius: ft.BorderRadius | float | None = None,
        header_shadow: ft.BoxShadow | Sequence[ft.BoxShadow] | None = None,
        header_gradient_tokens_by_orientation: Dict[str, Sequence[str] | tuple[str, str]]
        | None = None,
        header_actions_alignment: ft.MainAxisAlignment | str | None = None,
        header_actions_alignment_by_device: Dict[str, ft.MainAxisAlignment | str] | None = None,
        header_actions_alignment_by_orientation: Dict[
            str, ft.MainAxisAlignment | str
        ]
        | None = None,
    ) -> None:
        """Grid responsiva basada en breakpoints.

        ``ResponsiveGrid`` admite ahora span personalizados para cada item y
        estilos adaptables según dispositivo, lo que permite diseñar interfaces
        diferenciadas para web, escritorio y móviles con un único componente.
        """

        self.spacing = spacing
        self._base_spacing = spacing
        self.style = style
        self.run_spacing = run_spacing
        self._base_run_spacing = run_spacing
        self.alignment = alignment or ft.MainAxisAlignment.START
        self.section_gap = section_gap
        self._base_section_gap = section_gap
        self.theme = theme
        self.adaptive_spacing = adaptive_spacing
        default_scale = {"mobile": 0.75, "tablet": 0.9, "desktop": 1.0, "large_desktop": 1.2}
        if spacing_scale:
            default_scale.update(spacing_scale)
        self.spacing_scale = default_scale

        self.device_profiles: tuple[DeviceProfile, ...] = tuple(
            device_profiles or EXTENDED_DEVICE_PROFILES
        )
        base_columns = {"mobile": 1, "tablet": 2, "desktop": 3, "large_desktop": 4}
        if device_columns:
            base_columns.update(device_columns)
        self.device_columns = base_columns

        self.section_title = header_title
        self.section_subtitle = header_subtitle
        self.section_description = header_description
        self.section_background = section_background
        self.section_gradient_token = section_gradient_token
        self.section_gradient = section_gradient
        self.section_border_radius = section_border_radius
        self.section_shadow = section_shadow
        self.section_max_content_width = section_max_content_width
        self.section_max_content_width_by_device = {
            str(key).lower(): value
            for key, value in (section_max_content_width_by_device or {}).items()
        }
        self.section_background_image = section_background_image
        self.section_background_image_fit = section_background_image_fit
        self.section_overlay_color = section_overlay_color
        self.section_border = section_border
        self.section_glass_background = section_glass_background
        self.section_gap_by_device = {}
        if section_gap_by_device:
            for key, value in section_gap_by_device.items():
                try:
                    normalized = max(0, int(value))
                except (TypeError, ValueError):
                    continue
                self.section_gap_by_device[str(key).lower()] = normalized
        self.header_background = header_background
        self.header_gradient_token = header_gradient_token
        self.header_gradient = header_gradient
        self.header_background_by_device = {
            str(key).lower(): value
            for key, value in (header_background_by_device or {}).items()
            if isinstance(value, str)
        }
        self.header_background_by_orientation = {
            str(key).lower(): value
            for key, value in (header_background_by_orientation or {}).items()
            if isinstance(value, str)
        }
        self.header_gradient_by_device = {
            str(key).lower(): value
            for key, value in (header_gradient_by_device or {}).items()
            if not _GRADIENT_TYPES or isinstance(value, _GRADIENT_TYPES)
        }
        self.header_gradient_by_orientation = {
            str(key).lower(): value
            for key, value in (header_gradient_by_orientation or {}).items()
            if not _GRADIENT_TYPES or isinstance(value, _GRADIENT_TYPES)
        }
        gradient_token_map: dict[str, tuple[str, str]] = {}
        if header_gradient_tokens_by_device:
            for key, value in header_gradient_tokens_by_device.items():
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    gradient_token_map[str(key).lower()] = (str(value[0]), str(value[1]))
        self.header_gradient_tokens_by_device = gradient_token_map

        orientation_gradient_tokens_map: dict[str, tuple[str, str]] = {}
        if header_gradient_tokens_by_orientation:
            for key, value in header_gradient_tokens_by_orientation.items():
                orientation = str(key).strip().lower()
                if orientation not in {"portrait", "landscape"}:
                    continue
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    orientation_gradient_tokens_map[orientation] = (str(value[0]), str(value[1]))
        self.header_gradient_tokens_by_orientation = orientation_gradient_tokens_map

        self.header_border = header_border
        self.header_border_radius = header_border_radius
        self.header_shadow = header_shadow
        layout_value = (header_layout or "auto").strip().lower()
        if layout_value not in {"auto", "centered", "split"}:
            layout_value = "auto"
        self.header_layout = layout_value
        normalized_layouts: Dict[str, str] = {}
        if header_layout_by_device:
            for key, value in header_layout_by_device.items():
                if not isinstance(value, str):
                    continue
                normalized = value.strip().lower()
                if normalized not in {"auto", "centered", "split"}:
                    continue
                normalized_layouts[str(key).lower()] = normalized
        self.header_layout_by_device = normalized_layouts
        orientation_layouts: Dict[str, str] = {}
        if header_layout_by_orientation:
            for key, value in header_layout_by_orientation.items():
                if not isinstance(value, str):
                    continue
                orientation = str(key).strip().lower()
                if orientation not in {"portrait", "landscape"}:
                    continue
                normalized = value.strip().lower()
                if normalized not in {"auto", "centered", "split"}:
                    continue
                orientation_layouts[orientation] = normalized
        self.header_layout_by_orientation = orientation_layouts

        self.section_device_backgrounds = {
            str(key).lower(): value
            for key, value in (section_device_backgrounds or {}).items()
            if isinstance(value, str)
        }
        self.section_orientation_backgrounds = {
            str(key).lower(): value
            for key, value in (section_orientation_backgrounds or {}).items()
            if isinstance(value, str)
        }
        self.section_device_gradient_tokens = {
            str(key).lower(): value
            for key, value in (section_device_gradient_tokens or {}).items()
            if isinstance(value, str)
        }
        self.section_orientation_gradient_tokens = {
            str(key).lower(): value
            for key, value in (section_orientation_gradient_tokens or {}).items()
            if isinstance(value, str)
        }
        self.section_device_gradients = {
            str(key).lower(): value
            for key, value in (section_device_gradients or {}).items()
            if not _GRADIENT_TYPES or isinstance(value, _GRADIENT_TYPES)
        }
        self.section_orientation_gradients = {
            str(key).lower(): value
            for key, value in (section_orientation_gradients or {}).items()
            if not _GRADIENT_TYPES or isinstance(value, _GRADIENT_TYPES)
        }
        self.section_overlay_color_by_device = {
            str(key).lower(): value
            for key, value in (section_overlay_color_by_device or {}).items()
            if isinstance(value, str)
        }

        try:
            self.header_tag_spacing = max(0, int(header_tag_spacing))
        except (TypeError, ValueError):
            self.header_tag_spacing = 10

        self._header_tag_controls: list[ft.Control] = []
        if header_tags:
            for tag in header_tags:
                control = self._create_tag_control(tag, header_tag_style)
                if control is not None:
                    self._header_tag_controls.append(control)

        self._header_highlights: list[HeaderHighlight] = []
        if header_highlights:
            for highlight in header_highlights:
                normalized = self._normalize_highlight(highlight)
                if normalized is not None:
                    self._header_highlights.append(normalized)

        self._section_actions_row = ft.Row(
            controls=list(header_actions or []), spacing=12, wrap=True
        )
        self._section_metadata_row = ft.Row(
            controls=list(header_metadata or []), spacing=12, wrap=True, run_spacing=10
        )
        self._custom_actions_alignment = _parse_main_axis_alignment(
            header_actions_alignment
        )
        alignment_by_device: Dict[str, ft.MainAxisAlignment] = {}
        if header_actions_alignment_by_device:
            for key, value in header_actions_alignment_by_device.items():
                alignment = _parse_main_axis_alignment(value)
                if alignment is None:
                    continue
                alignment_by_device[str(key).lower()] = alignment
        self._actions_alignment_by_device = alignment_by_device
        orientation_alignment_map: Dict[str, ft.MainAxisAlignment] = {}
        if header_actions_alignment_by_orientation:
            for key, value in header_actions_alignment_by_orientation.items():
                orientation = str(key).strip().lower()
                if orientation not in {"portrait", "landscape"}:
                    continue
                alignment = _parse_main_axis_alignment(value)
                if alignment is None:
                    continue
                orientation_alignment_map[orientation] = alignment
        self._actions_alignment_by_orientation = orientation_alignment_map
        self._section_icon_control: ft.Control | None
        if isinstance(header_icon, ft.Control):
            self._section_icon_control = header_icon
        elif isinstance(header_icon, str):
            self._section_icon_control = ft.Icon(header_icon, size=30)
        else:
            self._section_icon_control = None

        self._header_badge: ft.Control | None = None
        if isinstance(header_badge, ft.Control):
            self._header_badge = header_badge
        elif header_badge:
            badge_text = ft.Text(str(header_badge), weight=ft.FontWeight.BOLD, size=12)
            badge_content: ft.Control = badge_text
            if header_badge_icon:
                badge_content = ft.Row(
                    controls=[ft.Icon(header_badge_icon, size=14), badge_text],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            if header_badge_style:
                self._header_badge = header_badge_style.apply(badge_content)
            else:
                accent = None
                if self.theme:
                    accent = (
                        self.theme.get_color("accent")
                        or self.theme.get_color("primary")
                        or ft.Colors.BLUE_400
                    )
                self._header_badge = ft.Container(
                    content=badge_content,
                    padding=ft.Padding(12, 6, 12, 6),
                    bgcolor=ft.Colors.with_opacity(0.14, accent or ft.Colors.BLUE_200),
                    border_radius=ft.border_radius.all(40),
                    border=ft.border.all(1, ft.Colors.with_opacity(0.2, accent or ft.Colors.BLUE)),
                )

        self._wrap_requested = False

        shared_padding = _as_padding(section_padding)
        if isinstance(section_padding, dict):
            self._section_padding_config: Dict[str, ft.Padding | None] = {
                str(device): _as_padding(value)
                for device, value in section_padding.items()
            }
        elif section_padding is not None:
            base_padding = shared_padding or ft.Padding(20, 20, 20, 20)
            self._section_padding_config = {
                "mobile": base_padding,
                "tablet": ft.Padding(
                    base_padding.left * 1.1,
                    base_padding.top * 1.1,
                    base_padding.right * 1.1,
                    base_padding.bottom * 1.1,
                ),
                "desktop": ft.Padding(
                    base_padding.left * 1.3,
                    base_padding.top * 1.3,
                    base_padding.right * 1.3,
                    base_padding.bottom * 1.3,
                ),
                "large_desktop": ft.Padding(
                    base_padding.left * 1.5,
                    base_padding.top * 1.5,
                    base_padding.right * 1.5,
                    base_padding.bottom * 1.5,
                ),
            }
        else:
            self._section_padding_config = {}

        shared_margin = _as_margin(section_margin)
        if isinstance(section_margin, dict):
            self._section_margin_device_config: Dict[str, ft.Margin | None] = {
                str(device).lower(): _as_margin(value)
                for device, value in section_margin.items()
            }
        elif section_margin is not None:
            base_margin = shared_margin or ft.Margin(0, 0, 0, 0)
            self._section_margin_device_config = {
                "mobile": base_margin,
                "tablet": ft.Margin(
                    base_margin.left * 1.05,
                    base_margin.top * 1.05,
                    base_margin.right * 1.05,
                    base_margin.bottom * 1.05,
                ),
                "desktop": ft.Margin(
                    base_margin.left * 1.2,
                    base_margin.top * 1.2,
                    base_margin.right * 1.2,
                    base_margin.bottom * 1.2,
                ),
                "large_desktop": ft.Margin(
                    base_margin.left * 1.35,
                    base_margin.top * 1.35,
                    base_margin.right * 1.35,
                    base_margin.bottom * 1.35,
                ),
            }
        else:
            self._section_margin_device_config = {}

        orientation_margin_config: Dict[str, ft.Margin | None] = {}
        if section_margin_by_orientation:
            for key, value in section_margin_by_orientation.items():
                orientation = str(key).strip().lower()
                if orientation not in {"portrait", "landscape"}:
                    continue
                orientation_margin_config[orientation] = _as_margin(value)
        self._section_margin_orientation_config = orientation_margin_config

        header_shared_padding = _as_padding(header_padding)
        if isinstance(header_padding, dict):
            self._header_padding_config: Dict[str, ft.Padding | None] = {
                str(device).lower(): _as_padding(value)
                for device, value in header_padding.items()
            }
        elif header_shared_padding is not None:
            self._header_padding_config = {"*": header_shared_padding}
        else:
            self._header_padding_config = {}

        self._wrap_requested = any(
            [
                header_title,
                header_subtitle,
                header_description,
                header_icon,
                header_actions,
                header_metadata,
                section_background,
                section_gradient_token,
                section_gradient,
                section_border_radius,
                section_shadow,
                section_max_content_width,
                section_background_image,
                section_overlay_color,
                section_border,
                section_glass_background,
                bool(header_tags),
                bool(header_highlights),
                bool(self._section_padding_config),
                bool(self._section_margin_device_config),
                bool(self._section_margin_orientation_config),
                bool(self._header_padding_config),
                header_background,
                header_gradient_token,
                header_gradient,
                header_border,
                header_border_radius,
                header_shadow,
            ]
        )

        self._items = [ResponsiveGridItem(control=child) for child in (children or [])]
        if items:
            self._items.extend(items)

        if columns is not None:
            self.breakpoints = {0: columns}
        elif breakpoints is not None:
            normalized = BreakpointRegistry.normalize(breakpoints)
            self.breakpoints = {
                bp: max(1, int(cols)) for bp, cols in normalized.items()
            }
        else:
            computed: Dict[int, int] = {}
            for profile in iter_device_profiles(self.device_profiles):
                span = self.device_columns.get(profile.name)
                if span is None:
                    span = max(1, round(profile.columns / 4))
                computed[profile.min_width] = max(1, min(6, int(span)))
            self.breakpoints = computed or {0: 1, 600: 2, 900: 3, 1200: 4}

        self._manager: ResponsiveManager | None = None
        self._row: ft.ResponsiveRow | None = None
        self._section_container: ft.Container | None = None
        self._section_column: ft.Column | None = None
        self._section_header_container: ft.Container | None = None
        self._section_inner_container: ft.Container | None = None
        self._layout_root: ft.Control | None = None
        self._current_orientation: str = "landscape"

    # ------------------------------------------------------------------
    def _resolve_columns(self, width: int) -> int:
        columns = 1
        for bp, cols in sorted(self.breakpoints.items()):
            if width >= bp:
                columns = cols
        return max(1, columns)

    # ------------------------------------------------------------------
    def _resolve_device_name(self, width: int) -> DeviceName:
        profile = get_device_profile(width, self.device_profiles)
        return profile.name

    # ------------------------------------------------------------------
    def _scale_padding(self, value: object, scale: float) -> object:
        if isinstance(value, ft.Padding):
            return ft.Padding(
                value.left * scale,
                value.top * scale,
                value.right * scale,
                value.bottom * scale,
            )
        if isinstance(value, (int, float)):
            return int(round(float(value) * scale))
        return value

    # ------------------------------------------------------------------
    def _resolve_spacing_values(self, width: int) -> tuple[object, int | float | None]:
        base_item = self._base_spacing
        base_run: object | None = self._base_run_spacing
        if base_run is None and self.adaptive_spacing:
            base_run = self._base_spacing
        if not self.adaptive_spacing:
            return base_item, base_run

        device = self._resolve_device_name(width)
        scale = self.spacing_scale.get(device, 1.0)
        item_spacing = self._scale_padding(base_item, scale)
        run_spacing = None if base_run is None else self._scale_padding(base_run, scale)
        if isinstance(run_spacing, ft.Padding):
            # ``run_spacing`` solo admite valores numéricos
            run_spacing = run_spacing.left
        return item_spacing, run_spacing

    # ------------------------------------------------------------------
    def _apply_spacing_to_row(self, row: ft.ResponsiveRow, width: int) -> None:
        item_padding, run_spacing = self._resolve_spacing_values(width)
        for control in row.controls:
            if isinstance(control, ft.Container):
                control.padding = item_padding
        if run_spacing is not None:
            try:
                row.run_spacing = int(run_spacing)
            except (TypeError, ValueError):
                row.run_spacing = run_spacing

    # ------------------------------------------------------------------
    def _build_item_container(
        self,
        item: ResponsiveGridItem,
        width: int,
        columns: int,
        device: DeviceName | None = None,
        *,
        resolved_span: int | None = None,
    ) -> ft.Container:
        device = device or self._resolve_device_name(width)
        content: ft.Control = item.control
        if item.style:
            styled = item.style.apply(content)
            if isinstance(styled, ft.Control):
                content = styled

        container = ft.Container(
            content=content,
            col=resolved_span or item.resolve_span(width, columns, device),
            padding=self._resolve_spacing_values(width)[0],
        )

        style: ResponsiveStyle | None = None
        if isinstance(item.responsive_style, ResponsiveStyle):
            style = item.responsive_style
        elif isinstance(item.responsive_style, dict):
            style = ResponsiveStyle(width=item.responsive_style)

        if style is not None:
            setattr(container, "_fletplus_responsive_style", style)

        return container

    # ------------------------------------------------------------------
    def _build_row(self, width: int) -> ft.ResponsiveRow:
        columns = self._resolve_columns(width)
        device = self._resolve_device_name(width)
        descriptors: list[dict[str, object]] | None = None

        if _plan_grid_items_native_from_objects is not None:
            try:
                native_result = _plan_grid_items_native_from_objects(
                    width, columns, device, self._items
                )
            except Exception:
                native_result = None

            if native_result is not None:
                descriptors = list(native_result)

        if descriptors is None and _plan_grid_items_native is not None:
            payload: list[dict[str, object]] = []
            for index, item in enumerate(self._items):
                payload.append(
                    {
                        "index": index,
                        "span": item.span,
                        "span_breakpoints": dict(item.span_breakpoints or {}),
                        "span_devices": dict(item.span_devices or {}),
                        "visible_devices": list(item.visible_devices)
                        if item.visible_devices
                        else None,
                        "hidden_devices": list(item.hidden_devices)
                        if item.hidden_devices
                        else None,
                        "min_width": item.min_width,
                        "max_width": item.max_width,
                        "has_responsive_style": isinstance(
                            item.responsive_style, (ResponsiveStyle, dict)
                        ),
                    }
                )

            try:
                native_result = _plan_grid_items_native(
                    width, columns, device, payload
                )
            except Exception:
                native_result = None

            if native_result is not None:
                descriptors = list(native_result)

        if descriptors is None:
            descriptors = []
            for index, item in enumerate(self._items):
                if not item.is_visible(width, device):
                    continue
                descriptors.append(
                    {
                        "index": index,
                        "col": item.resolve_span(width, columns, device),
                        "has_responsive_style": isinstance(
                            item.responsive_style, (ResponsiveStyle, dict)
                        ),
                    }
                )

        containers = []
        for descriptor in descriptors:
            item = self._items[int(descriptor.get("index", 0))]
            resolved_span = descriptor.get("col")
            try:
                span_value = int(resolved_span) if resolved_span is not None else None
            except (TypeError, ValueError):
                span_value = None
            containers.append(
                self._build_item_container(
                    item,
                    width,
                    columns,
                    device,
                    resolved_span=span_value,
                )
            )
        row = ft.ResponsiveRow(
            controls=containers,
            alignment=self.alignment,
            run_spacing=self.run_spacing,
        )
        self._apply_spacing_to_row(row, width)
        return row

    # ------------------------------------------------------------------
    def build(self, page_width: Optional[int]) -> ft.Control:
        width = page_width or 0
        row = self._build_row(width)
        self._row = row

        styled = self.style.apply(row) if self.style else row
        self._layout_root = styled

        wrapped = self._wrap_section(styled, width)
        self._update_section_layout(width)
        return wrapped

    # ------------------------------------------------------------------
    def _wrap_section(self, layout: ft.Control, width: int) -> ft.Control:
        has_header = any(
            [
                self.section_title,
                self.section_subtitle,
                self.section_description,
                self._section_actions_row.controls,
                self._section_metadata_row.controls,
                self._section_icon_control,
            ]
        )

        needs_wrapper = has_header or self._wrap_requested

        if not needs_wrapper:
            self._section_container = None
            self._section_column = None
            self._section_header_container = None
            return layout

        header_container = ft.Container()
        column_controls: list[ft.Control] = [header_container, layout]

        column = ft.Column(controls=column_controls, spacing=self.section_gap, tight=True)
        self._section_header_container = header_container
        self._section_column = column

        content: ft.Control = column
        need_inner = bool(
            self.section_max_content_width or self.section_max_content_width_by_device
        )
        if need_inner:
            device = self._resolve_device_name(width)
            inner_width = self._resolve_section_max_width(device)
            inner = ft.Container(width=inner_width, content=column)
            self._section_inner_container = inner
            wrapper = ft.Column(
                controls=[inner],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            content = wrapper
        else:
            self._section_inner_container = None

        container = ft.Container(content=content, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)
        self._section_container = container
        return container

    # ------------------------------------------------------------------
    def _resolve_section_padding(self, device: DeviceName) -> ft.Padding:
        padding: ft.Padding | None = None
        for key in [device, "desktop", "tablet", "mobile"]:
            stored = self._section_padding_config.get(key)
            if stored is not None:
                padding = stored
                break
        if padding is None:
            padding = ft.Padding(20, 20, 20, 20)
        return _clone_padding(padding) or ft.Padding(20, 20, 20, 20)

    # ------------------------------------------------------------------
    def _resolve_section_margin(self, device: DeviceName) -> ft.Margin | None:
        orientation = getattr(self, "_current_orientation", "landscape")
        if orientation in self._section_margin_orientation_config:
            margin = self._section_margin_orientation_config[orientation]
            if isinstance(margin, ft.Margin):
                return _clone_margin(margin)
            return margin

        margin: ft.Margin | None = None
        for key in [device, "desktop", "tablet", "mobile"]:
            stored = self._section_margin_device_config.get(key)
            if stored is not None:
                margin = stored
                break
        if isinstance(margin, ft.Margin):
            return _clone_margin(margin)
        return margin

    # ------------------------------------------------------------------
    def _resolve_section_gap(self, device: DeviceName) -> int:
        if not self.section_gap_by_device:
            return self._base_section_gap
        for key in (device, "desktop", "tablet", "mobile"):
            if key in self.section_gap_by_device:
                return self.section_gap_by_device[key]
        return self._base_section_gap

    # ------------------------------------------------------------------
    def _resolve_section_max_width(self, device: DeviceName) -> float | int | None:
        if self.section_max_content_width_by_device:
            for key in (device, "desktop", "tablet", "mobile"):
                if key in self.section_max_content_width_by_device:
                    return self.section_max_content_width_by_device[key]
        return self.section_max_content_width

    # ------------------------------------------------------------------
    def _resolve_header_padding(self, device: DeviceName) -> ft.Padding | None:
        if not self._header_padding_config:
            return None
        padding: ft.Padding | None = None
        for key in [device, "*", "desktop", "tablet", "mobile"]:
            stored = self._header_padding_config.get(key)
            if stored is not None:
                padding = stored
                break
        if isinstance(padding, ft.Padding):
            return _clone_padding(padding)
        return padding

    # ------------------------------------------------------------------
    def _resolve_section_background(self, device: DeviceName) -> str | None:
        orientation = getattr(self, "_current_orientation", "landscape")
        if self.section_orientation_backgrounds:
            background = self.section_orientation_backgrounds.get(orientation)
            if background:
                return background
        device_backgrounds = getattr(self, "section_device_backgrounds", None)
        if device_backgrounds:
            custom = device_backgrounds.get(device)
            if custom:
                return custom
        if self.section_background:
            return self.section_background
        if self.theme:
            return (
                self.theme.get_color("surface_variant")
                or self.theme.get_color("surface")
                or self.theme.get_color("background")
        )
        return ft.Colors.with_opacity(0.02, "#000000")

    # ------------------------------------------------------------------
    def _resolve_section_gradient(self, device: DeviceName) -> ft.Gradient | None:
        orientation = getattr(self, "_current_orientation", "landscape")
        if self.section_orientation_gradients:
            gradient = self.section_orientation_gradients.get(orientation)
            if gradient:
                return gradient
        if self.section_device_gradients:
            gradient = self.section_device_gradients.get(device)
            if gradient:
                return gradient
        if self.section_gradient is not None:
            return self.section_gradient
        if self.section_orientation_gradient_tokens and self.theme:
            token = self.section_orientation_gradient_tokens.get(orientation)
            if token:
                gradient = self.theme.get_gradient(token)
                if gradient is not None:
                    return gradient
        if self.theme and self.section_gradient_token:
            gradient = self.theme.get_gradient(self.section_gradient_token)
            if gradient is not None:
                return gradient
        if self.theme and self.section_device_gradient_tokens:
            token = self.section_device_gradient_tokens.get(device)
            if token:
                gradient = self.theme.get_gradient(token)
                if gradient is not None:
                    return gradient
        return None

    # ------------------------------------------------------------------
    def _gradient_from_color_tokens(
        self, tokens: Sequence[str] | tuple[str, ...]
    ) -> ft.LinearGradient | None:
        if not self.theme:
            return None
        colors: list[str] = []
        for token in tokens:
            color = self.theme.get_color(token)
            if isinstance(color, str):
                colors.append(color)
        if len(colors) < 2:
            return None
        return ft.LinearGradient(
            colors=colors,
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
        )

    # ------------------------------------------------------------------
    def _resolve_header_gradient(self, device: DeviceName) -> ft.Gradient | None:
        orientation = getattr(self, "_current_orientation", "landscape")
        if self.header_gradient_by_orientation:
            gradient = self.header_gradient_by_orientation.get(orientation)
            if gradient is not None:
                return gradient
        if self.header_gradient_by_device:
            gradient = self.header_gradient_by_device.get(device)
            if gradient is not None:
                return gradient
        if (
            self.theme
            and self.header_gradient_tokens_by_orientation
            and orientation in self.header_gradient_tokens_by_orientation
        ):
            tokens = self.header_gradient_tokens_by_orientation[orientation]
            gradient = self._gradient_from_color_tokens(tokens)
            if gradient is not None:
                return gradient
        if (
            self.theme
            and self.header_gradient_tokens_by_device
            and device in self.header_gradient_tokens_by_device
        ):
            tokens = self.header_gradient_tokens_by_device[device]
            gradient = self._gradient_from_color_tokens(tokens)
            if gradient is not None:
                return gradient
        if self.header_gradient is not None:
            return self.header_gradient
        if self.theme and self.header_gradient_token:
            gradient = self.theme.get_gradient(self.header_gradient_token)
            if gradient is not None:
                return gradient
        return None

    # ------------------------------------------------------------------
    def _resolve_header_background(self, device: DeviceName) -> str | None:
        orientation = getattr(self, "_current_orientation", "landscape")
        if orientation in self.header_background_by_orientation:
            return self.header_background_by_orientation[orientation]
        if device in self.header_background_by_device:
            return self.header_background_by_device[device]
        if self.header_background is not None:
            return self.header_background
        if self.theme:
            fallback = (
                self.theme.get_color("surface_variant")
                or self.theme.get_color("surface")
                or self.theme.get_color("background")
            )
            if isinstance(fallback, str):
                return fallback
        return None

    # ------------------------------------------------------------------
    def _resolve_actions_alignment(
        self, device: DeviceName
    ) -> ft.MainAxisAlignment | None:
        orientation = getattr(self, "_current_orientation", "landscape")
        if orientation in self._actions_alignment_by_orientation:
            return self._actions_alignment_by_orientation[orientation]
        if device in self._actions_alignment_by_device:
            return self._actions_alignment_by_device[device]
        return self._custom_actions_alignment

    # ------------------------------------------------------------------
    def _resolve_icon_background(self) -> str | None:
        if not self.theme:
            return ft.Colors.with_opacity(0.08, "#000000")
        accent = (
            self.theme.get_color("accent")
            or self.theme.get_color("primary")
            or self.theme.get_color("surface_variant")
        )
        if isinstance(accent, str):
            return ft.Colors.with_opacity(0.15, accent)
        return ft.Colors.with_opacity(0.08, "#000000")

    # ------------------------------------------------------------------
    def _resolve_accent_color(self) -> str:
        if self.theme:
            for token in (
                "accent",
                "primary",
                "secondary",
                "info_500",
                "primary_500",
            ):
                color = self.theme.get_color(token)
                if isinstance(color, str):
                    return color
        return "#4C6EF5"

    # ------------------------------------------------------------------
    def _create_tag_control(
        self,
        tag: object,
        style: Style | None,
    ) -> ft.Control | None:
        if isinstance(tag, ft.Control):
            return tag

        label: str | None = None
        icon_value: object | None = None
        tooltip: object | None = None

        if isinstance(tag, Mapping):
            label = tag.get("label") or tag.get("text")
            icon_value = tag.get("icon")
            tooltip = tag.get("tooltip")
        elif isinstance(tag, (list, tuple)) and tag:
            label = tag[0]
            if len(tag) > 1:
                icon_value = tag[1]
            if len(tag) > 2:
                tooltip = tag[2]
        else:
            label = tag

        if label is None:
            return None

        label_text = str(label).strip()
        if not label_text:
            return None

        icon_control: ft.Control | None = None
        if isinstance(icon_value, ft.Control):
            icon_control = icon_value
        elif isinstance(icon_value, str) and icon_value:
            icon_control = ft.Icon(icon_value, size=14)

        accent = self._resolve_accent_color()
        text_color = accent
        content_controls: list[ft.Control] = []
        if icon_control is not None:
            if isinstance(icon_control, ft.Icon):
                icon_control.color = accent
            content_controls.append(icon_control)
        content_controls.append(
            ft.Text(label_text, size=12, weight=ft.FontWeight.W_600, color=text_color)
        )

        tag_row = ft.Row(
            controls=content_controls,
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=False,
        )

        container: ft.Control = ft.Container(
            content=tag_row,
            padding=ft.Padding(14, 8, 14, 8),
            bgcolor=ft.Colors.with_opacity(0.1, accent),
            border_radius=ft.border_radius.all(40),
            border=ft.border.all(1, ft.Colors.with_opacity(0.22, accent)),
        )

        if style:
            styled = style.apply(container)
            if isinstance(styled, ft.Control):
                container = styled

        if tooltip:
            container = ft.Tooltip(content=container, message=str(tooltip))

        return container

    # ------------------------------------------------------------------
    def _normalize_highlight(self, highlight: object) -> HeaderHighlight | None:
        if isinstance(highlight, HeaderHighlight):
            return highlight

        label: object | None = None
        value: object | None = None
        icon: object | None = None
        description: object | None = None

        if isinstance(highlight, Mapping):
            label = highlight.get("label") or highlight.get("title")
            value = highlight.get("value") or highlight.get("amount")
            icon = highlight.get("icon")
            description = highlight.get("description") or highlight.get("help")
        elif isinstance(highlight, (list, tuple)):
            if len(highlight) < 2:
                return None
            label, value = highlight[0], highlight[1]
            if len(highlight) > 2:
                icon = highlight[2]
            if len(highlight) > 3:
                description = highlight[3]
        else:
            return None

        if label is None or value is None:
            return None

        label_text = str(label).strip()
        value_text = str(value).strip()
        if not label_text or not value_text:
            return None

        description_text = None
        if description is not None:
            description_text = str(description)

        return HeaderHighlight(
            label=label_text,
            value=value_text,
            icon=icon,
            description=description_text,
        )

    # ------------------------------------------------------------------
    def _build_tags_layout(self, device: DeviceName) -> ft.Control | None:
        if not self._header_tag_controls:
            return None

        alignment = (
            ft.MainAxisAlignment.CENTER
            if device == "mobile"
            else ft.MainAxisAlignment.START
        )

        return ft.Row(
            controls=list(self._header_tag_controls),
            spacing=self.header_tag_spacing,
            run_spacing=8,
            wrap=True,
            alignment=alignment,
        )

    # ------------------------------------------------------------------
    def _build_highlight_layout(self, device: DeviceName) -> ft.Control | None:
        if not self._header_highlights:
            return None

        accent = self._resolve_accent_color()
        controls = [
            highlight.build_control(self.theme, accent, device)
            for highlight in self._header_highlights
        ]

        if device == "mobile":
            return ft.Column(controls=controls, spacing=8, tight=True)

        return ft.Row(
            controls=controls,
            spacing=12,
            run_spacing=10,
            wrap=True,
            alignment=ft.MainAxisAlignment.START,
        )

    # ------------------------------------------------------------------
    def _update_section_layout(self, width: int) -> None:
        if not self._section_container:
            return

        device = self._resolve_device_name(width)
        self.section_gap = self._resolve_section_gap(device)
        if self._section_inner_container is not None:
            self._section_inner_container.width = self._resolve_section_max_width(device)

        padding = self._resolve_section_padding(device)
        self._section_container.padding = padding
        self._section_container.margin = self._resolve_section_margin(device)

        gradient = self._resolve_section_gradient(device)
        if gradient:
            self._section_container.gradient = gradient
            self._section_container.bgcolor = None
        else:
            self._section_container.gradient = None
            base_color = self._resolve_section_background(device)
            self._section_container.bgcolor = base_color
            if self.section_glass_background and not self.section_background_image:
                tint_source = base_color
                if not isinstance(tint_source, str) and self.theme:
                    tint_source = self.theme.get_color("surface")
                if not isinstance(tint_source, str):
                    tint_source = "#FFFFFF"
                self._section_container.bgcolor = ft.Colors.with_opacity(0.78, tint_source)

        if self.section_background_image:
            self._section_container.image_src = self.section_background_image
            self._section_container.image_fit = (
                self.section_background_image_fit or ft.ImageFit.COVER
            )
            overlay_color = (
                self.section_overlay_color_by_device.get(device)
                if isinstance(getattr(self, "section_overlay_color_by_device", None), dict)
                else None
            )
            if overlay_color is None:
                overlay_color = self.section_overlay_color
            if overlay_color:
                self._section_container.bgcolor = overlay_color
        else:
            self._section_container.image_src = None

        if isinstance(self.section_border_radius, ft.BorderRadius):
            self._section_container.border_radius = self.section_border_radius
        elif self.section_border_radius is not None:
            try:
                radius_value = float(self.section_border_radius)
            except (TypeError, ValueError):
                radius_value = 20
            self._section_container.border_radius = ft.border_radius.all(radius_value)

        if self.section_border is not None:
            self._section_container.border = self.section_border
        elif self.section_glass_background:
            accent = self._resolve_accent_color()
            self._section_container.border = ft.border.all(
                1, ft.Colors.with_opacity(0.26, accent)
            )
        else:
            self._section_container.border = None

        if self.section_shadow is None:
            blur_radius = 22
            offset_y = 10
            shadow_opacity = 0.12
            if self.section_glass_background:
                blur_radius = 36
                offset_y = 16
                shadow_opacity = 0.18
            self._section_container.shadow = ft.BoxShadow(
                blur_radius=blur_radius,
                spread_radius=0,
                color=ft.Colors.with_opacity(shadow_opacity, "#000000"),
                offset=ft.Offset(0, offset_y),
            )
        else:
            self._section_container.shadow = self.section_shadow

        if self._section_column:
            self._section_column.spacing = self.section_gap

        self._update_section_header(width)

    # ------------------------------------------------------------------
    def _update_section_header(self, width: int) -> None:
        if not self._section_header_container:
            return

        has_content = any(
            [
                self.section_title,
                self.section_subtitle,
                self.section_description,
                self._section_actions_row.controls,
                self._section_metadata_row.controls,
                self._section_icon_control,
            ]
        )

        if not has_content:
            self._section_header_container.visible = False
            self._section_header_container.content = None
            return

        self._section_header_container.visible = True

        device = self._resolve_device_name(width)
        layout_mode = self.header_layout_by_device.get(device, self.header_layout)
        orientation_layout = self.header_layout_by_orientation.get(
            getattr(self, "_current_orientation", "landscape"),
            "auto",
        )
        if orientation_layout != "auto":
            layout_mode = orientation_layout

        if self._header_padding_config:
            padding = self._resolve_header_padding(device)
            self._section_header_container.padding = padding

        header_gradient = self._resolve_header_gradient(device)
        header_background = self._resolve_header_background(device)
        if header_gradient:
            self._section_header_container.gradient = header_gradient
            self._section_header_container.bgcolor = None
        elif header_background is not None:
            self._section_header_container.gradient = None
            self._section_header_container.bgcolor = header_background
        else:
            self._section_header_container.gradient = None
            if self._section_header_container.bgcolor is not None:
                self._section_header_container.bgcolor = None

        accent = self._resolve_accent_color()
        if self.header_border is not None:
            self._section_header_container.border = self.header_border
        elif header_background is not None or header_gradient is not None:
            self._section_header_container.border = ft.border.all(
                1, ft.Colors.with_opacity(0.16, accent)
            )
        else:
            self._section_header_container.border = None

        if isinstance(self.header_border_radius, ft.BorderRadius):
            self._section_header_container.border_radius = self.header_border_radius
        elif self.header_border_radius is not None:
            try:
                radius_value = float(self.header_border_radius)
            except (TypeError, ValueError):
                radius_value = 20
            self._section_header_container.border_radius = ft.border_radius.all(
                radius_value
            )
        elif header_background is not None or header_gradient is not None:
            self._section_header_container.border_radius = ft.border_radius.all(20)
        else:
            self._section_header_container.border_radius = None

        if self.header_shadow is not None:
            self._section_header_container.shadow = self.header_shadow
        elif header_background is not None or header_gradient is not None:
            self._section_header_container.shadow = ft.BoxShadow(
                blur_radius=18,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.12, "#000000"),
                offset=ft.Offset(0, 8),
            )
        else:
            self._section_header_container.shadow = None

        title_size = {"mobile": 20, "tablet": 22, "desktop": 24, "large_desktop": 28}
        subtitle_size = {"mobile": 15, "tablet": 16, "desktop": 18, "large_desktop": 20}
        description_size = {"mobile": 14, "tablet": 15, "desktop": 15, "large_desktop": 16}

        title_control = None
        if self.section_title:
            title_control = ft.Text(
                self.section_title,
                size=title_size.get(device, 22),
                weight=ft.FontWeight.W_600,
            )

        subtitle_control = None
        if self.section_subtitle:
            subtitle_control = ft.Text(
                self.section_subtitle,
                size=subtitle_size.get(device, 16),
                color=self.theme.get_color("muted") if self.theme else ft.Colors.GREY_600,
            )

        description_control = None
        if self.section_description:
            description_control = ft.Text(
                self.section_description,
                size=description_size.get(device, 15),
                color=(
                    self.theme.get_color("on_surface_variant")
                    if self.theme
                    else ft.Colors.GREY_700
                ),
            )

        text_controls: list[ft.Control] = []
        if self._header_badge:
            text_controls.append(self._header_badge)
        if title_control:
            text_controls.append(title_control)
        if subtitle_control:
            text_controls.append(subtitle_control)
        if description_control:
            text_controls.append(description_control)

        tag_layout = self._build_tags_layout(device)
        if tag_layout:
            text_controls.append(tag_layout)

        text_column = ft.Column(controls=text_controls, spacing=4, tight=True)

        icon_wrapper = None
        if self._section_icon_control:
            icon_color = (
                self.theme.get_color("primary")
                if self.theme
                else ft.Colors.with_opacity(0.9, "#000000")
            )
            if isinstance(self._section_icon_control, ft.Icon):
                self._section_icon_control.color = icon_color
            icon_wrapper = ft.Container(
                content=self._section_icon_control,
                padding=ft.Padding(10, 10, 10, 10),
                border_radius=ft.border_radius.all(16),
                bgcolor=self._resolve_icon_background(),
            )

        metadata_segments: list[ft.Control] = []
        if self._section_metadata_row.controls:
            meta_alignment = (
                ft.MainAxisAlignment.CENTER
                if device == "mobile" or layout_mode == "centered"
                else ft.MainAxisAlignment.START
            )
            self._section_metadata_row.alignment = meta_alignment
            metadata_segments.append(self._section_metadata_row)

        highlight_layout = self._build_highlight_layout(device)
        if highlight_layout:
            metadata_segments.append(highlight_layout)

        if not metadata_segments:
            metadata_control: ft.Control | None = None
        elif len(metadata_segments) == 1:
            metadata_control = metadata_segments[0]
        else:
            metadata_control = ft.Column(
                controls=metadata_segments,
                spacing=12,
                tight=True,
            )

        custom_actions_alignment = self._resolve_actions_alignment(device)
        if custom_actions_alignment is not None:
            self._section_actions_row.alignment = custom_actions_alignment

        if device == "mobile":
            mobile_controls: list[ft.Control] = []
            if icon_wrapper:
                mobile_controls.append(
                    ft.Row([icon_wrapper], alignment=ft.MainAxisAlignment.CENTER)
                )
            mobile_controls.append(
                ft.Column(
                    controls=list(text_controls),
                    spacing=4,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            if metadata_control:
                mobile_controls.append(metadata_control)
            if self._section_actions_row.controls:
                self._section_actions_row.wrap = True
                if custom_actions_alignment is None:
                    self._section_actions_row.alignment = ft.MainAxisAlignment.CENTER
                mobile_controls.append(self._section_actions_row)

            header_layout = ft.Column(
                controls=mobile_controls,
                spacing=10,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            if layout_mode == "centered":
                centered_controls: list[ft.Control] = []
                if icon_wrapper:
                    centered_controls.append(
                        ft.Row([icon_wrapper], alignment=ft.MainAxisAlignment.CENTER)
                    )
                stacked_controls: list[ft.Control] = [text_column]
                if metadata_control:
                    stacked_controls.append(metadata_control)
                centered_controls.append(
                    ft.Column(
                        controls=stacked_controls,
                        spacing=6,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )
                if self._section_actions_row.controls:
                    self._section_actions_row.wrap = True
                    if custom_actions_alignment is None:
                        self._section_actions_row.alignment = ft.MainAxisAlignment.CENTER
                    centered_controls.append(self._section_actions_row)

                header_layout = ft.Column(
                    controls=centered_controls,
                    spacing=12,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            else:
                column_controls: list[ft.Control] = [text_column]
                if metadata_control:
                    column_controls.append(metadata_control)
                text_stack = ft.Column(controls=column_controls, spacing=6, tight=True)

                left_controls: list[ft.Control] = []
                if icon_wrapper:
                    left_controls.append(icon_wrapper)
                left_controls.append(text_stack)

                left_block = ft.Row(
                    controls=left_controls,
                    spacing=16 if device == "large_desktop" else 12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=False,
                    expand=True,
                )

                if layout_mode == "split":
                    self._section_actions_row.wrap = False
                    if custom_actions_alignment is None:
                        self._section_actions_row.alignment = ft.MainAxisAlignment.END
                    row_controls: list[ft.Control] = [left_block]
                    if self._section_actions_row.controls:
                        row_controls.append(self._section_actions_row)
                    header_layout = ft.Row(
                        controls=row_controls,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                elif device == "tablet":
                    self._section_actions_row.wrap = True
                    if custom_actions_alignment is None:
                        self._section_actions_row.alignment = ft.MainAxisAlignment.END
                    layout_controls = [left_block]
                    if self._section_actions_row.controls:
                        layout_controls.append(self._section_actions_row)
                    header_layout = ft.Column(
                        controls=layout_controls,
                        spacing=12,
                        tight=True,
                    )
                else:
                    self._section_actions_row.wrap = False
                    if custom_actions_alignment is None:
                        self._section_actions_row.alignment = ft.MainAxisAlignment.END
                    row_controls = [left_block]
                    if self._section_actions_row.controls:
                        row_controls.append(ft.Container(expand=1))
                        row_controls.append(self._section_actions_row)
                    header_layout = ft.Row(
                        controls=row_controls,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )

        self._section_header_container.content = header_layout

    # ------------------------------------------------------------------
    def init_responsive(self, page: ft.Page) -> ft.Control:
        """Inicializa el grid y reacciona ante cambios de tamaño."""

        if self.theme:
            orientation = (
                "landscape"
                if (page.width or 0) >= (page.height or 0)
                else "portrait"
            )
            device = self._resolve_device_name(page.width or 0)
            self.theme.apply_theme(
                device=device,
                orientation=orientation,
                width=page.width or 0,
            )
            self._current_orientation = orientation

        layout = self.build(page.width)
        row = self._row
        if row is None:
            return layout

        def rebuild(width: int) -> None:
            if self._row is None:
                return
            if self.theme:
                orientation = (
                    "landscape"
                    if (page.width or 0) >= (page.height or 0)
                    else "portrait"
                )
                device_name = self._resolve_device_name(page.width or 0)
                self.theme.apply_theme(
                    device=device_name,
                    orientation=orientation,
                    width=page.width or 0,
                )
                self._current_orientation = orientation
            new_row = self._build_row(width)
            self._row.controls.clear()
            self._row.controls.extend(new_row.controls)
            self._row.alignment = new_row.alignment
            self._row.run_spacing = new_row.run_spacing
            self._apply_spacing_to_row(self._row, width)
            self._register_item_styles(page, self._row.controls)
            self._update_section_layout(width)
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}

        def _orientation_changed(orientation: str) -> None:
            normalized = orientation.lower()
            if normalized not in {"portrait", "landscape"}:
                return
            self._current_orientation = normalized
            if self.theme:
                device_name = self._resolve_device_name(page.width or 0)
                self.theme.apply_theme(
                    device=device_name,
                    orientation=normalized,
                    width=page.width or 0,
                )
            self._update_section_layout(page.width or 0)

        orientation_callbacks = {
            "portrait": _orientation_changed,
            "landscape": _orientation_changed,
        }

        self._manager = ResponsiveManager(
            page,
            callbacks,
            orientation_callbacks=orientation_callbacks,
        )
        self._register_item_styles(page, row.controls, self._manager)
        return layout

    # ------------------------------------------------------------------
    def _register_item_styles(
        self,
        page: ft.Page,
        containers: Sequence[ft.Control],
        manager: ResponsiveManager | None = None,
    ) -> None:
        has_styles = any(
            isinstance(getattr(control, "_fletplus_responsive_style", None), ResponsiveStyle)
            for control in containers
        )
        if not has_styles:
            return

        target_manager = manager or self._manager or getattr(page, "_fletplus_responsive_grid_manager", None)
        if target_manager is None:
            target_manager = ResponsiveManager(page)
            setattr(page, "_fletplus_responsive_grid_manager", target_manager)
        self._manager = target_manager

        for control in containers:
            style = getattr(control, "_fletplus_responsive_style", None)
            if isinstance(style, ResponsiveStyle):
                target_manager.register_styles(control, style)
