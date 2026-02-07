from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
import logging
from typing import Any

logger = logging.getLogger(__name__)

Subscriber = Callable[["State"], None]
Refresher = Callable[[], None]


@dataclass
class State:
    """Contenedor de estado observable y actualizable."""

    _data: dict[str, Any] = field(default_factory=dict)
    _subscribers: list[Subscriber] = field(default_factory=list, init=False)
    _refresher: Refresher | None = field(default=None, init=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any, *, notify: bool = True) -> None:
        self._data[key] = value
        if notify:
            self.notify()

    def update(self, values: dict[str, Any] | Iterable[tuple[str, Any]], *, notify: bool = True) -> None:
        self._data.update(values)
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
