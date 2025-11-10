"""Motor de enrutamiento para FletPlus."""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Callable, Dict, Iterable, List, Optional, Sequence

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
        matches = self._match(path)
        if not matches:
            raise RouteNotFoundError(f"Ruta no encontrada: {path}")
        path_nodes = matches[0]
        params = MappingProxyType(path_nodes[-1][1])
        parent_match: Optional[RouteMatch] = None
        route_matches: List[RouteMatch] = []
        if self._root.layout_builder is not None:
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
        segments = _normalize_path(path)
        results: List[List[tuple[_RouteNode, Dict[str, str]]]] = []
        if not segments:
            if self._root.view_builder is not None:
                results.append([(self._root, {})])
            return results
        self._dfs_match(self._root, segments, 0, {}, [], results)
        return results

    def _dfs_match(
        self,
        node: _RouteNode,
        segments: Sequence[str],
        index: int,
        params: Dict[str, str],
        stack: List[tuple[_RouteNode, Dict[str, str]]],
        results: List[List[tuple[_RouteNode, Dict[str, str]]]],
    ) -> None:
        if index == len(segments):
            if node.view_builder is not None:
                results.append(stack + [(node, dict(params))])
            return
        segment = segments[index]
        for child in node.children:
            if child.dynamic:
                new_params = dict(params)
                key = child.parameter_name or "param"
                new_params[key] = segment
                self._dfs_match(child, segments, index + 1, new_params, stack + [(child, dict(new_params))], results)
            elif child.segment == segment:
                new_params = dict(params)
                self._dfs_match(child, segments, index + 1, new_params, stack + [(child, dict(new_params))], results)

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


def _normalize_path_string(path: str) -> str:
    return "/" + "/".join(_normalize_path(path)) if path else "/"


def _normalize_path(path: str) -> List[str]:
    cleaned = path.strip()
    if not cleaned or cleaned == "/":
        return []
    if cleaned.startswith("/"):
        cleaned = cleaned[1:]
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return [segment for segment in cleaned.split("/") if segment]


def _parse_segment(segment: str) -> tuple[bool, Optional[str]]:
    if segment.startswith("<") and segment.endswith(">") and len(segment) > 2:
        return True, segment[1:-1]
    return False, None


def _join_paths(base: str, segment: str) -> str:
    base = base.rstrip("/")
    if not base:
        base = "/"
    if segment.startswith("/"):
        return _normalize_path_string(segment)
    return f"{base}/{segment}" if base != "/" else f"/{segment}"
