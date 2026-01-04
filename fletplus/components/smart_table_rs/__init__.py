"""Backend opcional en Rust para ``SmartTable``.

El módulo expone ``apply_query`` cuando la extensión nativa está disponible.
De lo contrario, la variable queda en ``None`` permitiendo al código Python
aplicar el fallback automáticamente.
"""
from __future__ import annotations

import importlib
import importlib.util
from typing import Any, Callable, Optional

_native: Optional[Any]
apply_query: Optional[Callable[..., Any]]

_spec = importlib.util.find_spec("fletplus.components.smart_table_rs._native")
if _spec is None:
    _native = None
else:
    _native = importlib.import_module("fletplus.components.smart_table_rs._native")

if _native is not None:
    apply_query = _native.apply_query
else:
    apply_query = None

__all__ = ["apply_query"]
