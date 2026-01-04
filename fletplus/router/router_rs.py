"""Puente ligero hacia la extensión Rust del router.

El módulo compilado se distribuye como ``router_rs`` (top-level). Este
archivo facilita su carga desde el paquete ``fletplus.router`` y expone
las mismas funciones utilizadas por ``router.py``.
"""
from __future__ import annotations

try:  # pragma: no cover - la extensión puede no estar instalada
    import router_rs as _native
except Exception:  # pragma: no cover - fallback limpio
    _native = None

if _native is not None:
    _normalize_path = _native._normalize_path
    _normalize_path_string = _native._normalize_path_string
    _parse_segment = _native._parse_segment
    _join_paths = _native._join_paths
    _dfs_match = _native._dfs_match
    _match = _native._match
else:  # pragma: no cover - compatibilidad cuando no existe el módulo
    _normalize_path = None
    _normalize_path_string = None
    _parse_segment = None
    _join_paths = None
    _dfs_match = None
    _match = None

__all__ = [
    "_normalize_path",
    "_normalize_path_string",
    "_parse_segment",
    "_join_paths",
    "_dfs_match",
    "_match",
]
