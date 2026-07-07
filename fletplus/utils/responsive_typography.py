"""Utilidades para tipografía y espaciado responsivo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict
from weakref import WeakKeyDictionary

import flet as ft

from fletplus.frontend.config import FrontEndConfig
from fletplus.utils.responsive_manager import ResponsiveManager

if TYPE_CHECKING:
    from fletplus.themes.theme_manager import ThemeManager

# Registro global por página para reutilizar la instancia
_INSTANCES: "WeakKeyDictionary[ft.Page, ResponsiveTypography]" = WeakKeyDictionary()


class ResponsiveTypography:
    """Ajusta tamaño de texto y espaciado según el ancho de la página."""

    def __init__(
        self,
        page: ft.Page,
        theme: "ThemeManager | None" = None,
        text_sizes: Dict[int, int] | None = None,
        spacings: Dict[int, int] | None = None,
        config: FrontEndConfig | None = None,
        default_role: str = "body",
    ) -> None:
        self.page = page
        self.theme = theme
        self.config = config or FrontEndConfig()
        self.default_role = default_role
        self._text_sizes = text_sizes or {0: 14, 600: 18, 900: 24}
        self._spacings = spacings or {0: 8, 600: 12, 900: 16}
        self._texts: list[tuple[ft.Text, str | None]] = []
        self._spacing_controls: list[ft.Control] = []
        callbacks = {bp: self._update for bp in set(self._text_sizes) | set(self._spacings)}
        self._manager = ResponsiveManager(page, breakpoints=callbacks)
        _INSTANCES[page] = self
        self.current_text_size: int = 0
        self.current_spacing: int = 0
        self._update(page.width or 0)
        self._register_cleanup()

    def _register_cleanup(self) -> None:
        def _cleanup(_: ft.ControlEvent) -> None:
            _INSTANCES.pop(self.page, None)

        for attr in ("on_close", "on_disconnect"):
            existing = getattr(self.page, attr, None)
            if existing is None:
                setattr(self.page, attr, _cleanup)
            else:
                def _combined(event: ft.ControlEvent, *, _existing=existing) -> None:
                    _existing(event)
                    _cleanup(event)

                setattr(self.page, attr, _combined)

    def register_text(self, text: ft.Text, role: str | None = None) -> ft.Text:
        """Registra ``text`` para actualizar su estilo tipográfico automáticamente.

        ``role`` puede ser ``display``, ``headline``, ``title``, ``body``,
        ``label`` o ``caption``. Si se omite, mantiene la compatibilidad usando
        el tamaño legacy de ``responsive_text``.
        """
        self._texts.append((text, role))
        self._apply_text_style(text, role)
        return text

    def _apply_text_style(self, text: ft.Text, role: str | None) -> None:
        if text.style is None:
            text.style = ft.TextStyle()
        if role is None:
            text.style.size = self.current_text_size
            return
        values = self.config.resolve_typography(role, int(self.page.width or 0))
        text.style.size = values.get("size", self.current_text_size)
        text.style.weight = values.get("weight")
        text.style.height = values.get("line_height")

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
        for txt, role in self._texts:
            self._apply_text_style(txt, role)
        for ctrl in self._spacing_controls:
            if hasattr(ctrl, "padding"):
                ctrl.padding = self.current_spacing
        if self.theme is not None:
            self.theme.tokens.setdefault("spacing", {})["default"] = self.current_spacing
            self.theme.tokens.setdefault("typography", {}).update(
                self.config.resolved_typography_tokens()
            )
            self.theme.apply_theme()


def _get_instance(page: ft.Page) -> ResponsiveTypography:
    inst = _INSTANCES.get(page)
    if inst is None:
        inst = ResponsiveTypography(page)
    return inst


def responsive_text(page: ft.Page, role: str = "body") -> int | float | None:
    """Devuelve el tamaño de texto recomendado para ``page`` y ``role``."""
    inst = _get_instance(page)
    if role == "body":
        return inst.current_text_size
    return inst.config.typography_size(role, int(page.width or 0))


def responsive_spacing(page: ft.Page) -> int:
    """Devuelve el espaciado recomendado para ``page``."""
    return _get_instance(page).current_spacing
