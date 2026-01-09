"""Backend opcional en Rust para filtrar la paleta de comandos.

Cuando la extensión nativa no está disponible, se usa un filtro
implementado en Python para mantener la compatibilidad.
"""
from __future__ import annotations

import importlib
import importlib.util
from typing import Callable, List, Optional

native_filter_commands: Optional[Callable[[List[str], str], List[int]]]


def filter_commands_python(names: List[str], query: str) -> List[int]:
    query_normalized = (query or "").lower()
    if not query_normalized:
        return list(range(len(names)))

    return [
        index
        for index, name in enumerate(names)
        if query_normalized in (name or "").lower()
    ]


_spec = importlib.util.find_spec("fletplus.components.command_palette_rs._native")
if _spec is None:
    _native: Optional[object] = None
else:
    _native = importlib.import_module("fletplus.components.command_palette_rs._native")

if _native is not None:
    native_filter_commands = _native.filter_commands
else:
    native_filter_commands = None


def filter_commands(names: List[str], query: str) -> List[int]:
    if native_filter_commands is not None:
        return native_filter_commands(names, query)
    return filter_commands_python(names, query)


__all__ = ["filter_commands", "filter_commands_python", "native_filter_commands"]
