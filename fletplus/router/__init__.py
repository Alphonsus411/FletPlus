"""Herramientas de enrutamiento para FletPlus."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

LAZY_IMPORTS = {
    "Route": "fletplus.router.route",
    "RouteMatch": "fletplus.router.route",
    "LayoutInstance": "fletplus.router.route",
    "layout_from_attribute": "fletplus.router.route",
    "Router": "fletplus.router.router",
}

if TYPE_CHECKING:
    from fletplus.router.route import Route, RouteMatch, LayoutInstance, layout_from_attribute
    from fletplus.router.router import Router

__all__ = [
    "Route",
    "RouteMatch",
    "Router",
    "LayoutInstance",
    "layout_from_attribute",
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
