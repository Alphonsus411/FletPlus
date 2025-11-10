"""Agrupa las utilidades expuestas por :mod:`fletplus.utils`.

Al centralizar aquí las importaciones más habituales evitamos que los usuarios
tengan que navegar por submódulos internos (``responsive_style``,
``responsive_typography``, etc.) cuando trabajan desde un entorno donde sólo
se dispone del paquete instalado. Esto reduce los errores de ``ImportError``
causados por rutas relativas o internas que pueden cambiar entre versiones.
"""

from fletplus.utils.device import is_mobile, is_web, is_desktop
from fletplus.utils.device_profiles import (
    DeviceProfile,
    DEFAULT_DEVICE_PROFILES,
    device_name,
    columns_for_width,
)
from fletplus.utils.accessibility import AccessibilityPreferences
from fletplus.utils.dragdrop import FileDropZone
from fletplus.utils.responsive_breakpoints import BreakpointRegistry
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.utils.responsive_style import ResponsiveStyle
from fletplus.utils.responsive_typography import (
    ResponsiveTypography,
    responsive_text,
    responsive_spacing,
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
