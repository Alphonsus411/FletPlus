"""Definiciones de estilos adaptables a distintos breakpoints."""

from __future__ import annotations

from typing import Dict, Optional

import flet as ft

from fletplus.styles import Style

try:  # soporte opcional para detección de dispositivo
    from fletplus.utils import device
except ImportError:  # pragma: no cover - el módulo puede no existir
    device = None  # type: ignore


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
        width: Optional[Dict[int, Style]] = None,
        height: Optional[Dict[int, Style]] = None,
        orientation: Optional[Dict[str, Style]] = None,
        device: Optional[Dict[str, Style]] = None,
        base: Optional[Style] = None,
    ) -> None:
        self.width = width or {}
        self.height = height or {}
        self.orientation = orientation or {}
        self.device = device or {}
        self.base = base

    # ------------------------------------------------------------------
    def _select_bp(self, mapping: Dict[int, Style], value: int) -> Optional[Style]:
        bp = max((bp for bp in mapping if value >= bp), default=None)
        if bp is None:
            return None
        return mapping.get(bp)

    # ------------------------------------------------------------------
    def _merge(self, a: Optional[Style], b: Optional[Style]) -> Optional[Style]:
        if b is None:
            return a
        if a is None:
            return b
        data = a.__dict__.copy()
        for field, value in b.__dict__.items():
            if value is not None:
                data[field] = value
        return Style(**data)

    # ------------------------------------------------------------------
    def get_style(self, page: ft.Page) -> Optional[Style]:
        """Devuelve el :class:`Style` adecuado para ``page``."""

        style = self.base

        # Dispositivo
        if device and self.device:
            if device.is_mobile(page) and "mobile" in self.device:
                style = self._merge(style, self.device["mobile"])
            elif device.is_web(page) and "web" in self.device:
                style = self._merge(style, self.device["web"])
            elif device.is_desktop(page) and "desktop" in self.device:
                style = self._merge(style, self.device["desktop"])

        # Breakpoints por ancho
        if self.width:
            w_style = self._select_bp(self.width, page.width or 0)
            style = self._merge(style, w_style)

        # Breakpoints por alto
        if self.height:
            h_style = self._select_bp(self.height, page.height or 0)
            style = self._merge(style, h_style)

        # Orientación
        if self.orientation:
            orientation = "landscape" if (page.width or 0) >= (page.height or 0) else "portrait"
            o_style = self.orientation.get(orientation)
            style = self._merge(style, o_style)

        return style
