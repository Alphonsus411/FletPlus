import flet as ft

from fletplus.animation import AnimationController
from fletplus.context import locale_context, theme_context, user_context
from fletplus.core_legacy import FletPlusApp
from fletplus.router import Route
from fletplus.state import Store


class DummyPage:
    def __init__(self, platform: str = "web", storage=None):
        self.platform = platform
        self.title = ""
        self.controls = []
        self.theme = None
        self.theme_mode = None
        self.scroll = None
        self.horizontal_alignment = None
        self.updated = False
        self.client_storage = storage

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.updated = True


class DummyStorage:
    def __init__(self):
        self._data: dict[str, object] = {}

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value):
        self._data[key] = value


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


def test_fletplus_app_context_lifecycle_multiple_instances():
    def home_view():
        return ft.Text("Inicio")

    routes = {"Inicio": home_view}

    page = DummyPage()
    page.user = "Admin"
    page.locale = "en-US"

    app_first = FletPlusApp(page, routes, title="Primera")
    app_first.build()
    app_first.dispose()

    page.user = "Maria"
    page.locale = "es-MX"
    app_second = FletPlusApp(page, routes, title="Segunda")
    app_second.build()

    assert page.contexts["theme"] is theme_context
    assert theme_context.get() is app_second.theme
    assert user_context.get() == "Maria"
    assert locale_context.get() == "es-MX"

    app_second.dispose()


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


def test_fletplus_app_route_view_triggers_unmount(monkeypatch):
    def route_view(match):
        return ft.Text(match.path)

    page = DummyPage()
    app = FletPlusApp(page, [Route(path="/home", view=route_view, name="Home")])
    triggers: list[str] = []

    def record_trigger(self, event):
        triggers.append(event)

    monkeypatch.setattr(AnimationController, "trigger", record_trigger)
    app.build()

    assert "unmount" in triggers
    assert isinstance(app.content_container.content, ft.Text)
    assert app.content_container.content.value == "/home"

    app.dispose()


def test_theme_preferences_persist_between_sessions():
    def home_view():
        return ft.Text("Inicio")

    routes = {"Inicio": home_view}
    storage = DummyStorage()

    page_first = DummyPage(storage=storage)
    app_first = FletPlusApp(page_first, routes)
    app_first.theme.set_token("colors.primary", "#102030")
    app_first.theme.set_dark_mode(True)

    saved = storage.get("fletplus.preferences")
    assert isinstance(saved, dict)
    theme_prefs = saved.get("theme")
    assert isinstance(theme_prefs, dict)
    assert theme_prefs["dark_mode"] is True
    assert theme_prefs["overrides"]["colors"]["primary"] == "#102030"

    app_first.dispose()

    page_second = DummyPage(storage=storage)
    app_second = FletPlusApp(page_second, routes)
    app_second.build()

    assert app_second.theme.dark_mode is True
    assert app_second.theme.get_token("colors.primary") == "#102030"
    assert app_second._theme_button.icon == ft.Icons.LIGHT_MODE

    app_second.dispose()
