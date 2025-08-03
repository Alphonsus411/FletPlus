"""Gestor de breakpoints para responder a cambios de tamaño de la página."""

from __future__ import annotations

import flet as ft
from typing import Callable, Dict

from fletplus.styles import Style


class ResponsiveManager:
    """Observa cambios en ancho, alto y orientación ejecutando callbacks.

    También permite aplicar estilos diferentes a controles según el breakpoint
    actual del ancho de la página.
    """

    def __init__(
        self,
        page: ft.Page,
        breakpoints: Dict[int, Callable[[int], None]] | None = None,
        height_breakpoints: Dict[int, Callable[[int], None]] | None = None,
        orientation_callbacks: Dict[str, Callable[[str], None]] | None = None,
    ):
        self.page = page
        self.breakpoints = breakpoints or {}
        self.height_breakpoints = height_breakpoints or {}
        self.orientation_callbacks = orientation_callbacks or {}

        self._current_width_bp: int | None = None
        self._current_height_bp: int | None = None
        self._current_orientation: str | None = None

        # Registro de estilos por control: {control: {bp: Style}}
        self._styles: Dict[ft.Control, Dict[int, Style]] = {}

        self.page.on_resize = self._handle_resize
        self._handle_resize()

    # ------------------------------------------------------------------
    def register_styles(self, control: ft.Control, styles: Dict[int, Style]) -> None:
        """Registra ``styles`` para ``control``.

        ``styles`` es un diccionario donde la clave es el breakpoint de ancho y
        el valor es una instancia de :class:`Style` que se aplica cuando el ancho
        actual pertenece a dicho breakpoint.
        """

        self._styles[control] = styles
        self._apply_style(control)

    # ------------------------------------------------------------------
    def _apply_style(self, control: ft.Control) -> None:
        styles = self._styles.get(control)
        if not styles:
            return

        width = self.page.width or 0
        bp = max((bp for bp in styles if width >= bp), default=None)
        style = styles.get(bp)
        if style:
            style.apply(control)

    # ------------------------------------------------------------------
    def _handle_resize(self, e: ft.ControlEvent | None = None) -> None:
        width = self.page.width or 0
        height = self.page.height or 0

        # Breakpoints por ancho
        bp_w = max((bp for bp in self.breakpoints if width >= bp), default=None)
        if bp_w != self._current_width_bp:
            self._current_width_bp = bp_w
            callback = self.breakpoints.get(bp_w)
            if callback:
                callback(width)

        # Breakpoints por alto
        bp_h = max((bp for bp in self.height_breakpoints if height >= bp), default=None)
        if bp_h != self._current_height_bp:
            self._current_height_bp = bp_h
            callback = self.height_breakpoints.get(bp_h)
            if callback:
                callback(height)

        # Orientación
        orientation = "landscape" if width >= height else "portrait"
        if orientation != self._current_orientation:
            self._current_orientation = orientation
            callback = self.orientation_callbacks.get(orientation)
            if callback:
                callback(orientation)

        # Aplicar estilos
        for control in list(self._styles):
            self._apply_style(control)

        self.page.update()
