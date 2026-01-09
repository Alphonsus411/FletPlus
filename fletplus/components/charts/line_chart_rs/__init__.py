"""Backend opcional en Rust para el gráfico de líneas.

Este paquete intenta cargar la extensión ``_native`` compilada con
``pyrust-native``/``maturin``. Si no está disponible, las funciones se
exponen como ``None`` para permitir un fallback automático al backend
Python.
"""
from __future__ import annotations

try:  # pragma: no cover - extensión opcional
    from . import _native
except Exception:  # pragma: no cover - fallback limpio
    _native = None

if _native is not None:
    screen_points = _native.screen_points
    nearest_point = _native.nearest_point
    line_segments = _native.line_segments
else:  # pragma: no cover - backend ausente
    screen_points = None
    nearest_point = None
    line_segments = None

__all__ = ["screen_points", "nearest_point", "line_segments"]
