"""Puente hacia la extensión nativa para señales compilada con ``pyrust-native``.

Si el binario nativo no está disponible se expone ``None`` para permitir un
*fallback* limpio al backend en Python/Cython.
"""
from __future__ import annotations

try:  # pragma: no cover - extensión opcional
    from . import _native
except Exception:  # pragma: no cover - fallback limpio
    _native = None

if _native is not None:
    SignalState = _native.SignalState  # type: ignore[attr-defined]
    notify = _native.notify  # type: ignore[attr-defined]
    snapshot = _native.snapshot  # type: ignore[attr-defined]
else:  # pragma: no cover - backend ausente
    SignalState = None
    notify = None
    snapshot = None

__all__ = ["SignalState", "notify", "snapshot"]
