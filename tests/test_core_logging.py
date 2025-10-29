import importlib
import logging
from pathlib import Path
import sys


def _ensure_tests_importable() -> None:
    """Garantiza que ``tests`` sea importable aunque se ejecute el archivo directamente."""

    project_root = Path(__file__).resolve().parent.parent
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)


_ensure_tests_importable()
DummyPage = importlib.import_module("tests.test_fletplus_app").DummyPage

import flet as ft

from fletplus.core import FletPlusApp


def test_load_route_invalid_index_logs_error(caplog):
    def home_view():
        return ft.Text("Inicio")

    page = DummyPage()
    app = FletPlusApp(page, {"home": home_view})

    with caplog.at_level(logging.ERROR):
        app._load_route(99)

    assert "Invalid route index: 99" in caplog.text
