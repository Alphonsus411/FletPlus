"""Almacenamiento persistente de preferencias para FletPlus."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

if os.name == "nt":
    import msvcrt
else:
    import fcntl

logger = logging.getLogger(__name__)


class _BaseBackend:
    def load(self) -> dict[str, Any] | None:  # pragma: no cover - interfaz
        raise NotImplementedError

    def save(self, data: Mapping[str, Any]) -> None:  # pragma: no cover - interfaz
        raise NotImplementedError


class _ClientStorageBackend(_BaseBackend):
    def __init__(
        self,
        storage,
        key: str,
        *,
        json_default: Callable[[Any], Any] | None = None,
    ) -> None:
        self._storage = storage
        self._key = key
        self._json_default = json_default

    def load(self) -> dict[str, Any] | None:
        try:
            raw = self._storage.get(self._key)
        except Exception:  # pragma: no cover - errores de Flet
            logger.exception("No se pudieron leer preferencias desde client_storage")
            return None
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Preferencias corruptas en client_storage: %s", raw)
                return None
        if isinstance(raw, Mapping):
            return dict(raw)
        return None

    def save(self, data: Mapping[str, Any]) -> None:
        payload = dict(data)
        try:
            self._storage.set(self._key, payload)
            return
        except TypeError:
            pass
        except Exception:  # pragma: no cover - errores de Flet
            logger.exception("No se pudieron guardar preferencias en client_storage")
            return
        try:
            serialized = json.dumps(payload, default=self._json_default)
        except TypeError:
            logger.exception(
                "No se pudieron serializar preferencias para client_storage: %s (tipo=%s)",
                payload,
                type(payload),
            )
            return
        try:
            self._storage.set(self._key, serialized)
        except Exception:  # pragma: no cover - errores de Flet
            logger.exception("No se pudieron guardar preferencias en client_storage")


class _FileBackend(_BaseBackend):
    def __init__(self, key: str) -> None:
        self._key = key
        env_path = os.environ.get("FLETPLUS_PREFS_FILE")
        if env_path:
            self._path = Path(env_path)
            self._expected_base_dir: Path | None = None
        else:
            base_dir = Path.home() / ".fletplus"
            self._path = base_dir / "preferences.json"
            self._expected_base_dir = base_dir
        self._lock_path = self._path.with_suffix(f"{self._path.suffix}.lock")

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

    def _is_path_secure(self, path: Path, *, label: str) -> bool:
        if path.exists() and path.is_symlink():
            logger.error("Guardado de preferencias abortado: %s es symlink (%s)", label, path)
            return False
        return True

    def _is_default_path_inside_expected_base(self) -> bool:
        if self._expected_base_dir is None:
            return True
        try:
            expected_base = self._expected_base_dir.resolve()
            resolved_target = self._path.resolve(strict=False)
        except OSError:
            logger.exception(
                "Guardado de preferencias abortado: no se pudo resolver ruta segura %s",
                self._path,
            )
            return False
        if not resolved_target.is_relative_to(expected_base):
            logger.error(
                "Guardado de preferencias abortado: ruta fuera del directorio esperado (%s -> %s)",
                self._path,
                resolved_target,
            )
            return False
        return True

    def _validate_save_target(self) -> bool:
        if not self._is_path_secure(self._path.parent, label="directorio padre"):
            return False
        if not self._is_path_secure(self._path, label="archivo de preferencias"):
            return False
        return self._is_default_path_inside_expected_base()

    def _read_all(self) -> dict[str, Any]:
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.warning("JSON inválido en archivo de preferencias %s", self._path)
            return {}
        except Exception:  # pragma: no cover - errores inesperados
            logger.exception("No se pudieron leer preferencias desde %s", self._path)
            return {}
        if isinstance(data, dict):
            return data
        return {}

    def load(self) -> dict[str, Any] | None:
        data = self._read_all()
        entry = data.get(self._key)
        if isinstance(entry, dict):
            return dict(entry)
        return None

    def save(self, data: Mapping[str, Any]) -> None:
        try:
            with self._file_lock():
                self._path.parent.mkdir(parents=True, exist_ok=True)
                if not self._validate_save_target():
                    return
                payload = self._read_all()
                payload[self._key] = dict(data)

                tmp_path: Path | None = None
                try:
                    with tempfile.NamedTemporaryFile(
                        "w",
                        delete=False,
                        dir=self._path.parent,
                        prefix=f"{self._path.name}.",
                        suffix=".tmp",
                        encoding="utf-8",
                    ) as fh:
                        tmp_path = Path(fh.name)

                        if hasattr(os, "O_NOFOLLOW"):
                            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
                            check_fd = os.open(tmp_path, flags)
                            os.close(check_fd)

                        json.dump(payload, fh, ensure_ascii=False, indent=2)
                        fh.flush()
                        os.fsync(fh.fileno())
                    if tmp_path is None:
                        return
                    if not self._validate_save_target() or not self._is_path_secure(
                        tmp_path,
                        label="archivo temporal de preferencias",
                    ):
                        tmp_path.unlink(missing_ok=True)
                        return
                    os.replace(tmp_path, self._path)
                    os.chmod(self._path, 0o600)
                finally:
                    if tmp_path is not None and tmp_path.exists():
                        tmp_path.unlink(missing_ok=True)
        except Exception:  # pragma: no cover - errores inesperados
            logger.exception("No se pudieron guardar preferencias en %s", self._path)


class PreferenceStorage:
    """Abstracción ligera para leer/escribir preferencias persistentes."""

    DEFAULT_KEY = "fletplus.preferences"

    def __init__(
        self,
        page,
        *,
        key: str | None = None,
        json_default: Callable[[Any], Any] | None = None,
    ) -> None:
        self._key = key or self.DEFAULT_KEY
        storage = getattr(page, "client_storage", None)
        if storage is not None and hasattr(storage, "get") and hasattr(storage, "set"):
            self._backend = _ClientStorageBackend(
                storage,
                self._key,
                json_default=json_default,
            )
        else:
            self._backend = _FileBackend(self._key)

    def load(self) -> dict[str, Any]:
        prefs = self._backend.load()
        if isinstance(prefs, dict):
            return dict(prefs)
        return {}

    def save(self, data: Mapping[str, Any]) -> None:
        self._backend.save(dict(data))
