"""Almacenamiento persistente de preferencias para FletPlus."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)


class _BaseBackend:
    def load(self) -> dict[str, Any] | None:  # pragma: no cover - interfaz
        raise NotImplementedError

    def save(self, data: Mapping[str, Any]) -> None:  # pragma: no cover - interfaz
        raise NotImplementedError


class _ClientStorageBackend(_BaseBackend):
    def __init__(self, storage, key: str) -> None:
        self._storage = storage
        self._key = key

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
        except TypeError:
            try:
                serialized = json.dumps(payload)
            except (TypeError, ValueError):
                logger.warning(
                    "Preferencias no serializables para client_storage: %s", payload
                )
                return
            try:
                self._storage.set(self._key, serialized)
            except TypeError:
                logger.warning(
                    "Preferencias no serializables para client_storage: %s", payload
                )
            except Exception:  # pragma: no cover - errores de Flet
                logger.exception(
                    "No se pudieron guardar preferencias en client_storage"
                )
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
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
        except Exception:  # pragma: no cover - errores inesperados
            logger.exception("No se pudieron guardar preferencias en %s", self._path)


class PreferenceStorage:
    """Abstracción ligera para leer/escribir preferencias persistentes."""

    DEFAULT_KEY = "fletplus.preferences"

    def __init__(self, page, *, key: str | None = None) -> None:
        self._key = key or self.DEFAULT_KEY
        storage = getattr(page, "client_storage", None)
        if storage and hasattr(storage, "get") and hasattr(storage, "set"):
            self._backend: _BaseBackend = _ClientStorageBackend(storage, self._key)
        else:
            self._backend = _FileBackend(self._key)

    def load(self) -> dict[str, Any]:
        prefs = self._backend.load()
        if isinstance(prefs, dict):
            return dict(prefs)
        return {}

    def save(self, data: Mapping[str, Any]) -> None:
        self._backend.save(dict(data))
