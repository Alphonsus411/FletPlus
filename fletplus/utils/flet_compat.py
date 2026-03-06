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

Política de uso de APIs internas (temporal y de retirada)
---------------------------------------------------------
- Regla principal: priorizar siempre API pública de Flet (``ft.Icons``,
  ``ft.icons``, ``ft.Alignment``, ``ft.alignment``, ``ft.transform``, etc.).
- APIs internas (``flet.controls.*``) sólo se usan como último recurso
  temporal cuando la API pública no está disponible.
- Cada uso de fallback interno emite telemetría de warning estructurada una
  sola vez por símbolo, para detectar cambios de compatibilidad pronto.
- Criterio de retirada: eliminar cada fallback interno antes de
  ``2026-06-30`` o en la primera versión mínima soportada de Flet donde la
  API pública correspondiente esté estabilizada en CI, lo que ocurra antes.

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
import inspect
import importlib
import logging
import os
from pathlib import Path
from threading import current_thread, main_thread
from typing import Any

import flet as _ft


class _FtProxy:
    __slots__ = ("_m",)
    def __init__(self, module):
        object.__setattr__(self, "_m", module)
    def __getattr__(self, name: str):
        return getattr(self._m, name)
    def __setattr__(self, name: str, value):
        setattr(self._m, name, value)
    def __delattr__(self, name: str):
        try:
            delattr(self._m, name)
        except (AttributeError, TypeError) as exc:
            # Tolerar eliminación repetida o símbolos dinámicos ausentes
            _logger.debug(
                "No se pudo eliminar símbolo en proxy ft: symbol=%s flet_version=%s error=%r",
                name,
                getattr(_ft, "__version__", "unknown"),
                exc,
            )
    @property
    def __dict__(self):
        return self._m.__dict__

ft = _FtProxy(_ft)
_logger = logging.getLogger(__name__)
_WARNED_COMPAT_KEYS: set[str] = set()


def _warn_once(event: str, symbol: str, **context: Any) -> None:
    """Emite warning estructurado una sola vez por símbolo/evento."""

    warning_id = f"{event}:{symbol}"
    if warning_id in _WARNED_COMPAT_KEYS:
        return
    _WARNED_COMPAT_KEYS.add(warning_id)
    _logger.warning(
        "event=%s symbol=%s context=%s",
        event,
        symbol,
        context,
        extra={
            "event": event,
            "symbol": symbol,
            "context": context,
        },
    )


def _resolve_internal_symbol(
    module_path: str,
    *,
    attr: str | None = None,
    default: Any = None,
    warning_key: str | None = None,
) -> Any:
    """Resuelve símbolos internos de Flet con fallback y warning controlado."""

    try:
        module = importlib.import_module(module_path)
    except (ModuleNotFoundError, ImportError) as exc:
        if warning_key is not None:
            _warn_once(
                "fletplus.compat.internal_import_unavailable",
                warning_key,
                module_path=module_path,
                attr=attr,
                error=repr(exc),
            )
        return default

    if warning_key is not None:
        _warn_once(
            "fletplus.compat.internal_fallback_used",
            warning_key,
            module_path=module_path,
            attr=attr,
        )

    if attr is None:
        return module
    return getattr(module, attr, default)


def _resolve_public_first_symbol(
    *,
    public_candidates: tuple[str, ...],
    internal_module_path: str,
    internal_attr: str | None = None,
    default: Any = None,
    warning_key: str,
) -> Any:
    """Resuelve símbolo priorizando API pública y sólo luego internals."""

    for candidate in public_candidates:
        public_symbol = getattr(_ft, candidate, None)
        if public_symbol is not None:
            return public_symbol

    return _resolve_internal_symbol(
        internal_module_path,
        attr=internal_attr,
        default=default,
        warning_key=warning_key,
    )

LEGACY_PAGE_WINDOW_PATCH_ENV_VAR = "FLETPLUS_ENABLE_LEGACY_PAGE_WINDOW_PATCH"
"""Variable de entorno para habilitar explícitamente el parche legacy de ``Page.window``."""

_TRUTHY_VALUES = frozenset({"1", "true", "yes", "on", "enabled"})
_FALSY_VALUES = frozenset({"0", "false", "no", "off", "disabled"})

# Proveer alias ft.icons en entornos donde no exista (compatibilidad de tests y monkeypatch)
if not hasattr(ft, "icons"):
    _icons_mod = _resolve_public_first_symbol(
        public_candidates=("icons", "Icons"),
        internal_module_path="flet.controls.material.icons",
        default=type("icons", (), {})(),
        warning_key="icons_namespace",
    )
    try:
        setattr(ft, "icons", _icons_mod)
    except (AttributeError, TypeError) as exc:
        _logger.warning(
            "No se pudo exponer alias ft.icons: symbol=icons flet_version=%s fallback=namespace error=%r",
            getattr(_ft, "__version__", "unknown"),
            exc,
        )
if "Icons" not in getattr(ft, "__dict__", {}):
    try:
        _icons_cls = _resolve_public_first_symbol(
            public_candidates=("Icons", "icons"),
            internal_module_path="flet.controls.material.icons",
            internal_attr="Icons",
            warning_key="icons_class",
        )
        if _icons_cls is None:
            _icons_cls = type("Icons", (), {})()
        setattr(ft, "Icons", _icons_cls)
    except (AttributeError, TypeError) as exc:
        _logger.warning(
            "Fallo al resolver alias ft.Icons primario: symbol=Icons flet_version=%s fallback=namespace_vacio error=%r",
            getattr(_ft, "__version__", "unknown"),
            exc,
        )
        try:
            setattr(ft, "Icons", type("Icons", (), {})())
        except (AttributeError, TypeError) as fallback_exc:
            _logger.warning(
                "Fallo al aplicar fallback ft.Icons vacío: symbol=Icons flet_version=%s fallback=omitido error=%r",
                getattr(_ft, "__version__", "unknown"),
                fallback_exc,
            )

# Alias de `ft.transform` cuando no exista (compatibilidad con código legacy)
if not hasattr(ft, "transform"):
    _transform_mod = _resolve_public_first_symbol(
        public_candidates=("transform",),
        internal_module_path="flet.controls.transform",
        warning_key="transform_namespace",
    )
    if _transform_mod is None:
        # Fallback mínimo: objeto con Offset/Scale/Rotate si existen a nivel top
        _transform_mod = type(
            "transform",
            (),
            {
                "Offset": getattr(_ft, "Offset", object),
                "Scale": getattr(_ft, "Scale", object),
                "Rotate": getattr(_ft, "Rotate", object),
            },
        )()
    try:
        setattr(ft, "transform", _transform_mod)
    except (AttributeError, TypeError) as exc:
        _logger.warning(
            "No se pudo exponer alias ft.transform: symbol=transform flet_version=%s fallback=namespace_transform error=%r",
            getattr(_ft, "__version__", "unknown"),
            exc,
        )

# Completar constantes de alineación comunes si faltan
try:
    _alignment_mod = _resolve_public_first_symbol(
        public_candidates=("alignment", "Alignment"),
        internal_module_path="flet.controls.alignment",
        warning_key="alignment_namespace",
    )
    if _alignment_mod is None:
        raise RuntimeError("alignment namespace unavailable")
    _align_defaults = {
        "top_left": (-1, -1),
        "top_center": (0, -1),
        "top_right": (1, -1),
        "center_left": (-1, 0),
        "center": (0, 0),
        "center_right": (1, 0),
        "bottom_left": (-1, 1),
        "bottom_center": (0, 1),
        "bottom_right": (1, 1),
    }
    for _name, (_x, _y) in _align_defaults.items():
        if not hasattr(_alignment_mod, _name):
            try:
                setattr(_alignment_mod, _name, _ft.Alignment(_x, _y))
            except (AttributeError, TypeError) as exc:
                _logger.debug(
                    "No se pudo completar constante de alineación: symbol=%s flet_version=%s fallback=constante_omitida error=%r",
                    _name,
                    getattr(_ft, "__version__", "unknown"),
                    exc,
                )
except (AttributeError, TypeError, RuntimeError) as exc:
    _logger.warning(
        "No se pudo completar namespace de alineación: symbol=alignment flet_version=%s fallback=omitido error=%r",
        getattr(_ft, "__version__", "unknown"),
        exc,
    )

def is_legacy_page_window_patch_enabled_from_env(default: bool = False) -> bool:
    """Indica si el parche legacy de ``Page.window`` se activa por entorno."""

    raw_value = os.getenv(LEGACY_PAGE_WINDOW_PATCH_ENV_VAR)
    if raw_value is None:
        return default

    value = raw_value.strip().lower()
    if value in _TRUTHY_VALUES:
        return True
    if value in _FALSY_VALUES:
        return False
    return default


def _has_functional_window_descriptor(page_cls: type[Any]) -> bool:
    """Detecta si ``Page.window`` ya está implementado con descriptor usable."""

    sentinel = object()
    window_attr = inspect.getattr_static(page_cls, "window", sentinel)
    if window_attr is sentinel:
        return False

    if isinstance(window_attr, property):
        return window_attr.fget is not None

    return hasattr(window_attr, "__get__")


def _needs_legacy_page_window_patch(page_cls: type[Any]) -> bool:
    """Determina si ``Page.window`` está ausente o es inequívocamente incompatible."""

    sentinel = object()
    window_attr = inspect.getattr_static(page_cls, "window", sentinel)
    if window_attr is sentinel:
        return True
    if _has_functional_window_descriptor(page_cls):
        return False
    return True


def _patch_page_window_property() -> bool:
    """Aplica el alias legacy de ``Page.window`` únicamente cuando hace falta."""

    page_cls = _ft.Page
    if not _needs_legacy_page_window_patch(page_cls):
        return False

    def _get_window(self):
        return getattr(self, "_window", None)

    setattr(page_cls, "window", property(_get_window))
    return True


def enable_legacy_page_window_patch(force: bool | None = None) -> bool:
    """Habilita el parche legacy de ``Page.window`` bajo bandera explícita."""

    should_enable = force if force is not None else is_legacy_page_window_patch_enabled_from_env()
    if not should_enable:
        return False

    with contextlib.suppress(Exception):
        _patch_page_window_property()
    return True

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


def safe_request_page_update(page: Any) -> None:
    """Solicita un refresh tolerante a contexto/hilo y API disponible.

    Estrategia:
    1) En hilo principal intenta ``page.update()`` directo.
    2) Si existe ``page.run_task``, delega ``update_async`` o ``update``.
    3) Como último fallback, intenta ``update`` de forma protegida.
    """

    if current_thread() is main_thread():
        update = getattr(page, "update", None)
        if callable(update):
            with contextlib.suppress(Exception):
                update()
                return

    run_task = getattr(page, "run_task", None)
    if callable(run_task):
        update_async = getattr(page, "update_async", None)
        if callable(update_async):
            with contextlib.suppress(Exception):
                run_task(update_async)
                return
        update = getattr(page, "update", None)
        if callable(update):
            with contextlib.suppress(Exception):
                run_task(update)
                return

    safe_update_page_sync(page)


def set_page_title(page: Any, title: str) -> bool:
    """Asigna ``page.title`` de forma defensiva."""

    with contextlib.suppress(Exception):
        setattr(page, "title", title)
        return True
    return False


def set_page_drawer(page: Any, drawer: Any) -> bool:
    """Asigna ``page.drawer`` sin propagar errores de compatibilidad."""

    with contextlib.suppress(Exception):
        setattr(page, "drawer", drawer)
        return True
    return False


def append_page_overlay(page: Any, control: Any) -> bool:
    """Añade un control a ``page.overlay`` cuando la colección está disponible."""

    overlay = getattr(page, "overlay", None)
    if overlay is None:
        return False

    append = getattr(overlay, "append", None)
    if callable(append):
        with contextlib.suppress(Exception):
            append(control)
            return True
    return False




def has_page_overlay_control(page: Any, control: Any) -> bool:
    """Comprueba si un control ya está en ``page.overlay`` de forma segura."""

    overlay = getattr(page, "overlay", None)
    if overlay is None:
        return False
    with contextlib.suppress(Exception):
        return control in overlay
    return False

def safe_page_set_focus(page: Any, control: Any) -> bool:
    """Ejecuta ``page.set_focus(control)`` si existe, con fallback seguro."""

    focus = getattr(page, "set_focus", None)
    if callable(focus):
        with contextlib.suppress(Exception):
            focus(control)
            return True
    return False


def safe_page_speak(page: Any, message: str) -> bool:
    """Ejecuta ``page.speak(message)`` cuando esté disponible."""

    speak = getattr(page, "speak", None)
    if callable(speak):
        with contextlib.suppress(Exception):
            speak(message)
            return True
    return False


def get_flet_icons() -> Any | None:
    """Devuelve el namespace de iconos soportado (`Icons` o `icons`).

    Prioriza atributos explícitos del módulo (set por monkeypatch),
    después intenta acceso dinámico."""

    d = getattr(ft, "__dict__", None)
    if isinstance(d, dict):
        return d.get("Icons") or d.get("icons")
    return None


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


def build_flet_control(name: str, /, **kwargs: Any) -> Any:
    """Construye un control de Flet por nombre con detección defensiva.

    Devuelve ``None`` cuando el símbolo no existe o la construcción falla.
    """

    control_cls = getattr(ft, name, None)
    if control_cls is None:
        return None
    with contextlib.suppress(Exception):
        return control_cls(**kwargs)
    return None


def make_navigation_bar_destination(
    *,
    icon: Any,
    label: str,
    selected_icon: Any | None = None,
    tooltip: str | None = None,
) -> Any:
    """Crea un destino de ``NavigationBar`` con fallback seguro."""

    destination = build_flet_control(
        "NavigationBarDestination",
        icon=icon,
        label=label,
        selected_icon=selected_icon if selected_icon is not None else icon,
        tooltip=tooltip,
    )
    if destination is not None:
        return destination
    return ft.Container(content=ft.Text(label))


def make_navigation_rail_destination(
    *,
    icon: Any,
    label: str,
    selected_icon: Any | None = None,
) -> Any:
    """Crea un destino de ``NavigationRail`` con fallback seguro."""

    destination = build_flet_control(
        "NavigationRailDestination",
        icon=icon,
        selected_icon=selected_icon if selected_icon is not None else icon,
        label=label,
    )
    if destination is not None:
        return destination
    return ft.Container(content=ft.Text(label))


def make_navigation_drawer_destination(*, icon: Any, label: str) -> Any:
    """Crea un destino de ``NavigationDrawer`` con fallback seguro."""

    destination = build_flet_control("NavigationDrawerDestination", icon=icon, label=label)
    if destination is not None:
        return destination
    return ft.Container(content=ft.Text(label))


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
