"""Atajos de importación para el paquete :mod:`fletplus`.

La intención es que las aplicaciones consumidoras puedan realizar importaciones
absolutas estables como ``from fletplus import ThemeManager`` sin depender de
la estructura interna de submódulos. Esto evita errores de importación cuando
se distribuye la librería y mejora la experiencia para los usuarios finales.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

import flet as ft

_patched = getattr(ft, "_fletplus_patched_controls", False)
if not _patched:
    try:
        Page = ft.Page
        if (getattr(Page, "width", None) is None) and (getattr(Page, "window_width", None) is None):
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
        if (getattr(Page, "height", None) is None) and (getattr(Page, "window_height", None) is None):
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
    except Exception:
        pass
    try:
        _OriginalTextButton = ft.TextButton
        class _TextButtonCompat(_OriginalTextButton):
            def __init__(self, *args, text: Any = None, content: Any = None, **kwargs):
                if content is not None and "content" not in kwargs:
                    kwargs["content"] = content
                if not args and text is not None and "content" not in kwargs:
                    kwargs["content"] = text
                super().__init__(*args, **kwargs)
        ft.TextButton = _TextButtonCompat  # type: ignore[assignment]
    except Exception:
        pass
    try:
        _OriginalIcon = ft.Icon
        class _IconCompat(_OriginalIcon):
            def __init__(self, *args, name: Any = None, icon: Any = None, **kwargs):
                if name is not None and not args:
                    args = (name,)
                elif icon is not None and not args:
                    args = (icon,)
                super().__init__(*args, **kwargs)
        ft.Icon = _IconCompat  # type: ignore[assignment]
    except Exception:
        pass
    try:
        setattr(ft, "_fletplus_patched_controls", True)
    except Exception:
        pass

LAZY_IMPORTS = {
    "AdaptiveDestination": "fletplus.components",
    "AdaptiveNavigationLayout": "fletplus.components",
    "AccessibilityPanel": "fletplus.components",
    "AnimatedContainer": "fletplus.animation",
    "AnimationController": "fletplus.animation",
    "CommandPalette": "fletplus.components",
    "Context": "fletplus.context",
    "ContextProvider": "fletplus.context",
    "DangerButton": "fletplus.components",
    "DEFAULT_ICON_SET": "fletplus.icons",
    "DerivedSignal": "fletplus.state",
    "DiskCache": "fletplus.http",
    "FadeIn": "fletplus.animation",
    "FileDropZone": "fletplus.utils",
    "FileStorageProvider": "fletplus.storage.files",
    "FlexColumn": "fletplus.components",
    "FlexRow": "fletplus.components",
    "FloatingActionButton": "fletplus.components",
    # Contrato público oficial por compatibilidad: API legacy.
    # La nueva core desacoplada sigue disponible vía `fletplus.core`.
    "FletPlusApp": "fletplus.core_legacy",
    "Grid": "fletplus.components",
    "GridItem": "fletplus.components",
    "HttpClient": "fletplus.http",
    "HttpInterceptor": "fletplus.http",
    "Icon": "fletplus.icons",
    "IconButton": "fletplus.components",
    "InfoButton": "fletplus.components",
    "LayoutInstance": "fletplus.router",
    "LineChart": "fletplus.components",
    "LocalStorageProvider": "fletplus.storage.local",
    "OutlinedButton": "fletplus.components",
    "PrimaryButton": "fletplus.components",
    "RequestEvent": "fletplus.http",
    "ResponsiveContainer": "fletplus.components",
    "ResponsiveGrid": "fletplus.components",
    "ResponsiveManager": "fletplus.utils",
    "Layout": "fletplus.core",
    "State": "fletplus.core",
    "ResponsiveStyle": "fletplus.utils",
    "ResponsiveTypography": "fletplus.utils",
    "ResponsiveVisibility": "fletplus.utils",
    "ResponseEvent": "fletplus.http",
    "Route": "fletplus.router",
    "Router": "fletplus.router",
    "Scale": "fletplus.animation",
    "SecondaryButton": "fletplus.components",
    "SessionStorageProvider": "fletplus.storage.session",
    "ShortcutManager": "fletplus.utils",
    "SidebarAdmin": "fletplus.components",
    "Signal": "fletplus.state",
    "SlideTransition": "fletplus.animation",
    "SmartTable": "fletplus.components",
    "Spacer": "fletplus.components",
    "Stack": "fletplus.components",
    "StackItem": "fletplus.components",
    "StorageProvider": "fletplus.storage",
    "Store": "fletplus.state",
    "SuccessButton": "fletplus.components",
    "SystemTray": "fletplus.desktop",
    "TextButton": "fletplus.components",
    "ThemeManager": "fletplus.themes",
    "WindowManager": "fletplus.desktop",
    "Wrap": "fletplus.components",
    "animation_controller_context": "fletplus.animation",
    "available_icon_sets": "fletplus.icons",
    "generate_manifest": "fletplus.web",
    "generate_service_worker": "fletplus.web",
    "get_palette_definition": "fletplus.themes",
    "get_palette_tokens": "fletplus.themes",
    "get_preset_definition": "fletplus.themes",
    "has_icon": "fletplus.icons",
    "has_palette": "fletplus.themes",
    "has_preset": "fletplus.themes",
    "icon": "fletplus.icons",
    "is_desktop": "fletplus.utils",
    "is_mobile": "fletplus.utils",
    "is_web": "fletplus.utils",
    "layout_from_attribute": "fletplus.router",
    "list_icons": "fletplus.icons",
    "list_palettes": "fletplus.themes",
    "list_presets": "fletplus.themes",
    "load_palette_from_file": "fletplus.themes",
    "load_theme_from_json": "fletplus.themes",
    "locale_context": "fletplus.context",
    "reactive": "fletplus.state",
    "register_icon": "fletplus.icons",
    "register_icon_set": "fletplus.icons",
    "register_pwa": "fletplus.web",
    "resolve_icon_name": "fletplus.icons",
    "responsive_spacing": "fletplus.utils",
    "responsive_text": "fletplus.utils",
    "show_notification": "fletplus.desktop",
    "theme_context": "fletplus.context",
    "use_signal": "fletplus.state",
    "use_state": "fletplus.state",
    "user_context": "fletplus.context",
    "watch": "fletplus.state",
    "WarningButton": "fletplus.components",
}

if TYPE_CHECKING:
    from fletplus.animation import (
        AnimatedContainer,
        AnimationController,
        FadeIn,
        Scale,
        SlideTransition,
        animation_controller_context,
    )
    from fletplus.components import (
        AccessibilityPanel,
        AdaptiveDestination,
        AdaptiveNavigationLayout,
        CommandPalette,
        DangerButton,
        FlexColumn,
        FlexRow,
        FloatingActionButton,
        Grid,
        GridItem,
        IconButton,
        InfoButton,
        LineChart,
        OutlinedButton,
        PrimaryButton,
        ResponsiveContainer,
        ResponsiveGrid,
        SecondaryButton,
        SidebarAdmin,
        SmartTable,
        Spacer,
        Stack,
        StackItem,
        SuccessButton,
        TextButton,
        WarningButton,
        Wrap,
    )
    from fletplus.context import (
        Context,
        ContextProvider,
        locale_context,
        theme_context,
        user_context,
    )
    from fletplus.core import Layout, State
    from fletplus.core_legacy import FletPlusApp
    from fletplus.desktop import SystemTray, WindowManager, show_notification
    from fletplus.http import (
        DiskCache,
        HttpClient,
        HttpInterceptor,
        RequestEvent,
        ResponseEvent,
    )
    from fletplus.icons import (
        DEFAULT_ICON_SET,
        Icon,
        available_icon_sets,
        has_icon,
        icon,
        list_icons,
        register_icon,
        register_icon_set,
        resolve_icon_name,
    )
    from fletplus.router import LayoutInstance, Route, Router, layout_from_attribute
    from fletplus.state import (
        DerivedSignal,
        Signal,
        Store,
        reactive,
        use_signal,
        use_state,
        watch,
    )
    from fletplus.storage import StorageProvider
    from fletplus.storage.files import FileStorageProvider
    from fletplus.storage.local import LocalStorageProvider
    from fletplus.storage.session import SessionStorageProvider
    from fletplus.themes import (
        ThemeManager,
        get_palette_definition,
        get_palette_tokens,
        get_preset_definition,
        has_palette,
        has_preset,
        list_palettes,
        list_presets,
        load_palette_from_file,
        load_theme_from_json,
    )
    from fletplus.utils import (
        FileDropZone,
        ResponsiveManager,
        ResponsiveStyle,
        ResponsiveTypography,
        ResponsiveVisibility,
        ShortcutManager,
        is_desktop,
        is_mobile,
        is_web,
        responsive_spacing,
        responsive_text,
    )
    from fletplus.web import generate_manifest, generate_service_worker, register_pwa


__all__ = [
    "FletPlusApp",
    "Layout",
    "State",
    "AnimationController",
    "animation_controller_context",
    "FadeIn",
    "SlideTransition",
    "Scale",
    "AnimatedContainer",
    "ThemeManager",
    "load_palette_from_file",
    "load_theme_from_json",
    "list_palettes",
    "get_palette_tokens",
    "has_palette",
    "get_palette_definition",
    "list_presets",
    "has_preset",
    "get_preset_definition",
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
    "ResponsiveContainer",
    "ResponsiveGrid",
    "Spacer",
    "Stack",
    "StackItem",
    "Wrap",
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
    "HttpClient",
    "DiskCache",
    "HttpInterceptor",
    "RequestEvent",
    "ResponseEvent",
    "generate_manifest",
    "generate_service_worker",
    "register_pwa",
    "Router",
    "Route",
    "LayoutInstance",
    "layout_from_attribute",
    "DEFAULT_ICON_SET",
    "icon",
    "Icon",
    "available_icon_sets",
    "list_icons",
    "has_icon",
    "resolve_icon_name",
    "register_icon",
    "register_icon_set",
    "DerivedSignal",
    "Signal",
    "Store",
    "reactive",
    "use_state",
    "use_signal",
    "watch",
    "StorageProvider",
    "LocalStorageProvider",
    "SessionStorageProvider",
    "FileStorageProvider",
    "Context",
    "ContextProvider",
    "theme_context",
    "user_context",
    "locale_context",
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
