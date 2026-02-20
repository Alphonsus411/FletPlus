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
- ``Page.open_drawer`` / ``Page.close_drawer`` pueden no existir según target.
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

import flet as ft


def get_page_window(page: Any) -> Any | None:
    """Devuelve ``page.window`` si existe; en caso contrario ``None``."""

    return getattr(page, "window", None)


def get_page_width(page: Any, default: float = 0.0) -> float:
    """Lee el ancho de página priorizando ``page.window.width``.

    Fallbacks soportados:
    1) ``page.window.width`` (API reciente)
    2) ``page.window_width`` (API legacy)
    3) ``page.width`` (medida de viewport)
    """

    window = get_page_window(page)
    if window is not None:
        width = getattr(window, "width", None)
        if isinstance(width, (int, float)):
            return float(width)

    for attr in ("window_width", "width"):
        width = getattr(page, attr, None)
        if isinstance(width, (int, float)):
            return float(width)

    return default


def set_page_width(page: Any, width: float) -> bool:
    """Escribe el ancho usando la mejor API disponible sin lanzar excepción."""

    window = get_page_window(page)
    if window is not None and hasattr(window, "width"):
        with contextlib.suppress(Exception):
            setattr(window, "width", width)
            return True

    for attr in ("window_width", "width"):
        if hasattr(page, attr):
            with contextlib.suppress(Exception):
                setattr(page, attr, width)
                return True

    with contextlib.suppress(Exception):
        setattr(page, "width", width)
        return True

    return False


def get_page_height(page: Any, default: float = 0.0) -> float:
    """Lee el alto de página priorizando ``page.window.height``."""

    window = get_page_window(page)
    if window is not None:
        height = getattr(window, "height", None)
        if isinstance(height, (int, float)):
            return float(height)

    for attr in ("window_height", "height"):
        height = getattr(page, attr, None)
        if isinstance(height, (int, float)):
            return float(height)

    return default


def set_page_height(page: Any, height: float) -> bool:
    """Escribe el alto usando la mejor API disponible sin lanzar excepción."""

    window = get_page_window(page)
    if window is not None and hasattr(window, "height"):
        with contextlib.suppress(Exception):
            setattr(window, "height", height)
            return True

    for attr in ("window_height", "height"):
        if hasattr(page, attr):
            with contextlib.suppress(Exception):
                setattr(page, attr, height)
                return True

    with contextlib.suppress(Exception):
        setattr(page, "height", height)
        return True

    return False


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


def safe_update_page_sync(page: Any) -> None:
    """Actualiza la página en contexto síncrono sin propagar errores de compat."""

    update = getattr(page, "update", None)
    if callable(update):
        with contextlib.suppress(Exception):
            update()


def get_flet_icons() -> Any | None:
    """Devuelve el namespace de iconos soportado (`Icons` o `icons`)."""

    return getattr(ft, "Icons", None) or getattr(ft, "icons", None)


def get_flet_colors() -> Any | None:
    """Devuelve el namespace de colores soportado (`Colors` o `colors`)."""

    return getattr(ft, "Colors", None) or getattr(ft, "colors", None)


def get_flet_icon(name: str, default: Any = None) -> Any:
    """Obtiene un icono por nombre con fallback seguro."""

    icons = get_flet_icons()
    if icons is None:
        return default
    return getattr(icons, name, default)


def get_flet_color(name: str, default: Any = None) -> Any:
    """Obtiene un color por nombre con fallback seguro."""

    colors = get_flet_colors()
    if colors is None:
        return default
    return getattr(colors, name, default)


def get_flet_enum(enum_name: str) -> Any | None:
    """Devuelve un enum/namespace de Flet por nombre si existe."""

    return getattr(ft, enum_name, None)


def get_flet_enum_member(enum_name: str, member: str, default: Any = None) -> Any:
    """Obtiene un miembro de enum de Flet con detección de presencia."""

    enum_obj = get_flet_enum(enum_name)
    if enum_obj is None:
        return default
    return getattr(enum_obj, member, default)


def with_opacity(opacity: float, color: Any, default: Any = None) -> Any:
    """Aplica opacidad usando la API de colores disponible (`with_opacity`)."""

    colors = get_flet_colors()
    if colors is None:
        return default if default is not None else color
    with_opacity_fn = getattr(colors, "with_opacity", None)
    if not callable(with_opacity_fn):
        return default if default is not None else color
    with contextlib.suppress(Exception):
        return with_opacity_fn(opacity, color)
    return default if default is not None else color


def safe_open_drawer(page: Any) -> bool:
    """Abre el drawer si la API está disponible para la versión actual."""

    open_drawer = getattr(page, "open_drawer", None)
    if callable(open_drawer):
        with contextlib.suppress(Exception):
            open_drawer()
            return True
    return False


def safe_close_drawer(page: Any) -> bool:
    """Cierra el drawer con la API disponible (``close_drawer`` o ``drawer.open``)."""

    close_drawer = getattr(page, "close_drawer", None)
    if callable(close_drawer):
        with contextlib.suppress(Exception):
            close_drawer()
            return True

    drawer = getattr(page, "drawer", None)
    if drawer is not None and hasattr(drawer, "open"):
        with contextlib.suppress(Exception):
            setattr(drawer, "open", False)
            return True

    return False


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
