"""Grid responsiva con soporte para span adaptable y estilos por dispositivo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import flet as ft

from fletplus.styles import Style
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.utils.responsive_style import ResponsiveStyle


DeviceName = str


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

        self._items = [ResponsiveGridItem(control=child) for child in (children or [])]
        if items:
            self._items.extend(items)

        if columns is not None:
            self.breakpoints = {0: columns}
        else:
            self.breakpoints = breakpoints or {0: 1, 600: 2, 900: 3, 1200: 4}

        self._manager: ResponsiveManager | None = None

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
    def build(self, page_width: Optional[int]) -> ft.Control:
        width = page_width or 0
        columns = self._resolve_columns(width)

        row = ft.ResponsiveRow(
            controls=[self._build_item_container(item, width, columns) for item in self._items],
            alignment=self.alignment,
            run_spacing=self.run_spacing,
        )

        return self.style.apply(row) if self.style else row

    # ------------------------------------------------------------------
    def init_responsive(self, page: ft.Page) -> ft.Control:
        """Inicializa el grid y reacciona ante cambios de tamaño."""

        layout = self.build(page.width)
        row = layout.content if self.style else layout

        def rebuild(width: int) -> None:
            updated = self.build(width)
            new_row = updated.content if self.style else updated
            row.controls.clear()
            row.controls.extend(new_row.controls)
            self._register_item_styles(page, row.controls)
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
