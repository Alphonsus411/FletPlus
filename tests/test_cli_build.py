from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from fletplus.cli import build as build_module


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

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
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
        assert desktop_command[:4] == [sys.executable, "-m", "flet", "build"]
        assert desktop_command[4] in {"linux", "macos", "windows"}
        assert mobile_command[:5] == [sys.executable, "-m", "flet", "build", "apk"]
        assert "FLETPLUS_METADATA" in mobile_kwargs.get("env", {})
        assert "FLETPLUS_ICON" in mobile_kwargs.get("env", {})
        assert "✅ web" in result.output
        assert "✅ desktop" in result.output
        assert "✅ android-apk" in result.output


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        ("windows", [build_module.BuildTarget.WINDOWS]),
        ("macos", [build_module.BuildTarget.MACOS]),
        ("linux", [build_module.BuildTarget.LINUX]),
        (
            "desktop-all",
            [
                build_module.BuildTarget.WINDOWS,
                build_module.BuildTarget.MACOS,
                build_module.BuildTarget.LINUX,
            ],
        ),
    ],
)
def test_build_target_parse_option_desktop_platforms(
    option: str, expected: list[build_module.BuildTarget]
) -> None:
    assert build_module.BuildTarget.parse_option(option) == expected


@pytest.mark.parametrize("target", ["windows", "macos", "linux"])
def test_build_desktop_platform_targets_generate_flet_commands(
    monkeypatch, target: str
) -> None:
    _configure_watchdog(monkeypatch, available=True)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        _setup_minimal_project(base)

        calls: list[tuple[list[str], dict]] = []

        def fake_run(command, **kwargs):
            calls.append(([str(part) for part in command], kwargs))
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", target])

        assert result.exit_code == 0, result.output
        assert len(calls) == 1
        command, kwargs = calls[0]
        assert command[:5] == [sys.executable, "-m", "flet", "build", target]
        assert command[command.index("--output") + 1] == str(
            (base / "dist" / target).resolve()
        )
        assert (
            tuple(kwargs.get("env_whitelist", ()))
            == build_module.BUILD_ENV_PROFILES["flet_build"]
        )
        assert f"✅ {target}" in result.output


def test_build_desktop_all_generates_each_desktop_platform(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=True)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        _setup_minimal_project(base)

        calls: list[list[str]] = []

        def fake_run(command, **kwargs):
            calls.append([str(part) for part in command])
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "desktop-all"])

        assert result.exit_code == 0, result.output
        assert [command[4] for command in calls] == ["windows", "macos", "linux"]
        assert "✅ windows" in result.output
        assert "✅ macos" in result.output
        assert "✅ linux" in result.output


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
            if "aab" in command:
                raise subprocess.CalledProcessError(returncode=1, cmd=command)
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "android-aab"])

        assert result.exit_code != 0
        assert "❌ android-aab" in result.output
        assert "La compilación terminó con errores" in result.output
        assert "código=1" in result.output
        assert "comando='" in result.output
        assert "cwd=" in result.output
        mobile_command = next(command for command in calls if "aab" in command)
        assert mobile_command[:5] == [sys.executable, "-m", "flet", "build", "aab"]
        assert mobile_command.count(sys.executable) == 1
        assert mobile_command[1:].count(sys.executable) == 0


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_build_normalizes_name_for_pyinstaller(
    monkeypatch, watchdog_available: bool
) -> None:
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

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "desktop"])

        assert result.exit_code == 0, result.output
        assert build_module._load_metadata(base).name == "demo-app-name2024"


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_build_uses_directory_name_when_pyproject_missing(
    monkeypatch, watchdog_available: bool
) -> None:
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

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "desktop"])

        assert result.exit_code == 0, result.output
        expected_name = re.sub(r"[\\/\s]+", "-", base.name)
        expected_name = (
            re.sub(r"[^A-Za-z0-9_-]", "", expected_name).strip("-_") or "app"
        )
        assert build_module._load_metadata(base).name == expected_name


@pytest.mark.parametrize(
    ("target", "profile"),
    [
        ("web", "flet_build"),
        ("desktop", "flet_build"),
        ("mobile", "flet_mobile"),
        ("android-aab", "flet_mobile"),
        ("ios", "flet_mobile"),
    ],
)
def test_build_uses_whitelist_profile(monkeypatch, target: str, profile: str) -> None:
    _configure_watchdog(monkeypatch, available=True)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        _setup_minimal_project(base)

        captured_kwargs: list[dict] = []

        def fake_run(command, **kwargs):
            captured_kwargs.append(kwargs)
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", target])

        assert result.exit_code == 0, result.output
        assert captured_kwargs
        kwargs = captured_kwargs[0]
        assert (
            tuple(kwargs.get("env_whitelist", ()))
            == build_module.BUILD_ENV_PROFILES[profile]
        )


def test_build_timeout_error_is_reported(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=True)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        _setup_minimal_project(base)

        def fake_run(command, **kwargs):
            raise subprocess.TimeoutExpired(
                cmd=command, timeout=kwargs.get("timeout", 1.0)
            )

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(
                app, ["build", "--target", "desktop", "--timeout", "1.5"]
            )

        assert result.exit_code != 0
        assert "tiempo límite" in result.output
        assert "1.5s" in result.output
        assert "comando='" in result.output


def test_build_uses_tool_fletplus_defaults_and_paths(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=True)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        (base / "app").mkdir()
        (base / "app" / "main.py").write_text("print('configured')\n", encoding="utf-8")
        (base / "static").mkdir()
        (base / "static" / "custom.png").write_bytes(b"fake")
        (base / "pyproject.toml").write_text(
            """[project]
name = 'configured-app'
version = '2.0.0'

[tool.fletplus]
app = 'app/main.py'
default_target = 'web'
assets_dir = 'static'
icon = 'static/custom.png'
build_timeout = 12.5

[tool.fletplus.web]
base_url = '/demo'
""",
            encoding="utf-8",
        )

        calls: list[tuple[list[str], dict]] = []

        def fake_run(command, **kwargs):
            calls.append(([str(part) for part in command], kwargs))
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(app, ["build"])

        assert result.exit_code == 0, result.output
        assert len(calls) == 1
        command, kwargs = calls[0]
        assert command[:5] == [sys.executable, "-m", "flet", "build", "web"]
        assert str((base / "app" / "main.py").resolve()) in command
        assert "--base-url" in command
        assert command[command.index("--base-url") + 1] == "/demo"
        assert kwargs["timeout"] == 12.5
        assert (base / "build" / "web" / "static" / "custom.png").exists()


def test_build_uses_tool_fletplus_mobile_package(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=True)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        _setup_minimal_project(base)
        with (base / "pyproject.toml").open("a", encoding="utf-8") as fh:
            fh.write("\n[tool.fletplus.mobile]\npackage = 'com.example.demo'\n")

        calls: list[tuple[list[str], dict]] = []

        def fake_run(command, **kwargs):
            calls.append(([str(part) for part in command], kwargs))
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "mobile"])

        assert result.exit_code == 0, result.output
        command, kwargs = calls[0]
        assert "--project" not in command
        assert kwargs["env"]["FLETPLUS_PACKAGE"] == "com.example.demo"


def test_full_stack_config_is_loaded_into_context_without_building() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        (base / "src").mkdir()
        (base / "src" / "main.py").write_text("print('main')\n", encoding="utf-8")
        for directory in ("backend", "frontend", "docs", "config", "deploy"):
            (base / directory).mkdir()
        (base / "backend" / "api.py").write_text("app = object()\n", encoding="utf-8")
        (base / "frontend" / "app.py").write_text("view = object()\n", encoding="utf-8")
        (base / "docs" / "index.md").write_text("# Docs\n", encoding="utf-8")
        (base / "config" / ".env.example").write_text("DEBUG=0\n", encoding="utf-8")
        (base / "deploy" / "Dockerfile").write_text("FROM python\n", encoding="utf-8")
        (base / "shared_pkg").mkdir()
        (base / "shared_pkg" / "__init__.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        (base / "pyproject.toml").write_text(
            """[project]
name = 'full-stack-demo'
version = '1.0.0'

[tool.fletplus]
backend_app = 'backend/api.py'
frontend_app = 'frontend/app.py'
docs_dir = 'docs'
config_dir = 'config'
deployment_dir = 'deploy'
include_python_packages = ['shared_pkg']
""",
            encoding="utf-8",
        )

        context = build_module.FullStackBuildContext.from_project(
            base, Path("src/main.py")
        )

        assert context.backend_app == (base / "backend" / "api.py").resolve()
        assert context.frontend_app == (base / "frontend" / "app.py").resolve()
        assert context.docs_dir == (base / "docs").resolve()
        assert context.config_dir == (base / "config").resolve()
        assert context.deployment_dir == (base / "deploy").resolve()
        assert context.include_python_packages == [(base / "shared_pkg").resolve()]


def test_full_stack_prepare_copies_contract_files_without_real_build() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        (base / "src").mkdir()
        (base / "src" / "main.py").write_text("print('main')\n", encoding="utf-8")
        (base / "backend").mkdir()
        (base / "backend" / "api.py").write_text("app = object()\n", encoding="utf-8")
        (base / "frontend").mkdir()
        (base / "frontend" / "app.py").write_text("view = object()\n", encoding="utf-8")
        (base / "docs").mkdir()
        (base / "docs" / "index.md").write_text("# Docs\n", encoding="utf-8")
        (base / "config").mkdir()
        (base / "config" / ".env.example").write_text("DEBUG=0\n", encoding="utf-8")
        (base / "deploy").mkdir()
        (base / "deploy" / "Dockerfile").write_text("FROM python\n", encoding="utf-8")
        (base / "shared_pkg").mkdir()
        (base / "shared_pkg" / "__init__.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        (base / "pyproject.toml").write_text(
            """[project]
name = 'full-stack-demo'
version = '1.0.0'

[tool.fletplus]
backend_app = 'backend/api.py'
frontend_app = 'frontend/app.py'
docs_dir = 'docs'
config_dir = 'config'
deployment_dir = 'deploy'
include_python_packages = ['shared_pkg']
""",
            encoding="utf-8",
        )

        context = build_module.FullStackBuildContext.from_project(
            base, Path("src/main.py")
        )
        adapter = build_module.WebAdapter(context)
        prepared = adapter.prepare()

        staging = base / "build" / "web"
        assert (staging / "backend" / "api.py").exists()
        assert (staging / "frontend" / "app.py").exists()
        assert (staging / "docs" / "index.md").exists()
        assert (staging / "config" / ".env.example").exists()
        assert (staging / "deployment" / "Dockerfile").exists()
        assert (staging / "python-packages" / "shared_pkg" / "__init__.py").exists()
        assert prepared["backend"] == staging / "backend"
        assert prepared["python_packages"] == staging / "python-packages"


def test_web_deploy_config_reads_tool_fletplus_web_options() -> None:
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        (base / "src").mkdir()
        (base / "src" / "main.py").write_text("print('main')\n", encoding="utf-8")
        (base / "pyproject.toml").write_text(
            """[project]
name = 'web-config-demo'
version = '1.0.0'

[tool.fletplus.web]
base_url = '/app/'
backend_entrypoint = 'server/main.py'
static_dir = 'public'
pwa = true
env_file = '.env.production'
deploy_provider = 'nginx'
""",
            encoding="utf-8",
        )

        config = build_module._load_fletplus_config(base)

        assert config.web_deploy.base_url == "/app/"
        assert config.web_deploy.backend_entrypoint == "server/main.py"
        assert config.web_deploy.static_dir == "public"
        assert config.web_deploy.pwa is True
        assert config.web_deploy.env_file == ".env.production"
        assert config.web_deploy.deploy_provider == "nginx"
        assert config.web_deploy.has_backend is True


def test_web_build_writes_deploy_manifest_and_templates(monkeypatch) -> None:
    _configure_watchdog(monkeypatch, available=True)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        (base / "src").mkdir()
        (base / "src" / "main.py").write_text("print('configured')\n", encoding="utf-8")
        (base / "server").mkdir()
        (base / "server" / "main.py").write_text("print('backend')\n", encoding="utf-8")
        (base / ".env.production").write_text("DEBUG=0\n", encoding="utf-8")
        (base / "pyproject.toml").write_text(
            """[project]
name = 'manifest-demo'
version = '2.1.0'

[tool.fletplus.web]
base_url = '/portal/'
backend_entrypoint = 'server/main.py'
static_dir = 'dist/web'
pwa = true
env_file = '.env.production'
deploy_provider = 'external-proxy'
""",
            encoding="utf-8",
        )

        def fake_run(command, **kwargs):
            return subprocess.CompletedProcess(command, 0)

        with patch("fletplus.utils.safe_subprocess.safe_run", side_effect=fake_run):
            result = runner.invoke(app, ["build", "--target", "web"])

        assert result.exit_code == 0, result.output
        manifest_path = base / "dist" / "web" / "fletplus-deploy.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema_version"] == 1
        assert manifest["project"] == {"name": "manifest-demo", "version": "2.1.0"}
        assert manifest["web"]["base_url"] == "/portal/"
        assert manifest["web"]["backend_entrypoint"] == "server/main.py"
        assert manifest["web"]["pwa"] is True
        assert manifest["web"]["deploy_provider"] == "external-proxy"
        assert manifest["deployment"]["mode"] == "backend-python"
        assert manifest["paths"]["backend_entrypoint"] == str(
            (base / "server" / "main.py").resolve()
        )
        assert (base / "dist" / "web" / "deploy-static.sh").exists()
        backend_template = (
            base / "dist" / "web" / "deploy-backend-python.sh"
        ).read_text(encoding="utf-8")
        assert "source .env.production" in backend_template
        assert "python server/main.py" in backend_template
