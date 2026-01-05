"""Merge helpers respaldados por Rust para tokens de temas.

El módulo intenta cargar la extensión compilada con ``pyrust-native`` y
exponer :func:`merge_token_layers`. Si no está disponible, se recurre a
una implementación en Python con el mismo contrato.
"""
from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Mapping, Sequence
from typing import Any, Callable

merge_token_layers: Callable[[Mapping[str, Mapping[str, Any]], Sequence[Mapping[str, Mapping[str, Any]]]], dict[str, dict[str, Any]]]

_spec = importlib.util.find_spec("fletplus.themes.token_merge_rs._native")
if _spec is None:
    _native = None
else:
    _native = importlib.import_module("fletplus.themes.token_merge_rs._native")


def _py_merge_token_layers(
    base: Mapping[str, Mapping[str, Any]],
    layers: Sequence[Mapping[str, Mapping[str, Any]]],
) -> dict[str, dict[str, Any]]:
    merged = {group: dict(values) for group, values in base.items()}
    for layer in layers:
        for group, values in layer.items():
            target = merged.setdefault(group, {})
            target.update(values)
    return merged


if _native is None:
    merge_token_layers = _py_merge_token_layers
else:
    merge_token_layers = _native.merge_token_layers

__all__ = ["merge_token_layers"]
