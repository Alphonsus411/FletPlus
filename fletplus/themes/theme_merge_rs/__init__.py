"""Merge de tokens de temas acelerado con Rust.

El módulo intenta cargar la extensión compilada con ``pyrust-native`` para
fusionar grupos de tokens y aplicar overrides de variantes. Si no está
presente, se usa una implementación en Python con el mismo contrato.
"""
from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Mapping
from typing import Any, Callable

merge_token_groups: Callable[[Mapping[str, Any], Mapping[str, Any] | None], dict[str, Any]]
merge_variant_overrides: Callable[
    [Mapping[str, Any], Mapping[str, Any] | None, Mapping[str, Any] | None],
    dict[str, Any],
]

_spec = importlib.util.find_spec("fletplus.themes.theme_merge_rs._native")
if _spec is None:
    _native = None
else:
    _native = importlib.import_module("fletplus.themes.theme_merge_rs._native")


def _py_merge_token_groups(
    base: Mapping[str, Any],
    updates: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if updates is None:
        return dict(base) if not isinstance(base, dict) else base
    target: dict[str, Any] = base if isinstance(base, dict) else dict(base)
    for group, values in updates.items():
        if not isinstance(values, Mapping):
            continue
        existing = target.setdefault(group, {})
        if not isinstance(existing, dict):
            target[group] = dict(values)
        else:
            existing.update(values)
    return target


def _py_merge_variant_overrides(
    definition: Mapping[str, Any],
    common_tokens: Mapping[str, Any] | None,
    overrides: Mapping[str, Any] | None,
) -> dict[str, Any]:
    updated: dict[str, Any] = definition if isinstance(definition, dict) else dict(definition)
    for variant in ("light", "dark"):
        variant_mapping = updated.setdefault(variant, {})
        if not isinstance(variant_mapping, dict):
            variant_mapping = dict(variant_mapping)
            updated[variant] = variant_mapping
        if isinstance(common_tokens, Mapping):
            variant_mapping = _py_merge_token_groups(variant_mapping, common_tokens)
            updated[variant] = variant_mapping
        if isinstance(overrides, Mapping):
            variant_override = overrides.get(variant)
            if isinstance(variant_override, Mapping):
                variant_mapping = _py_merge_token_groups(variant_mapping, variant_override)
                updated[variant] = variant_mapping
    return updated


if _native is None:
    merge_token_groups = _py_merge_token_groups
    merge_variant_overrides = _py_merge_variant_overrides
else:
    merge_token_groups = _native.merge_token_groups
    merge_variant_overrides = _native.merge_variant_overrides

__all__ = ["merge_token_groups", "merge_variant_overrides"]
