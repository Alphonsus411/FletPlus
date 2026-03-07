"""Contratos para prevenir regresiones del namespace legacy `ft.padding.*`."""

from __future__ import annotations

import warnings
from pathlib import Path

import flet as ft

from fletplus.components.accessibility_panel import AccessibilityPanel
from fletplus.styles import Style

ROOT = Path(__file__).resolve().parent.parent
SCOPES = ("fletplus", "examples")


class _PaddingContractPage:
    def __init__(self) -> None:
        self.width = 1024
        self.height = 768
        self.window_width = 1024
        self.platform = "web"
        self.on_resize = None
        self.theme = ft.Theme()

    def update(self) -> None:
        pass

    def set_focus(self, _control: ft.Control) -> None:
        pass


def test_padding_namespace_contract() -> None:
    assert hasattr(ft, "Padding")
    assert callable(ft.Padding)
    assert callable(ft.Padding.all)
    assert callable(ft.Padding.only)
    assert callable(ft.Padding.symmetric)


def test_no_legacy_ft_padding_usage_in_scoped_sources() -> None:
    legacy_hits: list[str] = []

    for scope in SCOPES:
        for file in (ROOT / scope).rglob("*.py"):
            if "target" in file.parts:
                continue
            text = file.read_text(encoding="utf-8")
            if "ft.padding." in text:
                legacy_hits.append(str(file.relative_to(ROOT)))

    assert legacy_hits == [], (
        "Se detectaron usos legacy de `ft.padding.`; usar `ft.Padding` en su lugar: "
        + ", ".join(sorted(legacy_hits))
    )


def test_components_do_not_emit_padding_deprecation_warning() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)

        Style(padding=(4, 6)).apply(ft.Text("ok"))

        panel = AccessibilityPanel()
        panel.build(_PaddingContractPage())

    padding_warnings = [
        str(item.message).lower()
        for item in captured
        if issubclass(item.category, DeprecationWarning)
    ]

    assert all("padding" not in message for message in padding_warnings), padding_warnings
