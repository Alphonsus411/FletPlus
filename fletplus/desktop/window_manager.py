import flet as ft
from typing import Dict


class WindowManager:
    """Gestiona la creación, cierre y foco de ventanas adicionales."""

    def __init__(self, main_page: ft.Page):
        self.main_page = main_page
        self.windows: Dict[str, ft.Page] = {"main": main_page}
        self.current = "main"

    def open_window(self, name: str, page: ft.Page) -> None:
        """Registra una nueva ventana y la pone en foco."""
        self.windows[name] = page
        self.current = name

    def close_window(self, name: str) -> None:
        """Cierra una ventana y devuelve el foco a la principal si es necesario."""
        if name == "main":
            return
        self.windows.pop(name, None)
        if self.current == name:
            self.current = "main"

    def focus_window(self, name: str) -> None:
        """Cambia el foco a la ventana indicada."""
        if name in self.windows:
            self.current = name
            page = self.windows[name]
            if hasattr(page, "window_to_front"):
                page.window_to_front()

    def get_current_page(self) -> ft.Page:
        return self.windows[self.current]
