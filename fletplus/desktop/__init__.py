from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

LAZY_IMPORTS = {
    "WindowManager": "fletplus.desktop.window_manager",
    "SystemTray": "fletplus.desktop.system_tray",
    "show_notification": "fletplus.desktop.notifications",
}

if TYPE_CHECKING:
    from fletplus.desktop.notifications import show_notification
    from fletplus.desktop.system_tray import SystemTray
    from fletplus.desktop.window_manager import WindowManager

__all__ = ["WindowManager", "SystemTray", "show_notification"]


def __getattr__(name: str) -> Any:
    if name in LAZY_IMPORTS:
        module = importlib.import_module(LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(set(__all__))
