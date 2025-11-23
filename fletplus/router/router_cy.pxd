# cython: language_level=3
"""Declaraciones compartidas para las utilidades del enrutador en Cython."""
from __future__ import annotations

cpdef list _normalize_path(str path)
cpdef tuple _parse_segment(str segment)
cpdef _join_paths(str base, str segment)
cpdef str _normalize_path_string(str path)
cpdef list _match(object root, str path)
cpdef _dfs_match(object root, list segments, list results)
