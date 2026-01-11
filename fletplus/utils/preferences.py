"""Almacenamiento persistente de preferencias para FletPlus."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Mapping

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
        else:
            base_dir = Path.home() / ".fletplus"
            self._path = base_dir / "preferences.json"

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
        payload = self._read_all()
        payload[self._key] = dict(data)
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._path.with_name(f"{self._path.name}.tmp")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            try:
                fd = os.open(tmp_path, flags, 0o600)
            except FileExistsError:
                tmp_path.unlink(missing_ok=True)
                fd = os.open(tmp_path, flags, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(tmp_path, self._path)
                os.chmod(self._path, 0o600)
            finally:
                if tmp_path.exists():
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
        if storage and hasattr(storage, "get") and hasattr(storage, "set"):
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
