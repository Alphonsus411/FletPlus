import logging
from typing import Callable

import flet as ft

from fletplus.themes.theme_manager import ThemeManager
from fletplus.components.sidebar_admin import SidebarAdmin
from fletplus.desktop.window_manager import WindowManager
from fletplus.utils.shortcut_manager import ShortcutManager
from fletplus.components.command_palette import CommandPalette
from fletplus.utils.device import is_mobile, is_web, is_desktop
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.styles import Style

logger = logging.getLogger(__name__)


class FletPlusApp:
    def __init__(
        self,
        page: ft.Page,
        routes: dict[str, Callable[[], ft.Control]],
        sidebar_items=None,
        commands: dict | None = None,
        title: str = "FletPlus App",
        theme_config: dict | None = None,
        use_window_manager: bool = False,
    ) -> None:
        self.page = page
        self.routes = routes
        raw_sidebar = list(sidebar_items or [])
        self.title = title

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
        self.window_manager = WindowManager(page) if use_window_manager else None

        self.command_palette = CommandPalette(commands or {})
        self.shortcuts = ShortcutManager(page)
        self.shortcuts.register("k", lambda: self.command_palette.open(self.page), ctrl=True)

        self._routes_order = list(self.routes.keys())
        self._nav_items = []
        for index, route_key in enumerate(self._routes_order):
            item = raw_sidebar[index] if index < len(raw_sidebar) else {}
            title_value = item.get("title") or route_key.replace("_", " ").title()
            icon_value = item.get("icon", ft.Icons.CIRCLE)
            self._nav_items.append({"title": title_value, "icon": icon_value})

        if not self._nav_items:
            for route_key in self._routes_order:
                self._nav_items.append({"title": route_key.title(), "icon": ft.Icons.CIRCLE})

        self.sidebar_items = self._nav_items
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

        if self.routes:
            self._activate_route(0)

        if not hasattr(self.page, "width") or self.page.width is None:
            self.page.width = 1280
        if not hasattr(self.page, "height") or self.page.height is None:
            self.page.height = 800

        self._responsive_manager = ResponsiveManager(
            self.page,
            breakpoints={
                0: self._handle_resize,
                640: self._handle_resize,
                900: self._handle_resize,
                1280: self._handle_resize,
            },
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

        self._body_row = ft.Row(
            controls=[self._sidebar_container, self.content_container],
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
        if not self._nav_items:
            return

        destinations = [
            ft.NavigationBarDestination(
                icon=item.get("icon", ft.Icons.CIRCLE),
                label=item.get("title", ""),
            )
            for item in self._nav_items
        ]
        indicator = self.theme.get_color("accent", self.theme.get_color("primary", ft.Colors.PRIMARY))
        nav_bg = self.theme.get_color("surface_variant")
        if not nav_bg:
            nav_bg = ft.Colors.with_opacity(0.08, indicator if isinstance(indicator, str) else ft.Colors.PRIMARY)
        self._mobile_nav = ft.NavigationBar(
            destinations=destinations,
            on_change=self._handle_mobile_nav_change,
            selected_index=0,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            indicator_color=indicator,
            bgcolor=nav_bg,
        )

        drawer_controls = [
            ft.NavigationDrawerDestination(
                label=item.get("title", ""),
                icon=item.get("icon", ft.Icons.CIRCLE),
            )
            for item in self._nav_items
        ]
        self._drawer = ft.NavigationDrawer(
            controls=drawer_controls,
            selected_index=0,
            on_change=self._handle_drawer_change,
        )

    # ------------------------------------------------------------------
    def _handle_mobile_nav_change(self, e: ft.ControlEvent) -> None:
        self._activate_route(e.control.selected_index)

    # ------------------------------------------------------------------
    def _handle_drawer_change(self, e: ft.ControlEvent) -> None:
        self._activate_route(e.control.selected_index)
        self.page.close_drawer()

    # ------------------------------------------------------------------
    def _open_drawer(self, _e: ft.ControlEvent | None = None) -> None:
        if self.page.drawer:
            self.page.open_drawer()

    # ------------------------------------------------------------------
    def _toggle_theme(self, _e: ft.ControlEvent | None = None) -> None:
        self.theme.toggle_dark_mode()
        self._update_header_colors()
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
    @staticmethod
    def _resolve_layout_mode(width: int) -> str:
        if width < 720:
            return "mobile"
        if width < 1100:
            return "tablet"
        return "desktop"

    # ------------------------------------------------------------------
    def _apply_layout_mode(self, mode: str, *, force: bool = False) -> None:
        if not force and mode == self._layout_mode:
            return

        self._layout_mode = mode
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

        if self._sidebar_container is not None:
            self._sidebar_container.visible = not is_mobile
            sidebar_width = 260 if mode == "desktop" else 220
            if hasattr(self.sidebar, "width"):
                self.sidebar.width = sidebar_width
            self._sidebar_container.width = sidebar_width if not is_mobile else 0

        if self._menu_button is not None:
            self._menu_button.visible = is_mobile or is_tablet

        if self._drawer is not None:
            self.page.drawer = self._drawer if (is_mobile or is_tablet) else None

        if self._mobile_nav is not None:
            self._mobile_nav.selected_index = getattr(self.sidebar, "selected_index", 0)
            self.page.navigation_bar = self._mobile_nav if is_mobile else None

        self.page.update()

    # ------------------------------------------------------------------
    def _activate_route(self, index: int) -> None:
        if not 0 <= index < len(self._routes_order):
            logger.error("Invalid route index: %s", index)
            return

        route_key = self._routes_order[index]
        builder = self.routes[route_key]
        try:
            content = builder()
        except Exception:  # pragma: no cover - errores del usuario
            logger.exception("Error building route '%s'", route_key)
            content = ft.Container(
                content=ft.Text(f"No se pudo cargar la ruta '{route_key}'"),
                padding=20,
            )
        self.content_container.content = content

        if hasattr(self.sidebar, "select"):
            self.sidebar.select(index)
        else:
            self.sidebar.selected_index = index

        if self._mobile_nav is not None:
            self._mobile_nav.selected_index = index
        if self._drawer is not None:
            self._drawer.selected_index = index

        self.page.update()

    # ------------------------------------------------------------------
    def _on_nav(self, index: int) -> None:
        self._activate_route(index)

    # ------------------------------------------------------------------
    def _load_route(self, index: int) -> None:
        self._activate_route(index)

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
            )
            app.build()

        ft.app(target=main)
