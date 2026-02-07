"""Núcleo desacoplado de FletPlus."""

from .app import FletPlusApp
from .layout import Layout, LayoutComposition, SimpleLayout
from .state import AppState, StateProtocol

__all__ = [
    "AppState",
    "FletPlusApp",
    "Layout",
    "LayoutComposition",
    "SimpleLayout",
    "StateProtocol",
]
