from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import flet as ft

from .state import State


class LayoutBuilder(Protocol):
    def __call__(self, state: State) -> ft.Control | list[ft.Control]:
        ...


class LayoutUpdater(Protocol):
    def __call__(self, state: State, controls: list[ft.Control]) -> None:
        ...


@dataclass
class Layout:
    """Abstracción declarativa para componer UI."""

    builder: LayoutBuilder
    updater: LayoutUpdater | None = None

    def build(self, state: State) -> list[ft.Control]:
        controls = self.builder(state)
        if isinstance(controls, list):
            return controls
        return [controls]

    def update(self, state: State, controls: list[ft.Control]) -> list[ft.Control]:
        if self.updater is None:
            return self.build(state)
        self.updater(state, controls)
        return controls

    @classmethod
    def from_callable(cls, builder: Callable[[State], ft.Control | list[ft.Control]]) -> "Layout":
        return cls(builder=builder)
