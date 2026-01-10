"""Almacenamiento basado en archivos JSON con sincronización reactiva."""

from __future__ import annotations

import json
import os
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
        tmp_path = self._path.with_name(f"{self._path.name}.tmp")
        tmp_name: str | None = None
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            try:
                fd = os.open(tmp_path, flags, 0o600)
            except FileExistsError:
                tmp_path.unlink(missing_ok=True)
                fd = os.open(tmp_path, flags, 0o600)
            with os.fdopen(fd, "w", encoding=self._encoding) as fp:
                json.dump(
                    self._cache,
                    fp,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                fp.flush()
                os.fsync(fp.fileno())
                tmp_name = str(tmp_path)
            os.replace(tmp_name, self._path)
            os.chmod(self._path, 0o600)
        finally:
            if tmp_name:
                try:
                    Path(tmp_name).unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    pass

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
