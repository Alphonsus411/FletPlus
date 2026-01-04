"""Pasarela hacia la extensión nativa del router.

El paquete intenta cargar el binario construido con ``pyrust-native``
y reexpone las funciones compatibles con ``router.py``. Si la
extensión no está disponible, los atributos quedan en ``None`` para
permitir al router elegir un backend alternativo.
"""
from __future__ import annotations

try:  # pragma: no cover - extensión opcional
    from . import _native
except Exception:  # pragma: no cover - fallback limpio
    _native = None

if _native is not None:
    _normalize_path = _native._normalize_path
    _normalize_path_string = _native._normalize_path_string
    _parse_segment = _native._parse_segment
    _join_paths = _native._join_paths
    _dfs_match = _native._dfs_match
    _match = _native._match
else:  # pragma: no cover - backend ausente
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
