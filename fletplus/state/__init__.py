"""Utilidades reactivas para gestionar el estado de aplicaciones FletPlus.

Este paquete expone primitivas basadas en extensiones Cython para ofrecer
notificaciones eficientes entre señales y *stores* integradas con Flet.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

LAZY_IMPORTS = {
    "DerivedSignal": "fletplus.state.state",
    "Signal": "fletplus.state.state",
    "Store": "fletplus.state.state",
    "reactive": "fletplus.state.hooks",
    "use_signal": "fletplus.state.hooks",
    "use_state": "fletplus.state.hooks",
    "watch": "fletplus.state.hooks",
}

if TYPE_CHECKING:
    from fletplus.state.hooks import reactive, use_signal, use_state, watch
    from fletplus.state.state import DerivedSignal, Signal, Store

__all__ = [
    "Signal",
    "DerivedSignal",
    "Store",
    "reactive",
    "use_state",
    "use_signal",
    "watch",
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
