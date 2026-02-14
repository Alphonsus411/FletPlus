"""Shim para exponer la implementación nativa de responsive manager si existe."""
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
    try:
        return importlib.import_module(module_name)
    except (ImportError, OSError, RuntimeError):
        return None
    except Exception:
        return None


_native_module = _load_extension("fletplus.utils.responsive_manager")

if _native_module is not None:
    ResponsiveManager = getattr(_native_module, "ResponsiveManager", None)
else:
    ResponsiveManager = None


__all__ = ["ResponsiveManager"]
