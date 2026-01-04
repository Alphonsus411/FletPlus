"""Pasarela a la variante nativa del router compilada con pyrust-native.

Este módulo intenta importar ``fletplus.router.router_pr_rs._native`` y
reexpone las funciones aceleradas. Si el binario no está disponible, los
atributos quedan en ``None`` para que el router elija el siguiente backend
(otro módulo nativo, Cython o la versión pura en Python).
"""
from __future__ import annotations

try:  # pragma: no cover - extensión opcional
    from .router_pr_rs import _native
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
