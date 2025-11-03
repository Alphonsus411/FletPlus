"""Atajos de importación para el paquete :mod:`fletplus`.

La intención es que las aplicaciones consumidoras puedan realizar importaciones
absolutas estables como ``from fletplus import ThemeManager`` sin depender de
la estructura interna de submódulos. Esto evita errores de importación cuando
se distribuye la librería y mejora la experiencia para los usuarios finales.
"""

from fletplus.core import FletPlusApp
from fletplus.router import Router, Route, LayoutInstance, layout_from_attribute
from fletplus.themes import (
    ThemeManager,
    load_palette_from_file,
    list_palettes,
    get_palette_tokens,
    has_palette,
    get_palette_definition,
)
from fletplus.components import (
    PrimaryButton,
    SecondaryButton,
    SuccessButton,
    WarningButton,
    DangerButton,
    InfoButton,
    IconButton,
    OutlinedButton,
    TextButton,
    FloatingActionButton,
    CommandPalette,
    AccessibilityPanel,
    AdaptiveDestination,
    AdaptiveNavigationLayout,
    FlexRow,
    FlexColumn,
    ResponsiveContainer,
    ResponsiveGrid,
    SidebarAdmin,
    SmartTable,
    LineChart,
)
from fletplus.utils import (
    ResponsiveStyle,
    ResponsiveTypography,
    responsive_text,
    responsive_spacing,
    ResponsiveManager,
    ShortcutManager,
    FileDropZone,
    ResponsiveVisibility,
    is_mobile,
    is_web,
    is_desktop,
)
from fletplus.desktop import WindowManager, SystemTray, show_notification
from fletplus.web import (
    generate_manifest,
    generate_service_worker,
    register_pwa,
)

__all__ = [
    "FletPlusApp",
    "ThemeManager",
    "load_palette_from_file",
    "list_palettes",
    "get_palette_tokens",
    "has_palette",
    "get_palette_definition",
    "PrimaryButton",
    "SecondaryButton",
    "SuccessButton",
    "WarningButton",
    "DangerButton",
    "InfoButton",
    "IconButton",
    "OutlinedButton",
    "TextButton",
    "FloatingActionButton",
    "CommandPalette",
    "AccessibilityPanel",
    "AdaptiveDestination",
    "AdaptiveNavigationLayout",
    "FlexRow",
    "FlexColumn",
    "ResponsiveContainer",
    "ResponsiveGrid",
    "SidebarAdmin",
    "SmartTable",
    "LineChart",
    "ResponsiveStyle",
    "ResponsiveTypography",
    "responsive_text",
    "responsive_spacing",
    "ResponsiveManager",
    "ShortcutManager",
    "FileDropZone",
    "ResponsiveVisibility",
    "is_mobile",
    "is_web",
    "is_desktop",
    "WindowManager",
    "SystemTray",
    "show_notification",
    "generate_manifest",
    "generate_service_worker",
    "register_pwa",
    "Router",
    "Route",
    "LayoutInstance",
    "layout_from_attribute",
]
