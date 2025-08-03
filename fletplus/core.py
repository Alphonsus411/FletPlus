import flet as ft
from fletplus.themes.theme_manager import ThemeManager
from fletplus.components.sidebar_admin import SidebarAdmin
from fletplus.desktop.window_manager import WindowManager
from fletplus.utils.shortcut_manager import ShortcutManager
from fletplus.components.command_palette import CommandPalette
from fletplus.utils.device import is_mobile, is_web

class FletPlusApp:
    def __init__(
        self,
        page: ft.Page,
        routes: dict,
        sidebar_items=None,
        commands: dict | None = None,
        title="FletPlus App",
        theme_config=None,
        use_window_manager: bool = False,
    ):
        """
        :param page: Página Flet actual
        :param routes: Diccionario de rutas {str: Callable}
        :param sidebar_items: Lista de ítems del sidebar [{title, icon}]
        :param title: Título de la app
        :param theme_config: Diccionario de configuración inicial del tema
        :param commands: Diccionario {str: Callable} para la paleta de comandos
        """
        self.page = page
        self.routes = routes
        self.sidebar_items = sidebar_items or []

        # Detectar plataforma para usos posteriores
        self.platform = (
            "mobile" if is_mobile(page) else "web" if is_web(page) else "desktop"
        )

        config = (theme_config or {}).copy()
        tokens = config.get("tokens", {}).copy()
        platform_tokens = config.get(f"{self.platform}_tokens", {})
        tokens.update(platform_tokens)
        config["tokens"] = tokens
        for key in ("mobile_tokens", "web_tokens", "desktop_tokens"):
            config.pop(key, None)

        self.theme = ThemeManager(page, **config)
        self.title = title
        self.window_manager = WindowManager(page) if use_window_manager else None

        self.command_palette = CommandPalette(commands or {})
        self.shortcuts = ShortcutManager(page)
        self.shortcuts.register("k", lambda: self.command_palette.open(self.page), ctrl=True)

        self.content_container = ft.Container(expand=True, bgcolor=ft.colors.BACKGROUND)
        self.sidebar = SidebarAdmin(self.sidebar_items, on_select=self._on_nav)

    def build(self):
        self.page.title = self.title
        self.page.horizontal_alignment = ft.CrossAxisAlignment.START
        self.page.scroll = "auto"

        self.theme.apply_theme()

        # Mostrar primer contenido
        self._load_route(0)

        self.page.add(
            ft.Row([
                self.sidebar.build(),
                self.content_container
            ])
        )

    def _on_nav(self, index):
        self._load_route(index)

    def _load_route(self, index):
        route_key = list(self.routes.keys())[index]
        builder = self.routes[route_key]
        self.content_container.content = builder()
        self.page.update()

    def open_window(self, name: str, page: ft.Page) -> None:
        if self.window_manager:
            self.window_manager.open_window(name, page)

    def close_window(self, name: str) -> None:
        if self.window_manager:
            self.window_manager.close_window(name)

    def focus_window(self, name: str) -> None:
        if self.window_manager:
            self.window_manager.focus_window(name)

    @classmethod
    def start(
        cls,
        routes,
        sidebar_items=None,
        commands: dict | None = None,
        title="FletPlus App",
        theme_config=None,
        use_window_manager: bool = False,
    ):
        def main(page: ft.Page):
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
