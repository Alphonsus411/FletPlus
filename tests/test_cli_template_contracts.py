from __future__ import annotations

import ast
import importlib
import sys
import types
from pathlib import Path

import pytest
from click.testing import CliRunner

TEMPLATE_ROOT = Path("fletplus/cli/templates")
TEMPLATES = ("app", "web", "desktop", "mobile", "fullstack")
PLATFORM_TEMPLATES = ("web", "desktop", "mobile", "fullstack")
REQUIRED_TEMPLATE_FILES = (
    "src/frontend/config.py",
    "src/frontend/theme.py",
    "src/frontend/layout.py",
    "src/frontend/routes.py",
    "src/frontend/assets.py",
    "README.md",
    "requirements.txt",
    "pyproject.toml",
)
FULLSTACK_TEMPLATE_FILES = (
    "src/backend/__init__.py",
    "src/backend/services.py",
    "src/shared/__init__.py",
    "src/shared/config.py",
    "src/shared/models.py",
    "docs/README.md",
    "deploy/README.md",
)
COMMON_LAYOUT_HELPERS = (
    "active_profile",
    "orientation",
    "spacing",
    "max_width_container",
    "responsive_shell",
)
PLATFORM_LAYOUT_HELPERS = ("density", "safe_padding")


def _configure_watchdog(monkeypatch: pytest.MonkeyPatch, *, available: bool) -> None:
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


def _defined_functions(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in module.body if isinstance(node, ast.FunctionDef)}


@pytest.mark.parametrize("template_name", TEMPLATES)
def test_frontend_templates_include_minimum_common_structure(template_name: str) -> None:
    template_dir = TEMPLATE_ROOT / template_name

    missing_files = [
        relative_path
        for relative_path in REQUIRED_TEMPLATE_FILES
        if not (template_dir / relative_path).is_file()
    ]

    assert not missing_files, f"{template_name} no incluye: {missing_files}"


@pytest.mark.parametrize("template_name", TEMPLATES)
def test_frontend_templates_expose_common_layout_helpers(template_name: str) -> None:
    layout_path = TEMPLATE_ROOT / template_name / "src" / "frontend" / "layout.py"

    functions = _defined_functions(layout_path)

    assert set(COMMON_LAYOUT_HELPERS).issubset(functions)


@pytest.mark.parametrize("template_name", PLATFORM_TEMPLATES)
def test_platform_frontend_templates_expose_platform_layout_helpers(
    template_name: str,
) -> None:
    layout_path = TEMPLATE_ROOT / template_name / "src" / "frontend" / "layout.py"

    functions = _defined_functions(layout_path)

    assert set(PLATFORM_LAYOUT_HELPERS).issubset(functions)


def test_app_template_keeps_unified_full_layout_interface() -> None:
    """La plantilla general debe seguir la interfaz completa tras la unificación."""
    layout_path = TEMPLATE_ROOT / "app" / "src" / "frontend" / "layout.py"

    functions = _defined_functions(layout_path)

    assert set(COMMON_LAYOUT_HELPERS + PLATFORM_LAYOUT_HELPERS).issubset(functions)


def test_fullstack_template_includes_backend_shared_docs_and_deploy() -> None:
    template_dir = TEMPLATE_ROOT / "fullstack"

    missing_files = [
        relative_path
        for relative_path in FULLSTACK_TEMPLATE_FILES
        if not (template_dir / relative_path).is_file()
    ]

    assert not missing_files, f"fullstack no incluye: {missing_files}"

    pyproject = (template_dir / "pyproject.toml").read_text(encoding="utf-8")
    for marker in (
        'backend_dir = "src/backend"',
        'frontend_dir = "src/frontend"',
        'docs_dir = "docs"',
        'deploy_dir = "deploy"',
    ):
        assert marker in pyproject


@pytest.mark.parametrize("watchdog_available", [True, False])
@pytest.mark.parametrize("target_name", TEMPLATES)
def test_create_target_generates_frontend_template_contract(
    monkeypatch: pytest.MonkeyPatch, watchdog_available: bool, target_name: str
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(app, ["create", "demo", "--target", target_name])

        assert result.exit_code == 0, result.output
        project_dir = base / "demo"
        expected_files = list(REQUIRED_TEMPLATE_FILES)
        if target_name == "fullstack":
            expected_files.extend(FULLSTACK_TEMPLATE_FILES)
        for relative_path in expected_files:
            assert (project_dir / relative_path).is_file()

        functions = _defined_functions(project_dir / "src" / "frontend" / "layout.py")

    assert set(COMMON_LAYOUT_HELPERS).issubset(functions)
    if target_name in PLATFORM_TEMPLATES or target_name == "app":
        assert set(PLATFORM_LAYOUT_HELPERS).issubset(functions)
