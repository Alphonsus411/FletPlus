"""Núcleo desacoplado de FletPlus."""

from .app import FletPlusApp
from .layout import Layout, LayoutComposition
from .state import AppState, StateProtocol

__all__ = [
    "AppState",
    "FletPlusApp",
    "Layout",
    "LayoutComposition",
    "StateProtocol",
]
