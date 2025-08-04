import flet as ft
from typing import Callable, Dict, List, Tuple


class CommandPalette:
    """Paleta de comandos con búsqueda."""

    def __init__(self, commands: Dict[str, Callable]):
        self.commands = commands
        self.filtered: List[Tuple[str, Callable]] = list(commands.items())

        self.search = ft.TextField(on_change=self._on_search, autofocus=True)
        self.list_view = ft.ListView(expand=True, spacing=0)
        self.dialog = ft.AlertDialog(
            modal=False,
            content=ft.Column(
                [self.search, self.list_view],
                width=400,
                height=400,
            ),
        )
        self._refresh()

    def _on_search(self, _):
        query = (self.search.value or "").lower()
        self.filtered = [
            (name, cb)
            for name, cb in self.commands.items()
            if query in name.lower()
        ]
        self._refresh()

    def _refresh(self):
        self.list_view.controls = [
            ft.ListTile(
                title=ft.Text(name),
                on_click=lambda _, cb=cb: self._execute(cb),
            )
            for name, cb in self.filtered
        ]
        if self.list_view.page:
            self.list_view.update()

    def _execute(self, cb: Callable):
        self.dialog.open = False
        if self.dialog.page:
            self.dialog.update()
        cb()

    def open(self, page: ft.Page):
        self._refresh()
        page.dialog = self.dialog
        self.dialog.open = True
        page.update()
