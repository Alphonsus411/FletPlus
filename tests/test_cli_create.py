from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest
from click.testing import CliRunner

def _configure_watchdog(monkeypatch, *, available: bool) -> None:
    if available:
        watchdog_module = types.ModuleType("watchdog")
        events_module = types.ModuleType("watchdog.events")
        events_module.FileSystemEvent = object
        events_module.FileSystemEventHandler = object
        observers_module = types.ModuleType("watchdog.observers")
        observers_module.Observer = object
        monkeypatch.setitem(sys.modules, "watchdog", watchdog_module)
        monkeypatch.setitem(sys.modules, "watchdog.events", events_module)
        monkeypatch.setitem(sys.modules, "watchdog.observers", observers_module)
    else:
        monkeypatch.setitem(sys.modules, "watchdog", None)
        monkeypatch.setitem(sys.modules, "watchdog.events", None)
        monkeypatch.setitem(sys.modules, "watchdog.observers", None)


def _load_cli_app():
    import fletplus.cli.main as cli_main

    return importlib.reload(cli_main).app


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_generates_project_with_valid_package_name(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(app, ["create", "Mi App"])

        assert result.exit_code == 0, result.output
        project = base / "Mi App"
        init_path = project / "src" / "__init__.py"
        assert project.exists()
        assert "mi_app" in init_path.read_text(encoding="utf-8")


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_prefixes_numeric_package_name(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(app, ["create", "123app"])

        assert result.exit_code == 0, result.output
        project = base / "123app"
        init_path = project / "src" / "__init__.py"
        assert "_123app" in init_path.read_text(encoding="utf-8")


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_rejects_invalid_package_name(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["create", "mi-app!"])

    assert result.exit_code != 0
    assert "identificador Python válido" in result.output
    assert "Ejemplos válidos" in result.output
    assert "Ejemplos inválidos" in result.output


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_fails_when_target_exists_as_file(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        target = base / "demo"
        target.write_text("archivo", encoding="utf-8")

        result = runner.invoke(app, ["create", "demo"])

    assert result.exit_code != 0
    assert "ya existe y no es un directorio" in result.output


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_allows_existing_empty_directory(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        target = base / "demo"
        target.mkdir(parents=True)

        result = runner.invoke(app, ["create", "demo"])

        assert result.exit_code == 0, result.output
        assert (target / "src" / "__init__.py").exists()


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_fails_when_target_directory_is_not_empty(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        target = base / "demo"
        target.mkdir(parents=True)
        (target / "README.md").write_text("contenido", encoding="utf-8")

        result = runner.invoke(app, ["create", "demo"])

    assert result.exit_code != 0
    assert "ya existe y no está vacío" in result.output
