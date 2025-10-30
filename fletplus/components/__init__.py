"""Punto de entrada público para los componentes de FletPlus.

Este módulo reúne las clases más utilizadas del paquete para evitar que los
usuarios tengan que recurrir a importaciones profundas (por ejemplo,
``from fletplus.components.responsive_grid import ResponsiveGrid``). Cuando el
paquete se distribuye, esas rutas largas suelen terminar en errores de
``ImportError`` si se intenta usar atajos relativos desde una aplicación que
solo conoce ``fletplus.components``. Al exponer explícitamente los componentes
desde aquí garantizamos importaciones absolutas estables.
"""

from fletplus.components.adaptive_app_header import AdaptiveAppHeader, MetadataBadge
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
from fletplus.components.command_palette import CommandPalette
from fletplus.components.adaptive_layout import (
    AdaptiveDestination,
    AdaptiveNavigationLayout,
)
from fletplus.components.caption_overlay import CaptionOverlay
from fletplus.components.accessibility_panel import AccessibilityPanel
from fletplus.components.layouts import FlexRow, FlexColumn
from fletplus.components.responsive_container import ResponsiveContainer
from fletplus.components.responsive_grid import ResponsiveGrid, ResponsiveGridItem
from fletplus.components.sidebar_admin import SidebarAdmin
from fletplus.components.smart_table import SmartTable
from fletplus.components.charts import LineChart
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
