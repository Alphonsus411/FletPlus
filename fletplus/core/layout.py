from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import flet as ft

from .state import StateProtocol


@runtime_checkable
class LayoutComposition(Protocol):
    """Interfaz de composición de UI independiente del ciclo de vida."""

    def build(self, state: StateProtocol) -> list[ft.Control]:
        ...

    def update(self, state: StateProtocol, controls: list[ft.Control]) -> list[ft.Control]:
        ...


LayoutBuilder = Callable[[StateProtocol], ft.Control | list[ft.Control]]
LayoutUpdater = Callable[[StateProtocol, list[ft.Control]], ft.Control | list[ft.Control] | None]


@dataclass
class Layout(LayoutComposition):
    """Implementación concreta de ``LayoutComposition`` basada en callables."""

    builder: LayoutBuilder
    updater: LayoutUpdater | None = None

    def build(self, state: StateProtocol) -> list[ft.Control]:
        return _normalize_controls(self.builder(state))

    def update(self, state: StateProtocol, controls: list[ft.Control]) -> list[ft.Control]:
        if self.updater is None:
            return self.build(state)
        updated_controls = self.updater(state, controls)
        if updated_controls is None:
            return controls
        return _normalize_controls(updated_controls)

    @classmethod
    def from_callable(cls, builder: LayoutBuilder) -> "Layout":
        return cls(builder=builder)


def _normalize_controls(controls: ft.Control | list[ft.Control]) -> list[ft.Control]:
    if isinstance(controls, list):
        return controls
    return [controls]
