import importlib
import pytest


class DummyPage:
    """Página mínima para simular ft.Page en las demos."""

    def __init__(self):
        self.controls = []
        self.title = ""
        self.width = 800
        self.height = 600
        self.theme = None
        self.theme_mode = None
        self.on_resize = None

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        pass


# Listado de (módulo, función) de las demos a probar
DEMO_SCRIPTS = [
    ("examples.buttons_examples", "main"),
    ("examples.responsive_container_example", "main"),
    ("examples.layouts_examples", "typography_demo"),
]


@pytest.mark.parametrize("module_name, func_name", DEMO_SCRIPTS)
def test_responsive_demos(module_name: str, func_name: str):
    module = importlib.import_module(module_name)
    demo = getattr(module, func_name)

    page = DummyPage()
    demo(page)

    assert page.controls, "Se esperaban controles en la página tras ejecutar la demo"
