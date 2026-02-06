"""Capa de compatibilidad para exponer el contenedor nativo de listeners.

Se intenta cargar primero la extensión construida con ``pyrust-native``
(``listeners_pr_rs``). Si no está disponible, se recurre al binario Rust
preexistente (``listeners_rs``) y, en última instancia, el código de Python
usa el backend puro.
"""
from __future__ import annotations

import importlib

try:  # pragma: no cover - backend preferente (pyrust-native)
    from .listeners_pr_rs import ListenerContainer as _pr_listener
except Exception:  # pragma: no cover - fallback limpio
    _pr_listener = None

_native_listener = None
if _pr_listener is None:
    try:  # pragma: no cover - backend legacy
        _native_listener = importlib.import_module("fletplus.animation.listeners_rs")
    except Exception:  # pragma: no cover - fallback limpio
        _native_listener = None

    ListenerContainer = (
        getattr(_native_listener, "ListenerContainer", None) if _native_listener else None
    )
else:
    ListenerContainer = _pr_listener

__all__ = ["ListenerContainer"]
