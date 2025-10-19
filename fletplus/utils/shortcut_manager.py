import flet as ft
from typing import Callable, Dict, Tuple


class ShortcutManager:
    """Gestiona combinaciones de teclas para ejecutar callbacks."""

    def __init__(self, page: ft.Page):
        self.page = page
        self._shortcuts: Dict[Tuple[str, bool, bool, bool], Callable] = {}
        self._previous_handler = getattr(page, "on_keyboard_event", None)
        self.page.on_keyboard_event = self._handle_event

    def register(
        self,
        key: str,
        callback: Callable,
        *,
        ctrl: bool = False,
        shift: bool = False,
        alt: bool = False,
    ) -> None:
        """Registra un atajo.

        :param key: tecla principal (ej. "k")
        :param callback: función a ejecutar
        :param ctrl: requiere Ctrl
        :param shift: requiere Shift
        :param alt: requiere Alt
        """
        combo = (key.lower(), ctrl, shift, alt)
        self._shortcuts[combo] = callback

    def _handle_event(self, e: ft.KeyboardEvent) -> None:
        key = (e.key or "").lower()
        combo = (key, e.ctrl, e.shift, e.alt)
        callback = self._shortcuts.get(combo)
        try:
            if callback:
                callback()
        finally:
            if callable(self._previous_handler):
                self._previous_handler(e)
