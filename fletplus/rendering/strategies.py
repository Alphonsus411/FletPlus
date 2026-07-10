"""Estrategias de renderizado declarativas para FletPlus."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import flet as ft


@dataclass(frozen=True, slots=True)
class RenderStrategy:
    """Contrato base para adaptar renderizado, layout y metadatos por plataforma."""

    name: str = "base"
    target: str = "all"
    page_padding: int | None = None
    max_content_width: int | None = None
    spacing: int | None = None
    layout_density: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def configure_page(self, page: ft.Page) -> None:
        """Aplica ajustes no destructivos sobre una página Flet."""
        if self.page_padding is not None:
            page.padding = self.page_padding
        theme = page.theme or ft.Theme()
        if self.layout_density:
            try:
                theme.visual_density = self.layout_density
            except AttributeError:
                pass
        page.theme = theme

    def wrap_controls(
        self, controls: Sequence[ft.Control], page: ft.Page
    ) -> list[ft.Control]:
        """Envuelve controles raíz si la estrategia necesita un shell específico."""
        if self.max_content_width is None:
            return list(controls)
        return [
            ft.Container(
                content=ft.Column(controls=list(controls), spacing=self.spacing or 0),
                width=self.max_content_width,
                padding=self.page_padding,
                alignment=getattr(getattr(ft, "alignment", object()), "center", None),
            )
        ]

    def build_metadata(self) -> dict[str, object]:
        """Devuelve metadatos serializables para CLI, docs o diagnósticos."""
        return {
            "name": self.name,
            "target": self.target,
            "page_padding": self.page_padding,
            "max_content_width": self.max_content_width,
            "spacing": self.spacing,
            "layout_density": self.layout_density,
            **dict(self.metadata),
        }


class WebRenderStrategy(RenderStrategy):
    def __init__(self, **metadata: object) -> None:
        super().__init__("web", "web", 32, 1280, 20, "comfortable", metadata)


class DesktopRenderStrategy(RenderStrategy):
    def __init__(self, **metadata: object) -> None:
        super().__init__("desktop", "desktop", 28, 1180, 18, "comfortable", metadata)


class MobileRenderStrategy(RenderStrategy):
    def __init__(self, target: str = "mobile", **metadata: object) -> None:
        super().__init__("mobile", target, 16, 480, 12, "compact", metadata)


class FullStackRenderStrategy(RenderStrategy):
    def __init__(self, target: str = "all", **metadata: object) -> None:
        super().__init__("full-stack", target, 24, 1200, 16, "comfortable", metadata)


def strategy_for_target(target: str) -> RenderStrategy:
    normalized = target.lower()
    if normalized == "web":
        return WebRenderStrategy()
    if normalized == "desktop":
        return DesktopRenderStrategy()
    if normalized in {"mobile", "android-apk", "android-aab", "ios"}:
        return MobileRenderStrategy(target=normalized)
    return FullStackRenderStrategy(target=normalized)
