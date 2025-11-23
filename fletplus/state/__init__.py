"""Utilidades reactivas para gestionar el estado de aplicaciones FletPlus.

Este paquete expone primitivas basadas en extensiones Cython para ofrecer
notificaciones eficientes entre señales y *stores* integradas con Flet.
"""

from __future__ import annotations

from .state import DerivedSignal, Signal, Store
from .hooks import reactive, use_signal, use_state, watch

__all__ = [
    "Signal",
    "DerivedSignal",
    "Store",
    "reactive",
    "use_state",
    "use_signal",
    "watch",
]
