import flet as ft
from typing import Callable, Dict


class ResponsiveManager:
    """Observa cambios en el ancho de la página y ejecuta callbacks."""

    def __init__(self, page: ft.Page, breakpoints: Dict[int, Callable[[int], None]]):
        self.page = page
        self.breakpoints = breakpoints or {}
        self._current_bp: int | None = None
        self.page.on_resize = self._handle_resize
        self._handle_resize()

    def _handle_resize(self, e: ft.ControlEvent | None = None) -> None:
        width = self.page.width or 0
        bp = max((bp for bp in self.breakpoints if width >= bp), default=None)
        if bp != self._current_bp:
            self._current_bp = bp
            callback = self.breakpoints.get(bp)
            if callback:
                callback(width)
