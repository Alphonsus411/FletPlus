"""Proveedor reactivo para el almacenamiento de sesión de Flet."""

from __future__ import annotations

from typing import Any

from flet.core.session_storage import SessionStorage

from . import Deserializer, Serializer, StorageProvider

__all__ = ["SessionStorageProvider"]


class SessionStorageProvider(StorageProvider[Any]):
    """Envuelve :class:`SessionStorage` con señales reactivas."""

    def __init__(
        self,
        storage: SessionStorage,
        *,
        serializer: Serializer | None = None,
        deserializer: Deserializer | None = None,
    ) -> None:
        self._storage = storage
        super().__init__(serializer=serializer, deserializer=deserializer)

    # ------------------------------------------------------------------
    def _iter_keys(self) -> list[str]:
        return list(self._storage.get_keys())

    # ------------------------------------------------------------------
    def _read_raw(self, key: str) -> Any:
        if key not in self._storage.get_keys():
            raise KeyError(key)
        return self._storage.get(key)

    # ------------------------------------------------------------------
    def _write_raw(self, key: str, value: Any) -> None:
        self._storage.set(key, value)

    # ------------------------------------------------------------------
    def _remove_raw(self, key: str) -> None:
        if key not in self._storage.get_keys():
            raise KeyError(key)
        self._storage.remove(key)

    # ------------------------------------------------------------------
    def _clear_raw(self) -> None:
        self._storage.clear()

    # ------------------------------------------------------------------
    @classmethod
    def from_page(
        cls,
        page,
        *,
        serializer: Serializer | None = None,
        deserializer: Deserializer | None = None,
    ) -> "SessionStorageProvider":
        """Inicializa el proveedor a partir de la página actual de Flet."""

        return cls(
            page.session,
            serializer=serializer,
            deserializer=deserializer,
        )
