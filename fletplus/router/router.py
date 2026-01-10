"""Motor de enrutamiento para FletPlus."""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Callable, Dict, Iterable, List, Optional, Sequence
import warnings

try:  # pragma: no cover - la importación puede fallar en entornos sin compilación
    from . import router_pr as _router_pr
except Exception:  # pragma: no cover - fallback cuando no hay compilación
    _router_pr = None

try:  # pragma: no cover - la importación puede fallar en entornos sin compilación
    from . import router_rs as _router_rs
except Exception:  # pragma: no cover - fallback cuando no hay compilación
    _router_rs = None

try:  # pragma: no cover - la importación puede fallar en entornos sin compilación
    from . import router_cy as _router_cy
except Exception:  # pragma: no cover - fallback cuando no hay compilación
    _router_cy = None

if _router_pr is None and _router_rs is None:
    warnings.warn(
        "Backends nativos del router no disponibles; se usará la implementación "
        "pura en Python (rendimiento reducido).",
        RuntimeWarning,
        stacklevel=2,
    )

import flet as ft

from .route import LayoutInstance, Route, RouteMatch


@dataclass(slots=True)
class _RouteNode:
    segment: str
    name: Optional[str] = None
    view_builder: Optional[Callable[[RouteMatch], ft.Control]] = None
    layout_builder: Optional[Callable[[RouteMatch], LayoutInstance]] = None
    parent: Optional["_RouteNode"] = None
    children: List["_RouteNode"] = field(default_factory=list)
    dynamic: bool = False
    parameter_name: Optional[str] = None
    full_path: str = "/"

    def child_for_segment(self, segment: str) -> Optional["_RouteNode"]:
        for child in self.children:
            if child.dynamic:
                return child if segment else None
            if child.segment == segment:
                return child
        return None

    def add_child(self, child: "_RouteNode") -> None:
        self.children.append(child)


class RouteNotFoundError(ValueError):
    """Se lanza cuando una ruta no existe."""


class Router:
    """Gestor de rutas para aplicaciones FletPlus."""

    def __init__(self, routes: Iterable[Route] | None = None) -> None:
        self._root = _RouteNode(segment="", full_path="/")
        self._history: List[str] = []
        self._index: int = -1
        self._observers: List[Callable[[RouteMatch, ft.Control], None]] = []
        self._layouts: Dict[int, LayoutInstance] = {}
        self._active_match: Optional[RouteMatch] = None
        if routes:
            for route in routes:
                self.register(route)

    # ------------------------------------------------------------------
    def register(self, route: Route, parent: Optional[_RouteNode] = None) -> None:
        parent = parent or self._root
        segments = _normalize_path(route.path)
        node = parent
        current_path = parent.full_path.rstrip("/") or "/"
        for segment in segments:
            child = self._find_child(node, segment)
            if child is None:
                dynamic, param = _parse_segment(segment)
                full_path = _join_paths(current_path, segment)
                child = _RouteNode(
                    segment=segment,
                    dynamic=dynamic,
                    parameter_name=param,
                    parent=node,
                    full_path=full_path,
                )
                node.add_child(child)
            node = child
            current_path = node.full_path
        node.name = route.name or node.name
        node.view_builder = route.view or node.view_builder
        node.layout_builder = route.layout or node.layout_builder
        for child_route in route.children:
            self.register(child_route, parent=node)

    # ------------------------------------------------------------------
    def observe(self, callback: Callable[[RouteMatch, ft.Control], None]) -> Callable[[], None]:
        self._observers.append(callback)

        def unsubscribe() -> None:
            try:
                self._observers.remove(callback)
            except ValueError:  # pragma: no cover - tolerancia extra
                pass

        return unsubscribe

    # ------------------------------------------------------------------
    @property
    def current_path(self) -> Optional[str]:
        return self._history[self._index] if 0 <= self._index < len(self._history) else None

    @property
    def active_match(self) -> Optional[RouteMatch]:
        return self._active_match

    # ------------------------------------------------------------------
    def go(self, path: str) -> None:
        self._activate(path, push=True)

    def replace(self, path: str) -> None:
        self._activate(path, push=False)

    def back(self) -> None:
        if self._index <= 0:
            return
        self._index -= 1
        path = self._history[self._index]
        self._render_path(path)

    # ------------------------------------------------------------------
    def _activate(self, path: str, *, push: bool) -> None:
        normalized = _normalize_path_string(path)
        if push:
            if self._index < len(self._history) - 1:
                self._history = self._history[: self._index + 1]
            self._history.append(normalized)
            self._index = len(self._history) - 1
        else:
            if self._index == -1:
                self._history.append(normalized)
                self._index = 0
            else:
                self._history[self._index] = normalized
        self._render_path(normalized)

    def _render_path(self, path: str) -> None:
        matches = _match(self._root, path)
        if not matches:
            raise RouteNotFoundError(f"Ruta no encontrada: {path}")
        path_nodes = matches[0]
        params = MappingProxyType({})
        parent_match: Optional[RouteMatch] = None
        route_matches: List[RouteMatch] = []
        if self._root.layout_builder is not None:
            # La raíz no hereda params del leaf para evitar confundir layouts globales.
            root_match = RouteMatch(
                router=self,
                node=self._root,
                params=params,
                path="/",
                parent=None,
            )
            route_matches.append(root_match)
            parent_match = root_match
        for node, node_params in path_nodes:
            match = RouteMatch(
                router=self,
                node=node,
                params=MappingProxyType(node_params),
                path=node.full_path,
                parent=parent_match,
            )
            route_matches.append(match)
            parent_match = match
        final = route_matches[-1]
        if final.node.view_builder is None:
            raise RouteNotFoundError(f"La ruta '{path}' no tiene vista asociada")
        view = final.node.view_builder(final)
        composed = self._compose_with_layouts(route_matches, view)
        self._active_match = final
        for callback in list(self._observers):
            callback(final, composed)

    # ------------------------------------------------------------------
    def _compose_with_layouts(self, matches: Sequence[RouteMatch], leaf: ft.Control) -> ft.Control:
        content: ft.Control | None = leaf
        for match in reversed(matches):
            layout_builder = match.node.layout_builder
            if layout_builder is None:
                continue
            node_key = id(match.node)
            instance = self._layouts.get(node_key)
            if instance is None:
                instance = layout_builder(match)
                if not isinstance(instance, LayoutInstance):
                    raise TypeError("El layout debe devolver una instancia de LayoutInstance")
                self._layouts[node_key] = instance
            instance.mount(content)
            content = instance.root
        assert content is not None  # pragma: no cover - nunca debería ser None
        return content

    # ------------------------------------------------------------------
    def _match(self, path: str) -> List[List[tuple[_RouteNode, Dict[str, str]]]]:
        return _match(self._root, path)
    # ------------------------------------------------------------------
    @staticmethod
    def _find_child(node: _RouteNode, segment: str) -> Optional[_RouteNode]:
        dynamic, param = _parse_segment(segment)
        for child in node.children:
            if child.dynamic and dynamic:
                return child
            if not child.dynamic and child.segment == segment:
                return child
        return None


def _normalize_path_py(path: str) -> List[str]:
    cleaned = path.strip()
    if not cleaned or cleaned == "/":
        return []
    if cleaned.startswith("/"):
        cleaned = cleaned[1:]
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return [segment for segment in cleaned.split("/") if segment]


def _normalize_path_string_py(path: str) -> str:
    return "/" + "/".join(_normalize_path_py(path)) if path else "/"


def _parse_segment_py(segment: str) -> tuple[bool, Optional[str]]:
    if segment.startswith("<") and segment.endswith(">") and len(segment) > 2:
        return True, segment[1:-1]
    return False, None


def _join_paths_py(base: str, segment: str) -> str:
    base = base.rstrip("/")
    if not base:
        base = "/"
    if segment.startswith("/"):
        return _normalize_path_string_py(segment)
    return f"{base}/{segment}" if base != "/" else f"/{segment}"


def _match_py(root: _RouteNode, path: str) -> List[List[tuple[_RouteNode, Dict[str, str]]]]:
    segments = _normalize_path_py(path)
    results: List[List[tuple[_RouteNode, Dict[str, str]]]] = []
    if not segments:
        if root.view_builder is not None:
            results.append([(root, {})])
        return results
    _dfs_match_py(root, segments, 0, {}, [None] * (len(segments) + 1), results)
    return results


def _dfs_match_py(
    node: _RouteNode,
    segments: Sequence[str],
    index: int,
    params: Dict[str, str],
    stack: List[tuple[_RouteNode, Dict[str, str]] | None],
    results: List[List[tuple[_RouteNode, Dict[str, str]]]],
) -> None:
    if index == len(segments):
        if node.view_builder is not None:
            stack[index] = (node, dict(params))
            results.append([entry for entry in stack[: index + 1] if entry is not None])
        return
    segment = segments[index]
    static_children: List[_RouteNode] = []
    dynamic_children: List[_RouteNode] = []
    for child in node.children:
        if child.dynamic:
            dynamic_children.append(child)
        else:
            static_children.append(child)

    for child in static_children:
        if child.segment == segment:
            stack[index] = (child, dict(params))
            _dfs_match_py(child, segments, index + 1, params, stack, results)

    for child in dynamic_children:
        key = child.parameter_name or "param"
        params[key] = segment
        stack[index] = (child, dict(params))
        _dfs_match_py(child, segments, index + 1, params, stack, results)
        params.pop(key, None)


# Selección de la implementación optimizada
_normalize_path = (
    (_router_pr._normalize_path if _router_pr else None)
    or (_router_rs._normalize_path if _router_rs else None)
    or (_router_cy._normalize_path if _router_cy else None)
    or _normalize_path_py
)
_normalize_path_string = (
    (_router_pr._normalize_path_string if _router_pr else None)
    or (_router_rs._normalize_path_string if _router_rs else None)
    or (_router_cy._normalize_path_string if _router_cy else None)
    or _normalize_path_string_py
)
_parse_segment = (
    (_router_pr._parse_segment if _router_pr else None)
    or (_router_rs._parse_segment if _router_rs else None)
    or (_router_cy._parse_segment if _router_cy else None)
    or _parse_segment_py
)
_join_paths = (
    (_router_pr._join_paths if _router_pr else None)
    or (_router_rs._join_paths if _router_rs else None)
    or (_router_cy._join_paths if _router_cy else None)
    or _join_paths_py
)
_dfs_match = (
    (_router_pr._dfs_match if _router_pr else None)
    or (_router_rs._dfs_match if _router_rs else None)
    or (_router_cy._dfs_match if _router_cy else None)
    or _dfs_match_py
)
_match = (
    (_router_pr._match if _router_pr else None)
    or (_router_rs._match if _router_rs else None)
    or (_router_cy._match if _router_cy else None)
    or _match_py
)
