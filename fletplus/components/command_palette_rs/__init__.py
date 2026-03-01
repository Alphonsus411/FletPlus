from __future__ import annotations

import importlib
import importlib.util
from typing import Callable, List, Optional

native_filter_commands: Optional[Callable[[List[str], str], List[int]]]


def filter_commands_python(names: List[str], query: str) -> List[int]:
    query_normalized = (query or "").lower()
    if not query_normalized:
        return list(range(len(names)))
    return [i for i, name in enumerate(names) if query_normalized in (name or "").lower()]


def _load_native() -> Optional[object]:
    spec = importlib.util.find_spec("fletplus.components.command_palette_rs._native")
    if spec is not None:
        try:
            return importlib.import_module("fletplus.components.command_palette_rs._native")
        except Exception:
            return None
    # Fallback para entornos de `maturin develop` que instalan un módulo toplevel `_native`
    try:
        top = importlib.import_module("_native")
        # Validar que exponga la función esperada
        if hasattr(top, "filter_commands"):
            return top
    except Exception:
        return None
    return None


_native = _load_native()
native_filter_commands = getattr(_native, "filter_commands", None) if _native else None


def filter_commands(names: List[str], query: str) -> List[int]:
    if native_filter_commands is not None:
        return native_filter_commands(names, query)
    return filter_commands_python(names, query)


__all__ = ["filter_commands", "filter_commands_python", "native_filter_commands"]
