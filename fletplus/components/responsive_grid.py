"""Grid responsiva con soporte para span adaptable y estilos por dispositivo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import flet as ft

from fletplus.styles import Style
from fletplus.themes.theme_manager import ThemeManager
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.utils.responsive_style import ResponsiveStyle


DeviceName = str


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


def _clone_padding(padding: ft.Padding | None) -> ft.Padding | None:
    if padding is None:
        return None
    return ft.Padding(padding.left, padding.top, padding.right, padding.bottom)


def _device_from_width(width: int) -> DeviceName:
    """Clasifica ``width`` en *mobile*, *tablet* o *desktop*.

    Los límites coinciden con los breakpoints por defecto de ``ResponsiveGrid``.
    """

    if width < 600:
        return "mobile"
    if width < 900:
        return "tablet"
    return "desktop"


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
        Diccionario ``{"mobile"|"tablet"|"desktop": span}`` que permite
        personalizar aún más cada dispositivo.
    style:
        Estilo opcional aplicado al contenedor del item.
    responsive_style:
        Instancia de :class:`ResponsiveStyle` aplicada automáticamente cuando el
        grid se registra mediante :meth:`ResponsiveGrid.init_responsive`.
    """

    control: ft.Control
    span: int | None = None
    span_breakpoints: Dict[int, int] | None = None
    span_devices: Dict[DeviceName, int] | None = None
    style: Style | None = None
    responsive_style: ResponsiveStyle | Dict[int, Style] | None = None

    def resolve_span(self, width: int, columns: int) -> int:
        device = _device_from_width(width)
        if self.span_devices and device in self.span_devices:
            return self._sanitize_span(self.span_devices[device])

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


class ResponsiveGrid:
    def __init__(
        self,
        children: Sequence[ft.Control] | None = None,
        columns: int | None = None,
        breakpoints: Dict[int, int] | None = None,
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
        section_padding: Dict[str, object] | ft.Padding | int | float | None = None,
        section_gap: int = 18,
        section_background: str | None = None,
        section_gradient_token: str | None = None,
        section_gradient: ft.Gradient | None = None,
        section_border_radius: ft.BorderRadius | float | None = None,
        section_shadow: ft.BoxShadow | Sequence[ft.BoxShadow] | None = None,
        section_max_content_width: int | None = None,
        theme: ThemeManager | None = None,
    ) -> None:
        """Grid responsiva basada en breakpoints.

        ``ResponsiveGrid`` admite ahora span personalizados para cada item y
        estilos adaptables según dispositivo, lo que permite diseñar interfaces
        diferenciadas para web, escritorio y móviles con un único componente.
        """

        self.spacing = spacing
        self.style = style
        self.run_spacing = run_spacing
        self.alignment = alignment or ft.MainAxisAlignment.START
        self.section_gap = section_gap
        self.theme = theme

        self.section_title = header_title
        self.section_subtitle = header_subtitle
        self.section_description = header_description
        self.section_background = section_background
        self.section_gradient_token = section_gradient_token
        self.section_gradient = section_gradient
        self.section_border_radius = section_border_radius
        self.section_shadow = section_shadow
        self.section_max_content_width = section_max_content_width
        self._section_actions_row = ft.Row(
            controls=list(header_actions or []), spacing=12, wrap=True
        )
        self._section_metadata_row = ft.Row(
            controls=list(header_metadata or []), spacing=12, wrap=True, run_spacing=10
        )
        self._section_icon_control: ft.Control | None
        if isinstance(header_icon, ft.Control):
            self._section_icon_control = header_icon
        elif isinstance(header_icon, str):
            self._section_icon_control = ft.Icon(header_icon, size=30)
        else:
            self._section_icon_control = None

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
            }
        else:
            self._section_padding_config = {}

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
                bool(self._section_padding_config),
            ]
        )

        self._items = [ResponsiveGridItem(control=child) for child in (children or [])]
        if items:
            self._items.extend(items)

        if columns is not None:
            self.breakpoints = {0: columns}
        else:
            self.breakpoints = breakpoints or {0: 1, 600: 2, 900: 3, 1200: 4}

        self._manager: ResponsiveManager | None = None
        self._row: ft.ResponsiveRow | None = None
        self._section_container: ft.Container | None = None
        self._section_column: ft.Column | None = None
        self._section_header_container: ft.Container | None = None
        self._layout_root: ft.Control | None = None

    # ------------------------------------------------------------------
    def _resolve_columns(self, width: int) -> int:
        columns = 1
        for bp, cols in sorted(self.breakpoints.items()):
            if width >= bp:
                columns = cols
        return max(1, columns)

    # ------------------------------------------------------------------
    def _build_item_container(
        self,
        item: ResponsiveGridItem,
        width: int,
        columns: int,
    ) -> ft.Container:
        content: ft.Control = item.control
        if item.style:
            styled = item.style.apply(content)
            if isinstance(styled, ft.Control):
                content = styled

        container = ft.Container(
            content=content,
            col=item.resolve_span(width, columns),
            padding=self.spacing,
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
        return ft.ResponsiveRow(
            controls=[self._build_item_container(item, width, columns) for item in self._items],
            alignment=self.alignment,
            run_spacing=self.run_spacing,
        )

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
        if self.section_max_content_width:
            inner = ft.Container(width=self.section_max_content_width, content=column)
            wrapper = ft.Column(
                controls=[inner],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            content = wrapper

        container = ft.Container(content=content)
        self._section_container = container
        return container

    # ------------------------------------------------------------------
    def _resolve_section_padding(self, device: DeviceName) -> ft.Padding:
        padding = (
            self._section_padding_config.get(device)
            or self._section_padding_config.get("mobile")
            or ft.Padding(20, 20, 20, 20)
        )
        return _clone_padding(padding) or ft.Padding(20, 20, 20, 20)

    # ------------------------------------------------------------------
    def _resolve_section_background(self) -> str | None:
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
    def _resolve_section_gradient(self) -> ft.Gradient | None:
        if self.section_gradient is not None:
            return self.section_gradient
        if self.theme and self.section_gradient_token:
            gradient = self.theme.get_gradient(self.section_gradient_token)
            if gradient is not None:
                return gradient
        return None

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
    def _update_section_layout(self, width: int) -> None:
        if not self._section_container:
            return

        device = _device_from_width(width)
        padding = self._resolve_section_padding(device)
        self._section_container.padding = padding

        gradient = self._resolve_section_gradient()
        if gradient:
            self._section_container.gradient = gradient
            self._section_container.bgcolor = None
        else:
            self._section_container.gradient = None
            self._section_container.bgcolor = self._resolve_section_background()

        if isinstance(self.section_border_radius, ft.BorderRadius):
            self._section_container.border_radius = self.section_border_radius
        elif self.section_border_radius is not None:
            try:
                radius_value = float(self.section_border_radius)
            except (TypeError, ValueError):
                radius_value = 20
            self._section_container.border_radius = ft.border_radius.all(radius_value)

        if self.section_shadow is None:
            self._section_container.shadow = ft.BoxShadow(
                blur_radius=22,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.12, "#000000"),
                offset=ft.Offset(0, 10),
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

        device = _device_from_width(width)

        title_size = {"mobile": 20, "tablet": 22, "desktop": 24}
        subtitle_size = {"mobile": 15, "tablet": 16, "desktop": 18}

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
                size=14 if device == "mobile" else 15,
                color=(
                    self.theme.get_color("on_surface_variant")
                    if self.theme
                    else ft.Colors.GREY_700
                ),
            )

        text_controls: list[ft.Control] = []
        if title_control:
            text_controls.append(title_control)
        if subtitle_control:
            text_controls.append(subtitle_control)
        if description_control:
            text_controls.append(description_control)

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

        if self._section_metadata_row.controls:
            self._section_metadata_row.alignment = (
                ft.MainAxisAlignment.CENTER if device == "mobile" else ft.MainAxisAlignment.START
            )
            metadata_control: ft.Control | None = self._section_metadata_row
        else:
            metadata_control = None

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
                self._section_actions_row.alignment = ft.MainAxisAlignment.CENTER
                mobile_controls.append(self._section_actions_row)

            header_layout = ft.Column(
                controls=mobile_controls,
                spacing=10,
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
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=False,
            )

            if device == "tablet":
                self._section_actions_row.wrap = True
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
                self._section_actions_row.alignment = ft.MainAxisAlignment.END
                row_controls: list[ft.Control] = [left_block]
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

        layout = self.build(page.width)
        row = self._row
        if row is None:
            return layout

        def rebuild(width: int) -> None:
            if self._row is None:
                return
            new_row = self._build_row(width)
            self._row.controls.clear()
            self._row.controls.extend(new_row.controls)
            self._row.alignment = new_row.alignment
            self._row.run_spacing = new_row.run_spacing
            self._register_item_styles(page, self._row.controls)
            self._update_section_layout(width)
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}
        self._manager = ResponsiveManager(page, callbacks)
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
