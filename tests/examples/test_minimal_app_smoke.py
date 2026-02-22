import flet as ft
from fletplus.core_legacy import FletPlusApp


class DummyPage:
    def __init__(self, platform: str = "web", storage=None):
        self.platform = platform
        self.title = ""
        self.controls = []
        self.theme = None
        self.theme_mode = None
        self.scroll = None
        self.horizontal_alignment = None
        self.vertical_alignment = None
        self.padding = 0
        self.spacing = 0
        self.client_storage = storage
        self.updated = False
        self.update_calls = 0
        self.dialog = None

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.updated = True
        self.update_calls += 1


def test_minimal_app_smoke():
    page = DummyPage()
    app = FletPlusApp(page, {"Inicio": lambda: ft.Text("Inicio")}, title="Demo")
    app.build()
    assert isinstance(app.content_container.content, ft.Control) or app.content_container.content is None
    assert app.router.current_path in {"/", "/inicio", None}
    app.dispose()
