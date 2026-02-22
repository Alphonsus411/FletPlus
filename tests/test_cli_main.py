from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from fletplus.utils import safe_subprocess


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


def _load_cli_main_module():
    import fletplus.cli.main as cli_main

    return importlib.reload(cli_main)


def test_run_resolves_relative_app_prioritizing_watch_path(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    launched_app_path: list[Path] = []

    class _FakeProcess:
        def poll(self) -> int:
            return 0

    def _fake_launch(app_path: Path, port: int, devtools: bool) -> _FakeProcess:
        launched_app_path.append(app_path)
        return _FakeProcess()

    monkeypatch.setattr(cli_main, "_launch_flet_process", _fake_launch)
    monkeypatch.setattr(cli_main, "_stop_process", lambda process: None)

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        (base / "src").mkdir(parents=True, exist_ok=True)
        (base / "src" / "main.py").write_text("print('cwd')", encoding="utf-8")

        watch_root = base / "watch_tree"
        watch_main = watch_root / "src" / "main.py"
        watch_main.parent.mkdir(parents=True, exist_ok=True)
        watch_main.write_text("print('watch')", encoding="utf-8")

        result = runner.invoke(cli_main.app, ["run", "--watch", str(watch_root)])

    assert result.exit_code == 0, result.output
    assert launched_app_path == [watch_main.resolve()]


def test_run_fails_when_watch_path_does_not_exist(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(cli_main.app, ["run", "--watch", str(base / "missing")])

    assert result.exit_code != 0
    assert "ruta a monitorear no existe" in result.output


def test_run_without_watchdog_runs_without_reload(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    class _FakeProcess:
        def poll(self) -> int:
            return 0

    monkeypatch.setattr(cli_main, "_launch_flet_process", lambda *args, **kwargs: _FakeProcess())
    monkeypatch.setattr(cli_main, "_stop_process", lambda process: None)

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        app_file = base / "src" / "main.py"
        app_file.parent.mkdir(parents=True, exist_ok=True)
        app_file.write_text("print('ok')", encoding="utf-8")

        result = runner.invoke(cli_main.app, ["run", "--watch", str(base)])

    assert result.exit_code == 0, result.output
    assert "watchdog no está instalado" in result.output
    assert "se ejecuta sin recarga automática" in result.output


def test_run_restarts_on_change_event_with_watchdog(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=True)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    launches: list[Path] = []

    class _FakeProcess:
        def __init__(self, poll_values: list[int | None]) -> None:
            self._poll_values = poll_values

        def poll(self) -> int | None:
            if self._poll_values:
                return self._poll_values.pop(0)
            return 0

    class _FakeObserver:
        def __init__(self) -> None:
            self._handler = None

        def schedule(self, handler, _path: str, recursive: bool = True) -> None:
            self._handler = handler

        def start(self) -> None:
            assert self._handler is not None
            self._handler.on_any_event(
                SimpleNamespace(is_directory=False, src_path="src/main.py")
            )

        def stop(self) -> None:
            return None

        def join(self) -> None:
            return None

    queue = [_FakeProcess([None]), _FakeProcess([0])]

    def _fake_launch(app_path: Path, port: int, devtools: bool) -> _FakeProcess:
        launches.append(app_path)
        return queue.pop(0)

    monkeypatch.setattr(cli_main, "Observer", _FakeObserver)
    monkeypatch.setattr(cli_main, "_launch_flet_process", _fake_launch)
    monkeypatch.setattr(cli_main, "_stop_process", lambda process: None)

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        app_file = base / "src" / "main.py"
        app_file.parent.mkdir(parents=True, exist_ok=True)
        app_file.write_text("print('ok')", encoding="utf-8")

        result = runner.invoke(cli_main.app, ["run", "--watch", str(base)])

    assert result.exit_code == 0, result.output
    assert len(launches) == 2
    assert "Cambios detectados, reiniciando servidor" in result.output


def test_reload_handler_debounces_consecutive_events_for_same_path(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()

    trigger_calls: list[str] = []
    handler = cli_main._ReloadHandler(
        lambda: trigger_calls.append("trigger"),
        watch_path=Path.cwd(),
        patterns=(".py",),
        debounce_window_seconds=0.3,
    )

    monotonic_values = iter([10.0, 10.1, 10.2])
    monkeypatch.setattr(cli_main.time, "monotonic", lambda: next(monotonic_values))

    event = SimpleNamespace(is_directory=False, src_path="src/main.py")
    handler.on_any_event(event)
    handler.on_any_event(event)
    handler.on_any_event(event)

    assert trigger_calls == ["trigger"]


def test_reload_handler_allows_events_after_debounce_window(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()

    trigger_calls: list[str] = []
    handler = cli_main._ReloadHandler(
        lambda: trigger_calls.append("trigger"),
        watch_path=Path.cwd(),
        patterns=(".py",),
        debounce_window_seconds=0.3,
    )

    monotonic_values = iter([20.0, 20.35])
    monkeypatch.setattr(cli_main.time, "monotonic", lambda: next(monotonic_values))

    event = SimpleNamespace(is_directory=False, src_path="src/main.py")
    handler.on_any_event(event)
    handler.on_any_event(event)

    assert trigger_calls == ["trigger", "trigger"]


def test_should_ignore_does_not_match_external_parent_segments(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()

    watch_path = Path('/tmp/workspace/proyecto')
    external_file = Path('/tmp/dist/proyecto/src/main.py')

    assert cli_main._should_ignore(external_file, watch_path=watch_path) is False


def test_should_ignore_matches_internal_excluded_directories(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()

    watch_path = Path('/tmp/workspace/proyecto')

    assert cli_main._should_ignore(watch_path / 'dist' / 'bundle.js', watch_path=watch_path) is True
    assert cli_main._should_ignore(watch_path / 'build' / 'artifact.bin', watch_path=watch_path) is True


def test_reload_handler_ignores_event_outside_watch_root(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()

    trigger_calls: list[str] = []
    handler = cli_main._ReloadHandler(
        lambda: trigger_calls.append('trigger'),
        watch_path=Path('/tmp/workspace/proyecto'),
        patterns=(".py",),
    )

    handler.on_any_event(SimpleNamespace(is_directory=False, src_path='/tmp/other/main.py'))

    assert trigger_calls == []


def test_reload_handler_ignores_internal_dist_directory(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()

    trigger_calls: list[str] = []
    watch_path = Path('/tmp/workspace/proyecto')
    handler = cli_main._ReloadHandler(
        lambda: trigger_calls.append('trigger'),
        watch_path=watch_path,
        patterns=(".py",),
    )

    handler.on_any_event(SimpleNamespace(is_directory=False, src_path=str(watch_path / 'dist' / 'main.py')))

    assert trigger_calls == []


def test_run_propagates_subprocess_failure_without_watchdog(monkeypatch) -> None:
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
    assert "finalizó con código 2" in result.output


def test_run_with_port_zero_passes_and_transmits_port(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    captured_command: list[str] = []

    class _FakeProcess:
        def poll(self) -> int:
            return 0

    def _fake_popen(command, env=None, cwd=None):
        captured_command.extend(command)
        return _FakeProcess()

    monkeypatch.setattr(cli_main.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(cli_main, "_stop_process", lambda process: None)

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        app_file = base / "src" / "main.py"
        app_file.parent.mkdir(parents=True, exist_ok=True)
        app_file.write_text("print('ok')", encoding="utf-8")

        result = runner.invoke(cli_main.app, ["run", "--watch", str(base), "--port", "0"])

    assert result.exit_code == 0, result.output
    assert "--port" in captured_command
    assert "0" in captured_command


def test_profile_runs_subset_of_flows_with_flow_option(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    executed: list[str] = []

    monkeypatch.setattr(
        cli_main,
        "PROFILE_FLOWS",
        {
            "router": lambda: executed.append("router"),
            "scaffold": lambda: executed.append("scaffold"),
            "responsive": lambda: executed.append("responsive"),
        },
    )

    with runner.isolated_filesystem():
        result = runner.invoke(cli_main.app, ["profile", "--flow", "router", "--flow", "responsive"])

    assert result.exit_code == 0, result.output
    assert executed == ["router", "responsive"]
    assert "Ejecutando 2 flujo(s): router, responsive" in result.output


def test_profile_creates_non_empty_output_file(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    monkeypatch.setattr(
        cli_main,
        "PROFILE_FLOWS",
        {
            "router": lambda: sum(range(3)),
            "scaffold": lambda: "ok",
        },
    )

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        output = base / "out" / "profile.txt"
        result = runner.invoke(
            cli_main.app,
            ["profile", "--flow", "router", "--output", str(output)],
        )

        assert result.exit_code == 0, result.output
        assert "Ejecutando 1 flujo(s): router" in result.output
        assert output.exists()
        assert output.read_text(encoding="utf-8").strip() != ""


def test_profile_rejects_invalid_limit(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli_main.app, ["profile", "--limit", "0"])

    assert result.exit_code != 0
    assert "--limit debe ser un entero positivo" in result.output


def test_run_resolves_relative_app_fallback_to_cwd_when_missing_in_watch(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()
    runner = CliRunner()

    launched_app_path: list[Path] = []

    class _FakeProcess:
        def poll(self) -> int:
            return 0

    def _fake_launch(app_path: Path, port: int, devtools: bool) -> _FakeProcess:
        launched_app_path.append(app_path)
        return _FakeProcess()

    monkeypatch.setattr(cli_main, "_launch_flet_process", _fake_launch)
    monkeypatch.setattr(cli_main, "_stop_process", lambda process: None)

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        app_file = base / "src" / "main.py"
        app_file.parent.mkdir(parents=True, exist_ok=True)
        app_file.write_text("print('cwd')", encoding="utf-8")

        watch_root = base / "watch_root"
        watch_root.mkdir(parents=True, exist_ok=True)

        result = runner.invoke(cli_main.app, ["run", "--watch", str(watch_root)])

    assert result.exit_code == 0, result.output
    assert launched_app_path == [app_file.resolve()]


def test_launch_flet_process_preserves_critical_python_env_vars(monkeypatch, tmp_path) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()

    app_file = tmp_path / "src" / "main.py"
    app_file.parent.mkdir(parents=True, exist_ok=True)
    app_file.write_text("print('ok')", encoding="utf-8")

    monkeypatch.setenv("VIRTUAL_ENV", "/tmp/venv")
    monkeypatch.setenv("PYTHONPATH", "/tmp/pythonpath")
    monkeypatch.setenv("PYTHONHOME", "/tmp/pythonhome")
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/ld")
    monkeypatch.setenv("DYLD_LIBRARY_PATH", "/tmp/dyld")
    monkeypatch.setenv("APPDATA", "C:/Users/Test/AppData/Roaming")

    captured: dict[str, object] = {}

    def _fake_popen(command, *, env, env_whitelist, cwd):
        captured["command"] = command
        captured["env"] = env
        captured["env_whitelist"] = env_whitelist
        captured["cwd"] = cwd
        return SimpleNamespace(poll=lambda: 0)

    monkeypatch.setattr(safe_subprocess, "safe_popen", _fake_popen)

    cli_main._launch_flet_process(app_file, port=None, devtools=False)

    assert captured["env"]["VIRTUAL_ENV"] == "/tmp/venv"
    assert captured["env"]["PYTHONPATH"] == "/tmp/pythonpath"
    assert captured["env"]["PYTHONHOME"] == "/tmp/pythonhome"
    assert captured["env"]["LD_LIBRARY_PATH"] == "/tmp/ld"
    assert captured["env"]["DYLD_LIBRARY_PATH"] == "/tmp/dyld"
    assert captured["env"]["APPDATA"] == "C:/Users/Test/AppData/Roaming"
    assert "VIRTUAL_ENV" in captured["env_whitelist"]
    assert "PYTHONPATH" in captured["env_whitelist"]
    assert "PYTHONHOME" in captured["env_whitelist"]
    assert "LD_LIBRARY_PATH" in captured["env_whitelist"]
    assert "DYLD_LIBRARY_PATH" in captured["env_whitelist"]
    assert "APPDATA" in captured["env_whitelist"]


def test_launch_flet_process_keeps_devtools_toggle_in_whitelist(monkeypatch, tmp_path) -> None:
    _configure_watchdog(monkeypatch, available=False)
    cli_main = _load_cli_main_module()

    app_file = tmp_path / "src" / "main.py"
    app_file.parent.mkdir(parents=True, exist_ok=True)
    app_file.write_text("print('ok')", encoding="utf-8")

    monkeypatch.setenv("FLET_DEVTOOLS", "1")

    captured: dict[str, object] = {}

    def _fake_popen(command, *, env, env_whitelist, cwd):
        captured["env"] = env
        captured["env_whitelist"] = env_whitelist
        return SimpleNamespace(poll=lambda: 0)

    monkeypatch.setattr(safe_subprocess, "safe_popen", _fake_popen)

    cli_main._launch_flet_process(app_file, port=None, devtools=False)

    assert "FLET_DEVTOOLS" not in captured["env"]
    assert "FLET_DEVTOOLS" in captured["env_whitelist"]
