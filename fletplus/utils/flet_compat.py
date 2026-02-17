"""Compatibilidad defensiva para APIs de :mod:`flet` sensibles a versión.

Este módulo concentra accesos a atributos/métodos que han cambiado entre
versiones de Flet o no están disponibles en todos los targets (desktop/web).
La idea es encapsular *feature detection* y fallbacks en un único lugar para
que el resto del código no dependa de accesos dinámicos dispersos.

Atributos de compatibilidad actualmente cubiertos
------------------------------------------------
- ``Page.window``: puede no existir según plataforma/runner.
- ``Window.<attr>`` (``width``, ``height``, ``visible``, ``resizable``,
  ``left``, ``top``, ``skip_taskbar``): no todos los atributos están
  presentes en todas las combinaciones de versión/OS.
- ``Page.update_async`` vs ``Page.update``.
- ``Page.screenshot_async`` vs ``Page.screenshot`` vs invocación interna
  ``Page._invoke_method_async('screenshot', ...)``.
- ``Window.destroy`` vs ``Window.close``.

Cómo extender esta capa
-----------------------
1. Añade una función pequeña y explícita (p. ej. ``safe_foo(...)``) con
   contrato claro (retorno booleano, ``None`` o excepción controlada).
2. Implementa detección por capacidades con ``getattr(..., None)`` y
   ``callable(...)``.
3. Usa ``contextlib.suppress`` para blindar errores de compatibilidad donde
   el fallo no deba romper la ejecución.
4. Cubre ausencia/presencia en tests unitarios para asegurar fallback sin
   excepciones.
"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import Any


def get_page_window(page: Any) -> Any | None:
    """Devuelve ``page.window`` si existe; en caso contrario ``None``."""

    return getattr(page, "window", None)


def safe_set_window_attr(page: Any, attr: str, value: Any) -> bool:
    """Asigna un atributo de ``window`` cuando existe, sin lanzar excepción."""

    window = get_page_window(page)
    if window is None or not hasattr(window, attr):
        return False
    with contextlib.suppress(Exception):
        setattr(window, attr, value)
        return True
    return False


def safe_close_window(page: Any) -> bool:
    """Intenta cerrar la ventana con ``destroy`` o ``close``."""

    window = get_page_window(page)
    if window is None:
        return False

    for attr in ("destroy", "close"):
        method = getattr(window, attr, None)
        if callable(method):
            with contextlib.suppress(Exception):
                method()
                return True
    return False


async def safe_update_page(page: Any) -> None:
    """Actualiza la página usando ``update_async`` o fallback a ``update``."""

    update_async = getattr(page, "update_async", None)
    if callable(update_async):
        await update_async()
        return

    update = getattr(page, "update", None)
    if callable(update):
        update()


async def safe_take_screenshot(page: Any, path: Path) -> None:
    """Captura screenshot con el mejor método disponible para la versión."""

    screenshot_async = getattr(page, "screenshot_async", None)
    if callable(screenshot_async):
        await screenshot_async(path=str(path))
        return

    screenshot = getattr(page, "screenshot", None)
    if callable(screenshot):
        result = screenshot(path=str(path))
        if asyncio.iscoroutine(result):
            await result
        return

    invoke_method = getattr(page, "_invoke_method_async", None)
    if callable(invoke_method):
        await invoke_method(
            "screenshot",
            {"path": str(path)},
            wait_for_result=True,
            wait_timeout=30,
        )
