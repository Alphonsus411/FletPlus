from __future__ import annotations

from pathlib import Path
import sys
import types

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


def test_create_generates_project_with_valid_package_name() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(app, ["create", "Mi App"])

        assert result.exit_code == 0, result.output
        project = base / "Mi App"
        init_path = project / "src" / "__init__.py"
        assert project.exists()
        assert "mi_app" in init_path.read_text(encoding="utf-8")


def test_create_prefixes_numeric_package_name() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(app, ["create", "123app"])

        assert result.exit_code == 0, result.output
        project = base / "123app"
        init_path = project / "src" / "__init__.py"
        assert "_123app" in init_path.read_text(encoding="utf-8")


def test_create_rejects_invalid_package_name() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["create", "mi-app!"])

    assert result.exit_code != 0
    assert "identificador Python válido" in result.output
    assert "Ejemplos válidos" in result.output
    assert "Ejemplos inválidos" in result.output
