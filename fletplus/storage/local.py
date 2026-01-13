"""Adaptador para el almacenamiento local del lado del cliente de Flet."""

from __future__ import annotations

from typing import Any

from flet.core.client_storage import ClientStorage

from . import Deserializer, Serializer, StorageProvider

__all__ = ["LocalStorageProvider"]


class LocalStorageProvider(StorageProvider[Any]):
    """Proporciona una interfaz reactiva sobre :class:`ClientStorage`."""

    def __init__(
        self,
        storage: ClientStorage,
        *,
        serializer: Serializer | None = None,
        deserializer: Deserializer | None = None,
    ) -> None:
        self._storage = storage
        super().__init__(serializer=serializer, deserializer=deserializer)

    # ------------------------------------------------------------------
    def _iter_keys(self) -> list[str]:
        return list(self._storage.get_keys(""))

    # ------------------------------------------------------------------
    def _read_raw(self, key: str) -> Any:
        if key not in self._storage.get_keys(""):
            raise KeyError(key)
        return self._storage.get(key)

    # ------------------------------------------------------------------
    def _write_raw(self, key: str, value: Any) -> None:
        self._storage.set(key, value)

    # ------------------------------------------------------------------
    def _remove_raw(self, key: str) -> None:
        if key not in self._storage.get_keys(""):
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
    ) -> "LocalStorageProvider":
        """Crea el proveedor tomando la instancia de :class:`Page` completa."""

        return cls(
            page.client_storage,
            serializer=serializer,
            deserializer=deserializer,
        )
