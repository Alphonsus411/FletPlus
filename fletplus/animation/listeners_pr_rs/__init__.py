"""Puente hacia la extensión nativa de listeners compilada con ``pyrust-native``.

El paquete intenta importar ``_native`` (generado por `pyrust-native`/`maturin`)
para exponer :class:`ListenerContainer`. Si la extensión no está disponible, el
atributo queda en ``None`` para permitir un *fallback* limpio al backend Python.
"""
from __future__ import annotations

try:  # pragma: no cover - extensión opcional
    from . import _native
except Exception:  # pragma: no cover - fallback limpio
    _native = None

if _native is not None:
    ListenerContainer = _native.ListenerContainer  # type: ignore[attr-defined]
else:  # pragma: no cover - backend ausente
    ListenerContainer = None

__all__ = ["ListenerContainer"]
