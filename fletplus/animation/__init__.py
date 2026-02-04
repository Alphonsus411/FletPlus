"""Herramientas para animaciones coordinadas dentro de FletPlus."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

LAZY_IMPORTS = {
    "AnimationController": "fletplus.animation.controller",
    "animation_controller_context": "fletplus.animation.controller",
    "AnimatedContainer": "fletplus.animation.wrappers",
    "FadeIn": "fletplus.animation.wrappers",
    "Scale": "fletplus.animation.wrappers",
    "SlideTransition": "fletplus.animation.wrappers",
}

if TYPE_CHECKING:
    from fletplus.animation.controller import AnimationController, animation_controller_context
    from fletplus.animation.wrappers import AnimatedContainer, FadeIn, Scale, SlideTransition

__all__ = [
    "AnimationController",
    "animation_controller_context",
    "FadeIn",
    "SlideTransition",
    "Scale",
    "AnimatedContainer",
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
