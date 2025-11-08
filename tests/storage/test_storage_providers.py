"""Casos de prueba básicos para los proveedores de almacenamiento."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any, Dict, List

from fletplus.storage import StorageProvider
from fletplus.storage.files import FileStorageProvider
from fletplus.storage.local import LocalStorageProvider
from fletplus.storage.session import SessionStorageProvider


class _BaseFakeStorage:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self.data.get(key)

    def set(self, key: str, value: Any) -> bool:
        self.data[key] = value
        return True

    def remove(self, key: str) -> bool:
        self.data.pop(key, None)
        return True

    def clear(self) -> bool:
        self.data.clear()
        return True


class FakeClientStorage(_BaseFakeStorage):
    def get_keys(self, key_prefix: str) -> List[str]:
        return [key for key in self.data if key.startswith(key_prefix)]


class FakeSessionStorage(_BaseFakeStorage):
    def get_keys(self) -> List[str]:
        return list(self.data.keys())


def test_storage_provider_signals_update_on_set() -> None:
    storage = FakeClientStorage()
    provider = LocalStorageProvider(storage)

    assert provider.get("foo") is None
    provider.set("foo", {"count": 1})
    assert provider.get("foo") == {"count": 1}

    signal = provider.signal("foo")
    assert signal.get() == {"count": 1}

    provider.set("foo", {"count": 2})
    assert signal.get() == {"count": 2}

    provider.remove("foo")
    assert signal.get() is None

    snapshot = provider.snapshot()
    assert "foo" not in snapshot
    assert isinstance(snapshot, Mapping)


def test_session_storage_provider_tracks_keys() -> None:
    storage = FakeSessionStorage()
    provider = SessionStorageProvider(storage)

    provider.set("token", "abc")
    assert "token" in provider
    assert list(provider.keys()) == ["token"]

    collected: list[Any] = []

    def capture(value: Any) -> None:
        collected.append(value)

    unsubscribe = provider.subscribe("token", capture, immediate=True)
    provider.set("token", "xyz")
    provider.remove("token")
    unsubscribe()

    assert collected == ["abc", "xyz", None]
    assert "token" not in provider


def test_file_storage_provider_persists_data(tmp_path: Path) -> None:
    path = tmp_path / "storage.json"
    provider = FileStorageProvider(path)

    provider.set("settings", {"theme": "dark", "lang": "es"})
    provider.set("volume", 7)

    snapshot = provider.snapshot_signal().get()
    assert snapshot["volume"] == 7

    # Se guarda como JSON estructurado
    raw = json.loads(path.read_text("utf-8"))
    assert set(raw.keys()) == {"settings", "volume"}

    provider2 = FileStorageProvider(path)
    assert provider2.get("settings") == {"theme": "dark", "lang": "es"}

    provider2.clear()
    assert provider2.snapshot() == {}
    assert json.loads(path.read_text("utf-8")) == {}


class DummyProvider(StorageProvider[int]):
    """Implementación mínima para probar utilidades del base class."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}
        super().__init__()

    def _iter_keys(self) -> list[str]:
        return list(self._store.keys())

    def _read_raw(self, key: str) -> Any | None:
        return self._store.get(key)

    def _write_raw(self, key: str, value: Any) -> None:
        self._store[key] = value

    def _remove_raw(self, key: str) -> None:
        self._store.pop(key, None)

    def _clear_raw(self) -> None:
        self._store.clear()


def test_dummy_provider_len_and_contains() -> None:
    provider = DummyProvider()
    provider.set("a", 1)
    provider.set("b", 2)

    assert len(provider) == 2
    assert "a" in provider
    provider.remove("a")
    assert "a" not in provider

