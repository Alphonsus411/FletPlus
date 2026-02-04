"""Gestor de breakpoints para responder a cambios de tamaño de la página."""
from __future__ import annotations

import importlib
import importlib.util
from typing import Callable, Dict, Mapping, Sequence

import flet as ft

from fletplus.styles import Style
from fletplus.utils.device_profiles import (
    DeviceProfile,
    DEFAULT_DEVICE_PROFILES,
    get_device_profile,
)
from fletplus.utils.responsive_breakpoints import BreakpointRegistry
from fletplus.utils.responsive_manager_rs import apply_styles as _apply_styles_rs
from fletplus.utils.responsive_style import ResponsiveStyle

_STYLE_ATTRS = (
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

_spec = importlib.util.find_spec("fletplus.utils._native")
if _spec is None:
    _native = None
else:
    _native = importlib.import_module("fletplus.utils._native")

if _native is not None and hasattr(_native, "ResponsiveManager"):
    ResponsiveManager = _native.ResponsiveManager
else:

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
            device_callbacks: Dict[str, Callable[[str], None]] | None = None,
            device_profiles: Sequence[DeviceProfile] | None = None,
        ) -> None:
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
            self.device_profiles = (
                tuple(device_profiles) if device_profiles else DEFAULT_DEVICE_PROFILES
            )

            self._width_bp_keys = tuple(sorted(self.breakpoints, reverse=True))
            self._height_bp_keys = tuple(sorted(self.height_breakpoints, reverse=True))

            self._current_width_bp = None
            self._current_height_bp = None
            self._current_orientation = None
            self._current_device = None

            self._styles: dict[ft.Control, ResponsiveStyle] = {}
            self._style_state: dict[ft.Control, dict[str, dict[str, object]]] = {}

            previous_handler = getattr(self.page, "on_resize", None)

            def _combined_resize(event: ft.ControlEvent | None = None) -> None:
                self._handle_resize(event)
                if callable(previous_handler):
                    previous_handler(event)

            self.page.on_resize = _combined_resize
            self._handle_resize()

        # ------------------------------------------------------------------
        @staticmethod
        def normalize_breakpoints(
            mapping: Mapping[int | str, dict],
        ) -> dict[int, dict]:
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
        def _apply_style(self, control: ft.Control) -> None:
            state = self._style_state.get(control)
            rstyle = self._styles.get(control)

            if rstyle is None:
                return

            if state is None:
                state = {"base": self._capture_base_attributes(control)}
                self._style_state[control] = state

            base = state["base"]
            for attr in _STYLE_ATTRS:
                value = base.get(attr, MISSING)
                if value is not MISSING:
                    self._safe_setattr(control, attr, value)

            style = rstyle.get_style(self.page)
            if not style:
                return

            styled_container = style.apply(control)

            for attr in _STYLE_ATTRS:
                if hasattr(control, attr):
                    value = getattr(styled_container, attr, None)
                    if value is not None:
                        self._safe_setattr(control, attr, value)

        # ------------------------------------------------------------------
        def _capture_base_attributes(self, control: ft.Control) -> dict[str, object]:
            base: dict[str, object] = {}
            for attr in _STYLE_ATTRS:
                value = getattr(control, attr, MISSING)
                if value is not MISSING:
                    base[attr] = value
            return base

        # ------------------------------------------------------------------
        @staticmethod
        def _safe_setattr(control: ft.Control, attr: str, value: object) -> None:
            try:
                setattr(control, attr, value)
            except AttributeError:
                pass

        # ------------------------------------------------------------------
        def _handle_resize(self, _event: ft.ControlEvent | None = None) -> None:
            page = self.page
            width = page.width if page.width is not None else 0
            height = page.height if page.height is not None else 0

            bp_w = None
            bp_h = None

            # Breakpoints por ancho
            for bp in self._width_bp_keys:
                if width >= bp:
                    bp_w = bp
                    break

            if bp_w != self._current_width_bp:
                self._current_width_bp = bp_w
                bp_callback = self.breakpoints.get(bp_w)
                if bp_callback:
                    bp_callback(width)

            # Breakpoints por alto
            for bp in self._height_bp_keys:
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
            if self._styles:
                updates = _apply_styles_rs(list(self._styles.items()), list(_STYLE_ATTRS))
                for control, attr, value in updates:
                    self._safe_setattr(control, attr, value)

            page.update()


__all__ = ["ResponsiveManager"]
