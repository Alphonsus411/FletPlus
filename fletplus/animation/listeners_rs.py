"""Capa de compatibilidad para la extensión Rust de listeners."""
from __future__ import annotations

try:  # pragma: no cover - extensión opcional
    import listeners_rs as _native
except Exception:  # pragma: no cover - fallback
    _native = None

ListenerContainer = getattr(_native, "ListenerContainer", None) if _native else None

__all__ = ["ListenerContainer"]
