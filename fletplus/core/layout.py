from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import flet as ft

from .state import StateProtocol


@runtime_checkable
class LayoutComposition(Protocol):
    """Contrato declarativo para componer UI en función del estado.

    Las implementaciones describen qué controles deben existir para un estado
    dado. El runtime se encarga de montar o reemplazar los controles en la
    página, por lo que este contrato no expone ``page`` ni eventos de ciclo de
    vida.
    """

    def build(self, state: StateProtocol) -> list[ft.Control]:
        """Construye el árbol inicial de controles a partir del estado."""
        ...

    def update(self, state: StateProtocol, controls: list[ft.Control]) -> list[ft.Control]:
        """Reconstruye o reutiliza controles cuando cambia el estado."""
        ...


LayoutBuilder = Callable[[StateProtocol], ft.Control | list[ft.Control]]
LayoutUpdater = Callable[[StateProtocol, list[ft.Control]], ft.Control | list[ft.Control] | None]


@dataclass
class Layout(LayoutComposition):
    """Implementación declarativa basada en callables puros."""

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
        """Crea un layout declarativo sin updater explícito."""
        return cls(builder=builder)


def _normalize_controls(controls: ft.Control | list[ft.Control]) -> list[ft.Control]:
    if isinstance(controls, list):
        return controls
    return [controls]
