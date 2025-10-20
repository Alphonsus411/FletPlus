"""Disposición adaptable para web, escritorio y móviles con accesibilidad."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import flet as ft

from fletplus.utils.accessibility import AccessibilityPreferences
from fletplus.utils.device_profiles import (
    DeviceProfile,
    DEFAULT_DEVICE_PROFILES,
    iter_device_profiles,
    get_device_profile,
)
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.themes.theme_manager import ThemeManager


@dataclass
class AdaptiveDestination:
    """Describe un destino de navegación reutilizable por barra o riel."""

    label: str
    icon: str | ft.Control
    selected_icon: str | ft.Control | None = None
    tooltip: str | None = None

    def as_navigation_bar(self) -> ft.NavigationBarDestination:
        return ft.NavigationBarDestination(
            label=self.label,
            icon=self.icon,
            selected_icon=self.selected_icon or self.icon,
            tooltip=self.tooltip or self.label,
        )

    def as_navigation_rail(self) -> ft.NavigationRailDestination:
        return ft.NavigationRailDestination(
            icon=self.icon,
            selected_icon=self.selected_icon or self.icon,
            label=self.label,
        )


class AdaptiveNavigationLayout:
    """Crea una estructura de navegación adaptable para cualquier plataforma."""

    def __init__(
        self,
        destinations: Sequence[AdaptiveDestination],
        content_builder: Callable[[int, str], ft.Control],
        *,
        header: ft.Control | None = None,
        theme: ThemeManager | None = None,
        accessibility: AccessibilityPreferences | None = None,
        device_profiles: Sequence[DeviceProfile] | None = None,
    ) -> None:
        if not destinations:
            raise ValueError("AdaptiveNavigationLayout requiere al menos un destino")

        self.destinations = list(destinations)
        self.content_builder = content_builder
        self.header = header
        self.theme = theme
        self.accessibility = accessibility or AccessibilityPreferences()
        self.device_profiles = tuple(device_profiles or DEFAULT_DEVICE_PROFILES)

        self._page: ft.Page | None = None
        self._current_device: str = "mobile"
        self._selected_index: int = 0
        self._root = ft.Column(expand=True, spacing=0)

        self._caption_text = ft.Text("", selectable=True)
        self._caption_container = ft.Container(
            visible=self.accessibility.enable_captions,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.BLUE_GREY),
            padding=ft.Padding(12, 10, 12, 10),
            content=self._caption_text,
        )

        self._nav_bar = ft.NavigationBar(
            destinations=[dest.as_navigation_bar() for dest in self.destinations],
            selected_index=self._selected_index,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            on_change=self._handle_nav_event,
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.BLUE_GREY),
        )
        self._nav_rail = ft.NavigationRail(
            destinations=[dest.as_navigation_rail() for dest in self.destinations],
            selected_index=self._selected_index,
            label_type=ft.NavigationRailLabelType.ALL,
            on_change=self._handle_nav_event,
        )

        self._skip_button = ft.TextButton(
            "Saltar al contenido principal",
            icon=ft.Icons.SKIP_NEXT_OUTLINED,
            on_click=self._focus_content,
            tooltip="Ir directamente al contenido",
        )

        self._content_container = ft.Container(expand=True)
        self._manager: ResponsiveManager | None = None

    # Propiedades públicas ----------------------------------------------
    @property
    def root(self) -> ft.Column:
        return self._root

    @property
    def navigation_bar(self) -> ft.NavigationBar:
        return self._nav_bar

    @property
    def navigation_rail(self) -> ft.NavigationRail:
        return self._nav_rail

    @property
    def caption_container(self) -> ft.Container:
        return self._caption_container

    @property
    def current_device(self) -> str:
        return self._current_device

    @property
    def selected_index(self) -> int:
        return self._selected_index

    # API principal ------------------------------------------------------
    def build(self, page: ft.Page) -> ft.Control:
        """Configura la disposición en ``page`` y devuelve el control raíz."""

        self._page = page
        self.accessibility.apply(page, self.theme)
        self._current_device = get_device_profile(page.width or 0, self.device_profiles).name
        self._update_content()

        callbacks = {profile.min_width: self._on_width_change for profile in iter_device_profiles(self.device_profiles)}
        self._manager = ResponsiveManager(
            page,
            breakpoints=callbacks,
            device_callbacks={profile.name: self._apply_device_layout for profile in self.device_profiles},
            device_profiles=self.device_profiles,
        )
        # Asegurar disposición inicial
        self._apply_device_layout(self._current_device)
        return self._root

    def select_destination(self, index: int) -> None:
        """Permite cambiar de pestaña programáticamente."""

        self._on_navigation_index(index)

    # Internos -----------------------------------------------------------
    def _handle_nav_event(self, event: ft.ControlEvent) -> None:
        index = int(event.data or 0)
        self._on_navigation_index(index)

    def _on_navigation_index(self, index: int) -> None:
        if index == self._selected_index:
            return
        if index < 0 or index >= len(self.destinations):
            return
        self._selected_index = index
        self._nav_bar.selected_index = index
        self._nav_rail.selected_index = index
        self._update_content()
        self._announce_destination()
        if self._page:
            self._page.update()

    def _update_content(self) -> None:
        control = self.content_builder(self._selected_index, self._current_device)
        self._content_container.content = control
        self._caption_text.value = self._caption_message()

    def _caption_message(self) -> str:
        if not self.accessibility.enable_captions:
            return ""
        dest = self.destinations[self._selected_index]
        return f"Sección activa: {dest.label}"

    def _announce_destination(self) -> None:
        if not self.accessibility.enable_captions:
            return
        self._caption_text.value = self._caption_message()

    def _apply_device_layout(self, device: str) -> None:
        self._current_device = device
        self._update_content()
        body_controls: list[ft.Control] = []

        if device == "mobile":
            self._nav_bar.visible = True
            self._nav_rail.visible = False
            body_controls.append(self._content_container)
            if self.accessibility.enable_captions:
                body_controls.append(self._caption_container)
            layout = ft.Column(controls=body_controls, expand=True, spacing=0)
            controls = [self._skip_button]
            if self.header:
                controls.append(self.header)
            controls.append(layout)
            controls.append(self._nav_bar)
        else:
            self._nav_bar.visible = False
            self._nav_rail.visible = True
            self._nav_rail.extended = device == "desktop"
            content_stack = [self._content_container]
            if self.accessibility.enable_captions:
                content_stack.append(self._caption_container)
            layout = ft.Row(
                expand=True,
                spacing=0,
                controls=[
                    ft.Container(self._nav_rail, width=120 if device == "desktop" else 80),
                    ft.Column(controls=content_stack, expand=True, spacing=0),
                ],
            )
            controls = [self._skip_button]
            if self.header:
                controls.append(self.header)
            controls.append(layout)

        self._root.controls = controls
        if self._page:
            self._page.update()

    def _on_width_change(self, width: int) -> None:
        # Actualiza escala tipográfica si el ancho cambia significativamente
        if self._page and hasattr(self._page, "window_width"):
            setattr(self._page, "window_width", width)

    def _focus_content(self, _event: ft.ControlEvent) -> None:
        if not self._page:
            return
        focus = getattr(self._page, "set_focus", None)
        if callable(focus) and self._content_container.content is not None:
            focus(self._content_container.content)
