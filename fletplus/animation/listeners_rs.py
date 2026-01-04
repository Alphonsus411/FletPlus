"""Capa de compatibilidad para exponer el contenedor nativo de listeners.

Se intenta cargar primero la extensión construida con ``pyrust-native``
(``listeners_pr_rs``). Si no está disponible, se recurre a la versión Rust
preexistente (``listeners_rs``) y, en última instancia, el código de Python
usa el backend puro.
"""
from __future__ import annotations

try:  # pragma: no cover - backend preferente (pyrust-native)
    from .listeners_pr_rs import ListenerContainer as _pr_listener
except Exception:  # pragma: no cover - fallback limpio
    _pr_listener = None

if _pr_listener is None:
    try:  # pragma: no cover - backend legacy
        import listeners_rs as _legacy
    except Exception:  # pragma: no cover - fallback limpio
        _legacy = None

    ListenerContainer = getattr(_legacy, "ListenerContainer", None) if _legacy else None
else:
    ListenerContainer = _pr_listener

__all__ = ["ListenerContainer"]
