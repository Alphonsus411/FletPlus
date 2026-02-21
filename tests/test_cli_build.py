from __future__ import annotations

import importlib
import re
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

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


def _setup_minimal_project(base: Path, *, name: str = "demo-app") -> None:
    (base / "src").mkdir()
    (base / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (base / "pyproject.toml").write_text(
        f"""[project]\nname = '{name}'\nversion = '1.2.3'\n""",
        encoding="utf-8",
    )
    assets = base / "assets"
    assets.mkdir()
    (assets / "icon.png").write_bytes(b"fake")


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_build_all_targets_success(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        _setup_minimal_project(base)

        calls: list[tuple[list[str], dict]] = []

        def fake_run(command, **kwargs):
            calls.append(([str(part) for part in command], kwargs))
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.cli.build.subprocess.run", side_effect=fake_run):
            result = runner.invoke(app, ["build"])

        assert result.exit_code == 0, result.output
        web_command, _ = calls[0]
        desktop_command, _ = calls[1]
        mobile_command, mobile_kwargs = calls[2]

        expected_app_path = str((base / "src" / "main.py").resolve())
        expected_web_output = str((base / "dist" / "web").resolve())

        assert web_command[:5] == [sys.executable, "-m", "flet", "build", "web"]
        assert web_command[:6] == [
            sys.executable,
            "-m",
            "flet",
            "build",
            "web",
            expected_app_path,
        ]
        assert web_command.count(sys.executable) == 1
        assert web_command[1:].count(sys.executable) == 0
        assert web_command.count("web") == 1
        assert web_command.count("--output") == 1
        output_index = web_command.index("--output")
        assert web_command[output_index + 1] == expected_web_output
        assert web_command.count(expected_web_output) == 1
        assert expected_app_path in web_command
        assert web_command.count(expected_app_path) == 1
        assert any("PyInstaller" in part for part in desktop_command)
        assert mobile_command[0] == "briefcase"
        assert "FLETPLUS_METADATA" in mobile_kwargs.get("env", {})
        assert "FLETPLUS_ICON" in mobile_kwargs.get("env", {})
        assert "✅ web" in result.output
        assert "✅ desktop" in result.output
        assert "✅ mobile" in result.output


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_build_failure_reports_error(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        _setup_minimal_project(base)

        calls: list[list[str]] = []

        def fake_run(command, **kwargs):
            normalized = [str(part) for part in command]
            calls.append(normalized)
            if "PyInstaller" in command:
                raise subprocess.CalledProcessError(returncode=1, cmd=command)
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.cli.build.subprocess.run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "desktop"])

        assert result.exit_code != 0
        assert "❌ desktop" in result.output
        assert "La compilación terminó con errores" in result.output
        assert "código=1" in result.output
        assert "comando='" in result.output
        assert "cwd=" in result.output
        desktop_command = next(command for command in calls if "PyInstaller" in command)
        assert desktop_command[:3] == [sys.executable, "-m", "PyInstaller"]
        assert desktop_command.count(sys.executable) == 1
        assert desktop_command[1:].count(sys.executable) == 0


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_build_normalizes_name_for_pyinstaller(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        _setup_minimal_project(base, name="demo/app name@2024")

        calls: list[tuple[list[str], dict]] = []

        def fake_run(command, **kwargs):
            calls.append(([str(part) for part in command], kwargs))
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.cli.build.subprocess.run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "desktop"])

        assert result.exit_code == 0, result.output
        desktop_command = next(command for command, _ in calls if "PyInstaller" in command)
        assert desktop_command[:3] == [sys.executable, "-m", "PyInstaller"]
        assert desktop_command.count(sys.executable) == 1
        assert desktop_command[1:].count(sys.executable) == 0
        name_index = desktop_command.index("--name")
        assert desktop_command[name_index + 1] == "demo-app-name2024"


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_build_uses_directory_name_when_pyproject_missing(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        (base / "src").mkdir(parents=True, exist_ok=True)
        (base / "src" / "main.py").write_text("print('demo')", encoding="utf-8")

        calls: list[tuple[list[str], dict]] = []

        def fake_run(command, **kwargs):
            calls.append(([str(part) for part in command], kwargs))
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.cli.build.subprocess.run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "desktop"])

        assert result.exit_code == 0, result.output
        desktop_command = next(command for command, _ in calls if "PyInstaller" in command)
        name_index = desktop_command.index("--name")
        expected_name = re.sub(r"[\\/\s]+", "-", base.name)
        expected_name = re.sub(r"[^A-Za-z0-9_-]", "", expected_name).strip("-_") or "app"
        assert desktop_command[name_index + 1] == expected_name
