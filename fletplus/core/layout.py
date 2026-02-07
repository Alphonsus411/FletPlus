from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import flet as ft

from .state import StateProtocol


class LayoutBuilder(Protocol):
    def __call__(self, state: StateProtocol) -> ft.Control | list[ft.Control]:
        ...


class LayoutUpdater(Protocol):
    def __call__(self, state: StateProtocol, controls: list[ft.Control]) -> None:
        ...


@runtime_checkable
class LayoutComposition(Protocol):
    """Interfaz de composición de UI independiente del ciclo de vida."""

    def build(self, state: StateProtocol) -> list[ft.Control]:
        ...

    def update(self, state: StateProtocol, controls: list[ft.Control]) -> list[ft.Control]:
        ...


@dataclass
class Layout:
    """Abstracción declarativa para componer UI."""

    builder: LayoutBuilder
    updater: LayoutUpdater | None = None

    def build(self, state: StateProtocol) -> list[ft.Control]:
        controls = self.builder(state)
        if isinstance(controls, list):
            return controls
        return [controls]

    def update(self, state: StateProtocol, controls: list[ft.Control]) -> list[ft.Control]:
        if self.updater is None:
            return self.build(state)
        self.updater(state, controls)
        return controls

    @classmethod
    def from_callable(cls, builder: Callable[[StateProtocol], ft.Control | list[ft.Control]]) -> "Layout":
        return cls(builder=builder)
