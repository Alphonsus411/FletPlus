"""Almacenamiento basado en archivos JSON con sincronización reactiva."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping

if os.name == "nt":
    import msvcrt
else:
    import fcntl

from . import Deserializer, Serializer, StorageProvider

__all__ = ["FileStorageProvider"]


logger = logging.getLogger(__name__)


class FileStorageProvider(StorageProvider[Any]):
    """Persiste datos en un archivo JSON y emite señales al cambiar.

    Contrato de concurrencia:
    - Las escrituras de múltiples instancias/procesos que apunten al mismo
      archivo se serializan mediante un lock de archivo dedicado.
    - Durante la sección crítica se hace read-modify-write con lectura fresca
      del JSON antes de persistir para fusionar cambios externos con la caché
      local y evitar perder claves ajenas.
    - La persistencia final sigue siendo atómica (temporal + ``os.replace``)
      dentro del lock.
    - En lectura, cada instancia hace una comprobación ligera de mtime
      (``stat().st_mtime_ns``) y recarga la caché sólo si detecta cambios en
      disco. Así, múltiples instancias sobre el mismo archivo observan
      actualizaciones externas sin necesidad de escribir para sincronizarse.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        serializer: Serializer | None = None,
        deserializer: Deserializer | None = None,
        encoding: str = "utf-8",
    ) -> None:
        self._path = Path(path)
        self._lock_path = self._path.with_suffix(f"{self._path.suffix}.lock")
        self._encoding = encoding
        self._cache: Dict[str, Any] = {}
        self._last_mtime_ns: int | None = None
        self._dirty_keys: set[str] = set()
        self._deleted_keys: set[str] = set()
        self._clear_requested = False
        self._load_cache()
        super().__init__(
            serializer=serializer or json.dumps,
            deserializer=deserializer or json.loads,
        )

    # ------------------------------------------------------------------
    def _load_cache(self) -> None:
        self._cache = self._read_disk_data()
        self._last_mtime_ns = self._get_mtime_ns()

    # ------------------------------------------------------------------
    def _get_mtime_ns(self) -> int | None:
        try:
            return self._path.stat().st_mtime_ns
        except FileNotFoundError:
            return None
        except OSError:
            return None

    # ------------------------------------------------------------------
    def _refresh_cache_if_changed(self) -> bool:
        if self._clear_requested or self._dirty_keys or self._deleted_keys:
            return False
        current_mtime_ns = self._get_mtime_ns()
        if current_mtime_ns == self._last_mtime_ns:
            return False
        self._cache = self._read_disk_data()
        self._last_mtime_ns = current_mtime_ns
        return True

    # ------------------------------------------------------------------
    @contextmanager
    def _file_lock(self) -> Iterator[None]:
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._lock_path, "a+b") as lock_file:
            if os.name == "nt":
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if os.name == "nt":
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    # ------------------------------------------------------------------
    def _read_disk_data(self) -> Dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            text = self._path.read_text(encoding=self._encoding)
            data = json.loads(text)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    # ------------------------------------------------------------------
    def _persist(self) -> None:
        with self._file_lock():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            disk_data = self._read_disk_data()
            if self._clear_requested:
                merged_data = dict(self._cache)
            else:
                merged_data = dict(disk_data)
                for key in self._dirty_keys:
                    if key in self._cache:
                        merged_data[key] = self._cache[key]
                for key in self._deleted_keys:
                    merged_data.pop(key, None)
            self._cache = merged_data

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
                        merged_data,
                        fp,
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    )
                    fp.flush()
                    os.fsync(fp.fileno())
                if tmp_path is None:
                    return
                try:
                    os.chmod(tmp_path, 0o600)
                except OSError:
                    logger.warning(
                        "No se pudo ajustar permisos del temporal: %s",
                        tmp_path,
                        exc_info=True,
                    )
                os.replace(tmp_path, self._path)
                try:
                    os.chmod(self._path, 0o600)
                except OSError:
                    logger.warning(
                        "No se pudo ajustar permisos del archivo persistido: %s",
                        self._path,
                        exc_info=True,
                    )
                self._last_mtime_ns = self._get_mtime_ns()
                self._dirty_keys.clear()
                self._deleted_keys.clear()
                self._clear_requested = False
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
        self._refresh_cache_if_changed()
        return list(self._cache.keys())

    # ------------------------------------------------------------------
    def _read_raw(self, key: str) -> Any:
        self._refresh_cache_if_changed()
        if key in self._cache:
            return self._cache[key]
        raise KeyError(key)

    # ------------------------------------------------------------------
    def snapshot(self) -> Mapping[str, Any]:
        if self._refresh_cache_if_changed():
            self._refresh_snapshot()
        return super().snapshot()

    # ------------------------------------------------------------------
    def _write_raw(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._dirty_keys.add(key)
        self._deleted_keys.discard(key)
        self._persist()

    # ------------------------------------------------------------------
    def _remove_raw(self, key: str) -> None:
        if key not in self._cache:
            raise KeyError(key)
        self._cache.pop(key)
        self._deleted_keys.add(key)
        self._dirty_keys.discard(key)
        self._persist()

    # ------------------------------------------------------------------
    def _clear_raw(self) -> None:
        self._cache.clear()
        self._dirty_keys.clear()
        self._deleted_keys.clear()
        self._clear_requested = True
        self._persist()
