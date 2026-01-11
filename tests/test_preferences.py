from fletplus.utils.preferences import _ClientStorageBackend


class FailingStorage:
    def __init__(self):
        self.set_calls = []

    def get(self, key: str):
        return None

    def set(self, key: str, value):
        if isinstance(value, dict):
            raise TypeError("dict not supported")
        self.set_calls.append((key, value))


def test_client_storage_save_handles_non_serializable_payload():
    storage = FailingStorage()
    backend = _ClientStorageBackend(storage, "prefs")

    backend.save({"bad": object()})

    assert storage.set_calls == []
