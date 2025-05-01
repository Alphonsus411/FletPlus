import flet as ft
from fletplus.themes.theme_manager import ThemeManager
from fletplus.components.sidebar_admin import SidebarAdmin

class FletPlusApp:
    def __init__(self, page: ft.Page, routes: dict, sidebar_items=None, title="FletPlus App", theme_config=None):
        """
        :param page: Página Flet actual
        :param routes: Diccionario de rutas {str: Callable}
        :param sidebar_items: Lista de ítems del sidebar [{title, icon}]
        :param title: Título de la app
        :param theme_config: Diccionario de configuración inicial del tema
        """
        self.page = page
        self.routes = routes
        self.sidebar_items = sidebar_items or []
        self.theme = ThemeManager(page, **(theme_config or {}))
        self.title = title

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

    @classmethod
    def start(cls, routes, sidebar_items=None, title="FletPlus App", theme_config=None):
        def main(page: ft.Page):
            app = cls(page, routes, sidebar_items, title, theme_config)
            app.build()
        ft.app(target=main)
