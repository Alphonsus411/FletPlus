import importlib
import logging
from typing import Callable, Dict, List, Tuple

import flet as ft

from fletplus.context import locale_context, user_context

_rs_filter: Callable[[List[str], str], List[int]] | None = None

def filter_commands(names: List[str], query: str) -> List[int]:
    global _rs_filter
    if _rs_filter is None:
        try:
            spec = importlib.util.find_spec("fletplus.components.command_palette_rs")
        except Exception:
            spec = None
        if spec is not None:
            try:
                mod = importlib.import_module("fletplus.components.command_palette_rs")
                impl = getattr(mod, "filter_commands", None)
            except Exception:
                impl = None
            _rs_filter = impl
    if _rs_filter is not None:
        return _rs_filter(names, query)
    q = (query or "").strip().lower()
    if not q:
        return list(range(len(names)))
    result: List[int] = []
    for i, name in enumerate(names):
        if q in (name or "").lower():
            result.append(i)
    return result


class CommandPalette:
    """Paleta de comandos con búsqueda.

    Quien instancia esta clase debe llamar explícitamente a :meth:`dispose`
    al desmontar/cerrar la vista para liberar suscripciones de contexto.
    """

    def __init__(self, commands: Dict[str, Callable]):
        self.commands = commands
        self.filtered: List[Tuple[str, Callable]] = []
        self.search = ft.TextField(
            on_change=self._on_search,
            autofocus=True,
            hint_text="Search command...",
        )
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
        self._disposed = False
        self._setup_context_bindings()
        self.refresh()

    def _on_search(self, _):
        self.refresh()

    def refresh(self) -> None:
        """Reconstruye el listado de comandos visibles."""
        query = self.search.value or ""
        items = list(self.commands.items())
        names = [name for name, _ in items]
        indices = filter_commands(names, query)
        valid_indices: list[int] = []
        seen: set[int] = set()

        for index in indices:
            if not isinstance(index, int):
                logging.warning("filter_commands devolvió un índice no entero: %r", index)
                continue
            if index < 0 or index >= len(items):
                logging.warning(
                    "filter_commands devolvió un índice fuera de rango: %s (total: %s)",
                    index,
                    len(items),
                )
                continue
            if index in seen:
                logging.debug("Índice duplicado ignorado en command palette: %s", index)
                continue

            valid_indices.append(index)
            seen.add(index)

        self.filtered = [items[index] for index in valid_indices]
        self._refresh()

    def _refresh(self):
        self.list_view.controls = [
            ft.ListTile(
                title=ft.Text(name),
                on_click=lambda _, cb=cb: self._execute(cb),
            )
            for name, cb in self.filtered
        ]
        if self._is_attached_to_page(self.list_view):
            self.list_view.update()

    def _execute(self, cb: Callable):
        try:
            cb()
        except Exception:
            logging.exception("Error al ejecutar el comando")
        finally:
            self.dialog.open = False
            if self._is_attached_to_page(self.dialog):
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
        if self._is_attached_to_page(self.search):
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
        if self._is_attached_to_page(self.dialog):
            self.dialog.update()

    # ------------------------------------------------------------------
    @staticmethod
    def _is_attached_to_page(control: ft.Control) -> bool:
        try:
            return bool(control.page)
        except RuntimeError:
            return False

    # ------------------------------------------------------------------
    def dispose(self) -> None:
        """Libera las suscripciones asociadas a esta instancia."""
        if self._disposed:
            return

        for unsubscribe in self._subscriptions:
            try:
                unsubscribe()
            except Exception:
                logging.exception("Error al cancelar la subscripción de CommandPalette")

        self._subscriptions.clear()
        self._disposed = True

    # ------------------------------------------------------------------
    def __enter__(self) -> "CommandPalette":
        return self

    # ------------------------------------------------------------------
    def __exit__(self, exc_type, exc, tb) -> None:
        self.dispose()

    # ------------------------------------------------------------------
    def __del__(self):  # pragma: no cover - liberación defensiva
        try:
            subscriptions = getattr(self, "_subscriptions", None)
            if subscriptions:
                for unsubscribe in list(subscriptions):
                    try:
                        unsubscribe()
                    except Exception:
                        continue
                subscriptions.clear()
            setattr(self, "_disposed", True)
        except Exception:
            pass
