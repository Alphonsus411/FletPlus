"""Agrupa las utilidades expuestas por :mod:`fletplus.utils`.

Al centralizar aquí las importaciones más habituales evitamos que los usuarios
tengan que navegar por submódulos internos (``responsive_style``,
``responsive_typography``, etc.) cuando trabajan desde un entorno donde sólo
se dispone del paquete instalado. Esto reduce los errores de ``ImportError``
causados por rutas relativas o internas que pueden cambiar entre versiones.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

LAZY_IMPORTS = {
    "ResponsiveStyle": "fletplus.utils.responsive_style",
    "ResponsiveTypography": "fletplus.utils.responsive_typography",
    "responsive_text": "fletplus.utils.responsive_typography",
    "responsive_spacing": "fletplus.utils.responsive_typography",
    "ResponsiveManager": "fletplus.utils.responsive_manager",
    "BreakpointRegistry": "fletplus.utils.responsive_breakpoints",
    "ShortcutManager": "fletplus.utils.shortcut_manager",
    "FileDropZone": "fletplus.utils.dragdrop",
    "ResponsiveVisibility": "fletplus.utils.responsive_visibility",
    "is_mobile": "fletplus.utils.device",
    "is_web": "fletplus.utils.device",
    "is_desktop": "fletplus.utils.device",
    "DeviceProfile": "fletplus.utils.device_profiles",
    "DEFAULT_DEVICE_PROFILES": "fletplus.utils.device_profiles",
    "device_name": "fletplus.utils.device_profiles",
    "columns_for_width": "fletplus.utils.device_profiles",
    "AccessibilityPreferences": "fletplus.utils.accessibility",
}

if TYPE_CHECKING:
    from fletplus.utils.accessibility import AccessibilityPreferences
    from fletplus.utils.device import is_desktop, is_mobile, is_web
    from fletplus.utils.device_profiles import (
        DEFAULT_DEVICE_PROFILES,
        DeviceProfile,
        columns_for_width,
        device_name,
    )
    from fletplus.utils.dragdrop import FileDropZone
    from fletplus.utils.responsive_breakpoints import BreakpointRegistry
    from fletplus.utils.responsive_manager import ResponsiveManager
    from fletplus.utils.responsive_style import ResponsiveStyle
    from fletplus.utils.responsive_typography import (
        ResponsiveTypography,
        responsive_spacing,
        responsive_text,
    )
    from fletplus.utils.responsive_visibility import ResponsiveVisibility
    from fletplus.utils.shortcut_manager import ShortcutManager

__all__ = [
    "ResponsiveStyle",
    "ResponsiveTypography",
    "responsive_text",
    "responsive_spacing",
    "ResponsiveManager",
    "BreakpointRegistry",
    "ShortcutManager",
    "FileDropZone",
    "ResponsiveVisibility",
    "is_mobile",
    "is_web",
    "is_desktop",
    "DeviceProfile",
    "DEFAULT_DEVICE_PROFILES",
    "device_name",
    "columns_for_width",
    "AccessibilityPreferences",
]


def __getattr__(name: str) -> Any:
    if name in LAZY_IMPORTS:
        module = importlib.import_module(LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(set(__all__))
