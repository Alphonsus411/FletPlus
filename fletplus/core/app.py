from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from .layout import Layout, LayoutComposition
from .state import State, StateProtocol


LifecycleHook = Callable[[ft.Page, StateProtocol], None]
UpdateHook = Callable[[StateProtocol], None]


class FletPlusApp:
    """Aplicación FletPlus con ciclo de vida explícito."""

    def __init__(
        self,
        layout: LayoutComposition | Callable[[StateProtocol], ft.Control | list[ft.Control]],
        *,
        state: StateProtocol | None = None,
        title: str | None = None,
        on_start: LifecycleHook | None = None,
        on_update: UpdateHook | None = None,
        on_shutdown: LifecycleHook | None = None,
    ) -> None:
        self.layout = layout if isinstance(layout, LayoutComposition) else Layout.from_callable(layout)
        self.state = state or State()
        self.title = title
        self._on_start = on_start
        self._on_update = on_update
        self._on_shutdown = on_shutdown
        self._page: ft.Page | None = None
        self._controls: list[ft.Control] = []
        self._unsubscribe: Callable[[], None] | None = None

    @property
    def page(self) -> ft.Page | None:
        return self._page

    def run(self, **kwargs: Any) -> None:
        ft.app(target=self._main, **kwargs)

    def _main(self, page: ft.Page) -> None:
        self.start(page)

    def start(self, page: ft.Page) -> None:
        """Inicializa el ciclo de vida y registra los observadores."""
        self._page = page
        if self.title is not None:
            page.title = self.title
        self.state.bind_refresher(page.update)
        self._unsubscribe = self.state.subscribe(self._handle_state_update)
        if hasattr(page, "on_disconnect"):
            page.on_disconnect = lambda _: self.shutdown()
        self.rebuild_layout(self.state, initial=True)
        self.state.refresh_ui()
        self.on_start(page, self.state)

    def rebuild_layout(self, state: StateProtocol, *, initial: bool = False) -> None:
        """Reconstruye el layout en función del estado actual."""
        if self._page is None:
            return
        if initial:
            self._controls = self.layout.build(state)
        else:
            self._controls = self.layout.update(state, self._controls)
        self._page.controls.clear()
        self._page.add(*self._controls)

    def _handle_state_update(self, state: StateProtocol) -> None:
        self.on_update(state)
        self.rebuild_layout(state)
        state.refresh_ui()

    def on_start(self, page: ft.Page, state: StateProtocol) -> None:
        if self._on_start:
            self._on_start(page, state)

    def on_update(self, state: StateProtocol) -> None:
        if self._on_update:
            self._on_update(state)

    def on_shutdown(self, page: ft.Page, state: StateProtocol) -> None:
        if self._on_shutdown:
            self._on_shutdown(page, state)

    def shutdown(self) -> None:
        if self._page is None:
            return
        self.on_shutdown(self._page, self.state)
        if self._unsubscribe:
            self._unsubscribe()
        self.state.bind_refresher(None)
        self._page = None
