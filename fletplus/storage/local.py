"""Adaptador para el almacenamiento local del lado del cliente de Flet."""

from __future__ import annotations

from typing import Any

try:
    from flet.core.client_storage import ClientStorage  # type: ignore[attr-defined]
except Exception:
    try:
        from flet.client_storage import ClientStorage  # type: ignore[attr-defined]
    except Exception:
        from typing import Any as ClientStorage

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
        storage = getattr(page, "client_storage", None)
        if storage is None:
            raise ValueError(
                "No se encontró backend local compatible en la página. "
                "Se esperaba 'page.client_storage' "
                "con métodos: get, set, remove, clear, get_keys."
            )

        required_methods = ("get", "set", "remove", "clear", "get_keys")
        missing_methods = [
            method
            for method in required_methods
            if not callable(getattr(storage, method, None))
        ]
        if missing_methods:
            missing = ", ".join(missing_methods)
            raise TypeError(
                "El backend 'client_storage' no es compatible con LocalStorageProvider: "
                f"faltan métodos requeridos ({missing})."
            )

        return cls(
            storage,
            serializer=serializer,
            deserializer=deserializer,
        )
