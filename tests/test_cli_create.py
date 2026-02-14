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


def _load_cli_main_module():
    import fletplus.cli.main as cli_main

    return importlib.reload(cli_main)


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
@pytest.mark.parametrize("project_name", ["demo/sub", "demo\\sub"])
def test_create_rejects_path_separators_in_any_platform(
    monkeypatch, watchdog_available: bool, project_name: str
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["create", project_name])

    assert result.exit_code != 0
    assert "separadores de ruta Unix ('/') ni Windows ('\\\\')" in result.output


@pytest.mark.parametrize("watchdog_available", [True, False])
@pytest.mark.parametrize("project_name", ["mi_app", "_demo", "app2"])
def test_create_keeps_accepting_valid_project_names(
    monkeypatch, watchdog_available: bool, project_name: str
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["create", project_name])

    assert result.exit_code == 0, result.output


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


def test_run_resolves_relative_app_prioritizing_watch_path(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    launched_app_path: list[Path] = []

    class _FakeProcess:
        def wait(self, timeout: float | None = None) -> int:
            return 0

        def poll(self) -> int:
            return 0

    def _fake_launch(app_path: Path, port: int, devtools: bool) -> _FakeProcess:
        launched_app_path.append(app_path)
        return _FakeProcess()

    monkeypatch.setattr(cli_main, "_launch_flet_process", _fake_launch)
    monkeypatch.setattr(cli_main, "_stop_process", lambda process: None)

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        cwd_main = base / "src" / "main.py"
        cwd_main.parent.mkdir(parents=True, exist_ok=True)
        cwd_main.write_text("print('cwd')", encoding="utf-8")

        watch_root = base / "watch_tree"
        watch_main = watch_root / "src" / "main.py"
        watch_main.parent.mkdir(parents=True, exist_ok=True)
        watch_main.write_text("print('watch')", encoding="utf-8")

        result = runner.invoke(cli_main.app, ["run", "--watch", str(watch_root)])

    assert result.exit_code == 0, result.output
    assert launched_app_path == [watch_main.resolve()]


def test_run_fails_with_non_zero_exit_code_without_watchdog(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    class _FakeProcess:
        def poll(self) -> int:
            return 2

    monkeypatch.setattr(cli_main, "_launch_flet_process", lambda *args, **kwargs: _FakeProcess())
    monkeypatch.setattr(cli_main, "_stop_process", lambda process: None)

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        app_file = base / "src" / "main.py"
        app_file.parent.mkdir(parents=True, exist_ok=True)
        app_file.write_text("print('hola')", encoding="utf-8")

        result = runner.invoke(cli_main.app, ["run", "--watch", str(base)])

    assert result.exit_code != 0
    assert "código 2" in result.output


def test_run_fails_with_non_zero_exit_code_with_watchdog(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=True)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    class _FakeObserver:
        def schedule(self, *args, **kwargs) -> None:
            return None

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

        def join(self) -> None:
            return None

    class _FakeProcess:
        def poll(self) -> int:
            return 3

    monkeypatch.setattr(cli_main, "Observer", _FakeObserver)
    monkeypatch.setattr(cli_main, "_launch_flet_process", lambda *args, **kwargs: _FakeProcess())
    monkeypatch.setattr(cli_main, "_stop_process", lambda process: None)

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        app_file = base / "src" / "main.py"
        app_file.parent.mkdir(parents=True, exist_ok=True)
        app_file.write_text("print('hola')", encoding="utf-8")

        result = runner.invoke(cli_main.app, ["run", "--watch", str(base)])

    assert result.exit_code != 0
    assert "código 3" in result.output
