"""Disposición universal que adapta navegación y accesibilidad a cada plataforma.

Este módulo expone :class:`UniversalAdaptiveScaffold`, un contenedor de alto
nivel que reorganiza automáticamente la interfaz para entornos web, escritorio
y móviles. El objetivo es ofrecer una experiencia coherente con soporte
integrado para personas con baja visión o pérdida auditiva gracias a la
integración con :class:`~fletplus.utils.accessibility.AccessibilityPreferences`
y :class:`~fletplus.components.accessibility_panel.AccessibilityPanel`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Iterable, Sequence

import flet as ft

from fletplus.components.caption_overlay import CaptionOverlay, CaptionTone
from fletplus.utils.accessibility import AccessibilityPreferences
from fletplus.utils.device_profiles import (
    DeviceProfile,
    DEFAULT_DEVICE_PROFILES,
    EXTENDED_DEVICE_PROFILES,
    get_device_profile,
    iter_device_profiles,
)
from fletplus.utils.responsive_manager import ResponsiveManager

if TYPE_CHECKING:
    from fletplus.themes.theme_manager import ThemeManager

@dataclass(frozen=True, slots=True)
class AdaptiveNavigationItem:
    """Información para crear destinos de navegación accesibles."""

    id: str
    label: str
    icon: str | ft.Control
    selected_icon: str | ft.Control | None = None
    tooltip: str | None = None

    def navigation_bar_destination(self) -> ft.NavigationBarDestination:
        """Devuelve el destino listo para un :class:`ft.NavigationBar`."""

        return ft.NavigationBarDestination(
            label=self.label,
            icon=self.icon,
            selected_icon=self.selected_icon or self.icon,
            tooltip=self.tooltip or self.label,
        )

    def navigation_rail_destination(self) -> ft.NavigationRailDestination:
        """Devuelve el destino listo para un :class:`ft.NavigationRail`."""

        return ft.NavigationRailDestination(
            icon=self.icon,
            selected_icon=self.selected_icon or self.icon,
            label=self.label,
        )


class UniversalAdaptiveScaffold:
    """Estructura adaptable con control de accesibilidad integrado.

    La clase construye un ``Stack`` que distribuye la navegación y los paneles
    secundarios según el ancho disponible. Los tres modos principales son:

    * ``mobile``: utiliza ``NavigationBar`` fijo en la parte inferior.
    * ``tablet``: muestra ``NavigationRail`` compacto.
    * ``desktop``: expande el riel y habilita un panel lateral secundario.

    Además, ofrece un botón de accesibilidad que abre un panel con controles de
    contraste, subtítulos y reducción de movimiento, y emite mensajes mediante
    texto (captions) y lectores de pantalla cuando es posible.
    """

    def __init__(
        self,
        *,
        navigation_items: Sequence[AdaptiveNavigationItem],
        content_builder: Callable[[AdaptiveNavigationItem, int], ft.Control],
        theme: "ThemeManager" | None = None,
        accessibility: AccessibilityPreferences | None = None,
        accessibility_panel: "AccessibilityPanel" | None = None,
        caption_overlay: CaptionOverlay | None = None,
        header_controls: Iterable[ft.Control] | None = None,
        page_title: str | None = None,
        secondary_panel_builder: Callable[[AdaptiveNavigationItem], ft.Control] | None = None,
        floating_action_button: ft.Control | None = None,
        actions: Sequence[ft.Control] | None = None,
        drawer: ft.Control | None = None,
        device_profiles: Sequence[DeviceProfile] | None = None,
        desktop_max_content_width: int | None = None,
        large_desktop_panel_width: int = 360,
        auto_show_accessibility_on_large_desktop: bool = True,
        app_bar_gradient_token: str | None = "app_header",
        app_bar_background: str | None = None,
        app_bar_gradient: ft.Gradient | None = None,
    ) -> None:
        from fletplus.components.accessibility_panel import AccessibilityPanel

        if not navigation_items:
            raise ValueError("navigation_items no puede estar vacío")

        self.navigation_items = tuple(navigation_items)
        self.content_builder = content_builder
        self.theme = theme
        self.accessibility = accessibility or AccessibilityPreferences()
        self.caption_overlay = caption_overlay or CaptionOverlay()
        self.secondary_panel_builder = secondary_panel_builder
        self.floating_action_button = floating_action_button
        self.actions = list(actions or [])
        self.drawer = drawer
        self.device_profiles = tuple(device_profiles or EXTENDED_DEVICE_PROFILES)
        self.page_title = page_title
        self.desktop_max_content_width = desktop_max_content_width
        self.large_desktop_panel_width = large_desktop_panel_width
        self.auto_show_accessibility_on_large_desktop = auto_show_accessibility_on_large_desktop
        self.app_bar_gradient_token = app_bar_gradient_token
        self.app_bar_background = app_bar_background
        self._explicit_app_bar_gradient = app_bar_gradient

        if accessibility_panel is None:
            self.accessibility_panel = AccessibilityPanel(
                preferences=self.accessibility,
                theme=self.theme,
                on_change=self._handle_accessibility_change,
            )
        else:
            self.accessibility_panel = accessibility_panel
            self.accessibility_panel.preferences = self.accessibility
            self.accessibility_panel.on_change = self._handle_accessibility_change

        # Panel alternativo utilizado en la hoja inferior para evitar reutilizar
        # el mismo control en dos padres distintos.
        self._sheet_accessibility_panel = AccessibilityPanel(
            preferences=self.accessibility,
            theme=self.theme,
            on_change=self._handle_accessibility_change,
        )

        self.header_controls = list(header_controls or [])

        self._page: ft.Page | None = None
        self._manager: ResponsiveManager | None = None
        self._current_device: str = "mobile"
        self._selected_index: int = 0
        self._show_desktop_accessibility_panel = False

        self._nav_bar = ft.NavigationBar(
            destinations=[item.navigation_bar_destination() for item in self.navigation_items],
            on_change=self._on_navigation_bar_change,
            selected_index=self._selected_index,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        )
        self._nav_rail = ft.NavigationRail(
            destinations=[item.navigation_rail_destination() for item in self.navigation_items],
            on_change=self._on_navigation_rail_change,
            selected_index=self._selected_index,
        )

        self._fab_host = ft.Container(
            alignment=ft.alignment.bottom_right,
            padding=ft.Padding(0, 0, 16, 16),
            visible=floating_action_button is not None,
            content=floating_action_button,
        )

        self._skip_button = ft.TextButton(
            "Saltar al contenido principal",
            icon=ft.Icons.SKIP_NEXT_OUTLINED,
            on_click=self._focus_main_content,
            tooltip="Ir directamente a la sección de contenido",
            style=ft.ButtonStyle(
                color={"": ft.Colors.ON_PRIMARY},
                bgcolor={"": ft.Colors.with_opacity(0.8, ft.Colors.PRIMARY)},
                padding=ft.Padding(12, 6, 12, 6),
            ),
        )
        self._skip_container = ft.Container(
            content=self._skip_button,
            visible=True,
        )

        self._title_text = ft.Text(
            self.page_title or "",
            weight=ft.FontWeight.W_600,
            size=20,
            no_wrap=True,
        )
        self._title_semantics = ft.Semantics(
            label=self.page_title or "Cabecera",
            content=self._title_text,
            focusable=False,
        )

        self._drawer_button = ft.IconButton(
            icon=ft.Icons.MENU,
            tooltip="Abrir navegación",
            on_click=self._open_drawer,
            visible=self.drawer is not None,
        )

        self._accessibility_button = ft.IconButton(
            ft.Icons.ACCESSIBILITY_NEW,
            tooltip="Abrir panel de accesibilidad",
            on_click=self._toggle_accessibility_panel,
        )

        self._app_bar_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._drawer_button,
                        self._title_semantics,
                    ],
                ),
                ft.Row(
                    spacing=6,
                    alignment=ft.MainAxisAlignment.END,
                    controls=list(self.actions) + [self._accessibility_button],
                ),
            ],
        )

        self._app_bar_padding_base = (16, 12, 16, 12)
        self._app_bar = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.94, ft.Colors.SURFACE),
            padding=ft.Padding(*self._app_bar_padding_base),
            content=ft.Column(
                spacing=4,
                controls=[
                    self._skip_container,
                    self._app_bar_row,
                    ft.Row(controls=list(self.header_controls), visible=bool(self.header_controls)),
                ],
            ),
        )
        self._refresh_app_bar_style()

        self._content_host = ft.Container(expand=True)
        self._main_content = ft.Semantics(
            label="Contenido principal",
            content=self._content_host,
            focusable=True,
            container=True,
        )

        self._inline_caption_text = ft.Text("", selectable=True)
        self._inline_caption_container = ft.Container(
            visible=False,
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.BLUE_GREY),
            padding=ft.Padding(16, 12, 16, 12),
            content=self._inline_caption_text,
        )

        self._secondary_panel_host = ft.Container(width=320, visible=False)

        self._body_container = ft.Container(expand=True)
        self._footer_container = ft.Container()

        self._root_column = ft.Column(
            expand=True,
            spacing=0,
            controls=[self._body_container, self._footer_container],
        )

        self._stack = ft.Stack(
            expand=True,
            controls=[self._root_column, self.caption_overlay.control, self._fab_host],
        )

        self._accessibility_bottom_sheet = ft.BottomSheet(ft.Container())
        # El contenido real se inyectará al construir en ``build``.

    # ------------------------------------------------------------------
    @property
    def selected_item(self) -> AdaptiveNavigationItem:
        return self.navigation_items[self._selected_index]

    @property
    def root(self) -> ft.Control:
        """Control raíz que puede añadirse directamente a la página."""

        return self._stack

    # ------------------------------------------------------------------
    def build(self, page: ft.Page) -> ft.Control:
        """Configura listeners responsivos y devuelve el control raíz."""

        self._page = page
        if self.page_title:
            page.title = self.page_title
        if self.drawer is not None:
            setattr(page, "drawer", self.drawer)

        # Reemplazamos el contenido vacío del BottomSheet por la versión real
        panel_control = self.accessibility_panel.build(page)
        sheet_panel_control = self._sheet_accessibility_panel.build(page)
        sheet_content = ft.Container(
            padding=ft.Padding(16, 16, 16, 32),
            content=sheet_panel_control,
            expand=False,
        )
        self._accessibility_bottom_sheet.content = sheet_content
        if self._accessibility_bottom_sheet not in page.overlay:
            page.overlay.append(self._accessibility_bottom_sheet)

        self.caption_overlay.build(page)

        self.accessibility.apply(page, self.theme)
        self._refresh_app_bar_style()
        self._refresh_caption_targets()
        self._refresh_content()

        callbacks = {
            profile.min_width: self._handle_breakpoint_change
            for profile in iter_device_profiles(self.device_profiles)
        }
        self._manager = ResponsiveManager(
            page,
            breakpoints=callbacks,
            device_callbacks={profile.name: self._apply_device_layout for profile in self.device_profiles},
            device_profiles=self.device_profiles,
        )

        width = page.width or 0
        device = get_device_profile(width, self.device_profiles).name
        self._apply_device_layout(device)
        return self._stack

    # ------------------------------------------------------------------
    def announce(self, message: str, *, tone: CaptionTone = "info") -> None:
        """Comunica un mensaje accesible (texto y voz si está disponible)."""

        if not message:
            return

        if self.accessibility.enable_captions:
            if self.accessibility.caption_mode == "overlay":
                self.caption_overlay.announce(message, tone=tone)
            else:
                self._inline_caption_text.value = message
                self._inline_caption_container.visible = True

        if self._page and hasattr(self._page, "speak"):
            try:
                self._page.speak(message)
            except Exception:
                # Ignorar fallos de ``speak`` en plataformas no compatibles.
                pass

        if self._page:
            self._page.update()

    # ------------------------------------------------------------------
    def select(self, index: int) -> None:
        """Selecciona el índice indicado y refresca el contenido."""

        if not 0 <= index < len(self.navigation_items):
            return
        if index == self._selected_index:
            return
        self._selected_index = index
        self._nav_bar.selected_index = index
        self._nav_rail.selected_index = index
        self._refresh_content()
        self._refresh_secondary_panel()
        if self._page:
            self._page.update()

    # ------------------------------------------------------------------
    def _handle_accessibility_change(self, preferences: AccessibilityPreferences) -> None:
        self.accessibility = preferences
        if self._page:
            preferences.apply(self._page, self.theme)
        self._refresh_caption_targets()
        if self._page:
            self._page.update()

    # ------------------------------------------------------------------
    def _refresh_caption_targets(self) -> None:
        overlay_enabled = self.accessibility.enable_captions and self.accessibility.caption_mode == "overlay"
        self.caption_overlay.set_enabled(overlay_enabled)
        show_inline = (
            self.accessibility.enable_captions and self.accessibility.caption_mode == "inline"
        )
        if not show_inline:
            self._inline_caption_text.value = ""
        self._inline_caption_container.visible = show_inline and bool(self._inline_caption_text.value)

    # ------------------------------------------------------------------
    def _style_navigation(self, device_name: str) -> None:
        if not self.theme:
            return

        surface = (
            self.theme.get_color("surface")
            or self.theme.get_color("surface_variant")
            or self.theme.get_color("background")
        )
        accent = self.theme.get_color("accent") or self.theme.get_color("primary")

        nav_bg: str | None = None
        rail_bg: str | None = None
        if isinstance(surface, str):
            nav_bg = ft.Colors.with_opacity(0.95 if device_name == "mobile" else 0.9, surface)
            rail_bg = ft.Colors.with_opacity(
                0.16 if device_name == "large_desktop" else 0.1,
                surface,
            )

        if nav_bg is not None:
            self._nav_bar.bgcolor = nav_bg
        if rail_bg is not None:
            self._nav_rail.bgcolor = rail_bg

        if isinstance(accent, str):
            indicator = ft.Colors.with_opacity(0.22, accent)
            self._nav_bar.indicator_color = indicator
            self._nav_rail.indicator_color = indicator

    # ------------------------------------------------------------------
    def _resolve_app_bar_background(self) -> tuple[str | None, ft.Gradient | None]:
        if self._explicit_app_bar_gradient is not None:
            return None, self._explicit_app_bar_gradient

        gradient = None
        if self.theme and self.app_bar_gradient_token:
            gradient = self.theme.get_gradient(self.app_bar_gradient_token)
        if isinstance(gradient, ft.LinearGradient):
            return None, gradient

        if self.app_bar_background is not None:
            return self.app_bar_background, None

        if self.theme:
            candidate = (
                self.theme.get_color("surface")
                or self.theme.get_color("surface_variant")
                or self.theme.get_color("background")
            )
            if isinstance(candidate, str):
                return ft.Colors.with_opacity(0.96, candidate), None

        return ft.Colors.with_opacity(0.94, ft.Colors.SURFACE), None

    # ------------------------------------------------------------------
    def _refresh_app_bar_style(self) -> None:
        color, gradient = self._resolve_app_bar_background()
        self._app_bar.bgcolor = color
        self._app_bar.gradient = gradient

    # ------------------------------------------------------------------
    def _refresh_content(self) -> None:
        item = self.selected_item
        content = self.content_builder(item, self._selected_index)
        self._content_host.content = content
        if self._page:
            self._page.update()

    # ------------------------------------------------------------------
    def _refresh_secondary_panel(self) -> None:
        if not self.secondary_panel_builder:
            self._secondary_panel_host.visible = False
            self._secondary_panel_host.content = None
            return

        item = self.selected_item
        panel = self.secondary_panel_builder(item)
        self._secondary_panel_host.content = panel
        self._secondary_panel_host.visible = panel is not None

    # ------------------------------------------------------------------
    def _apply_device_layout(self, device_name: str) -> None:
        previous_device = getattr(self, "_current_device", device_name)
        self._current_device = device_name
        is_mobile = device_name == "mobile"
        is_desktop = device_name in {"desktop", "large_desktop"}
        is_large_desktop = device_name == "large_desktop"

        if self.theme and self._page:
            orientation = (
                "landscape"
                if (self._page.width or 0) >= (self._page.height or 0)
                else "portrait"
            )
            self.theme.apply_theme(
                device=device_name,
                orientation=orientation,
                width=self._page.width or 0,
            )
            self._refresh_app_bar_style()
        self._style_navigation(device_name)

        self._drawer_button.visible = bool(self.drawer) and not is_desktop
        self._nav_bar.visible = is_mobile
        self._nav_rail.visible = not is_mobile
        self._nav_rail.extended = is_desktop

        if is_large_desktop and self.auto_show_accessibility_on_large_desktop and previous_device != "large_desktop":
            self._show_desktop_accessibility_panel = True

        if is_large_desktop:
            self._app_bar.padding = ft.Padding(24, 18, 24, 18)
        elif is_desktop:
            self._app_bar.padding = ft.Padding(20, 14, 20, 14)
        else:
            self._app_bar.padding = ft.Padding(*self._app_bar_padding_base)

        central_column = ft.Column(
            expand=True,
            spacing=0,
            controls=[self._app_bar, self._main_content, self._inline_caption_container],
        )

        if is_mobile:
            self._body_container.content = central_column
            self._footer_container.content = ft.Container(
                bgcolor=ft.Colors.with_opacity(0.98, ft.Colors.SURFACE),
                border=ft.border.only(top=ft.BorderSide(1, ft.Colors.with_opacity(0.12, ft.Colors.BLACK))),
                content=self._nav_bar,
            )
            self._show_desktop_accessibility_panel = False
        else:
            self._accessibility_bottom_sheet.open = False
            rail_width = 110 if is_large_desktop else (92 if is_desktop else 80)
            rail_padding = ft.Padding(16, 16, 16, 16) if is_large_desktop else ft.Padding(12, 12, 12, 12)
            rail_bg = ft.Colors.with_opacity(0.04, ft.Colors.BLUE_GREY)
            if self.theme:
                candidate = self.theme.get_color("surface_variant")
                if isinstance(candidate, str):
                    rail_bg = ft.Colors.with_opacity(0.18 if is_large_desktop else 0.08, candidate)
            rail_container = ft.Container(
                width=rail_width,
                bgcolor=rail_bg,
                padding=rail_padding,
                content=self._nav_rail,
            )

            central_host: ft.Control = central_column
            if is_desktop and self.desktop_max_content_width:
                central_host = ft.Row(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=self.desktop_max_content_width,
                            content=central_column,
                        )
                    ],
                )

            controls: list[ft.Control] = [rail_container, central_host]

            self._refresh_secondary_panel()
            self._secondary_panel_host.width = (
                self.large_desktop_panel_width
                if is_large_desktop
                else (320 if is_desktop else 280)
            )
            if not is_desktop:
                self._show_desktop_accessibility_panel = False

            side_controls: list[ft.Control] = []
            if is_desktop and self._show_desktop_accessibility_panel:
                side_controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.BLUE_GREY),
                        padding=ft.Padding(18, 16, 18, 16) if is_large_desktop else ft.Padding(16, 12, 16, 12),
                        border=ft.border.only(left=ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.BLACK))),
                        content=ft.Column(
                            tight=True,
                            spacing=12,
                            controls=[
                                ft.Text("Accesibilidad", weight=ft.FontWeight.W_600, size=16),
                                self.accessibility_panel.control or ft.Container(),
                            ],
                        ),
                    )
                )

            if self._secondary_panel_host.visible and self._secondary_panel_host.content is not None:
                side_controls.append(self._secondary_panel_host)

            controls.extend(side_controls)

            self._body_container.content = ft.Row(
                expand=True,
                spacing=16 if is_large_desktop else 0,
                controls=controls,
            )
            self._footer_container.content = ft.Container()

        if self._page:
            self._page.update()

    # ------------------------------------------------------------------
    def _handle_breakpoint_change(self, _: int) -> None:
        if not self._page:
            return
        device = get_device_profile(self._page.width or 0, self.device_profiles).name
        self._apply_device_layout(device)

    # ------------------------------------------------------------------
    def _on_navigation_bar_change(self, event: ft.ControlEvent) -> None:
        index = getattr(event.control, "selected_index", self._selected_index)
        self.select(index)

    def _on_navigation_rail_change(self, event: ft.ControlEvent) -> None:
        index = getattr(event.control, "selected_index", self._selected_index)
        self.select(index)

    # ------------------------------------------------------------------
    def _focus_main_content(self, _: ft.ControlEvent | None = None) -> None:
        if self._page and hasattr(self._page, "set_focus"):
            try:
                self._page.set_focus(self._content_host)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def _toggle_accessibility_panel(self, _: ft.ControlEvent | None = None) -> None:
        if self._current_device in {"desktop", "large_desktop"}:
            self._show_desktop_accessibility_panel = not self._show_desktop_accessibility_panel
            self._apply_device_layout(self._current_device)
            return

        self._accessibility_bottom_sheet.open = True
        if self._page:
            self._page.update()

    # ------------------------------------------------------------------
    def _open_drawer(self, _: ft.ControlEvent | None = None) -> None:
        if self._page and hasattr(self._page, "open_drawer"):
            try:
                self._page.open_drawer()
            except Exception:
                pass


__all__ = ["AdaptiveNavigationItem", "UniversalAdaptiveScaffold"]
