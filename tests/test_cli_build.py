from __future__ import annotations

import subprocess
from pathlib import Path
import sys
import types
from unittest.mock import patch

from click.testing import CliRunner

watchdog_module = types.ModuleType("watchdog")
events_module = types.ModuleType("watchdog.events")
events_module.FileSystemEvent = object
events_module.FileSystemEventHandler = object
observers_module = types.ModuleType("watchdog.observers")
observers_module.Observer = object
sys.modules.setdefault("watchdog", watchdog_module)
sys.modules["watchdog.events"] = events_module
sys.modules["watchdog.observers"] = observers_module

from fletplus.cli.main import app


def _setup_minimal_project(base: Path) -> None:
    (base / "src").mkdir()
    (base / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (base / "pyproject.toml").write_text(
        """[project]\nname = 'demo-app'\nversion = '1.2.3'\n""",
        encoding="utf-8",
    )
    assets = base / "assets"
    assets.mkdir()
    (assets / "icon.png").write_bytes(b"fake")


def test_build_all_targets_success() -> None:
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
        assert any("flet" in part for part in web_command)
        assert any("PyInstaller" in part for part in desktop_command)
        assert mobile_command[0] == "briefcase"
        assert "FLETPLUS_METADATA" in mobile_kwargs.get("env", {})
        assert "FLETPLUS_ICON" in mobile_kwargs.get("env", {})
        assert "✅ web" in result.output
        assert "✅ desktop" in result.output
        assert "✅ mobile" in result.output


def test_build_failure_reports_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        _setup_minimal_project(base)

        def fake_run(command, **kwargs):
            if "PyInstaller" in command:
                raise subprocess.CalledProcessError(returncode=1, cmd=command)
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.cli.build.subprocess.run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "desktop"])

        assert result.exit_code != 0
        assert "❌ desktop" in result.output
        assert "La compilación terminó con errores" in result.output

