from __future__ import annotations

import ast
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


def _read_main_flet_dependency() -> str:
    pyproject_text = Path("pyproject.toml").read_text(encoding="utf-8")
    for line in pyproject_text.splitlines():
        stripped = line.strip()
        if stripped.startswith('"flet'):
            return stripped.strip('",')
    raise AssertionError("No se encontró dependencia de Flet en pyproject.toml")


def _read_main_flet_policy() -> str:
    dependency = _read_main_flet_dependency()
    return dependency.removeprefix("flet")


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_generates_project_with_valid_package_name(
    monkeypatch, watchdog_available: bool
) -> None:
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
def test_create_template_uses_main_flet_version_policy(
    monkeypatch, watchdog_available: bool
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()
    expected_flet_dependency = _read_main_flet_dependency()
    expected_flet_policy = _read_main_flet_policy()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(app, ["create", "demo"])

        assert result.exit_code == 0, result.output
        project = base / "demo"
        requirements = (project / "requirements.txt").read_text(encoding="utf-8")
        readme = (project / "README.md").read_text(encoding="utf-8")

    requirement_lines = {
        line.strip()
        for line in requirements.splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert expected_flet_dependency in requirement_lines
    assert f"Flet `{expected_flet_policy}`" in readme


@pytest.mark.parametrize("watchdog_available", [True, False])
@pytest.mark.parametrize(
    ("template_name", "expected_markers", "unexpected_markers"),
    [
        (
            "app",
            ["FrontEndConfig", "Plantilla responsive activa"],
            ["register_pwa", "safe_set_window_attr", "NavigationBar"],
        ),
        (
            "web",
            [
                "from fletplus.web.pwa import",
                "register_pwa(page",
                "prepare_pwa_assets",
                "view=ft.AppView.WEB_BROWSER",
                "assets_dir=str(PWA_DIR)",
            ],
            ["safe_set_window_attr", "NavigationBar"],
        ),
        (
            "desktop",
            [
                "from fletplus.utils.flet_compat import safe_set_window_attr",
                "from fletplus.components import CommandPalette",
                "from fletplus.cli.catalog import get_cli_command_catalog",
                "configure_window(page)",
                'safe_set_window_attr(page, "min_width"',
                "Panel principal",
                "Mostrar CLI de FletPlus",
                "ft.ListTile",
                "on_click=lambda _event, key=route_key: show_route(key)",
            ],
            ["register_pwa", "NavigationBar"],
        ),
        (
            "mobile",
            [
                "make_navigation_bar_destination",
                "ft.NavigationBar",
                "SafeArea",
                'layout_density="compact"',
            ],
            ["register_pwa", "safe_set_window_attr"],
        ),
        (
            "fullstack",
            [
                "from backend.services import get_project_status",
                "get_project_status()",
                "Backend local:",
                "Plantilla responsive activa",
            ],
            ["register_pwa", "safe_set_window_attr", "NavigationBar"],
        ),
    ],
)
def test_create_supports_frontend_templates(
    monkeypatch,
    watchdog_available: bool,
    template_name: str,
    expected_markers: list[str],
    unexpected_markers: list[str],
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(app, ["create", "demo", "--template", template_name])

        assert result.exit_code == 0, result.output
        main_py = (base / "demo" / "src" / "main.py").read_text(encoding="utf-8")
        readme = (base / "demo" / "README.md").read_text(encoding="utf-8")
        assert "FrontEndConfig" in main_py
        for marker in expected_markers:
            assert marker in main_py
        for marker in unexpected_markers:
            assert marker not in main_py
        assert "fletplus run" in readme
        assert "src/frontend/theme.py" in readme
        assert "breakpoints" in readme
        generated_paths = [
            "pyproject.toml",
            "src/main.py",
            "src/frontend/__init__.py",
            "src/frontend/config.py",
            "src/frontend/theme.py",
            "src/frontend/layout.py",
            "src/frontend/routes.py",
            "src/frontend/assets.py",
            "assets/README.md",
        ]
        if template_name == "web":
            generated_paths.extend(["web/manifest.json", "web/service_worker.js"])
        if template_name == "fullstack":
            generated_paths.extend(
                [
                    "src/backend/__init__.py",
                    "src/backend/services.py",
                    "src/shared/__init__.py",
                    "src/shared/config.py",
                    "src/shared/models.py",
                    "docs/README.md",
                    "deploy/README.md",
                ]
            )
        for generated_path in generated_paths:
            assert (base / "demo" / generated_path).exists()
        assert (base / "demo" / "requirements.txt").exists()
        pyproject = (base / "demo" / "pyproject.toml").read_text(encoding="utf-8")
        requirements = (base / "demo" / "requirements.txt").read_text(encoding="utf-8")
        assert 'requires-python = ">=3.10"' in pyproject
        assert '"fletplus>=0.4,<0.5"' in pyproject
        assert "fletplus>=0.4,<0.5" in requirements
        assert "[tool.fletplus]" in pyproject
        assert "[tool.fletplus.frontend]" in pyproject
        if template_name == "fullstack":
            assert 'backend_dir = "src/backend"' in pyproject
            assert 'frontend_dir = "src/frontend"' in pyproject
            assert 'docs_dir = "docs"' in pyproject
            assert 'deploy_dir = "deploy"' in pyproject


@pytest.mark.parametrize("watchdog_available", [True, False])
@pytest.mark.parametrize(
    "template_name", ["app", "web", "desktop", "mobile", "fullstack"]
)
def test_create_frontend_templates_expose_equivalent_responsive_layout_helpers(
    monkeypatch, watchdog_available: bool, template_name: str
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(app, ["create", "demo", "--template", template_name])

        assert result.exit_code == 0, result.output
        layout_py = (base / "demo" / "src" / "frontend" / "layout.py").read_text(
            encoding="utf-8"
        )

    expected_markers = [
        "from fletplus.utils.viewport import viewport_info",
        "def active_profile(page: ft.Page, frontend: FrontEndConfig):",
        ").profile",
        "def orientation(page: ft.Page, frontend: FrontEndConfig | None = None) -> str:",
        ").orientation",
        "def density(page: ft.Page, frontend: FrontEndConfig) -> str:",
        ").density",
        "def safe_padding(page: ft.Page, frontend: FrontEndConfig) -> ft.Padding:",
        ").padding",
        "container.padding = safe_padding(page, frontend)",
        "def responsive_shell(",
        "densidad {info.density}",
        "{info.width}×{info.height}",
    ]
    for marker in expected_markers:
        assert marker in layout_py


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_frontend_tasks_supports_markdown_format(
    monkeypatch, watchdog_available: bool
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    result = runner.invoke(
        app, ["frontend-tasks", "--target", "desktop", "--format", "markdown"]
    )

    assert result.exit_code == 0, result.output
    assert "Tareas FrontEndConfig" in result.output
    assert "task-stub{title=" in result.output
    assert "Pasos:" in result.output


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_cli_catalog_lists_core_commands(monkeypatch, watchdog_available: bool) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    result = runner.invoke(app, ["cli-catalog", "--format", "markdown"])

    assert result.exit_code == 0, result.output
    for marker in (
        "fletplus create <nombre>",
        "fletplus run",
        "fletplus frontend-tasks --format markdown",
        "fletplus profile --limit 40",
        "fletplus build --target desktop",
    ):
        assert marker in result.output


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_prefixes_numeric_package_name(
    monkeypatch, watchdog_available: bool
) -> None:
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
def test_create_rejects_invalid_package_name(
    monkeypatch, watchdog_available: bool
) -> None:
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
def test_create_fails_when_target_exists_as_file(
    monkeypatch, watchdog_available: bool
) -> None:
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
def test_create_allows_existing_empty_directory(
    monkeypatch, watchdog_available: bool
) -> None:
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
def test_create_fails_when_target_directory_is_not_empty(
    monkeypatch, watchdog_available: bool
) -> None:
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

    monkeypatch.setattr(
        cli_main, "_launch_flet_process", lambda *args, **kwargs: _FakeProcess()
    )
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
    monkeypatch.setattr(
        cli_main, "_launch_flet_process", lambda *args, **kwargs: _FakeProcess()
    )
    monkeypatch.setattr(cli_main, "_stop_process", lambda process: None)

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        app_file = base / "src" / "main.py"
        app_file.parent.mkdir(parents=True, exist_ok=True)
        app_file.write_text("print('hola')", encoding="utf-8")

        result = runner.invoke(cli_main.app, ["run", "--watch", str(base)])

    assert result.exit_code != 0
    assert "código 3" in result.output


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_web_template_generates_configured_pwa_files(
    monkeypatch, watchdog_available: bool
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(app, ["create", "Mi Web", "--template", "web"])

        assert result.exit_code == 0, result.output
        project = base / "Mi Web"
        manifest = (project / "web" / "manifest.json").read_text(encoding="utf-8")
        service_worker = (project / "web" / "service_worker.js").read_text(
            encoding="utf-8"
        )
        theme_py = (project / "src" / "frontend" / "theme.py").read_text(
            encoding="utf-8"
        )

    assert '"name": "Mi Web"' in manifest
    assert '"display": "standalone"' in manifest
    assert "mi_web-fletplus-v1" in service_worker
    assert "FrontEndConfig.from_pyproject" in theme_py
    assert "_find_pyproject" in theme_py


TEMPLATE_NAMES = ("app", "web", "desktop", "mobile")
COMMON_TEMPLATE_PATHS = (
    "src/frontend/config.py",
    "src/frontend/theme.py",
    "src/frontend/layout.py",
    "src/frontend/routes.py",
    "src/frontend/assets.py",
    "README.md",
    "requirements.txt",
    "pyproject.toml",
)
COMMON_LAYOUT_HELPERS = (
    "active_profile",
    "orientation",
    "spacing",
    "max_width_container",
    "responsive_shell",
)
PLATFORM_LAYOUT_HELPERS = ("density", "safe_padding")


def _template_root() -> Path:
    return Path("fletplus/cli/templates")


def _defined_functions(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _assert_minimal_template_contract(
    project_root: Path, *, template_name: str
) -> None:
    for relative_path in COMMON_TEMPLATE_PATHS:
        assert (
            project_root / relative_path
        ).is_file(), f"{template_name}: falta {relative_path}"

    layout_functions = _defined_functions(
        project_root / "src" / "frontend" / "layout.py"
    )
    expected_helpers = set(COMMON_LAYOUT_HELPERS)
    # Tras la unificación de plantillas, `app` mantiene la misma interfaz completa
    # que las plantillas específicas de plataforma para poder alternar target sin
    # cambiar imports ni helpers consumidos por la app generada.
    expected_helpers.update(PLATFORM_LAYOUT_HELPERS)
    assert expected_helpers <= layout_functions, (
        f"{template_name}: helpers ausentes "
        f"{sorted(expected_helpers - layout_functions)}"
    )


def test_frontend_template_files_have_common_minimal_contract() -> None:
    template_root = _template_root()

    for template_name in TEMPLATE_NAMES:
        _assert_minimal_template_contract(
            template_root / template_name, template_name=template_name
        )


def test_frontend_template_layout_helpers_have_unified_contract() -> None:
    template_root = _template_root()

    for template_name in TEMPLATE_NAMES:
        layout_py = template_root / template_name / "src" / "frontend" / "layout.py"
        layout_functions = _defined_functions(layout_py)
        assert set(COMMON_LAYOUT_HELPERS) <= layout_functions, template_name
        assert set(PLATFORM_LAYOUT_HELPERS) <= layout_functions, (
            f"{template_name}: la interfaz de layout debe incluir helpers de "
            "plataforma después de la unificación"
        )


@pytest.mark.parametrize("watchdog_available", [True, False])
@pytest.mark.parametrize("target_name", TEMPLATE_NAMES)
def test_create_target_generates_common_template_contract(
    monkeypatch, watchdog_available: bool, target_name: str
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(
            app, ["create", f"demo_{target_name}", "--target", target_name]
        )

        assert result.exit_code == 0, result.output
        _assert_minimal_template_contract(
            base / f"demo_{target_name}", template_name=target_name
        )


def test_frontend_template_static_structure_is_consistent() -> None:
    template_root = Path("fletplus/cli/templates")
    expected_frontend_files = {
        "__init__.py",
        "config.py",
        "theme.py",
        "layout.py",
        "assets.py",
        "routes.py",
    }

    for template_name in ("app", "web", "desktop", "mobile"):
        src = template_root / template_name / "src"
        frontend_dir = src / "frontend"
        assert frontend_dir.is_dir(), template_name
        assert {
            path.name for path in frontend_dir.glob("*.py")
        } == expected_frontend_files
        for legacy_module in ("theme.py", "layout.py", "assets.py", "routes.py"):
            assert not (
                src / legacy_module
            ).exists(), f"{template_name}: {legacy_module}"

        main_py = (src / "main.py").read_text(encoding="utf-8")
        assert "from frontend.theme import create_frontend_config" in main_py
        assert "from frontend.layout import responsive_shell, spacing" in main_py
        assert "from frontend.routes import render_initial_route" in main_py

        readme = (template_root / template_name / "README.md").read_text(
            encoding="utf-8"
        )
        for expected_doc in (
            "src/frontend/config.py",
            "colores",
            "Fuentes",
            "Densidad visual",
            "Assets",
            "Rutas",
        ):
            assert expected_doc in readme


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_injects_generation_options_into_frontend_files(
    monkeypatch, watchdog_available: bool
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(
            app,
            [
                "create",
                "Studio",
                "--target",
                "web",
                "--preset",
                "landing",
                "--palette",
                "sunset",
                "--theme-mode",
                "dark",
                "--font",
                "Inter",
                "--layout-density",
                "spacious",
            ],
        )

        assert result.exit_code == 0, result.output
        project = base / "Studio"
        pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
        config = (project / "src" / "frontend" / "config.py").read_text(
            encoding="utf-8"
        )
        readme = (project / "README.md").read_text(encoding="utf-8")

    assert 'default_target = "web"' in pyproject
    assert 'palette = "sunset"' in pyproject
    assert 'mode = "dark"' in pyproject
    assert 'font_family = "Inter"' in pyproject
    assert 'layout_density = "spacious"' in pyproject
    assert 'preset = "landing"' in pyproject
    assert 'target = "web"' in pyproject
    assert 'PALETTE_NAME = "sunset"' in config
    assert 'PALETTE_MODE = "dark"' in config
    assert 'FONT_FAMILY = "Inter"' in config
    assert 'LAYOUT_DENSITY = "spacious"' in config
    assert 'TARGET_NAME = "web"' in config
    assert "--target web --preset landing --palette sunset" in readme


@pytest.mark.parametrize("watchdog_available", [True, False])
def test_create_supports_system_theme_mode(
    monkeypatch, watchdog_available: bool
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    with runner.isolated_filesystem() as temp_dir:
        base = Path(temp_dir)
        result = runner.invoke(
            app, ["create", "MobileSys", "--target", "mobile", "--theme-mode", "system"]
        )

        assert result.exit_code == 0, result.output
        pyproject = (base / "MobileSys" / "pyproject.toml").read_text(encoding="utf-8")
        config = (base / "MobileSys" / "src" / "frontend" / "config.py").read_text(
            encoding="utf-8"
        )

    assert 'mode = "system"' in pyproject
    assert 'target = "mobile"' in pyproject
    assert 'PALETTE_MODE = "system"' in config


@pytest.mark.parametrize("watchdog_available", [True, False])
@pytest.mark.parametrize("target_name", ["web", "desktop", "mobile", "app", "all"])
def test_frontend_tasks_lists_base_tasks_for_supported_targets(
    monkeypatch, watchdog_available: bool, target_name: str
) -> None:
    _configure_watchdog(monkeypatch, available=watchdog_available)
    app = _load_cli_app()
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "frontend-tasks",
            "--target",
            target_name,
            "--palette",
            "zenith",
            "--font",
            "Inter",
            "--layout-density",
            "compact",
        ],
    )

    assert result.exit_code == 0, result.output
    assert f"Target: {target_name}" in result.output
    assert "Paleta: zenith" in result.output
    assert "Fuente: Inter" in result.output
    assert "Densidad: compact" in result.output
    for task_name in ("paleta", "pantalla", "diseño", "fuentes"):
        assert f"- {task_name} [{target_name}]" in result.output
    assert "Funciones:" in result.output
    assert "Tokens principales:" in result.output
