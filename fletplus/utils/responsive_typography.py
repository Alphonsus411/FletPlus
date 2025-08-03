"""Utilidades para tipografía y espaciado responsivo."""

from __future__ import annotations

from typing import Dict

import flet as ft

from .responsive_manager import ResponsiveManager
from fletplus.themes.theme_manager import ThemeManager

# Registro global por página para reutilizar la instancia
_INSTANCES: Dict[int, "ResponsiveTypography"] = {}


class ResponsiveTypography:
    """Ajusta tamaño de texto y espaciado según el ancho de la página."""

    def __init__(
        self,
        page: ft.Page,
        theme: ThemeManager | None = None,
        text_sizes: Dict[int, int] | None = None,
        spacings: Dict[int, int] | None = None,
    ) -> None:
        self.page = page
        self.theme = theme
        self._text_sizes = text_sizes or {0: 14, 600: 18, 900: 24}
        self._spacings = spacings or {0: 8, 600: 12, 900: 16}
        self._texts: list[ft.Text] = []
        self._spacing_controls: list[ft.Control] = []
        callbacks = {bp: self._update for bp in set(self._text_sizes) | set(self._spacings)}
        self._manager = ResponsiveManager(page, breakpoints=callbacks)
        _INSTANCES[id(page)] = self
        self.current_text_size: int = 0
        self.current_spacing: int = 0
        self._update(page.width or 0)

    def register_text(self, text: ft.Text) -> ft.Text:
        """Registra ``text`` para actualizar su tamaño automáticamente."""
        self._texts.append(text)
        if text.style is None:
            text.style = ft.TextStyle()
        text.style.size = self.current_text_size
        return text

    def register_spacing_control(self, control: ft.Control) -> ft.Control:
        """Registra un control cuyo ``padding`` seguirá el espaciado actual."""
        self._spacing_controls.append(control)
        if hasattr(control, "padding"):
            control.padding = self.current_spacing
        return control

    def _select(self, mapping: Dict[int, int], value: int) -> int:
        bp = max((bp for bp in mapping if value >= bp), default=0)
        return mapping[bp]

    def _update(self, width: int) -> None:
        self.current_text_size = self._select(self._text_sizes, width)
        self.current_spacing = self._select(self._spacings, width)
        for txt in self._texts:
            if txt.style is None:
                txt.style = ft.TextStyle()
            txt.style.size = self.current_text_size
        for ctrl in self._spacing_controls:
            if hasattr(ctrl, "padding"):
                ctrl.padding = self.current_spacing
        if self.theme is not None:
            self.theme.tokens.setdefault("spacing", {})["default"] = self.current_spacing
            self.theme.apply_theme()


def _get_instance(page: ft.Page) -> ResponsiveTypography:
    inst = _INSTANCES.get(id(page))
    if inst is None:
        inst = ResponsiveTypography(page)
    return inst


def responsive_text(page: ft.Page) -> int:
    """Devuelve el tamaño de texto recomendado para ``page``."""
    return _get_instance(page).current_text_size


def responsive_spacing(page: ft.Page) -> int:
    """Devuelve el espaciado recomendado para ``page``."""
    return _get_instance(page).current_spacing
