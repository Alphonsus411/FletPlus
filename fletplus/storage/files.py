"""Almacenamiento basado en archivos JSON con sincronización reactiva."""

from __future__ import annotations

import json
import os
import tempfile
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
        except (OSError, UnicodeDecodeError):
            # Si hay problemas de lectura o decodificación, reinicia la caché.
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
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                delete=False,
                dir=self._path.parent,
                prefix=self._path.name,
                suffix=".tmp",
                encoding=self._encoding,
            ) as fp:
                tmp_path = Path(fp.name)
                json.dump(
                    self._cache,
                    fp,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                fp.flush()
                os.fsync(fp.fileno())
            if tmp_path is None:
                return
            os.chmod(tmp_path, 0o600)
            os.replace(tmp_path, self._path)
            os.chmod(self._path, 0o600)
        finally:
            if tmp_path is not None:
                try:
                    tmp_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    pass

    # ------------------------------------------------------------------
    def _iter_keys(self) -> list[str]:
        return list(self._cache.keys())

    # ------------------------------------------------------------------
    def _read_raw(self, key: str) -> Any:
        if key in self._cache:
            return self._cache[key]
        raise KeyError(key)

    # ------------------------------------------------------------------
    def _write_raw(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._persist()

    # ------------------------------------------------------------------
    def _remove_raw(self, key: str) -> None:
        if key not in self._cache:
            raise KeyError(key)
        self._cache.pop(key)
        self._persist()

    # ------------------------------------------------------------------
    def _clear_raw(self) -> None:
        self._cache.clear()
        self._persist()
