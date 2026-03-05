"""Parche de compatibilidad legacy para la API pública de Flet.

Este módulo encapsula los parches opcionales que históricamente se aplicaban en
``fletplus.__init__``. A partir de esta versión, la activación es explícita:
la aplicación debe invocar :func:`enable_compat_patches` cuando realmente
necesite el comportamiento legacy.
"""

from __future__ import annotations

import os
from typing import Any

import flet as ft

LEGACY_PATCHES_ENV_VAR = "FLETPLUS_ENABLE_LEGACY_PATCHES"
"""Variable de entorno que gobierna la activación de parches legacy."""


_TRUTHY_VALUES = frozenset({"1", "true", "yes", "on", "enabled"})
_FALSY_VALUES = frozenset({"0", "false", "no", "off", "disabled"})


def is_legacy_patch_enabled_from_env(default: bool = False) -> bool:
    """Indica si los parches legacy están habilitados por entorno.

    La variable soporta valores booleanos comunes. Si se define un valor no
    reconocido, se devuelve ``default`` para evitar romper el inicio de la app.
    """

    raw_value = os.getenv(LEGACY_PATCHES_ENV_VAR)
    if raw_value is None:
        return default

    value = raw_value.strip().lower()
    if value in _TRUTHY_VALUES:
        return True
    if value in _FALSY_VALUES:
        return False
    return default


def _patch_page_size_aliases() -> None:
    page = ft.Page

    if (getattr(page, "width", None) is None) and (getattr(page, "window_width", None) is None):

        def _get_width(self):  # type: ignore[no-redef]
            win = getattr(self, "window", None)
            if win is not None and hasattr(win, "width"):
                return getattr(win, "width")
            return getattr(self, "__dict__", {}).get("width", None)

        def _set_width(self, value):  # type: ignore[no-redef]
            win = getattr(self, "window", None)
            if win is not None and hasattr(win, "width"):
                try:
                    setattr(win, "width", value)
                    return
                except Exception:
                    pass
            try:
                self.__dict__["width"] = value
            except Exception:
                pass

        ft.Page.width = property(_get_width, _set_width)  # type: ignore[assignment]

    if (getattr(page, "height", None) is None) and (getattr(page, "window_height", None) is None):

        def _get_height(self):  # type: ignore[no-redef]
            win = getattr(self, "window", None)
            if win is not None and hasattr(win, "height"):
                return getattr(win, "height")
            return getattr(self, "__dict__", {}).get("height", None)

        def _set_height(self, value):  # type: ignore[no-redef]
            win = getattr(self, "window", None)
            if win is not None and hasattr(win, "height"):
                try:
                    setattr(win, "height", value)
                    return
                except Exception:
                    pass
            try:
                self.__dict__["height"] = value
            except Exception:
                pass

        ft.Page.height = property(_get_height, _set_height)  # type: ignore[assignment]


def _patch_text_button_compat() -> None:
    original_text_button = ft.TextButton

    class _TextButtonCompat(original_text_button):
        def __init__(self, *args, text: Any = None, content: Any = None, **kwargs):
            if content is not None and "content" not in kwargs:
                kwargs["content"] = content
            if not args and text is not None and "content" not in kwargs:
                kwargs["content"] = text
            super().__init__(*args, **kwargs)

    ft.TextButton = _TextButtonCompat  # type: ignore[assignment]


def _patch_icon_compat() -> None:
    original_icon = ft.Icon

    class _IconCompat(original_icon):
        def __init__(self, *args, name: Any = None, icon: Any = None, **kwargs):
            if name is not None and not args:
                args = (name,)
            elif icon is not None and not args:
                args = (icon,)
            super().__init__(*args, **kwargs)

    ft.Icon = _IconCompat  # type: ignore[assignment]


def enable_compat_patches(force: bool | None = None) -> bool:
    """Aplica parches de compatibilidad legacy de forma idempotente.

    Args:
        force: si es ``True`` aplica siempre los parches. Si es ``False`` no
            aplica nada. Si es ``None``, se decide usando
            :func:`is_legacy_patch_enabled_from_env`.

    Returns:
        ``True`` cuando los parches quedan activos; ``False`` cuando no se
        activan por configuración.
    """

    should_enable = force if force is not None else is_legacy_patch_enabled_from_env()
    if not should_enable:
        return False

    if getattr(ft, "_fletplus_patched_controls", False):
        return True

    try:
        _patch_page_size_aliases()
    except Exception:
        pass

    try:
        _patch_text_button_compat()
    except Exception:
        pass

    try:
        _patch_icon_compat()
    except Exception:
        pass

    try:
        setattr(ft, "_fletplus_patched_controls", True)
    except Exception:
        pass

    return True
