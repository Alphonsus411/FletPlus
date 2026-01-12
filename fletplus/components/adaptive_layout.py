"""Disposición adaptable para web, escritorio y móviles con accesibilidad."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Mapping, Sequence

import flet as ft

from fletplus.components.caption_overlay import CaptionOverlay
from fletplus.styles import Style
from fletplus.utils.accessibility import AccessibilityPreferences
from fletplus.utils.device_profiles import (
    DeviceProfile,
    DEFAULT_DEVICE_PROFILES,
    iter_device_profiles,
    get_device_profile,
)
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.utils.responsive_style import ResponsiveStyle
from fletplus.themes.theme_manager import ThemeManager


if TYPE_CHECKING:
    from fletplus.components.accessibility_panel import AccessibilityPanel


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
        accessibility_panel: "AccessibilityPanel" | None = None,
        device_profiles: Sequence[DeviceProfile] | None = None,
        floating_action_button: ft.Control | None = None,
        drawer: ft.Control | None = None,
        secondary_panel_builder: Callable[[str], ft.Control] | None = None,
        caption_overlay: CaptionOverlay | None = None,
        header_style: Style | ResponsiveStyle | dict[int, Style] | None = None,
        header_background_token: str | None = "app_header",
        header_gradient_tokens: tuple[str, str] | None = (
            "gradient_app_header_start",
            "gradient_app_header_end",
        ),
        device_theme_tokens: Mapping[str, Mapping[str, Mapping[str, object]]] | None = None,
        header_backgrounds: Mapping[str, str] | None = None,
        header_gradient_tokens_by_device: Mapping[str, Sequence[str] | tuple[str, str]]
        | None = None,
    ) -> None:
        if not destinations:
            raise ValueError("AdaptiveNavigationLayout requiere al menos un destino")

        self.destinations = list(destinations)
        self.content_builder = content_builder
        self.header = header
        self.theme = theme
        self.accessibility = accessibility or AccessibilityPreferences()
        self.accessibility_panel = accessibility_panel
        if self.accessibility_panel and self.accessibility_panel.preferences is not self.accessibility:
            self.accessibility_panel.preferences = self.accessibility
        self.device_profiles = tuple(device_profiles or DEFAULT_DEVICE_PROFILES)
        self.floating_action_button = floating_action_button
        self.drawer = drawer
        self.secondary_panel_builder = secondary_panel_builder
        self.caption_overlay = caption_overlay
        self.header_style = header_style
        self.header_background_token = header_background_token
        self.header_gradient_tokens = header_gradient_tokens
        self.header_backgrounds = {
            str(key).lower(): value
            for key, value in (header_backgrounds or {}).items()
            if isinstance(value, str)
        }
        gradient_map: dict[str, tuple[str, str]] = {}
        if header_gradient_tokens_by_device:
            for key, value in header_gradient_tokens_by_device.items():
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    gradient_map[str(key).lower()] = (str(value[0]), str(value[1]))
        self.header_gradient_tokens_by_device = gradient_map

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
        self._accessibility_panel_control: ft.Control | None = None
        self._caption_overlay_control: ft.Control | None = None
        self._fab_host = ft.Container(
            alignment=ft.alignment.bottom_right,
            padding=ft.Padding(0, 0, 16, 16),
            visible=self.floating_action_button is not None,
            content=self.floating_action_button,
        )
        self._drawer_button = ft.IconButton(
            icon=ft.Icons.MENU,
            tooltip="Abrir navegación",
            on_click=self._open_drawer,
            visible=self.drawer is not None,
        )
        self._header_container: ft.Container | None = None
        self._header_responsive_style: ResponsiveStyle | None = None

        if self.theme and device_theme_tokens:
            for device, tokens_map in device_theme_tokens.items():
                try:
                    self.theme.set_device_tokens(device, tokens_map, refresh=False)
                except Exception:  # pragma: no cover - errores defensivos
                    continue
            self.theme.apply_theme()

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
    def caption_overlay_control(self) -> ft.Control | None:
        return self._caption_overlay_control

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
        if self.drawer is not None:
            setattr(page, "drawer", self.drawer)
        if self.caption_overlay is not None:
            self._caption_overlay_control = self.caption_overlay.build(page)
            self.caption_overlay.set_enabled(
                self.accessibility.enable_captions
                and self.accessibility.caption_mode == "overlay"
            )
        self._current_device = get_device_profile(page.width or 0, self.device_profiles).name
        self._update_content()

        callbacks = {
            profile.min_width: self._on_width_change
            for profile in iter_device_profiles(self.device_profiles)
        }
        self._manager = ResponsiveManager(
            page,
            breakpoints=callbacks,
            device_callbacks={profile.name: self._apply_device_layout for profile in self.device_profiles},
            device_profiles=self.device_profiles,
        )
        self._configure_header_styling()
        # Asegurar disposición inicial
        self._apply_device_layout(self._current_device)
        return self._root

    def select_destination(self, index: int) -> None:
        """Permite cambiar de pestaña programáticamente."""

        self._on_navigation_index(index)

    # ------------------------------------------------------------------
    def _configure_header_styling(self) -> None:
        if self.header is None or self._manager is None:
            return
        container = self._ensure_header_container()
        style: ResponsiveStyle | None = None
        if isinstance(self.header_style, ResponsiveStyle):
            style = self.header_style
        elif isinstance(self.header_style, dict):
            style = ResponsiveStyle(width=self.header_style)
        if style is not None:
            self._header_responsive_style = style
            self._manager.register_styles(container, style)

    # ------------------------------------------------------------------
    def _ensure_header_container(self) -> ft.Container:
        if self.header is None:
            raise ValueError("No header configured")

        if self._header_container is None:
            if isinstance(self.header_style, Style):
                applied = self.header_style.apply(self.header)
                if isinstance(applied, ft.Container):
                    container = applied
                else:  # pragma: no cover - Style devuelve control no contenedor
                    container = ft.Container(content=applied)
            else:
                container = ft.Container(content=self.header)

            if not isinstance(container, ft.Container):
                container = ft.Container(content=self.header)

            container.expand = True
            if container.padding is None:
                container.padding = ft.Padding(20, 16, 20, 18)
            if container.border_radius is None:
                container.border_radius = ft.border_radius.all(28)
            if container.alignment is None:
                container.alignment = ft.alignment.center_left
            if container.shadow is None:
                container.shadow = ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=18,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                )
            self._header_container = container
        else:
            self._header_container.content = self.header

        self._apply_header_theme(self._header_container, self._current_device)
        return self._header_container

    # ------------------------------------------------------------------
    def _apply_header_theme(self, container: ft.Container, device: str | None = None) -> None:
        if not self.theme:
            return

        device_key = (device or self._current_device or "").lower()
        container.gradient = None
        container.bgcolor = None
        gradient: ft.Gradient | None = None
        bgcolor: str | None = None

        # Aplicar gradientes específicos por dispositivo primero
        if self.header_gradient_tokens_by_device:
            tokens = self.header_gradient_tokens_by_device.get(device_key)
            if tokens:
                start = self.theme.get_color(tokens[0])
                end = self.theme.get_color(tokens[1])
                if start and end:
                    gradient = ft.LinearGradient(
                        colors=[start, end],
                        begin=ft.alignment.center_left,
                        end=ft.alignment.center_right,
                    )
                    bgcolor = None

        if gradient is None and self.header_background_token:
            gradient = self.theme.get_gradient(self.header_background_token)
            if gradient:
                bgcolor = None
            else:
                color = self.theme.get_color(self.header_background_token)
                if color:
                    gradient = None
                    bgcolor = color

        if gradient is None and self.header_gradient_tokens:
            start = self.theme.get_color(self.header_gradient_tokens[0])
            end = None
            if len(self.header_gradient_tokens) > 1:
                end = self.theme.get_color(self.header_gradient_tokens[1])
            if start and end:
                gradient = ft.LinearGradient(
                    colors=[start, end],
                    begin=ft.alignment.center_left,
                    end=ft.alignment.center_right,
                )
                bgcolor = None

        background_override = self.header_backgrounds.get(device_key)
        if background_override:
            gradient = None
            bgcolor = background_override

        if gradient is None and bgcolor is None:
            fallback = self.theme.get_color("primary") or ft.Colors.BLUE_GREY_500
            bgcolor = fallback

        container.gradient = gradient
        container.bgcolor = bgcolor

        tokens_source = getattr(self.theme, "effective_tokens", getattr(self.theme, "tokens", {}))
        shadows = tokens_source.get("shadows", {}) if isinstance(tokens_source, dict) else {}
        if container.shadow is None:
            header_shadow = (
                shadows.get("header")
                or shadows.get("surface")
                or shadows.get("card")
                or shadows.get("default")
            )
            if header_shadow is not None:
                container.shadow = header_shadow

    # ------------------------------------------------------------------
    def _build_header_block(self, device: str, with_drawer: bool) -> ft.Control | None:
        if self.header is None:
            self._drawer_button.visible = with_drawer and self.drawer is not None
            if with_drawer and self.drawer is not None:
                return ft.Row(
                    controls=[self._drawer_button],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.START,
                )
            return None

        container = self._ensure_header_container()
        self._apply_header_theme(container, device)

        if with_drawer and self.drawer is not None:
            self._drawer_button.visible = True
            container.expand = True
            return ft.Row(
                controls=[self._drawer_button, container],
                spacing=12,
                alignment=ft.MainAxisAlignment.START,
            )

        self._drawer_button.visible = False
        return container

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
        message = self._caption_message()
        inline_mode = self.accessibility.caption_mode == "inline"
        self._caption_container.visible = self.accessibility.enable_captions and inline_mode
        self._caption_text.value = message if inline_mode else ""
        if (
            self.caption_overlay is not None
            and self.accessibility.enable_captions
            and self.accessibility.caption_mode == "overlay"
        ):
            self.caption_overlay.announce(message)

    def _caption_message(self) -> str:
        if not self.accessibility.enable_captions:
            return ""
        dest = self.destinations[self._selected_index]
        return f"Sección activa: {dest.label}"

    def _announce_destination(self) -> None:
        if not self.accessibility.enable_captions:
            return
        if self.accessibility.caption_mode == "inline":
            self._caption_text.value = self._caption_message()
        elif self.caption_overlay is not None:
            self.caption_overlay.announce(self._caption_message())

    def _apply_device_layout(self, device: str) -> None:
        self._current_device = device
        if self.theme:
            try:
                self.theme.apply_theme(device=device)
            except Exception:  # pragma: no cover - manejo defensivo
                pass
        self._update_content()

        body_controls: list[ft.Control] = []

        if self.accessibility_panel:
            if self._page and (self._accessibility_panel_control is None):
                self._accessibility_panel_control = self.accessibility_panel.build(self._page)
            if self._accessibility_panel_control is not None:
                self._accessibility_panel_control.visible = self.accessibility.show_accessibility_panel
                if self.accessibility.show_accessibility_panel:
                    body_controls.append(self._accessibility_panel_control)

        inline_captions = (
            self.accessibility.enable_captions
            and self.accessibility.caption_mode == "inline"
        )
        overlay_captions = (
            self.accessibility.enable_captions
            and self.accessibility.caption_mode == "overlay"
            and self._caption_overlay_control is not None
        )

        if self.caption_overlay is not None:
            self.caption_overlay.set_enabled(overlay_captions)

        secondary_panel: ft.Control | None = None
        if self.secondary_panel_builder and device != "mobile":
            secondary_panel = self.secondary_panel_builder(device)
            if secondary_panel is not None:
                secondary_panel = ft.Container(secondary_panel, expand=True)

        controls: list[ft.Control]

        if device == "mobile":
            self._nav_bar.visible = True
            self._nav_rail.visible = False
            body_controls.append(self._content_container)
            if inline_captions:
                body_controls.append(self._caption_container)
            layout = ft.Column(controls=body_controls, expand=True, spacing=12)
            main_area = self._wrap_with_stack(layout, overlay_captions)
            controls = [self._skip_button]

            header_block = self._build_header_block(device, with_drawer=self.drawer is not None)
            if header_block is not None:
                controls.append(header_block)

            controls.append(main_area)
            controls.append(self._nav_bar)
        else:
            self._nav_bar.visible = False
            self._nav_rail.visible = True
            self._nav_rail.extended = device == "desktop"
            content_stack: list[ft.Control] = []
            if body_controls:
                content_stack.extend(body_controls)
            content_stack.append(self._content_container)
            if inline_captions:
                content_stack.append(self._caption_container)
            column_content = ft.Column(
                controls=content_stack,
                expand=True,
                spacing=12 if body_controls else 0,
            )
            main_column = self._wrap_with_stack(column_content, overlay_captions)
            row_controls: list[ft.Control] = [
                ft.Container(self._nav_rail, width=120 if device == "desktop" else 80),
                main_column,
            ]
            if secondary_panel is not None:
                row_controls.append(secondary_panel)

            layout = ft.Row(
                expand=True,
                spacing=0,
                controls=row_controls,
            )
            controls = [self._skip_button]
            header_block = self._build_header_block(device, with_drawer=False)
            if header_block is not None:
                controls.append(header_block)
            controls.append(layout)
            self._drawer_button.visible = False

        self._root.controls = controls
        if self._page:
            self._page.update()

    def _wrap_with_stack(self, control: ft.Control, overlay_active: bool) -> ft.Control:
        needs_fab = self.floating_action_button is not None
        needs_overlay = overlay_active and self._caption_overlay_control is not None
        if not needs_fab and not needs_overlay:
            return control

        layers: list[ft.Control] = [control]
        if needs_overlay and self._caption_overlay_control is not None:
            layers.append(self._caption_overlay_control)
        if needs_fab:
            self._fab_host.content = self.floating_action_button
            self._fab_host.visible = True
            layers.append(self._fab_host)
        else:
            self._fab_host.visible = False
        return ft.Stack(controls=layers, expand=True)

    def _on_width_change(self, width: int) -> None:
        if self._page and hasattr(self._page, "window_width"):
            setattr(self._page, "window_width", width)

    def _focus_content(self, _event: ft.ControlEvent) -> None:
        if not self._page:
            return
        focus = getattr(self._page, "set_focus", None)
        if callable(focus) and self._content_container.content is not None:
            focus(self._content_container.content)

    @property
    def accessibility_panel_control(self) -> ft.Control | None:
        """Devuelve el panel de accesibilidad asociado, si existe."""

        return self._accessibility_panel_control

    def _open_drawer(self, _event: ft.ControlEvent) -> None:
        if not self._page or self.drawer is None:
            return
        open_drawer = getattr(self._page, "open_drawer", None)
        if callable(open_drawer):
            open_drawer()
