import flet as ft
from unittest.mock import MagicMock

from fletplus.desktop.window_manager import WindowManager


def test_open_window_creates_and_focuses():
    main_page = MagicMock(spec=ft.Page)
    wm = WindowManager(main_page)

    new_page = MagicMock(spec=ft.Page)
    wm.open_window("secundaria", new_page)

    assert "secundaria" in wm.windows
    assert wm.get_current_page() is new_page


def test_focus_changes_between_windows():
    main_page = MagicMock(spec=ft.Page)
    wm = WindowManager(main_page)

    page1 = MagicMock(spec=ft.Page)
    page2 = MagicMock(spec=ft.Page)
    wm.open_window("p1", page1)
    wm.open_window("p2", page2)

    wm.focus_window("p1")
    assert wm.get_current_page() is page1

    wm.focus_window("main")
    assert wm.get_current_page() is main_page
