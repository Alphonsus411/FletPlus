"""Envoltura del backend nativo del caché de disco compilado con ``pyrust-native``."""
from __future__ import annotations

try:  # pragma: no cover - extensión opcional
    from . import _native
except Exception:  # pragma: no cover - fallback limpio
    _native = None

if _native is not None:
    build_key = _native.build_key
    cleanup = _native.cleanup
else:  # pragma: no cover - backend ausente
    build_key = None
    cleanup = None

__all__ = ["build_key", "cleanup"]
