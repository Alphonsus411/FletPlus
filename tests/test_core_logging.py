import logging
import flet as ft
from fletplus.core import FletPlusApp
from tests.test_fletplus_app import DummyPage


def test_load_route_invalid_index_logs_error(caplog):
    def home_view():
        return ft.Text("Inicio")

    page = DummyPage()
    app = FletPlusApp(page, {"home": home_view})

    with caplog.at_level(logging.ERROR):
        app._load_route(99)

    assert "Invalid route index: 99" in caplog.text
