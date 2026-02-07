from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from .layout import Layout, LayoutBuilder, LayoutComposition
from .state import State, StateProtocol


LifecycleHook = Callable[[ft.Page, StateProtocol], None]
UpdateHook = Callable[[StateProtocol], None]


class FletPlusApp:
    """Aplicación FletPlus con ciclo de vida explícito y hooks configurables.

    Permite construir una interfaz a partir de un layout y mantenerla
    sincronizada con el estado, disparando callbacks de inicio, actualización y
    cierre cuando corresponde.
    """

    def __init__(
        self,
        layout: LayoutComposition | LayoutBuilder,
        state: StateProtocol | None = None,
        on_start: LifecycleHook | None = None,
        on_update: UpdateHook | None = None,
        on_shutdown: LifecycleHook | None = None,
        *,
        title: str | None = None,
    ) -> None:
        """Inicializa la aplicación con layout, estado y callbacks de ciclo de vida."""
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
        """Página Flet actual, útil para inspección o pruebas."""
        return self._page

    def run(self, **kwargs: Any) -> None:
        """Ejecuta la aplicación y delega el control al runtime de Flet."""
        ft.app(target=self._on_page_ready, **kwargs)

    def _on_page_ready(self, page: ft.Page) -> None:
        """Configura la página cuando Flet la crea y arranca el ciclo de vida."""
        page.on_close = lambda _: self.shutdown()
        if hasattr(page, "on_disconnect"):
            page.on_disconnect = lambda _: self.shutdown()
        self.start(page)

    def start(self, page: ft.Page) -> None:
        """Inicializa el ciclo de vida, construye el layout y registra observadores.

        Nota: el refresco de UI se envuelve para ejecutarse en el loop de la página
        (priorizando ``page.run_task`` cuando existe) y hacer fallback a
        ``page.update()`` directo si el mecanismo seguro no está disponible.
        """
        self._page = page
        if self.title is not None:
            page.title = self.title

        self.state.bind_refresher(lambda: self._safe_page_update(page))
        self._unsubscribe = self.state.subscribe(self._handle_state_update)
        self.on_start(page, self.state)
        self.rebuild_layout(self.state, initial=True)
        self.state.refresh_ui()

    def rebuild_layout(self, state: StateProtocol, *, initial: bool = False) -> None:
        """Reconstruye el layout en función del estado actual."""
        if self._page is None:
            return
        if initial:
            self._controls = self.layout.build(state)
        else:
            updated_controls = self.layout.update(state, self._controls)
            if updated_controls is None:
                state.refresh_ui()
                return
            self._controls = updated_controls
        self._page.controls.clear()
        self._page.add(*self._controls)

    def _handle_state_update(self, state: StateProtocol) -> None:
        """Responde a cambios de estado actualizando el layout."""
        self.on_update(state)
        self.rebuild_layout(state)

    def on_start(self, page: ft.Page, state: StateProtocol) -> None:
        """Dispara el hook de inicio si fue provisto."""
        if self._on_start:
            self._on_start(page, state)

    def on_update(self, state: StateProtocol) -> None:
        """Dispara el hook de actualización si fue provisto."""
        if self._on_update:
            self._on_update(state)

    def on_shutdown(self, page: ft.Page, state: StateProtocol) -> None:
        """Dispara el hook de cierre si fue provisto."""
        if self._on_shutdown:
            self._on_shutdown(page, state)

    def shutdown(self) -> None:
        """Finaliza el ciclo de vida, liberando recursos y observadores.

        Tras ejecutar ``on_shutdown``, se limpian los controles de la página y se
        fuerza un refresco seguro para dejar la UI en un estado consistente.
        """
        if self._page is None:
            return
        page = self._page
        self.on_shutdown(page, self.state)
        page.controls.clear()
        self._safe_page_update(page)
        if self._unsubscribe:
            self._unsubscribe()
        self.state.bind_refresher(None)
        self._page = None

    @staticmethod
    def _safe_page_update(page: ft.Page) -> None:
        if hasattr(page, "run_task"):
            try:
                page.run_task(page.update)
                return
            except Exception:
                page.update()
        else:
            page.update()
