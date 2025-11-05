import logging
from typing import Callable, Dict, List, Tuple

import flet as ft

from fletplus.context import locale_context, user_context


class CommandPalette:
    """Paleta de comandos con búsqueda."""

    def __init__(self, commands: Dict[str, Callable]):
        self.commands = commands
        self.filtered: List[Tuple[str, Callable]] = []

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
        self.dialog.title = ft.Text("")
        self._subscriptions: list[Callable[[], None]] = []
        self._setup_context_bindings()
        self.refresh()

    def _on_search(self, _):
        self.refresh()

    def refresh(self) -> None:
        """Reconstruye el listado de comandos visibles."""
        query = (self.search.value or "").lower()
        if query:
            self.filtered = [
                (name, cb)
                for name, cb in self.commands.items()
                if query in name.lower()
            ]
        else:
            self.filtered = list(self.commands.items())
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
        try:
            cb()
        except Exception:
            logging.exception("Error al ejecutar el comando")
        finally:
            self.dialog.open = False
            if self.dialog.page:
                self.dialog.update()

    def open(self, page: ft.Page):
        self.refresh()
        page.dialog = self.dialog
        self.dialog.open = True
        page.update()

    # ------------------------------------------------------------------
    def _setup_context_bindings(self) -> None:
        try:
            unsubscribe_locale = locale_context.subscribe(self._on_locale_change, immediate=True)
            self._subscriptions.append(unsubscribe_locale)
        except LookupError:
            self._on_locale_change(locale_context.get(default="es"))

        try:
            unsubscribe_user = user_context.subscribe(self._on_user_change, immediate=True)
            self._subscriptions.append(unsubscribe_user)
        except LookupError:
            self._on_user_change(user_context.get(default=None))

    # ------------------------------------------------------------------
    def _on_locale_change(self, locale: str | None) -> None:
        hints = {
            "es": "Buscar comando...",
            "en": "Search command...",
            "pt": "Buscar comando...",
        }
        key = (locale or "es").lower()[:2]
        self.search.hint_text = hints.get(key, hints["es"])
        if self.search.page:
            self.search.update()

    # ------------------------------------------------------------------
    def _on_user_change(self, user: object | None) -> None:
        if user:
            title = f"Comandos para {user}"
        else:
            title = "Paleta de comandos"
        if isinstance(self.dialog.title, ft.Text):
            self.dialog.title.value = title
        else:
            self.dialog.title = ft.Text(title)
        if self.dialog.page:
            self.dialog.update()

    # ------------------------------------------------------------------
    def __del__(self):  # pragma: no cover - liberación defensiva
        for unsubscribe in self._subscriptions:
            try:
                unsubscribe()
            except Exception:
                logging.exception("Error al cancelar la subscripción de CommandPalette")
