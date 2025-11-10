from typing import Callable, List, Optional


class SystemTray:
    """Encapsula un icono en la bandeja del sistema con menú y eventos."""

    def __init__(self, icon: str, menu: Optional[List[str]] = None) -> None:
        self.icon = icon
        self.menu = menu or []
        self.visible = False
        self._on_click: Optional[Callable[[], None]] = None

    def show(self) -> None:
        """Muestra el icono en la bandeja."""
        self.visible = True

    def hide(self) -> None:
        """Oculta el icono de la bandeja."""
        self.visible = False

    def on_click(self, handler: Callable[[], None]) -> None:
        """Registra un manejador para el evento de clic."""
        self._on_click = handler

    def _emit_click(self) -> None:
        """Dispara manualmente el evento de clic (útil en tests)."""
        if self._on_click:
            self._on_click()
