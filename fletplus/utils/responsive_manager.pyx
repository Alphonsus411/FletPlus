# cython: language_level=3
"""Gestor de breakpoints para responder a cambios de tamaño de la página."""

import flet as ft
from typing import Callable, Dict, Mapping, Sequence

from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle
from fletplus.utils.device_profiles import (
    DeviceProfile,
    DEFAULT_DEVICE_PROFILES,
    get_device_profile,
)
from fletplus.utils.responsive_breakpoints import BreakpointRegistry
try:  # backend opcional en Rust
    from fletplus.utils.responsive_manager_rs import apply_styles as _apply_styles_rs
except Exception:  # pragma: no cover - fallback limpio
    _apply_styles_rs = None


cdef tuple _STYLE_ATTRS = (
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
)

MISSING = object()


cdef class ResponsiveManager:
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
        device_callbacks: Dict[str, Callable[[str], None]] | None = None,
        device_profiles: Sequence[DeviceProfile] | None = None,
    ):
        self.page = page
        self.breakpoints = {
            BreakpointRegistry.resolve(bp): callback
            for bp, callback in (breakpoints or {}).items()
        }
        self.height_breakpoints = {
            BreakpointRegistry.resolve(bp): callback
            for bp, callback in (height_breakpoints or {}).items()
        }
        self.orientation_callbacks = orientation_callbacks or {}
        self.device_callbacks = device_callbacks or {}
        self.device_profiles = tuple(device_profiles) if device_profiles else DEFAULT_DEVICE_PROFILES

        self._width_bp_keys = tuple(sorted(self.breakpoints, reverse=True))
        self._height_bp_keys = tuple(sorted(self.height_breakpoints, reverse=True))

        self._current_width_bp = None
        self._current_height_bp = None
        self._current_orientation = None
        self._current_device = None

        # Registro de estilos por control
        self._styles = {}
        self._style_state = {}

        previous_handler = getattr(self.page, "on_resize", None)

        def _combined_resize(event: ft.ControlEvent | None = None) -> None:
            self._handle_resize(event)
            if callable(previous_handler):
                previous_handler(event)

        self.page.on_resize = _combined_resize
        self._handle_resize()

    # ------------------------------------------------------------------
    @staticmethod
    def normalize_breakpoints(mapping: Mapping[int | str, dict]) -> dict[int, dict]:
        """Normaliza un ``mapping`` de breakpoints usando el registro."""

        return BreakpointRegistry.normalize(mapping)

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
        base = self._capture_base_attributes(control)
        self._style_state[control] = {
            "base": base,
        }
        try:
            setattr(control, "__fletplus_base_attrs__", base)
        except AttributeError:
            pass
        try:
            setattr(rstyle, "_fletplus_page", self.page)
        except AttributeError:
            pass
        self._apply_style(control)

    # ------------------------------------------------------------------
    cpdef void _apply_style(self, object control):
        cdef dict state = self._style_state.get(control)
        cdef dict base
        cdef object rstyle = self._styles.get(control)
        cdef object style
        cdef object styled_container
        cdef tuple attrs = _STYLE_ATTRS
        cdef object attr
        cdef object value

        if rstyle is None:
            return

        if state is None:
            state = {"base": self._capture_base_attributes(control)}
            self._style_state[control] = state

        base = state["base"]
        for attr in attrs:
            value = base.get(attr, MISSING)
            if value is not MISSING:
                self._safe_setattr(control, attr, value)

        style = rstyle.get_style(self.page)
        if not style:
            return

        styled_container = style.apply(control)

        for attr in attrs:
            if hasattr(control, attr):
                value = getattr(styled_container, attr, None)
                if value is not None:
                    self._safe_setattr(control, attr, value)

    # ------------------------------------------------------------------
    cpdef dict _capture_base_attributes(self, object control):
        cdef dict base = {}
        cdef tuple attrs = _STYLE_ATTRS
        cdef object attr
        cdef object value

        for attr in attrs:
            value = getattr(control, attr, MISSING)
            if value is not MISSING:
                base[attr] = value
        return base

    # ------------------------------------------------------------------
    cpdef void _safe_setattr(self, object control, str attr, object value):
        try:
            setattr(control, attr, value)
        except AttributeError:
            pass

    # ------------------------------------------------------------------
    cpdef void _handle_resize(self, object e=None):
        cdef object page = self.page
        cdef double width = page.width if page.width is not None else 0
        cdef double height = page.height if page.height is not None else 0

        cdef tuple width_keys = self._width_bp_keys
        cdef tuple height_keys = self._height_bp_keys
        cdef object bp
        cdef object bp_w = None
        cdef object bp_h = None

        # Breakpoints por ancho
        for bp in width_keys:
            if width >= bp:
                bp_w = bp
                break

        if bp_w != self._current_width_bp:
            self._current_width_bp = bp_w
            bp_callback = self.breakpoints.get(bp_w)
            if bp_callback:
                bp_callback(width)

        # Breakpoints por alto
        for bp in height_keys:
            if height >= bp:
                bp_h = bp
                break

        if bp_h != self._current_height_bp:
            self._current_height_bp = bp_h
            bh_callback = self.height_breakpoints.get(bp_h)
            if bh_callback:
                bh_callback(height)

        # Orientación
        orientation = "landscape" if width >= height else "portrait"
        if orientation != self._current_orientation:
            self._current_orientation = orientation
            orientation_callback = self.orientation_callbacks.get(orientation)
            if orientation_callback:
                orientation_callback(orientation)

        # Tipo de dispositivo (según ancho)
        if self.device_callbacks and self.device_profiles:
            profile = get_device_profile(width, self.device_profiles)
            if profile.name != self._current_device:
                self._current_device = profile.name
                device_callback = self.device_callbacks.get(profile.name)
                if device_callback:
                    device_callback(profile.name)

        # Aplicar estilos
        cdef dict styles = self._styles
        cdef object control
        if styles:
            if _apply_styles_rs is not None:
                updates = _apply_styles_rs(list(styles.items()), list(_STYLE_ATTRS))
                for control, attr, value in updates:
                    self._safe_setattr(control, attr, value)
            else:
                for control in styles.keys():
                    self._apply_style(control)

        page.update()
