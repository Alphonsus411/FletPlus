"""Wrapper para el backend de caché en disco."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable


def _native_candidate_paths() -> Iterable[Path]:
    base_path = Path(__file__).resolve().with_suffix("")
    for suffix in importlib.machinery.EXTENSION_SUFFIXES:
        candidate = base_path.with_suffix(suffix)
        if candidate.exists():
            yield candidate


def _load_native_module() -> ModuleType | None:
    for candidate in _native_candidate_paths():
        loader = importlib.machinery.ExtensionFileLoader(__name__, str(candidate))
        spec = importlib.util.spec_from_file_location(__name__, str(candidate), loader=loader)
        if spec is None:
            continue
        module = importlib.util.module_from_spec(spec)
        original = sys.modules.get(__name__)
        sys.modules[__name__] = module
        try:
            loader.exec_module(module)
        except Exception:
            if original is not None:
                sys.modules[__name__] = original
            else:
                sys.modules.pop(__name__, None)
            continue
        if original is not None:
            sys.modules[__name__] = original
        else:
            sys.modules.pop(__name__, None)
        return module
    return None


_native = _load_native_module()
if _native is None:
    from .disk_cache_py import *  # noqa: F403

    __all__ = [name for name in globals() if not name.startswith("_")]
else:
    for key, value in _native.__dict__.items():
        if key.startswith("__"):
            continue
        globals()[key] = value
    if hasattr(_native, "__all__"):
        __all__ = list(_native.__all__)  # type: ignore[attr-defined]
    else:
        __all__ = [name for name in _native.__dict__ if not name.startswith("_")]
