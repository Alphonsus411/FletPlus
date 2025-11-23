# cython: language_level=3
"""Implementaciones optimizadas en Cython para el enrutador."""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence


cpdef list _normalize_path(str path):
    cdef str cleaned = path.strip()
    if not cleaned or cleaned == "/":
        return []
    if cleaned.startswith("/"):
        cleaned = cleaned[1:]
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return [segment for segment in cleaned.split("/") if segment]


cpdef tuple _parse_segment(str segment):
    if segment.startswith("<") and segment.endswith(">") and len(segment) > 2:
        return True, segment[1:-1]
    return False, None


cpdef _join_paths(str base, str segment):
    base = base.rstrip("/")
    if not base:
        base = "/"
    if segment.startswith("/"):
        return _normalize_path_string(segment)
    return f"{base}/{segment}" if base != "/" else f"/{segment}"


cpdef str _normalize_path_string(str path):
    return "/" + "/".join(_normalize_path(path)) if path else "/"


cpdef list _match(object root, str path):
    cdef list segments = _normalize_path(path)
    cdef list results = []
    if not segments:
        if root.view_builder is not None:
            results.append([(root, {})])
        return results
    _dfs_match(root, segments, results)
    return results


cpdef _dfs_match(object root, list segments, list results):
    cdef Py_ssize_t seg_len = len(segments)
    cdef dict params = {}
    cdef list path_nodes = [None] * (seg_len + 1)

    # Pila manual: (node, index, phase, iterator list)
    cdef list stack = []
    stack.append((root, 0, 0, root.children))

    cdef Py_ssize_t index
    cdef object node
    cdef object child
    cdef str segment
    cdef list static_children
    cdef list dynamic_children
    cdef str key

    while stack:
        node, index, phase, children = stack.pop()
        if index == seg_len:
            if node.view_builder is not None:
                path_nodes[index] = (node, dict(params))
                results.append(path_nodes[: index + 1])
            continue

        segment = segments[index]
        if phase == 0:
            static_children = []
            dynamic_children = []
            for child in children:
                if child.dynamic:
                    dynamic_children.append(child)
                else:
                    static_children.append(child)

            # Guardamos los hijos dinámicos para el segundo pase
            stack.append((node, index, 1, dynamic_children))

            for child in static_children:
                if child.segment == segment:
                    path_nodes[index] = (child, dict(params))
                    stack.append((child, index + 1, 0, child.children))
        else:
            for child in children:
                key = child.parameter_name or "param"
                params[key] = segment
                path_nodes[index] = (child, dict(params))
                stack.append((child, index + 1, 0, child.children))
                params.pop(key, None)
