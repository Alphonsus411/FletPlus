"""Almacenamiento basado en archivos JSON con sincronización reactiva."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from . import Deserializer, Serializer, StorageProvider

__all__ = ["FileStorageProvider"]


class FileStorageProvider(StorageProvider[Any]):
    """Persiste datos en un archivo JSON y emite señales al cambiar."""

    def __init__(
        self,
        path: str | Path,
        *,
        serializer: Serializer | None = None,
        deserializer: Deserializer | None = None,
        encoding: str = "utf-8",
    ) -> None:
        self._path = Path(path)
        self._encoding = encoding
        self._cache: Dict[str, Any] = {}
        self._load_cache()
        super().__init__(
            serializer=serializer or json.dumps,
            deserializer=deserializer or json.loads,
        )

    # ------------------------------------------------------------------
    def _load_cache(self) -> None:
        if not self._path.exists():
            self._cache = {}
            return
        try:
            text = self._path.read_text(encoding=self._encoding)
        except OSError:
            self._cache = {}
            return
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            self._cache = {}
            return
        if isinstance(data, dict):
            self._cache = data
        else:
            self._cache = {}

    # ------------------------------------------------------------------
    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding=self._encoding) as fp:
            json.dump(self._cache, fp, ensure_ascii=False, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    def _iter_keys(self) -> list[str]:
        return list(self._cache.keys())

    # ------------------------------------------------------------------
    def _read_raw(self, key: str) -> Any | None:
        return self._cache.get(key)

    # ------------------------------------------------------------------
    def _write_raw(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._persist()

    # ------------------------------------------------------------------
    def _remove_raw(self, key: str) -> None:
        self._cache.pop(key, None)
        self._persist()

    # ------------------------------------------------------------------
    def _clear_raw(self) -> None:
        self._cache.clear()
        self._persist()

