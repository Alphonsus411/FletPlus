from __future__ import annotations

import importlib


def _try_load_native():
    try:  # pragma: no cover - extensión opcional
        from .router_pr_rs import _native as mod
        return mod
    except Exception:
        pass
    # Fallback para `maturin develop` que instala un módulo toplevel `_native`
    try:
        mod = importlib.import_module("_native")
        # Comprobar interfaz esperada
        required = ["_normalize_path", "_normalize_path_string", "_parse_segment", "_join_paths", "_dfs_match", "_match"]
        if all(hasattr(mod, name) for name in required):
            return mod
    except Exception:
        return None
    return None

_native = _try_load_native()

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
