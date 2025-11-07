import logging

import pytest

from fletplus.utils.preferences import _ClientStorageBackend


class RejectingStorage:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def get(self, key: str):  # pragma: no cover - no se usa en la prueba
        return None

    def set(self, key: str, value) -> None:
        self.calls.append((key, value))
        raise TypeError("unsupported")


def test_client_storage_backend_handles_unserializable_payload(caplog: pytest.LogCaptureFixture) -> None:
    storage = RejectingStorage()
    backend = _ClientStorageBackend(storage, "prefs")
    payload = {"theme": {"overrides": {"colors": {"primary": object()}}}}

    with caplog.at_level(logging.WARNING):
        backend.save(payload)

    assert len(storage.calls) == 1
    assert "Preferencias no serializables para client_storage" in caplog.text
