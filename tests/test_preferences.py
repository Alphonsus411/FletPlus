from fletplus.utils.preferences import PreferenceStorage, _ClientStorageBackend


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


class FalseyStorage:
    def __bool__(self):
        return False

    def get(self, key: str):
        return None

    def set(self, key: str, value):
        return None


class DummyPage:
    def __init__(self, storage):
        self.client_storage = storage


def test_preference_storage_uses_client_backend_with_falsey_storage():
    prefs = PreferenceStorage(DummyPage(FalseyStorage()))

    assert isinstance(prefs._backend, _ClientStorageBackend)
