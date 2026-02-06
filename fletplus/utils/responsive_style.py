"""Definiciones de estilos adaptables a distintos breakpoints."""

from __future__ import annotations

from typing import Dict, Mapping, Optional

import flet as ft

from fletplus.styles import Style
from fletplus.utils.responsive_breakpoints import BreakpointRegistry
from fletplus.utils.breakpoint_rs import select_breakpoint

try:  # soporte opcional para detección de dispositivo
    _device_module = __import__("fletplus.utils.device", fromlist=["device"])
except ImportError:  # pragma: no cover - ejecutando como script
    _device_module = None  # type: ignore


def _is_mobile(page: ft.Page) -> bool:
    """Detecta si la página corre en un dispositivo móvil."""

    if _device_module and hasattr(_device_module, "is_mobile"):
        try:
            return bool(_device_module.is_mobile(page))
        except Exception:  # pragma: no cover - defensivo ante implementaciones externas
            pass
    return getattr(page, "platform", None) in {"android", "ios"}


def _is_tablet(page: ft.Page) -> bool:
    """Determina si la ventana actual corresponde a una tableta."""

    if _device_module and hasattr(_device_module, "is_tablet"):
        try:
            return bool(_device_module.is_tablet(page))
        except Exception:  # pragma: no cover - defensivo ante implementaciones externas
            pass
    width = page.width or 0
    return 600 <= width < 1024 and getattr(page, "platform", None) not in {"windows", "macos", "linux"}


def _is_web(page: ft.Page) -> bool:
    """Detecta si la página corre en un entorno web."""

    if _device_module and hasattr(_device_module, "is_web"):
        try:
            return bool(_device_module.is_web(page))
        except Exception:  # pragma: no cover - defensivo
            pass
    return getattr(page, "platform", None) == "web"


def _is_desktop(page: ft.Page) -> bool:
    """Detecta si la página corre en un escritorio."""

    if _device_module and hasattr(_device_module, "is_desktop"):
        try:
            return bool(_device_module.is_desktop(page))
        except Exception:  # pragma: no cover - defensivo
            pass
    return getattr(page, "platform", None) in {"windows", "macos", "linux"}


def _is_large_desktop(page: ft.Page) -> bool:
    """Detecta estaciones de trabajo o monitores ultraanchos."""

    if _device_module and hasattr(_device_module, "is_large_desktop"):
        try:
            return bool(_device_module.is_large_desktop(page))
        except Exception:  # pragma: no cover - defensivo ante implementaciones externas
            pass
    width = page.width or 0
    return width >= 1440 and _is_desktop(page)


class ResponsiveStyle:
    """Asocia varios :class:`Style` a condiciones responsivas.

    Parameters
    ----------
    width
        Mapeo ``{breakpoint_minimo: Style}`` aplicado según el ancho.
    height
        Mapeo ``{breakpoint_minimo: Style}`` aplicado según el alto.
    orientation
        Estilos por orientación: ``{"portrait"|"landscape": Style}``.
    device
        Estilos por tipo de dispositivo ``{"mobile"|"web"|"desktop": Style}``.
    base
        Estilo base que se fusiona con el resto.
    """

    def __init__(
        self,
        *,
        width: Optional[Mapping[int | str, Style]] = None,
        height: Optional[Mapping[int | str, Style]] = None,
        orientation: Optional[Dict[str, Style]] = None,
        device: Optional[Dict[str, Style]] = None,
        base: Optional[Style] = None,
    ) -> None:
        self.width = BreakpointRegistry.normalize(width) if width else {}
        self.height = BreakpointRegistry.normalize(height) if height else {}
        self._width_keys = sorted(self.width)
        self._height_keys = sorted(self.height)
        self.orientation = orientation or {}
        self.device = device or {}
        self.base = base

    # ------------------------------------------------------------------
    def _select_bp(self, mapping: Dict[int, Style], keys: list[int], value: int) -> Optional[Style]:
        bp = select_breakpoint(keys, value)
        if bp is None:
            return None
        return mapping.get(bp)

    # ------------------------------------------------------------------
    def _merge(self, a: Optional[Style], b: Optional[Style]) -> Optional[Style]:
        if b is None:
            return a
        if a is None:
            return b
        declared = b.declared_fields()
        data = {field: value for field, value in a.__dict__.items() if field != "_declared_fields"}
        for field, value in b.__dict__.items():
            if field == "_declared_fields":
                continue
            if value is not None or field in declared:
                data[field] = value
        return Style(**data)

    # ------------------------------------------------------------------
    def get_style(self, page: ft.Page) -> Optional[Style]:
        """Devuelve el :class:`Style` adecuado para ``page``."""

        style = self.base

        # Dispositivo
        if self.device:
            if _is_mobile(page) and "mobile" in self.device:
                style = self._merge(style, self.device["mobile"])
            elif _is_tablet(page) and "tablet" in self.device:
                style = self._merge(style, self.device["tablet"])
            elif _is_web(page) and "web" in self.device:
                style = self._merge(style, self.device["web"])
            elif _is_large_desktop(page) and "large_desktop" in self.device:
                if "desktop" in self.device:
                    style = self._merge(style, self.device["desktop"])
                style = self._merge(style, self.device["large_desktop"])
            elif _is_desktop(page) and "desktop" in self.device:
                style = self._merge(style, self.device["desktop"])

        # Breakpoints por ancho
        if self.width:
            w_style = self._select_bp(self.width, self._width_keys, page.width or 0)
            style = self._merge(style, w_style)

        # Breakpoints por alto
        if self.height:
            h_style = self._select_bp(self.height, self._height_keys, page.height or 0)
            style = self._merge(style, h_style)

        # Orientación
        if self.orientation:
            orientation = "landscape" if (page.width or 0) >= (page.height or 0) else "portrait"
            o_style = self.orientation.get(orientation)
            style = self._merge(style, o_style)

        return style
