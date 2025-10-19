import logging
from pathlib import Path
import sys

if __package__:
    from .test_fletplus_app import DummyPage
else:  # pragma: no cover - solo ejecutado cuando se lanza como script
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from tests.test_fletplus_app import DummyPage

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
