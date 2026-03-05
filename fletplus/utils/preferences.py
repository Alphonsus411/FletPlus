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
        self._allow_arbitrary_path = (
            os.environ.get("FLETPLUS_PREFS_ALLOW_ARBITRARY_PATH") == "1"
        )
        configured_root = os.environ.get("FLETPLUS_PREFS_TRUSTED_ROOT")
        trusted_root = Path(configured_root).expanduser() if configured_root else Path.home() / ".fletplus"
        self._trusted_root = trusted_root
        env_path = os.environ.get("FLETPLUS_PREFS_FILE")
        if env_path:
            self._path = Path(env_path)
        else:
            self._path = self._trusted_root / "preferences.json"
        self._lock_path = self._path.with_suffix(f"{self._path.suffix}.lock")

    @contextmanager
    def _file_lock(self) -> Iterator[None]:
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

    def _has_symlink_component(self, path: Path) -> bool:
        candidate = path.expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate

        probe = Path(candidate.anchor)
        for part in candidate.parts[1:]:
            probe = probe / part
            if probe.exists() and probe.is_symlink():
                return True
        return False

    def _is_path_inside_trusted_root(self) -> bool:
        try:
            trusted_root = self._trusted_root.expanduser().resolve(strict=False)
            resolved_target = self._path.expanduser().resolve(strict=False)
        except OSError:
            logger.exception(
                "Guardado de preferencias abortado: no se pudo resolver ruta segura %s",
                self._path,
            )
            return False

        if resolved_target.is_relative_to(trusted_root):
            return True

        if self._allow_arbitrary_path:
            logger.warning(
                "Guardado de preferencias permitido fuera del directorio confiable por "
                "FLETPLUS_PREFS_ALLOW_ARBITRARY_PATH=1 (%s -> %s)",
                self._path,
                resolved_target,
            )
            return True

        logger.error(
            "Guardado de preferencias abortado: ruta fuera del directorio confiable "
            "(%s -> %s, root=%s)",
            self._path,
            resolved_target,
            trusted_root,
        )
        return False

    def _validate_save_target(self) -> bool:
        if self._has_symlink_component(self._path):
            logger.error(
                "Guardado de preferencias abortado: la ruta contiene symlinks (%s)",
                self._path,
            )
            return False
        if not self._is_path_secure(self._path.parent, label="directorio padre"):
            return False
        if not self._is_path_secure(self._path, label="archivo de preferencias"):
            return False
        return self._is_path_inside_trusted_root()

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
        if not self._validate_save_target():
            logger.warning(
                "Guardado de preferencias abortado por política de seguridad (%s)",
                self._path,
            )
            return

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._file_lock():
                payload = self._read_all()
                current_entry = payload.get(self._key)
                if isinstance(current_entry, Mapping):
                    merged_entry = dict(current_entry)
                    merged_entry.update(dict(data))
                else:
                    merged_entry = dict(data)
                payload[self._key] = merged_entry

                tmp_path: Path | None = None
                tmp_fd: int | None = None
                try:
                    tmp_fd, tmp_name = tempfile.mkstemp(
                        dir=self._path.parent,
                        prefix=f"{self._path.name}.",
                        suffix=".tmp",
                        text=False,
                    )
                    tmp_path = Path(tmp_name)
                    with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                        tmp_fd = None

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
                    if tmp_fd is not None:
                        os.close(tmp_fd)
                    if tmp_path is not None and tmp_path.exists():
                        tmp_path.unlink(missing_ok=True)
        except Exception:  # pragma: no cover - errores inesperados
            logger.exception("Error de I/O al guardar preferencias en %s", self._path)


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
