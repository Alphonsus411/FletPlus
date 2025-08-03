"""Contenedor responsive basado en :class:`ResponsiveStyle`."""

from __future__ import annotations

from typing import Callable, Dict

import flet as ft
from fletplus.utils.responsive_style import ResponsiveStyle
from fletplus.utils.responsive_manager import ResponsiveManager


class ResponsiveContainer:
    """Contenedor que aplica estilos según los breakpoints definidos."""

    def __init__(
        self,
        content: ft.Control,
        styles: ResponsiveStyle,
        breakpoints: Dict[int, Callable[[int], None]] | None = None,
    ) -> None:
        self.content = content
        self.styles = styles
        self.breakpoints = breakpoints or {}

    def build(self, page: ft.Page) -> ft.Control:
        """Devuelve el control con estilos responsivos aplicados."""
        target = (
            self.content
            if isinstance(self.content, ft.Container)
            else ft.Container(content=self.content)
        )

        def apply_style() -> None:
            style = self.styles.get_style(page)
            if not style:
                return
            styled = style.apply(self.content)
            container_attrs = [
                "padding",
                "margin",
                "bgcolor",
                "border_radius",
                "width",
                "height",
                "min_width",
                "max_width",
                "min_height",
                "max_height",
                "shadow",
                "gradient",
                "alignment",
                "opacity",
                "border",
                "image_src",
                "image_fit",
            ]
            for attr in container_attrs:
                setattr(target, attr, getattr(styled, attr, getattr(target, attr, None)))

        apply_style()

        width_bps = set(self.styles.width.keys()) | set(self.breakpoints.keys())
        height_bps = set(self.styles.height.keys())
        orientation_keys = set(self.styles.orientation.keys())

        callbacks: Dict[int, Callable[[int], None]] = {}

        for bp in width_bps:
            def make_cb(bp: int) -> Callable[[int], None]:
                def cb(width: int) -> None:
                    apply_style()
                    if bp in self.breakpoints:
                        self.breakpoints[bp](width)
                return cb

            callbacks[bp] = make_cb(bp)

        height_callbacks = {bp: lambda _h: apply_style() for bp in height_bps}
        orientation_callbacks = {o: lambda _o: apply_style() for o in orientation_keys}

        ResponsiveManager(
            page,
            breakpoints=callbacks,
            height_breakpoints=height_callbacks,
            orientation_callbacks=orientation_callbacks,
        )

        return target
