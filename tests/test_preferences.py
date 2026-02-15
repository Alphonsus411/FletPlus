import json
import os
import pytest

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


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink no soportado")
def test_file_backend_rejects_when_target_file_is_symlink(tmp_path, monkeypatch, caplog):
    real_target = tmp_path / "real-preferences.json"
    real_target.write_text("{}", encoding="utf-8")
    symlink_target = tmp_path / "preferences.json"
    symlink_target.symlink_to(real_target)
    monkeypatch.setenv("FLETPLUS_PREFS_FILE", str(symlink_target))

    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({"theme": "dark"})

    assert json.loads(real_target.read_text(encoding="utf-8")) == {}
    assert "archivo de preferencias es symlink" in caplog.text


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink no soportado")
def test_file_backend_rejects_when_parent_is_symlink(tmp_path, monkeypatch, caplog):
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    symlink_parent = tmp_path / "prefs"
    symlink_parent.symlink_to(real_parent, target_is_directory=True)
    target_path = symlink_parent / "preferences.json"
    monkeypatch.setenv("FLETPLUS_PREFS_FILE", str(target_path))

    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({"theme": "dark"})

    assert not (real_parent / "preferences.json").exists()
    assert "directorio padre es symlink" in caplog.text


def test_file_backend_writes_preferences_normally(tmp_path, monkeypatch):
    target_path = tmp_path / "preferences.json"
    monkeypatch.setenv("FLETPLUS_PREFS_FILE", str(target_path))

    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({"theme": "dark"})

    stored = json.loads(target_path.read_text(encoding="utf-8"))
    assert stored[PreferenceStorage.DEFAULT_KEY] == {"theme": "dark"}
