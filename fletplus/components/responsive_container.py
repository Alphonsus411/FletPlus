"""Contenedor responsive basado en :class:`ResponsiveStyle`.

Esta implementación es la fuente oficial de ``ResponsiveContainer`` dentro de
FletPlus.
"""

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
        initial_values = {attr: getattr(target, attr, None) for attr in container_attrs}

        def apply_style() -> None:
            for attr, value in initial_values.items():
                setattr(target, attr, value)

            style = self.styles.get_style(page)
            if not style:
                return

            styled = style.apply(self.content)
            for attr in container_attrs:
                value = getattr(styled, attr, None)
                if style.declares_container_attr(attr) or value is not None:
                    setattr(target, attr, value)

        def run_width_callback(width: int) -> None:
            active_bp = max((bp for bp in self.breakpoints if width >= bp), default=None)
            if active_bp is not None:
                callback = self.breakpoints.get(active_bp)
                if callback:
                    callback(width)

        apply_style()

        width_bps = set(self.styles.width.keys()) | set(self.breakpoints.keys())
        height_bps = set(self.styles.height.keys())
        orientation_keys = set(self.styles.orientation.keys())

        callbacks: Dict[int, Callable[[int], None]] = {}

        for bp in width_bps:
            def make_cb(bp: int) -> Callable[[int], None]:
                def cb(width: int) -> None:
                    apply_style()
                    run_width_callback(width)
                return cb

            callbacks[bp] = make_cb(bp)

        def _height_callback(_height: int) -> None:
            apply_style()
            run_width_callback(page.width or 0)

        height_callbacks = {bp: _height_callback for bp in height_bps}

        def _orientation_callback(_orientation_value: str) -> None:
            apply_style()
            run_width_callback(page.width or 0)

        orientation_callbacks = {
            key: _orientation_callback for key in orientation_keys
        }

        ResponsiveManager(
            page,
            breakpoints=callbacks,
            height_breakpoints=height_callbacks,
            orientation_callbacks=orientation_callbacks,
        )

        return target
