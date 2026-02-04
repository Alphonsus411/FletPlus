from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import flet as ft

from fletplus.styles import Style
from fletplus.utils.responsive_breakpoints import BreakpointRegistry
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.components.responsive_container import (
    ResponsiveContainer as _CanonicalResponsiveContainer,
)


# Alias para mantener compatibilidad con la ruta histórica.
ResponsiveContainer = _CanonicalResponsiveContainer


class _FlexBase:
    def __init__(
        self,
        controls: list[ft.Control],
        breakpoints: Mapping[int | str, dict] | None = None,
        style: Style | None = None,
    ):
        self.controls = controls or []
        mapping = dict(breakpoints) if breakpoints else {0: {}}
        self.breakpoints = ResponsiveManager.normalize_breakpoints(mapping)
        self.style = style

    def _get_config(self, width: int) -> dict:
        config: dict = {}
        for bp, cfg in sorted(self.breakpoints.items()):
            if width >= bp:
                config = cfg
        return config


class FlexRow(_FlexBase):
    """Fila flexible que recalcula espaciado, alineación y envoltura."""

    def init_responsive(self, page: ft.Page) -> ft.Control:
        cfg = self._get_config(page.width or 0)
        row = ft.Row(
            controls=self.controls,
            spacing=cfg.get("spacing", 0),
            alignment=cfg.get("alignment", ft.MainAxisAlignment.START),
            wrap=cfg.get("wrap", False),
        )
        layout = self.style.apply(row) if self.style else row
        target = layout.content if self.style else layout

        def rebuild(width: int) -> None:
            cfg = self._get_config(width)
            target.spacing = cfg.get("spacing", target.spacing)
            target.alignment = cfg.get("alignment", target.alignment)
            target.wrap = cfg.get("wrap", target.wrap)
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}
        ResponsiveManager(page, callbacks)
        return layout


class FlexColumn(_FlexBase):
    """Columna flexible que recalcula espaciado y alineación."""

    def init_responsive(self, page: ft.Page) -> ft.Control:
        cfg = self._get_config(page.width or 0)
        column = ft.Column(
            controls=self.controls,
            spacing=cfg.get("spacing", 0),
            alignment=cfg.get("alignment", ft.MainAxisAlignment.START),
            scroll=cfg.get("wrap", False),
        )
        layout = self.style.apply(column) if self.style else column
        target = layout.content if self.style else layout

        def rebuild(width: int) -> None:
            cfg = self._get_config(width)
            target.spacing = cfg.get("spacing", target.spacing)
            target.alignment = cfg.get("alignment", target.alignment)
            target.scroll = cfg.get("wrap", target.scroll)
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}
        ResponsiveManager(page, callbacks)
        return layout


@dataclass
class StackItem:
    control: ft.Control
    visible_breakpoints: Mapping[int | str, bool] | None = None

    def __post_init__(self) -> None:
        self._visibility = (
            BreakpointRegistry.normalize(self.visible_breakpoints)
            if self.visible_breakpoints
            else {}
        )

    def is_visible(self, width: int) -> bool:
        if not self._visibility:
            return True
        visible: bool | None = None
        for bp, value in sorted(self._visibility.items()):
            if width >= bp:
                visible = bool(value)
        return True if visible is None else bool(visible)


class Stack:
    """Pila de controles con visibilidad adaptable por breakpoint."""

    def __init__(
        self,
        items: Sequence[StackItem | ft.Control] | None = None,
        *,
        alignment_breakpoints: Mapping[int | str, ft.Alignment] | None = None,
    ) -> None:
        self.items = [self._ensure_item(item) for item in (items or [])]
        self.alignment_breakpoints = (
            BreakpointRegistry.normalize(alignment_breakpoints)
            if alignment_breakpoints
            else {}
        )

    @staticmethod
    def _ensure_item(item: StackItem | ft.Control) -> StackItem:
        if isinstance(item, StackItem):
            return item
        return StackItem(control=item)

    def _resolve_alignment(self, width: int) -> ft.Alignment:
        alignment = ft.alignment.top_left
        for bp, value in sorted(self.alignment_breakpoints.items()):
            if width >= bp:
                alignment = value
        return alignment

    def _collect_breakpoints(self) -> set[int]:
        bps = set(self.alignment_breakpoints.keys())
        for item in self.items:
            bps.update(getattr(item, "_visibility", {}).keys())
        return bps

    def init_responsive(self, page: ft.Page) -> ft.Stack:
        stack = ft.Stack(
            controls=[item.control for item in self.items],
            alignment=self._resolve_alignment(page.width or 0),
        )

        def rebuild(width: int) -> None:
            stack.alignment = self._resolve_alignment(width)
            for item in self.items:
                item.control.visible = item.is_visible(width)
            page.update()

        breakpoints = self._collect_breakpoints()
        if not breakpoints:
            breakpoints = {0}
        callbacks = {bp: rebuild for bp in breakpoints}
        ResponsiveManager(page, callbacks)
        rebuild(page.width or 0)
        return stack


@dataclass
class GridItem:
    control: ft.Control
    span: int | None = None
    span_breakpoints: Mapping[int | str, int] | None = None
    visible_breakpoints: Mapping[int | str, bool] | None = None

    def __post_init__(self) -> None:
        self._span_breakpoints = (
            BreakpointRegistry.normalize(self.span_breakpoints)
            if self.span_breakpoints
            else {}
        )
        self._visibility = (
            BreakpointRegistry.normalize(self.visible_breakpoints)
            if self.visible_breakpoints
            else {}
        )

    def resolve_span(self, width: int) -> int:
        span = self.span if self.span is not None else 12
        for bp, value in sorted(self._span_breakpoints.items()):
            if width >= bp:
                span = int(value)
        return max(1, min(12, span))

    def is_visible(self, width: int) -> bool:
        if not self._visibility:
            return True
        visible: bool | None = None
        for bp, value in sorted(self._visibility.items()):
            if width >= bp:
                visible = bool(value)
        return True if visible is None else bool(visible)


class Grid:
    """Grid simplificada basada en ``ResponsiveRow`` con spans dinámicos."""

    def __init__(
        self,
        items: Sequence[GridItem | ft.Control] | None = None,
        *,
        spacing: int = 10,
        spacing_breakpoints: Mapping[int | str, int] | None = None,
    ) -> None:
        self.items = [self._ensure_item(item) for item in (items or [])]
        self.spacing = max(0, int(spacing))
        self.spacing_breakpoints = (
            BreakpointRegistry.normalize(spacing_breakpoints)
            if spacing_breakpoints
            else {}
        )

    @staticmethod
    def _ensure_item(item: GridItem | ft.Control) -> GridItem:
        if isinstance(item, GridItem):
            return item
        return GridItem(control=item)

    def _resolve_spacing(self, width: int) -> int:
        spacing = self.spacing
        for bp, value in sorted(self.spacing_breakpoints.items()):
            if width >= bp:
                spacing = int(value)
        return max(0, spacing)

    def _collect_breakpoints(self) -> set[int]:
        mappings = [self.spacing_breakpoints]
        for item in self.items:
            mappings.append(getattr(item, "_span_breakpoints", {}))
            mappings.append(getattr(item, "_visibility", {}))
        values = set()
        for mapping in mappings:
            if mapping:
                values.update(mapping.keys())
        return values

    def init_responsive(self, page: ft.Page) -> ft.ResponsiveRow:
        row = ft.ResponsiveRow(spacing=self.spacing, run_spacing=self.spacing)
        wrappers: list[tuple[GridItem, ft.Container]] = []
        width = page.width or 0
        for item in self.items:
            wrapper = ft.Container(content=item.control)
            wrapper.col = item.resolve_span(width)
            wrapper.visible = item.is_visible(width)
            row.controls.append(wrapper)
            wrappers.append((item, wrapper))

        def rebuild(current_width: int) -> None:
            spacing = self._resolve_spacing(current_width)
            row.spacing = spacing
            row.run_spacing = spacing
            for item, wrapper in wrappers:
                wrapper.col = item.resolve_span(current_width)
                wrapper.visible = item.is_visible(current_width)
            page.update()

        breakpoints = self._collect_breakpoints()
        if not breakpoints:
            breakpoints = {0}
        callbacks = {bp: rebuild for bp in breakpoints}
        ResponsiveManager(page, callbacks)
        rebuild(width)
        return row


class Wrap(_FlexBase):
    """Fila envolvente cuyo espaciado puede adaptarse a breakpoints simbólicos."""

    def __init__(
        self,
        controls: list[ft.Control],
        breakpoints: Mapping[int | str, dict] | None = None,
        style: Style | None = None,
    ) -> None:
        super().__init__(controls, breakpoints=breakpoints, style=style)

    def init_responsive(self, page: ft.Page) -> ft.Control:
        cfg = self._get_config(page.width or 0)
        row = ft.Row(
            controls=self.controls,
            wrap=True,
            spacing=cfg.get("spacing", 0),
            run_spacing=cfg.get("run_spacing", cfg.get("spacing", 0)),
            alignment=cfg.get("alignment", ft.MainAxisAlignment.START),
        )
        layout = self.style.apply(row) if self.style else row
        target = layout.content if self.style else layout

        def rebuild(width: int) -> None:
            cfg = self._get_config(width)
            target.spacing = cfg.get("spacing", target.spacing)
            target.run_spacing = cfg.get("run_spacing", target.run_spacing)
            target.alignment = cfg.get("alignment", target.alignment)
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}
        ResponsiveManager(page, callbacks)
        return layout


class Spacer:
    """Control invisible que ajusta su tamaño según el breakpoint."""

    def __init__(
        self,
        *,
        orientation: str = "horizontal",
        breakpoints: Mapping[int | str, int] | None = None,
    ) -> None:
        self.orientation = orientation
        self.breakpoints = (
            BreakpointRegistry.normalize(breakpoints)
            if breakpoints
            else {0: 0}
        )

    def init_responsive(self, page: ft.Page) -> ft.Container:
        width = page.width or 0
        size = self._resolve_size(width)
        container = ft.Container(width=size if self._is_horizontal else None)
        if not self._is_horizontal:
            container.height = size

        def rebuild(current_width: int) -> None:
            value = self._resolve_size(current_width)
            if self._is_horizontal:
                container.width = value
            else:
                container.height = value
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}
        ResponsiveManager(page, callbacks)
        return container

    @property
    def _is_horizontal(self) -> bool:
        return self.orientation.lower() != "vertical"

    def _resolve_size(self, width: int) -> int:
        size = 0
        for bp, value in sorted(self.breakpoints.items()):
            if width >= bp:
                size = int(value)
        return max(0, size)
