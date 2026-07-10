from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from fletplus.cli.installer import InstallerError, generate_installer
from fletplus.cli.main import app


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.py").write_text("print('demo')\n", encoding="utf-8")
    (project / "requirements.txt").write_text("fletplus\n", encoding="utf-8")
    (project / "assets").mkdir()
    return project


def test_generate_all_installers_without_executing(tmp_path: Path) -> None:
    project = _project(tmp_path)
    output = tmp_path / "installers"

    generated = generate_installer(
        project,
        "all",
        output,
        {"app": "src/main.py", "assets_dir": "assets", "include_bat": True},
    )

    paths = {item.path.relative_to(output).as_posix() for item in generated}
    assert paths == {
        "windows/install.ps1",
        "windows/install.bat",
        "macos/install.command",
        "linux/install.sh",
        "web/deploy_static.sh",
    }
    assert '-m venv "$VENV_DIR"' in (output / "linux" / "install.sh").read_text(
        encoding="utf-8"
    )
    assert "Distribución detectada" in (output / "linux" / "install.sh").read_text(
        encoding="utf-8"
    )
    web_script = (output / "web" / "deploy_static.sh").read_text(encoding="utf-8")
    linux_script = (output / "linux" / "install.sh").read_text(encoding="utf-8")
    windows_script = (output / "windows" / "install.ps1").read_text(encoding="utf-8")
    assert "flet build web" in web_script
    assert ".[web-deploy]" in web_script
    assert ".[desktop-build]" in linux_script
    assert ".[desktop-build]" in windows_script
    assert "Remove-Item" not in (output / "windows" / "install.ps1").read_text(
        encoding="utf-8"
    )


def test_generate_installer_rejects_unsafe_relative_paths(tmp_path: Path) -> None:
    project = _project(tmp_path)

    try:
        generate_installer(project, "linux", tmp_path / "out", {"app": "../main.py"})
    except InstallerError as exc:
        assert "ruta relativa segura" in str(exc)
    else:  # pragma: no cover - protección del test
        raise AssertionError("InstallerError no fue lanzado")


def test_cli_installer_command_generates_selected_target(tmp_path: Path) -> None:
    project = _project(tmp_path)
    output = tmp_path / "generated"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "installer",
            "--target",
            "web",
            "--project-dir",
            str(project),
            "--output-dir",
            str(output),
            "--app",
            "src/main.py",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output / "web" / "deploy_static.sh").is_file()
    assert "Scripts generados" in result.output
