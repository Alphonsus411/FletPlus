import flet as ft

from fletplus.context import locale_context, theme_context, user_context
from fletplus.core import FletPlusApp
from fletplus.state import Store


class DummyPage:
    def __init__(self, platform: str = "web"):
        self.platform = platform
        self.title = ""
        self.controls = []
        self.theme = None
        self.theme_mode = None
        self.scroll = None
        self.horizontal_alignment = None
        self.updated = False

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.updated = True

def test_fletplus_app_initialization_and_routing():
    # Definir dos pantallas de prueba
    def home_view():
        return ft.Text("Inicio")

    def users_view():
        return ft.Text("Usuarios")

    routes = {
        "Inicio": home_view,
        "Usuarios": users_view
    }

    sidebar_items = [
        {"title": "Inicio", "icon": ft.Icons.HOME},
        {"title": "Usuarios", "icon": ft.Icons.PEOPLE}
    ]

    # Crear instancia falsa de la página
    page = DummyPage()
    page.user = "Admin"
    page.locale = "en-US"

    # Crear la app sin iniciar Flet
    app = FletPlusApp(page, routes, sidebar_items, title="TestApp")

    # Simular construcción
    app.build()

    # Verificaciones básicas
    assert page.title == "TestApp"
    assert len(page.controls) == 1  # Un solo ft.Row
    assert app.content_container.content is not None
    assert isinstance(app.content_container.content, ft.Text)
    assert app.content_container.content.value == "Inicio"
    assert app.router.current_path == "/inicio"
    assert isinstance(app.state, Store)
    assert page.state is app.state
    assert page.contexts["theme"] is theme_context
    assert theme_context.get() is app.theme
    assert user_context.get() == "Admin"
    assert locale_context.get() == "en-US"
    assert app.command_palette.dialog.title.value == "Comandos para Admin"
    assert app.command_palette.search.hint_text == "Search command..."

    # Simular navegación a la segunda página
    app._on_nav(1)
    assert app.content_container.content.value == "Usuarios"
    assert app.router.current_path == "/usuarios"

    # Actualizar contexto de usuario e idioma
    app.set_user("Carlos")
    assert user_context.get() == "Carlos"
    app.set_locale("pt-BR")
    assert locale_context.get() == "pt-BR"
    assert app.command_palette.search.hint_text == "Buscar comando..."

    app.dispose()


def test_fletplus_app_without_routes():
    page = DummyPage()
    app = FletPlusApp(page, {})
    app.build()
    assert app.content_container.content is None
    app.dispose()


def test_fletplus_app_invalid_route_index():
    def home_view():
        return ft.Text("Inicio")

    routes = {"Inicio": home_view}

    page = DummyPage()
    app = FletPlusApp(page, routes)
    app.build()

    # Guardar contenido actual
    original_content = app.content_container.content

    # Índice fuera de rango positivo
    app._on_nav(5)
    assert app.content_container.content == original_content

    # Índice negativo
    app._on_nav(-1)
    assert app.content_container.content == original_content
    app.dispose()
