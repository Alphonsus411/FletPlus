"""Backend opcional en Rust para aplicar estilos responsivos."""
from __future__ import annotations

import importlib
import importlib.util
from typing import Any, Iterable, List, Sequence, Tuple

ApplyStyleResult = List[Tuple[Any, str, Any]]

_spec = importlib.util.find_spec("fletplus.utils.responsive_manager_rs._native")
if _spec is None:
    _native = None
else:
    _native = importlib.import_module("fletplus.utils.responsive_manager_rs._native")


def _py_apply_styles(styles: Iterable[tuple[Any, Any]], attrs: Sequence[str]) -> ApplyStyleResult:
    updates: ApplyStyleResult = []
    for control, rstyle in styles:
        base = getattr(control, "__fletplus_base_attrs__", None)
        if isinstance(base, dict):
            for attr in attrs:
                if attr in base:
                    updates.append((control, attr, base[attr]))

        page = getattr(rstyle, "_fletplus_page", None) or getattr(control, "page", None)
        if page is None:
            continue

        style = rstyle.get_style(page)
        if not style:
            continue

        styled_container = style.apply(control)
        for attr in attrs:
            if hasattr(control, attr):
                value = getattr(styled_container, attr, None)
                if value is not None:
                    updates.append((control, attr, value))
    return updates


if _native is None:
    apply_styles = _py_apply_styles
else:
    apply_styles = _native.apply_styles

__all__ = ["apply_styles"]
