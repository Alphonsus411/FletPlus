"""Definiciones básicas de rutas para el enrutador de FletPlus."""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Callable, Dict, Iterable, Mapping, Optional

import flet as ft


@dataclass(slots=True)
class LayoutInstance:
    """Representa una instancia de layout persistente."""

    root: ft.Control
    _mount: Callable[[ft.Control | None], None]

    def mount(self, content: ft.Control | None) -> None:
        """Actualiza el contenido asociado al layout."""
        self._mount(content)


def layout_from_attribute(control: ft.Control, attribute: str = "content") -> LayoutInstance:
    """Crea una instancia de :class:`LayoutInstance` usando un atributo de control."""

    if not hasattr(control, attribute):  # pragma: no cover - protección adicional
        raise AttributeError(f"El control {control!r} no posee el atributo '{attribute}'")

    def _mount(child: ft.Control | None) -> None:
        setattr(control, attribute, child)

    return LayoutInstance(root=control, _mount=_mount)


@dataclass(slots=True)
class Route:
    """Declaración de ruta."""

    path: str
    view: Optional[Callable[["RouteMatch"], ft.Control]] = None
    layout: Optional[Callable[["RouteMatch"], LayoutInstance]] = None
    name: Optional[str] = None
    children: Iterable["Route"] = field(default_factory=tuple)


@dataclass(slots=True)
class RouteMatch:
    """Información contextual sobre una coincidencia de ruta."""

    router: "Router"
    node: "_RouteNode"
    params: Mapping[str, str]
    path: str
    parent: Optional["RouteMatch"] = None

    @property
    def name(self) -> Optional[str]:
        return self.node.name

    def param(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.params.get(key, default)

    def with_child(self, node: "_RouteNode", params: Dict[str, str], path: str) -> "RouteMatch":
        return RouteMatch(router=self.router, node=node, params=MappingProxyType(params), path=path, parent=self)


# Import diferido para evitar dependencia circular en tiempo de importación
from . import router as _router  # noqa: E402  # pylint: disable=wrong-import-position

Router = _router.Router
"""Alias para evitar dependencias circulares en anotaciones."""
