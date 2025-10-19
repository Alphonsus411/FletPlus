"""Gestor de breakpoints para responder a cambios de tamaño de la página."""

from __future__ import annotations

import flet as ft
from typing import Any, Callable, Dict

from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle


_STYLE_ATTRS = [
    "margin",
    "padding",
    "bgcolor",
    "border_radius",
    "border",
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
    "image_src",
    "image_fit",
    "animate",
    "scale",
    "rotate",
    "offset",
]


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

        # Registro de estilos por control
        self._styles: Dict[ft.Control, ResponsiveStyle] = {}
        self._style_state: Dict[ft.Control, Dict[str, Any]] = {}

        previous_handler = getattr(self.page, "on_resize", None)

        def _combined_resize(event: ft.ControlEvent | None = None) -> None:
            self._handle_resize(event)
            if callable(previous_handler):
                previous_handler(event)

        self.page.on_resize = _combined_resize
        self._handle_resize()

    # ------------------------------------------------------------------
    def register_styles(
        self,
        control: ft.Control,
        styles: Dict[int, Style] | ResponsiveStyle,
    ) -> None:
        """Registra ``styles`` para ``control``.

        ``styles`` puede ser un diccionario ``{breakpoint: Style}`` (por
        compatibilidad retroactiva) o una instancia de
        :class:`ResponsiveStyle`.
        """

        if isinstance(styles, ResponsiveStyle):
            rstyle = styles
        else:
            rstyle = ResponsiveStyle(width=styles)
        self._styles[control] = rstyle
        self._style_state[control] = {
            "base": self._capture_base_attributes(control),
        }
        self._apply_style(control)

    # ------------------------------------------------------------------
    def _apply_style(self, control: ft.Control) -> None:
        rstyle = self._styles.get(control)
        if not rstyle:
            return

        state = self._style_state.setdefault(
            control, {"base": self._capture_base_attributes(control)}
        )

        for attr, value in state["base"].items():
            self._safe_setattr(control, attr, value)

        style = rstyle.get_style(self.page)
        if not style:
            return

        styled_container = style.apply(control)

        for attr in _STYLE_ATTRS:
            if not hasattr(control, attr):
                continue
            value = getattr(styled_container, attr, None)
            if value is not None:
                self._safe_setattr(control, attr, value)

    # ------------------------------------------------------------------
    def _capture_base_attributes(self, control: ft.Control) -> Dict[str, Any]:
        base: Dict[str, Any] = {}
        for attr in _STYLE_ATTRS:
            if hasattr(control, attr):
                base[attr] = getattr(control, attr)
        return base

    # ------------------------------------------------------------------
    @staticmethod
    def _safe_setattr(control: ft.Control, attr: str, value: Any) -> None:
        try:
            setattr(control, attr, value)
        except AttributeError:
            pass

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
