"""Punto de entrada público para los componentes de FletPlus.

Este módulo reúne las clases más utilizadas del paquete para evitar que los
usuarios tengan que recurrir a importaciones profundas (por ejemplo,
``from fletplus.components.responsive_grid import ResponsiveGrid``). Cuando el
paquete se distribuye, esas rutas largas suelen terminar en errores de
``ImportError`` si se intenta usar atajos relativos desde una aplicación que
solo conoce ``fletplus.components``. Al exponer explícitamente los componentes
desde aquí garantizamos importaciones absolutas estables.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

LAZY_IMPORTS = {
    "AdaptiveAppHeader": "fletplus.components.adaptive_app_header",
    "MetadataBadge": "fletplus.components.adaptive_app_header",
    "PrimaryButton": "fletplus.components.buttons",
    "SecondaryButton": "fletplus.components.buttons",
    "SuccessButton": "fletplus.components.buttons",
    "WarningButton": "fletplus.components.buttons",
    "DangerButton": "fletplus.components.buttons",
    "InfoButton": "fletplus.components.buttons",
    "IconButton": "fletplus.components.buttons",
    "OutlinedButton": "fletplus.components.buttons",
    "TextButton": "fletplus.components.buttons",
    "FloatingActionButton": "fletplus.components.buttons",
    "CommandPalette": "fletplus.components.command_palette",
    "AdaptiveDestination": "fletplus.components.adaptive_layout",
    "AdaptiveNavigationLayout": "fletplus.components.adaptive_layout",
    "CaptionOverlay": "fletplus.components.caption_overlay",
    "AccessibilityPanel": "fletplus.components.accessibility_panel",
    "FlexRow": "fletplus.components.layouts",
    "FlexColumn": "fletplus.components.layouts",
    "Grid": "fletplus.components.layouts",
    "GridItem": "fletplus.components.layouts",
    "Spacer": "fletplus.components.layouts",
    "Stack": "fletplus.components.layouts",
    "StackItem": "fletplus.components.layouts",
    "Wrap": "fletplus.components.layouts",
    "ResponsiveContainer": "fletplus.components.responsive_container",
    "ResponsiveGrid": "fletplus.components.responsive_grid",
    "ResponsiveGridItem": "fletplus.components.responsive_grid",
    "SidebarAdmin": "fletplus.components.sidebar_admin",
    "SmartTable": "fletplus.components.smart_table",
    "LineChart": "fletplus.components.charts",
    "AdaptiveNavigationItem": "fletplus.components.universal_scaffold",
    "UniversalAdaptiveScaffold": "fletplus.components.universal_scaffold",
}

if TYPE_CHECKING:
    from fletplus.components.accessibility_panel import AccessibilityPanel
    from fletplus.components.adaptive_app_header import AdaptiveAppHeader, MetadataBadge
    from fletplus.components.adaptive_layout import (
        AdaptiveDestination,
        AdaptiveNavigationLayout,
    )
    from fletplus.components.buttons import (
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
    )
    from fletplus.components.caption_overlay import CaptionOverlay
    from fletplus.components.charts import LineChart
    from fletplus.components.command_palette import CommandPalette
    from fletplus.components.layouts import (
        FlexRow,
        FlexColumn,
        Grid,
        GridItem,
        Spacer,
        Stack,
        StackItem,
        Wrap,
    )
    from fletplus.components.responsive_container import ResponsiveContainer
    from fletplus.components.responsive_grid import ResponsiveGrid, ResponsiveGridItem
    from fletplus.components.sidebar_admin import SidebarAdmin
    from fletplus.components.smart_table import SmartTable
    from fletplus.components.universal_scaffold import (
        AdaptiveNavigationItem,
        UniversalAdaptiveScaffold,
    )

__all__ = [
    "AdaptiveAppHeader",
    "MetadataBadge",
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
    "Grid",
    "GridItem",
    "Spacer",
    "Stack",
    "StackItem",
    "Wrap",
    "AdaptiveNavigationItem",
    "UniversalAdaptiveScaffold",
    "CaptionOverlay",
    "ResponsiveContainer",
    "ResponsiveGrid",
    "ResponsiveGridItem",
    "SidebarAdmin",
    "SmartTable",
    "LineChart",
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
