from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)

Subscriber = Callable[["StateProtocol"], None]
Refresher = Callable[[], None]


class StateProtocol(Protocol):
    """Contrato mínimo para estados observables e inyectables."""

    def get(self, key: str, default: Any = None) -> Any:
        ...

    def set(self, key: str, value: Any, *, notify: bool = True) -> None:
        """Asigna un valor y notifica si corresponde."""
        ...

    def update(
        self,
        values: Mapping[str, Any] | Iterable[tuple[str, Any]],
        *,
        notify: bool = True,
    ) -> None:
        """Actualiza varias claves y notifica si corresponde."""
        ...

    def replace(self, values: Mapping[str, Any], *, notify: bool = True) -> None:
        """Reemplaza todo el estado y notifica si corresponde."""
        ...

    def clear(self, *, notify: bool = True) -> None:
        """Limpia el estado y notifica si corresponde."""
        ...

    def snapshot(self) -> dict[str, Any]:
        ...

    def subscribe(self, callback: Subscriber) -> Callable[[], None]:
        ...

    def unsubscribe(self, callback: Subscriber) -> None:
        ...

    def notify(self) -> None:
        ...

    def bind_refresher(self, refresher: Refresher | None) -> None:
        ...

    def refresh_ui(self) -> None:
        ...


@dataclass
class AppState(StateProtocol):
    """Contenedor de estado observable e inyectable.

    Contrato de actualización y notificación:
    - Las mutaciones (set, update, replace, clear) modifican el almacenamiento
      interno por instancia y, si ``notify=True``, disparan ``notify()``.
    - ``notify()`` ejecuta los callbacks suscritos pasando la instancia actual
      de estado (sin depender de estado global).
    - ``subscribe()`` registra listeners y devuelve una función de cancelación
      equivalente a ``unsubscribe()``.
    """

    _data: dict[str, Any] = field(default_factory=dict)
    _subscribers: list[Subscriber] = field(default_factory=list, init=False)
    _refresher: Refresher | None = field(default=None, init=False)

    def __init__(self, initial: Mapping[str, Any] | None = None) -> None:
        self._data = dict(initial or {})
        self._subscribers = []
        self._refresher = None

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any, *, notify: bool = True) -> None:
        self._data[key] = value
        if notify:
            self.notify()

    def update(
        self,
        values: Mapping[str, Any] | Iterable[tuple[str, Any]],
        *,
        notify: bool = True,
    ) -> None:
        self._data.update(dict(values))
        if notify:
            self.notify()

    def replace(self, values: Mapping[str, Any], *, notify: bool = True) -> None:
        self._data = dict(values)
        if notify:
            self.notify()

    def clear(self, *, notify: bool = True) -> None:
        self._data.clear()
        if notify:
            self.notify()

    def snapshot(self) -> dict[str, Any]:
        return dict(self._data)

    def bind_refresher(self, refresher: Refresher | None) -> None:
        self._refresher = refresher

    def subscribe(self, callback: Subscriber) -> Callable[[], None]:
        self._subscribers.append(callback)

        def _unsubscribe() -> None:
            self.unsubscribe(callback)

        return _unsubscribe

    def unsubscribe(self, callback: Subscriber) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def notify(self) -> None:
        for callback in list(self._subscribers):
            try:
                callback(self)
            except Exception:
                logger.exception("Error al notificar a un suscriptor del estado")
        self.refresh_ui()

    def refresh_ui(self) -> None:
        if not self._refresher:
            return
        try:
            self._refresher()
        except Exception:
            logger.exception("Error al refrescar la UI")


State = AppState
