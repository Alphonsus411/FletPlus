import asyncio
import inspect
from typing import Awaitable, Callable, Dict, Tuple

import flet as ft


class ShortcutManager:
    """Gestiona combinaciones de teclas para ejecutar callbacks."""

    def __init__(self, page: ft.Page):
        self.page = page
        self._shortcuts: Dict[Tuple[str, bool, bool, bool], Callable] = {}
        self._previous_handler = getattr(page, "on_keyboard_event", None)
        self._disposed = False
        self.page.on_keyboard_event = self._handle_event

    def dispose(self) -> None:
        """Libera recursos y restaura el handler previo de teclado."""
        if self._disposed:
            return

        self.page.on_keyboard_event = self._previous_handler
        self._shortcuts.clear()
        self._disposed = True

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
        if self._disposed:
            return

        key = (e.key or "").lower()
        combo = (key, e.ctrl, e.shift, e.alt)
        callback = self._shortcuts.get(combo)
        try:
            if callback:
                result = callback()
                if inspect.isawaitable(result):
                    if callable(getattr(self.page, "run_task", None)):
                        self.page.run_task(result)
                    else:
                        self._run_awaitable_fallback(result)
        finally:
            if callable(self._previous_handler):
                self._previous_handler(e)

    @staticmethod
    def _run_awaitable_fallback(result: Awaitable) -> None:
        """Ejecuta awaitables sin ``page.run_task`` y evita corutinas sin esperar.

        Si existe loop activo, agenda la tarea con ``asyncio.ensure_future``.
        En caso contrario, ejecuta el awaitable de forma bloqueante con ``asyncio.run``.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(ShortcutManager._await_result(result))
        else:
            asyncio.ensure_future(result)

    @staticmethod
    async def _await_result(result: Awaitable) -> None:
        await result
