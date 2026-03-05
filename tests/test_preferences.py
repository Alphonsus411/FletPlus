import json
import os
from concurrent.futures import ProcessPoolExecutor

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
    try:
        symlink_target.symlink_to(real_target)
    except OSError as e:
        if getattr(e, "winerror", 0) == 1314:
            pytest.skip("Symlinks not allowed on Windows without admin/dev mode")
        raise
    monkeypatch.setenv("FLETPLUS_PREFS_TRUSTED_ROOT", str(tmp_path))
    monkeypatch.setenv("FLETPLUS_PREFS_FILE", str(symlink_target))

    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({"theme": "dark"})

    assert json.loads(real_target.read_text(encoding="utf-8")) == {}
    assert "la ruta contiene symlinks" in caplog.text


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink no soportado")
def test_file_backend_rejects_when_parent_is_symlink(tmp_path, monkeypatch, caplog):
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    symlink_parent = tmp_path / "prefs"
    try:
        symlink_parent.symlink_to(real_parent, target_is_directory=True)
    except OSError as e:
        if getattr(e, "winerror", 0) == 1314:
            pytest.skip("Symlinks not allowed on Windows without admin/dev mode")
        raise
    target_path = symlink_parent / "preferences.json"
    monkeypatch.setenv("FLETPLUS_PREFS_TRUSTED_ROOT", str(tmp_path))
    monkeypatch.setenv("FLETPLUS_PREFS_FILE", str(target_path))

    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({"theme": "dark"})

    assert not (real_parent / "preferences.json").exists()
    assert "la ruta contiene symlinks" in caplog.text


def test_file_backend_writes_preferences_normally(tmp_path, monkeypatch):
    target_path = tmp_path / "preferences.json"
    monkeypatch.setenv("FLETPLUS_PREFS_TRUSTED_ROOT", str(tmp_path))
    monkeypatch.setenv("FLETPLUS_PREFS_FILE", str(target_path))

    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({"theme": "dark"})

    stored = json.loads(target_path.read_text(encoding="utf-8"))
    assert stored[PreferenceStorage.DEFAULT_KEY] == {"theme": "dark"}


def _save_preferences_entry(path: str, key: str, value: str) -> None:
    os.environ["FLETPLUS_PREFS_FILE"] = path
    prefs = PreferenceStorage(DummyPage(None), key=key)
    prefs.save({"value": value})


def _save_preferences_partial(path: str, field: str, value: str) -> None:
    os.environ["FLETPLUS_PREFS_FILE"] = path
    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({field: value})


def test_file_backend_parallel_writes_keep_all_keys(tmp_path, monkeypatch):
    target_path = tmp_path / "preferences.json"
    total_writers = 8
    monkeypatch.setenv("FLETPLUS_PREFS_TRUSTED_ROOT", str(tmp_path))

    with ProcessPoolExecutor(max_workers=total_writers) as executor:
        futures = [
            executor.submit(
                _save_preferences_entry,
                str(target_path),
                f"worker-{index}",
                f"value-{index}",
            )
            for index in range(total_writers)
        ]
        for future in futures:
            future.result()

    stored = json.loads(target_path.read_text(encoding="utf-8"))
    assert len(stored) == total_writers
    for index in range(total_writers):
        assert stored[f"worker-{index}"] == {"value": f"value-{index}"}


def test_file_backend_parallel_writes_merge_same_entry(tmp_path, monkeypatch):
    target_path = tmp_path / "preferences.json"
    total_writers = 8
    monkeypatch.setenv("FLETPLUS_PREFS_TRUSTED_ROOT", str(tmp_path))

    with ProcessPoolExecutor(max_workers=total_writers) as executor:
        futures = [
            executor.submit(
                _save_preferences_partial,
                str(target_path),
                f"field-{index}",
                f"value-{index}",
            )
            for index in range(total_writers)
        ]
        for future in futures:
            future.result()

    stored = json.loads(target_path.read_text(encoding="utf-8"))
    entry = stored[PreferenceStorage.DEFAULT_KEY]
    assert len(entry) == total_writers
    for index in range(total_writers):
        assert entry[f"field-{index}"] == f"value-{index}"


def test_file_backend_allows_path_inside_trusted_root(tmp_path, monkeypatch):
    allowed_root = tmp_path / "trusted"
    allowed_root.mkdir()
    target_path = allowed_root / "preferences.json"
    monkeypatch.setenv("FLETPLUS_PREFS_TRUSTED_ROOT", str(allowed_root))
    monkeypatch.setenv("FLETPLUS_PREFS_FILE", str(target_path))

    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({"theme": "dark"})

    stored = json.loads(target_path.read_text(encoding="utf-8"))
    assert stored[PreferenceStorage.DEFAULT_KEY] == {"theme": "dark"}


def test_file_backend_rejects_path_outside_trusted_root(tmp_path, monkeypatch, caplog):
    allowed_root = tmp_path / "trusted"
    allowed_root.mkdir()
    outside_target = tmp_path / "outside" / "preferences.json"
    outside_dir = outside_target.parent
    outside_lock = outside_target.with_suffix(f"{outside_target.suffix}.lock")
    monkeypatch.setenv("FLETPLUS_PREFS_TRUSTED_ROOT", str(allowed_root))
    monkeypatch.setenv("FLETPLUS_PREFS_FILE", str(outside_target))
    monkeypatch.delenv("FLETPLUS_PREFS_ALLOW_ARBITRARY_PATH", raising=False)

    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({"theme": "dark"})

    assert not outside_dir.exists()
    assert not outside_target.exists()
    assert not outside_lock.exists()
    assert "abortado por política de seguridad" in caplog.text
    assert "ruta fuera del directorio confiable" in caplog.text


def test_file_backend_allows_arbitrary_path_with_opt_in(tmp_path, monkeypatch, caplog):
    allowed_root = tmp_path / "trusted"
    allowed_root.mkdir()
    outside_target = tmp_path / "outside" / "preferences.json"
    monkeypatch.setenv("FLETPLUS_PREFS_TRUSTED_ROOT", str(allowed_root))
    monkeypatch.setenv("FLETPLUS_PREFS_FILE", str(outside_target))
    monkeypatch.setenv("FLETPLUS_PREFS_ALLOW_ARBITRARY_PATH", "1")

    prefs = PreferenceStorage(DummyPage(None))
    prefs.save({"theme": "dark"})

    stored = json.loads(outside_target.read_text(encoding="utf-8"))
    assert stored[PreferenceStorage.DEFAULT_KEY] == {"theme": "dark"}
    assert "FLETPLUS_PREFS_ALLOW_ARBITRARY_PATH=1" in caplog.text
