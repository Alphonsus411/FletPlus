"""Pasarela a la implementación acelerada del caché de disco."""
from __future__ import annotations

try:  # pragma: no cover - extensión opcional
    from .disk_cache_pr_rs import build_key, cleanup
except Exception:  # pragma: no cover - fallback limpio
    build_key = None
    cleanup = None

__all__ = ["build_key", "cleanup"]
