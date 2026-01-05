"""Backend opcional en Rust para ``ResponsiveGrid``.

El módulo expone ``plan_items`` cuando la extensión nativa está
compilada. Si no está disponible, ``plan_items`` queda en ``None`` para
permitir un fallback transparente en el código Python.
"""
from __future__ import annotations

import importlib
import importlib.util
from typing import Any, Callable, Optional

plan_items: Optional[Callable[..., Any]]

_spec = importlib.util.find_spec("fletplus.components.responsive_grid_rs._native")
if _spec is None:
    _native: Optional[Any] = None
else:
    _native = importlib.import_module("fletplus.components.responsive_grid_rs._native")

if _native is not None:
    plan_items = _native.plan_items
else:
    plan_items = None

__all__ = ["plan_items"]
