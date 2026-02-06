import logging
from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping

import flet as ft

from fletplus.animation import AnimationController, animation_controller_context

from fletplus.context import (
    ContextProvider,
    locale_context,
    theme_context,
    user_context,
)
from fletplus.themes.theme_manager import ThemeManager
from fletplus.components.sidebar_admin import SidebarAdmin
from fletplus.desktop.window_manager import WindowManager
from fletplus.utils.shortcut_manager import ShortcutManager
from fletplus.components.command_palette import CommandPalette
from fletplus.utils.device import is_mobile, is_web, is_desktop
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.styles import Style
from fletplus.router import Route, Router, RouteMatch
from fletplus.state import Store
from fletplus.utils.preferences import PreferenceStorage

logger = logging.getLogger(__name__)


def _default_menu_padding() -> ft.Padding:
    return ft.Padding(20, 20, 20, 20)


@dataclass(slots=True)
class FloatingMenuOptions:
    """Opciones visuales y de comportamiento del menú flotante móvil."""

    alignment: ft.alignment.Alignment = field(default_factory=lambda: ft.alignment.Alignment(1, 1))
    horizontal_margin: float = 24
    vertical_margin: float = 28
    width: float = 320
    max_height: float = 420
    padding: ft.Padding = field(default_factory=_default_menu_padding)
    border_radius: float = 26
    hidden_offset: float = 0.08
    backdrop_color: str = ft.Colors.BLACK
    backdrop_opacity: float = 0.35
    animation_duration: int = 280
    animation_curve: ft.AnimationCurve = ft.AnimationCurve.DECELERATE
    fab_icon: str = ft.Icons.MENU
    fab_bgcolor: str | None = None
    fab_icon_color: str | None = None


@dataclass(slots=True)
class ResponsiveNavigationConfig:
    """Configura los breakpoints y la variante móvil del menú."""

    mobile_breakpoint: int = 720
    tablet_breakpoint: int = 1100
    desktop_breakpoint: int = 1440
    floating_breakpoint: int | None = 720
    floating_options: FloatingMenuOptions = field(default_factory=FloatingMenuOptions)

    def layout_for_width(self, width: int) -> str:
        if width < self.mobile_breakpoint:
            return "mobile"
        if width < self.tablet_breakpoint:
            return "tablet"
        return "desktop"

    def should_use_floating(self, width: int) -> bool:
        return bool(self.floating_breakpoint is not None and width <= self.floating_breakpoint)


class FletPlusApp:
    def __init__(
        self,
        page: ft.Page,
        routes: dict[str, Callable[[], ft.Control]] | Iterable[Route] | Router,
        sidebar_items=None,
        commands: dict | None = None,
        title: str = "FletPlus App",
        theme_config: dict | None = None,
        use_window_manager: bool = False,
        state: Store | None = None,
        responsive_navigation: ResponsiveNavigationConfig | None = None,
    ) -> None:
        self.page = page
        self.state = state or Store()
        if not hasattr(self.page, "state"):
            setattr(self.page, "state", self.state)
        raw_sidebar = list(sidebar_items or [])
        self.title = title

        self.router, base_nav = self._build_router(routes, raw_sidebar)
        self._nav_routes: list[dict[str, object]] = []
        self._nav_index_by_path: dict[str, int] = {}
        for index, nav_data in enumerate(base_nav):
            item = raw_sidebar[index] if index < len(raw_sidebar) else {}
            title_value = item.get("title") if isinstance(item, dict) else None
            icon_value = item.get("icon") if isinstance(item, dict) else None
            path_value = self._normalize_path_value(str(nav_data["path"]))
            name_value = nav_data.get("name")
            match_value = nav_data.get("match")
            if isinstance(item, dict) and item.get("match"):
                match_value = item.get("match")
            resolved_title = title_value or name_value or path_value.strip("/").replace("-", " ").title() or "Inicio"
            resolved_icon = icon_value or ft.Icons.CIRCLE
            nav_entry = {"title": resolved_title, "icon": resolved_icon, "path": path_value}
            self._nav_routes.append(nav_entry)
            self._nav_index_by_path[path_value] = index
            if match_value:
                self._nav_index_by_path[self._normalize_path_value(str(match_value))] = index

        if is_mobile(page):
            self.platform = "mobile"
        elif is_web(page):
            self.platform = "web"
        elif is_desktop(page):
            self.platform = "desktop"
        else:
            self.platform = getattr(page, "platform", "unknown")

        config = (theme_config or {}).copy()
        tokens = config.get("tokens", {}).copy()
        platform_tokens = config.get(f"{self.platform}_tokens", {})
        tokens.update(platform_tokens)
        config["tokens"] = tokens
        for key in ("mobile_tokens", "web_tokens", "desktop_tokens"):
            config.pop(key, None)

        self.theme = ThemeManager(page, **config)
        self.animation_controller = AnimationController(self.page)
        self.responsive_navigation = responsive_navigation or ResponsiveNavigationConfig()
        self.window_manager = WindowManager(page) if use_window_manager else None
        self._preference_storage = PreferenceStorage(page)
        self._preference_unsubscribers: list[Callable[[], None]] = []
        self._restore_theme_preferences()
        self._observe_theme_preferences()
        self.theme_mode_signal = self.theme.mode_signal
        self.theme_tokens_signal = self.theme.tokens_signal
        self.theme_overrides_signal = self.theme.overrides_signal

        self.contexts: dict[str, object] = {
            "theme": theme_context,
            "user": user_context,
            "locale": locale_context,
            "animation": animation_controller_context,
        }
        self._context_providers: dict[str, ContextProvider] = {}
        self._activate_contexts()

        self.command_palette = CommandPalette(commands or {})
        self.shortcuts = ShortcutManager(page)
        self.shortcuts.register("k", lambda: self.command_palette.open(self.page), ctrl=True)
        self._reactive_renders: list[object] = []

        if not self._nav_routes:
            self.sidebar_items = []
        else:
            self.sidebar_items = self._nav_routes
        self.sidebar = SidebarAdmin(
            self.sidebar_items,
            on_select=self._on_nav,
            header="Navegación",
            width=260,
            style=self._create_sidebar_style(),
        )

        surface_color = self.theme.get_color("surface", ft.Colors.SURFACE) or ft.Colors.SURFACE
        self.content_container = ft.Container(
            expand=True,
            bgcolor=surface_color,
            padding=ft.Padding(32, 28, 32, 32),
            border_radius=ft.border_radius.only(top_left=28, top_right=0, bottom_left=0, bottom_right=0),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        self._content_stack = ft.Stack(controls=[self.content_container], expand=True)

        self._router_unsubscribe = self.router.observe(self._handle_route_change)

        self._layout_mode = "desktop"
        self._responsive_manager: ResponsiveManager | None = None
        self._menu_button: ft.IconButton | None = None
        self._theme_button: ft.IconButton | None = None
        self._command_button: ft.IconButton | None = None
        self._header_container: ft.Container | None = None
        self._title_text: ft.Text | None = None
        self._subtitle_text: ft.Text | None = None
        self._sidebar_container: ft.Container | None = None
        self._body_row: ft.Row | None = None
        self._main_shell: ft.Column | None = None
        self._mobile_nav: ft.NavigationBar | None = None
        self._drawer: ft.NavigationDrawer | None = None
        self._content_area_container: ft.Container | None = None
        self._floating_menu_visible: bool = False
        self._floating_backdrop: ft.Container | None = None
        self._floating_menu_control: ft.Container | None = None
        self._floating_menu_host: ft.Container | None = None
        self._floating_button: ft.FloatingActionButton | None = None
        self._floating_button_host: ft.Container | None = None
        self._floating_tiles: list[ft.ListTile] = []

    # ------------------------------------------------------------------
    def _create_sidebar_style(self) -> Style:
        shadow = ft.BoxShadow(
            blur_radius=28,
            spread_radius=-6,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 12),
        )
        surface_variant = self.theme.get_color("surface_variant", ft.Colors.with_opacity(0.05, ft.Colors.BLACK))
        return Style(
            padding=ft.Padding(12, 18, 12, 18),
            border_radius=ft.border_radius.all(26),
            bgcolor=surface_variant,
            shadow=shadow,
        )

    # ------------------------------------------------------------------
    def _activate_contexts(self) -> None:
        providers: dict[str, ContextProvider] = {}
        theme_provider = theme_context.provide(self.theme)
        providers["theme"] = theme_provider

        user_value = getattr(self.page, "user", None)
        providers["user"] = user_context.provide(user_value)

        locale_value = self._resolve_locale_value()
        providers["locale"] = locale_context.provide(locale_value)

        animation_provider = animation_controller_context.provide(
            self.animation_controller,
            inherit=False,
        )
        providers["animation"] = animation_provider

        for provider in providers.values():
            provider.__enter__()
        self._context_providers = providers
        setattr(self.page, "contexts", self.contexts)

    # ------------------------------------------------------------------
    def _restore_theme_preferences(self) -> None:
        try:
            preferences = self._preference_storage.load()
        except Exception:  # pragma: no cover - errores inesperados
            logger.exception("No se pudieron cargar las preferencias de tema")
            return

        theme_prefs = preferences.get("theme") if isinstance(preferences, Mapping) else None
        if not isinstance(theme_prefs, Mapping):
            return

        updated = False
        dark_mode = theme_prefs.get("dark_mode")
        overrides = theme_prefs.get("overrides")

        if isinstance(dark_mode, bool):
            self.theme.set_dark_mode(dark_mode, refresh=False)
            updated = True

        if isinstance(overrides, Mapping):
            self.theme.load_token_overrides(overrides, refresh=False)
            updated = True

        if updated:
            self.theme.apply_theme()

    # ------------------------------------------------------------------
    def _observe_theme_preferences(self) -> None:
        def persist_on_change(_value: object) -> None:
            self._persist_theme_preferences()

        self._preference_unsubscribers.append(
            self.theme.mode_signal.subscribe(persist_on_change)
        )
        self._preference_unsubscribers.append(
            self.theme.overrides_signal.subscribe(persist_on_change)
        )

    # ------------------------------------------------------------------
    def _persist_theme_preferences(self) -> None:
        snapshot = self._preference_storage.load()
        snapshot["theme"] = {
            "dark_mode": self.theme.dark_mode,
            "overrides": self.theme.get_token_overrides(),
        }
        self._preference_storage.save(snapshot)

    # ------------------------------------------------------------------
    def _resolve_locale_value(self) -> str:
        candidate = getattr(self.page, "locale", None) or getattr(self.page, "language", None)
        if isinstance(candidate, str) and candidate:
            return candidate
        default = getattr(locale_context, "default", None)
        if isinstance(default, str):
            return default
        return "es"

    # ------------------------------------------------------------------
    def dispose(self) -> None:
        if hasattr(self, "_router_unsubscribe") and callable(self._router_unsubscribe):
            try:
                self._router_unsubscribe()
            except Exception:  # pragma: no cover - la limpieza no debe romper la app
                logger.exception("Error al cancelar la subscripción del router")
            finally:
                self._router_unsubscribe = lambda: None
        for unsubscribe in list(getattr(self, "_preference_unsubscribers", [])):
            try:
                unsubscribe()
            except Exception:  # pragma: no cover - limpieza tolerante a fallos
                logger.exception("Error al cancelar observadores de preferencias")
        if hasattr(self, "_preference_unsubscribers"):
            self._preference_unsubscribers.clear()
        for runtime in list(getattr(self, "_reactive_renders", [])):
            dispose = getattr(runtime, "dispose", None)
            if callable(dispose):
                try:
                    dispose()
                except Exception:  # pragma: no cover - limpieza reactiva tolerante
                    logger.exception("Error al limpiar un render reactivo")
        if hasattr(self, "_reactive_renders"):
            self._reactive_renders.clear()
        self._cleanup_contexts()

    # ------------------------------------------------------------------
    def _cleanup_contexts(self) -> None:
        for provider in list(self._context_providers.values()):
            try:
                exit_handler = getattr(provider, "__exit__", None)
                if callable(exit_handler):
                    exit_handler(None, None, None)
                else:
                    provider.close()
            except Exception:  # pragma: no cover - limpieza tolerante a fallos
                logger.exception("Error al cerrar un proveedor de contexto")
        self._context_providers.clear()
        if getattr(self.page, "contexts", None) is self.contexts:
            setattr(self.page, "contexts", {})

    # ------------------------------------------------------------------
    def set_user(self, user: object) -> None:
        provider = self._context_providers.get("user")
        if provider is not None:
            provider.set(user)
        setattr(self.page, "user", user)

    # ------------------------------------------------------------------
    def set_locale(self, locale: str) -> None:
        provider = self._context_providers.get("locale")
        if provider is not None and locale:
            provider.set(locale)
        if locale:
            setattr(self.page, "locale", locale)

    # ------------------------------------------------------------------
    def __del__(self):  # pragma: no cover - método defensivo
        try:
            self.dispose()
        except Exception:
            logger.exception("Error liberando recursos de FletPlusApp")

    # ------------------------------------------------------------------
    def build(self) -> None:
        self.page.title = self.title
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.padding = 0
        self.page.spacing = 0
        self.page.scroll = ft.ScrollMode.AUTO

        self.theme.apply_theme()
        self._create_navigation_shell()
        self._setup_navigation_components()

        initial_path: str | None = None
        if self._nav_routes:
            candidate = str(self._nav_routes[0]["path"])
            if "<" in candidate and ">" in candidate:
                candidate = None
            initial_path = candidate
        if initial_path:
            try:
                self.router.replace(initial_path)
            except Exception:  # pragma: no cover - errores del usuario
                logger.exception("No se pudo activar la ruta inicial '%s'", initial_path)
        elif self.router.current_path is None:
            try:
                self.router.replace("/")
            except Exception:
                logger.debug("No hay ruta inicial disponible para '/'")

        if not hasattr(self.page, "width") or self.page.width is None:
            self.page.width = 1280
        if not hasattr(self.page, "height") or self.page.height is None:
            self.page.height = 800

        breakpoint_values = {0, self.responsive_navigation.mobile_breakpoint, self.responsive_navigation.tablet_breakpoint, self.responsive_navigation.desktop_breakpoint}
        if self.responsive_navigation.floating_breakpoint is not None:
            breakpoint_values.add(self.responsive_navigation.floating_breakpoint)
        sorted_breakpoints = {value: self._handle_resize for value in sorted(breakpoint_values)}

        self._responsive_manager = ResponsiveManager(
            self.page,
            breakpoints=sorted_breakpoints,
        )
        self._apply_layout_mode(self._resolve_layout_mode(self.page.width or 0), force=True)

    # ------------------------------------------------------------------
    def _create_navigation_shell(self) -> None:
        gradient = self.theme.get_gradient("app_header")
        header_bg = None if gradient else self.theme.get_color("primary", ft.Colors.PRIMARY)

        self._menu_button = ft.IconButton(
            icon=ft.Icons.MENU,
            tooltip="Abrir menú de navegación",
            on_click=self._open_drawer,
            visible=False,
        )
        self._theme_button = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE if self.theme.dark_mode else ft.Icons.DARK_MODE,
            tooltip="Alternar modo claro/oscuro",
            on_click=self._toggle_theme,
        )
        self._command_button = ft.IconButton(
            icon=ft.Icons.SEARCH,
            tooltip="Abrir paleta de comandos",
            on_click=lambda _: self.command_palette.open(self.page),
            visible=bool(self.command_palette.commands),
        )

        self._title_text = ft.Text(self.title, weight=ft.FontWeight.W_700, size=22, no_wrap=True)
        self._subtitle_text = ft.Text(
            "Interfaz adaptable para web, escritorio y móvil",
            size=12,
        )

        header_left = ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._menu_button,
                ft.Column(
                    spacing=2,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[self._title_text, self._subtitle_text],
                ),
            ],
        )
        header_right = ft.Row(
            spacing=6,
            alignment=ft.MainAxisAlignment.END,
            controls=[control for control in [self._command_button, self._theme_button] if control],
        )

        self._header_container = ft.Container(
            padding=ft.Padding(24, 20, 24, 20),
            bgcolor=header_bg,
            gradient=gradient,
            content=ft.Row(
                controls=[header_left, header_right],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        sidebar_control = self.sidebar.build()
        self._sidebar_container = ft.Container(
            content=sidebar_control,
            padding=ft.Padding(12, 18, 12, 18),
            alignment=ft.alignment.top_left,
        )

        self._content_area_container = ft.Container(
            expand=True,
            bgcolor=self.theme.get_color("background", ft.Colors.SURFACE),
            content=self._content_stack,
        )

        self._body_row = ft.Row(
            controls=[self._sidebar_container, self._content_area_container],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        body_background = self.theme.get_color("background", ft.Colors.SURFACE)
        self._main_shell = ft.Column(
            controls=[
                self._header_container,
                ft.Container(expand=True, bgcolor=body_background, content=self._body_row),
            ],
            spacing=0,
            expand=True,
        )

        self.page.controls.clear()
        self.page.add(self._main_shell)
        self._update_header_colors()

    # ------------------------------------------------------------------
    def _setup_navigation_components(self) -> None:
        if not self._nav_routes:
            return

        destinations = [
            ft.NavigationBarDestination(
                icon=item.get("icon", ft.Icons.CIRCLE),
                label=item.get("title", ""),
            )
            for item in self._nav_routes
        ]
        indicator = self.theme.get_color("accent", self.theme.get_color("primary", ft.Colors.PRIMARY))
        nav_bg = self.theme.get_color("surface_variant")
        if not nav_bg:
            nav_bg = ft.Colors.with_opacity(0.08, indicator if isinstance(indicator, str) else ft.Colors.PRIMARY)
        self._mobile_nav = ft.NavigationBar(
            destinations=destinations,
            on_change=self._handle_mobile_nav_change,
            selected_index=getattr(self.sidebar, "selected_index", 0),
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            indicator_color=indicator,
            bgcolor=nav_bg,
        )

        drawer_controls = [
            ft.NavigationDrawerDestination(
                label=item.get("title", ""),
                icon=item.get("icon", ft.Icons.CIRCLE),
            )
            for item in self._nav_routes
        ]
        self._drawer = ft.NavigationDrawer(
            controls=drawer_controls,
            selected_index=getattr(self.sidebar, "selected_index", 0),
            on_change=self._handle_drawer_change,
        )

        self._build_floating_navigation()

    # ------------------------------------------------------------------
    def _build_floating_navigation(self) -> None:
        if not self._nav_routes or self._content_stack is None:
            return

        # Elimina componentes previos cuando el tema se reconstruye
        for control in [self._floating_backdrop, self._floating_menu_host, self._floating_button_host]:
            if control is not None and control in self._content_stack.controls:
                self._content_stack.controls.remove(control)

        options = self.responsive_navigation.floating_options
        accent = self.theme.get_color("accent", self.theme.get_color("primary", ft.Colors.PRIMARY))
        surface = self.theme.get_color("surface_container_high", None) or self.theme.get_color("surface", ft.Colors.SURFACE)
        on_surface = self.theme.get_color("on_surface", ft.Colors.ON_SURFACE)
        muted = self.theme.get_color("muted", on_surface)

        self._floating_tiles = []
        for index, item in enumerate(self._nav_routes):
            tile = ft.ListTile(
                dense=True,
                data=index,
                leading=ft.Icon(item.get("icon", ft.Icons.CIRCLE), color=muted, size=22),
                title=ft.Text(item.get("title", ""), color=on_surface, weight=ft.FontWeight.W_500),
                on_click=lambda _e, idx=index: self._handle_floating_item_click(idx),
                selected=index == getattr(self.sidebar, "selected_index", 0),
            )
            tile.selected_color = accent
            tile.hover_color = ft.Colors.with_opacity(0.08, accent if isinstance(accent, str) else ft.Colors.PRIMARY)
            tile.shape = ft.RoundedRectangleBorder(radius=18)
            self._floating_tiles.append(tile)

        menu_column = ft.Column(
            controls=self._floating_tiles,
            tight=True,
            spacing=4,
            height=options.max_height,
            scroll=ft.ScrollMode.AUTO,
        )

        self._floating_menu_control = ft.Container(
            width=options.width,
            bgcolor=surface,
            border_radius=ft.border_radius.all(options.border_radius),
            padding=options.padding,
            content=menu_column,
            opacity=0,
            offset=ft.transform.Offset(0, options.hidden_offset),
            animate_opacity=ft.Animation(options.animation_duration, curve=options.animation_curve),
            animate_offset=ft.Animation(options.animation_duration, curve=options.animation_curve),
            shadow=ft.BoxShadow(
                blur_radius=36,
                spread_radius=-18,
                color=ft.Colors.with_opacity(0.22, ft.Colors.BLACK),
                offset=ft.Offset(0, 28),
            ),
        )

        self._floating_backdrop = ft.Container(
            expand=True,
            bgcolor=options.backdrop_color,
            opacity=0,
            visible=False,
            animate_opacity=ft.Animation(options.animation_duration, curve=options.animation_curve),
            on_click=lambda _e: self._toggle_floating_menu(False),
        )

        fab_bg = options.fab_bgcolor or accent
        fab_fg = options.fab_icon_color or self.theme.get_color("on_primary", ft.Colors.ON_PRIMARY)
        self._floating_button = ft.FloatingActionButton(
            icon=options.fab_icon,
            bgcolor=fab_bg,
            foreground_color=fab_fg,
            on_click=lambda _e: self._toggle_floating_menu(),
        )

        padding = ft.Padding(options.horizontal_margin, options.vertical_margin, options.horizontal_margin, options.vertical_margin)
        self._floating_menu_host = ft.Container(
            alignment=options.alignment,
            padding=padding,
            content=self._floating_menu_control,
            visible=False,
        )
        self._floating_button_host = ft.Container(
            alignment=options.alignment,
            padding=padding,
            content=self._floating_button,
            visible=False,
        )

        self._content_stack.controls.extend(
            [self._floating_backdrop, self._floating_menu_host, self._floating_button_host]
        )
        self._floating_menu_visible = False
        self._refresh_floating_controls()

    # ------------------------------------------------------------------
    def _handle_mobile_nav_change(self, e: ft.ControlEvent) -> None:
        self._navigate_to_index(e.control.selected_index)

    # ------------------------------------------------------------------
    def _handle_drawer_change(self, e: ft.ControlEvent) -> None:
        self._navigate_to_index(e.control.selected_index)
        self.page.close_drawer()

    # ------------------------------------------------------------------
    def _handle_floating_item_click(self, index: int) -> None:
        self._close_floating_menu()
        self._navigate_to_index(index)

    # ------------------------------------------------------------------
    def _refresh_floating_controls(self) -> None:
        use_floating = self._should_use_floating_navigation()
        if not use_floating:
            self._floating_menu_visible = False

        options = self.responsive_navigation.floating_options
        if self._floating_button_host is not None:
            self._floating_button_host.visible = use_floating
        if self._floating_backdrop is not None:
            self._floating_backdrop.visible = use_floating and self._floating_menu_visible
            self._floating_backdrop.opacity = options.backdrop_opacity if (use_floating and self._floating_menu_visible) else 0
        if self._floating_menu_host is not None:
            self._floating_menu_host.visible = use_floating
        if self._floating_menu_control is not None:
            self._floating_menu_control.opacity = 1 if (use_floating and self._floating_menu_visible) else 0
            self._floating_menu_control.offset = ft.transform.Offset(
                0, 0 if (use_floating and self._floating_menu_visible) else options.hidden_offset
            )

    # ------------------------------------------------------------------
    def _toggle_floating_menu(self, open_state: bool | None = None) -> None:
        if not self._should_use_floating_navigation():
            return

        desired_state = (not self._floating_menu_visible) if open_state is None else bool(open_state)
        if desired_state == self._floating_menu_visible:
            return

        self._floating_menu_visible = desired_state
        self._refresh_floating_controls()
        self.page.update()

    # ------------------------------------------------------------------
    def _close_floating_menu(self, *, refresh: bool = True) -> None:
        if self._floating_menu_visible:
            self._floating_menu_visible = False
            self._refresh_floating_controls()
            if refresh:
                self.page.update()

    # ------------------------------------------------------------------
    def _should_use_floating_navigation(self) -> bool:
        if not self._nav_routes or self.responsive_navigation is None:
            return False

        width = getattr(self.page, "width", 0) or 0
        try:
            numeric_width = int(width)
        except (TypeError, ValueError):  # pragma: no cover - ancho proviene de Flet
            numeric_width = 0
        return self.responsive_navigation.should_use_floating(numeric_width)

    # ------------------------------------------------------------------
    def _open_drawer(self, _e: ft.ControlEvent | None = None) -> None:
        if self.page.drawer:
            self.page.open_drawer()

    # ------------------------------------------------------------------
    def _toggle_theme(self, _e: ft.ControlEvent | None = None) -> None:
        self.theme.toggle_dark_mode()
        self._update_header_colors()
        self._build_floating_navigation()
        self._apply_layout_mode(self._layout_mode, force=True)

    # ------------------------------------------------------------------
    def _update_header_colors(self) -> None:
        primary = self.theme.get_color("primary", ft.Colors.PRIMARY)
        on_primary = self.theme.get_color("on_primary", ft.Colors.ON_PRIMARY) or ft.Colors.ON_PRIMARY
        muted = self.theme.get_color("muted", on_primary)
        gradient = self.theme.get_gradient("app_header")

        if self._header_container is not None:
            self._header_container.gradient = gradient
            self._header_container.bgcolor = None if gradient else primary

        if self._title_text is not None:
            self._title_text.color = on_primary
        if self._subtitle_text is not None:
            try:
                self._subtitle_text.color = ft.Colors.with_opacity(0.85, muted)
            except Exception:
                self._subtitle_text.color = muted

        icon_color = on_primary
        if self._menu_button is not None:
            self._menu_button.icon_color = icon_color
        if self._theme_button is not None:
            self._theme_button.icon = ft.Icons.LIGHT_MODE if self.theme.dark_mode else ft.Icons.DARK_MODE
            self._theme_button.icon_color = icon_color
        if self._command_button is not None:
            self._command_button.icon_color = icon_color

        if self._mobile_nav is not None:
            self._mobile_nav.indicator_color = self.theme.get_color("accent", primary)
            self._mobile_nav.bgcolor = self.theme.get_color("surface_variant", ft.Colors.SURFACE_VARIANT)

    # ------------------------------------------------------------------
    def _handle_resize(self, width: int) -> None:
        self._apply_layout_mode(self._resolve_layout_mode(width))

    # ------------------------------------------------------------------
    def _resolve_layout_mode(self, width: int) -> str:
        try:
            numeric_width = int(width)
        except (TypeError, ValueError):  # pragma: no cover - valores de Flet
            numeric_width = 0
        return self.responsive_navigation.layout_for_width(numeric_width)

    # ------------------------------------------------------------------
    def _apply_layout_mode(self, mode: str, *, force: bool = False) -> None:
        if not force and mode == self._layout_mode:
            return

        self._layout_mode = mode
        use_floating = self._should_use_floating_navigation()
        is_mobile = mode == "mobile"
        is_tablet = mode == "tablet"
        padding_map = {
            "mobile": ft.Padding(18, 20, 18, 24),
            "tablet": ft.Padding(26, 24, 28, 28),
            "desktop": ft.Padding(36, 28, 40, 32),
        }
        header_padding = {
            "mobile": ft.Padding(20, 16, 20, 16),
            "tablet": ft.Padding(24, 18, 24, 18),
            "desktop": ft.Padding(32, 22, 32, 22),
        }

        if self.content_container is not None:
            self.content_container.padding = padding_map.get(mode, self.content_container.padding)
            self.content_container.bgcolor = self.theme.get_color("surface", ft.Colors.SURFACE)

        if self._header_container is not None:
            self._header_container.padding = header_padding.get(mode, self._header_container.padding)

        if self._content_area_container is not None:
            self._content_area_container.bgcolor = self.theme.get_color("background", ft.Colors.SURFACE)

        if self._sidebar_container is not None:
            self._sidebar_container.visible = not is_mobile
            sidebar_width = 260 if mode == "desktop" else 220
            if hasattr(self.sidebar, "width"):
                self.sidebar.width = sidebar_width
            self._sidebar_container.width = sidebar_width if not is_mobile else 0

        if self._menu_button is not None:
            self._menu_button.visible = is_mobile or is_tablet

        if self._drawer is not None:
            self.page.drawer = self._drawer if (is_tablet or (is_mobile and not use_floating)) else None

        if self._mobile_nav is not None:
            self._mobile_nav.selected_index = getattr(self.sidebar, "selected_index", 0)
            if is_mobile and not use_floating:
                self.page.navigation_bar = self._mobile_nav
            else:
                current_nav = getattr(self.page, "navigation_bar", None)
                if current_nav is self._mobile_nav:
                    setattr(self.page, "navigation_bar", None)

        self._refresh_floating_controls()

        self.page.update()

    # ------------------------------------------------------------------
    def _navigate_to_index(self, index: int) -> None:
        if not 0 <= index < len(self._nav_routes):
            logger.error("Invalid route index: %s", index)
            return

        path = str(self._nav_routes[index]["path"])
        try:
            self.router.go(path)
        except Exception:  # pragma: no cover - errores del usuario
            logger.exception("No se pudo navegar a la ruta '%s'", path)

    # ------------------------------------------------------------------
    def _on_nav(self, index: int) -> None:
        self._navigate_to_index(index)

    # ------------------------------------------------------------------
    def _load_route(self, index: int) -> None:
        self._navigate_to_index(index)

    # ------------------------------------------------------------------
    def _handle_route_change(self, match: RouteMatch, control: ft.Control) -> None:
        if self.content_container is not None:
            self.content_container.content = control
        index = self._nav_index_by_path.get(match.node.full_path)
        if index is not None:
            self._update_nav_selection(index)
        if self._floating_menu_visible:
            self._close_floating_menu(refresh=False)
        self.page.update()
        self.animation_controller.trigger("mount")

    # ------------------------------------------------------------------
    def _register_reactive_render(self, runtime: object) -> None:
        if runtime not in self._reactive_renders:
            self._reactive_renders.append(runtime)

    # ------------------------------------------------------------------
    def _reactive_trigger(self, _runtime: object | None = None) -> None:
        try:
            self.page.update()
        except Exception:  # pragma: no cover - errores del usuario
            logger.exception("No se pudo actualizar la página tras un cambio reactivo")

    # ------------------------------------------------------------------
    def _update_nav_selection(self, index: int) -> None:
        if hasattr(self.sidebar, "select"):
            self.sidebar.select(index)
        else:
            self.sidebar.selected_index = index

        if self._mobile_nav is not None:
            self._mobile_nav.selected_index = index
        if self._drawer is not None:
            self._drawer.selected_index = index
        accent = self.theme.get_color("accent", self.theme.get_color("primary", ft.Colors.PRIMARY))
        muted = self.theme.get_color("muted", self.theme.get_color("on_surface", ft.Colors.ON_SURFACE))
        for idx, tile in enumerate(self._floating_tiles):
            tile.selected = idx == index
            if isinstance(tile.leading, ft.Icon):
                tile.leading.color = accent if idx == index else muted

    # ------------------------------------------------------------------
    def _build_router(
        self,
        routes_input: dict[str, Callable[[], ft.Control]] | Iterable[Route] | Router,
        sidebar_items: list,
    ) -> tuple[Router, list[dict[str, object]]]:
        if isinstance(routes_input, Router):
            nav_data: list[dict[str, object]] = []
            for item in sidebar_items:
                if isinstance(item, dict) and "path" in item:
                    nav_data.append({"path": self._normalize_path_value(str(item["path"])), "name": item.get("title")})
            return routes_input, nav_data

        router = Router()
        nav_data: list[dict[str, object]] = []

        if isinstance(routes_input, dict):
            for key, target in routes_input.items():
                if isinstance(target, Route):
                    wrapped_route = self._wrap_route(target)
                    router.register(wrapped_route)
                    nav_data.append({
                        "path": self._normalize_path_value(wrapped_route.path),
                        "name": wrapped_route.name or key,
                    })
                else:
                    if not callable(target):
                        raise TypeError(f"El valor asociado a la ruta '{key}' debe ser callable o Route")
                    path = self._path_from_key(str(key))
                    router.register(Route(path=path, name=str(key), view=self._wrap_view(target)))
                    nav_data.append({"path": path, "name": str(key)})
            return router, nav_data

        for route in routes_input:
            if not isinstance(route, Route):
                raise TypeError("Todos los elementos deben ser instancias de Route")
            wrapped_route = self._wrap_route(route)
            router.register(wrapped_route)
            nav_data.append({
                "path": self._normalize_path_value(wrapped_route.path),
                "name": wrapped_route.name,
            })

        if not nav_data:
            for item in sidebar_items:
                if isinstance(item, dict) and "path" in item:
                    nav_data.append({"path": self._normalize_path_value(str(item["path"])), "name": item.get("title")})

        return router, nav_data

    # ------------------------------------------------------------------
    def _wrap_view(self, builder: Callable[[], ft.Control]) -> Callable[[RouteMatch], ft.Control]:
        def _view(_match: RouteMatch) -> ft.Control:
            self.animation_controller.trigger("unmount")
            self.animation_controller.reset()
            return builder()

        return _view

    # ------------------------------------------------------------------
    def _wrap_route(self, route: Route) -> Route:
        if route.view is None:
            return route
        return Route(
            path=route.path,
            view=self._wrap_route_view(route.view),
            layout=route.layout,
            name=route.name,
            children=route.children,
        )

    # ------------------------------------------------------------------
    def _wrap_route_view(self, builder: Callable[[RouteMatch], ft.Control]) -> Callable[[RouteMatch], ft.Control]:
        def _view(match: RouteMatch) -> ft.Control:
            self.animation_controller.trigger("unmount")
            self.animation_controller.reset()
            return builder(match)

        return _view

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_path_value(path: str) -> str:
        cleaned = path.strip()
        if not cleaned:
            return "/"
        if not cleaned.startswith("/"):
            cleaned = "/" + cleaned
        if len(cleaned) > 1 and cleaned.endswith("/"):
            cleaned = cleaned[:-1]
        return cleaned

    # ------------------------------------------------------------------
    @staticmethod
    def _path_from_key(key: str) -> str:
        slug = key.strip().lower().replace(" ", "-")
        allowed = []
        for char in slug:
            if char.isalnum() or char in {"-", "_"}:
                allowed.append(char)
            else:
                allowed.append("-")
        cleaned = "".join(allowed)
        cleaned = "-".join(filter(None, cleaned.split("-")))
        if not cleaned:
            cleaned = "inicio"
        return "/" + cleaned

    # ------------------------------------------------------------------
    def open_window(self, name: str, page: ft.Page) -> None:
        if self.window_manager:
            self.window_manager.open_window(name, page)

    # ------------------------------------------------------------------
    def close_window(self, name: str) -> None:
        if self.window_manager:
            self.window_manager.close_window(name)

    # ------------------------------------------------------------------
    def focus_window(self, name: str) -> None:
        if self.window_manager:
            self.window_manager.focus_window(name)

    # ------------------------------------------------------------------
    @classmethod
    def start(
        cls,
        routes,
        sidebar_items=None,
        commands: dict | None = None,
        title: str = "FletPlus App",
        theme_config=None,
        use_window_manager: bool = False,
        responsive_navigation: ResponsiveNavigationConfig | None = None,
    ) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        def main(page: ft.Page) -> None:
            app = cls(
                page,
                routes,
                sidebar_items,
                commands,
                title,
                theme_config,
                use_window_manager,
                responsive_navigation,
            )
            app.build()

        ft.app(target=main)
