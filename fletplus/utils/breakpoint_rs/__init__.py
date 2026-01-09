"""Helpers nativos opcionales para seleccionar breakpoints.

El módulo intenta cargar la extensión compilada con ``pyrust-native`` y
exponer :func:`select_breakpoint`. Si no está disponible, se recurre a una
implementación en Python con el mismo contrato.
"""
from __future__ import annotations

import importlib
import importlib.util
from bisect import bisect_right
from collections.abc import Sequence
from typing import Callable, Optional

select_breakpoint: Callable[[Sequence[int], int], Optional[int]]

_spec = importlib.util.find_spec("fletplus.utils.breakpoint_rs._native")
if _spec is None:
    _native = None
else:
    _native = importlib.import_module("fletplus.utils.breakpoint_rs._native")


def _py_select_breakpoint(keys: Sequence[int], value: int) -> Optional[int]:
    if not keys:
        return None
    idx = bisect_right(keys, value)
    if idx == 0:
        return None
    return int(keys[idx - 1])


if _native is None:
    select_breakpoint = _py_select_breakpoint
else:
    select_breakpoint = _native.select_breakpoint

__all__ = ["select_breakpoint"]
