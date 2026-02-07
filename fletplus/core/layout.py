from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import flet as ft

from .state import AppState, StateProtocol


class LayoutBuilder(Protocol):
    def __call__(self, page: ft.Page, state: AppState) -> ft.Control:
        ...


class LayoutUpdater(Protocol):
    def __call__(
        self, page: ft.Page, state: AppState, controls: list[ft.Control]
    ) -> list[ft.Control] | None:
        ...


@runtime_checkable
class LayoutComposition(Protocol):
    """Interfaz de composición de UI independiente del ciclo de vida."""

    def build(self, state: StateProtocol) -> list[ft.Control]:
        ...

    def update(self, state: StateProtocol, controls: list[ft.Control]) -> list[ft.Control]:
        ...


class Layout(Protocol):
    """Contrato de layout declarativo basado en página.

    Este contrato mantiene la construcción de UI libre de APIs legacy y hace
    explícita la dependencia de la instancia de ``ft.Page``. Para evolucionar
    hacia un modelo más declarativo:

    - Mantén ``build`` como función pura que solo describe controles.
    - Evita mutaciones directas sobre ``page``; delega efectos a un orquestador.
    - Usa componentes reutilizables (funciones o clases) para componer jerarquías.
    """

    def build(self, page: ft.Page, state: AppState) -> ft.Control:
        ...


@dataclass
class SimpleLayout:
    """Implementación básica de ``Layout`` usando callables.

    Si necesitas migrar a un enfoque más declarativo, comienza moviendo la
    lógica de composición a funciones puras y reemplaza la mutación en ``update``
    por reconstrucciones parciales con el estado actual.
    """

    builder: LayoutBuilder
    updater: LayoutUpdater | None = None

    def build(self, page: ft.Page, state: AppState) -> ft.Control:
        return self.builder(page, state)

    def update(self, page: ft.Page, state: AppState, controls: list[ft.Control]) -> list[ft.Control]:
        if self.updater is None:
            return [self.build(page, state)]
        updated_controls = self.updater(page, state, controls)
        if updated_controls is None:
            return controls
        return updated_controls

    @classmethod
    def from_callable(cls, builder: Callable[[ft.Page, AppState], ft.Control]) -> "SimpleLayout":
        return cls(builder=builder)
