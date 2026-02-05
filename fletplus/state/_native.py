"""Shim para exponer las clases nativas de estado si están disponibles."""
from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util


def _load_extension(module_name: str):
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None:
        return None
    if not spec.origin.endswith(tuple(importlib.machinery.EXTENSION_SUFFIXES)):
        return None
    return importlib.import_module(module_name)


_native_module = _load_extension("fletplus.state.state")

if _native_module is not None:
    Signal = getattr(_native_module, "Signal", None)
    DerivedSignal = getattr(_native_module, "DerivedSignal", None)
    Store = getattr(_native_module, "Store", None)
else:
    Signal = None
    DerivedSignal = None
    Store = None


__all__ = ["Signal", "DerivedSignal", "Store"]
