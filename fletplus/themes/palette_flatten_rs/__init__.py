"""Aplanado de paletas respaldado por Rust.

Intenta cargar la extensión compilada con ``pyrust-native`` para acelerar el
aplanado de diccionarios anidados. Si no está disponible, se usa la versión
pura en Python con el mismo contrato.
"""
from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Mapping
from typing import Any, Callable

flatten_palette: Callable[[Mapping[str, Any]], dict[str, Any]]

_spec = importlib.util.find_spec("fletplus.themes.palette_flatten_rs._native")
if _spec is None:
    _native = None
else:
    _native = importlib.import_module("fletplus.themes.palette_flatten_rs._native")


def _py_flatten_palette(palette: Mapping[str, Any]) -> dict[str, Any]:
    def _flatten(prefix: str, value: Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            flattened: dict[str, Any] = {}
            for key, nested in value.items():
                new_prefix = f"{prefix}_{key}" if prefix else str(key)
                flattened.update(_flatten(new_prefix, nested))
            return flattened
        return {prefix: value}

    return _flatten("", palette)


if _native is None:
    flatten_palette = _py_flatten_palette
else:
    flatten_palette = _native.flatten_palette

__all__ = ["flatten_palette"]
