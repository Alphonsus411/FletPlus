"""Generación segura de instaladores auxiliares para proyectos FletPlus."""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

SUPPORTED_TARGETS = ("windows", "macos", "linux", "web")
_SAFE_RELATIVE_PATH = re.compile(r"^[A-Za-z0-9_./\\-]+$")


@dataclass(frozen=True)
class GeneratedInstaller:
    """Archivo generado por :func:`generate_installer`."""

    target_os: str
    path: Path


class InstallerError(ValueError):
    """Error de validación al generar scripts de instalación."""


def _resolve_directory(path: Path, *, must_exist: bool) -> Path:
    resolved = path.expanduser().resolve()
    if must_exist and not resolved.is_dir():
        raise InstallerError(f"La ruta debe existir y ser un directorio: {resolved}")
    if not must_exist:
        resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _validate_relative_path(value: str, option_name: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise InstallerError(f"{option_name} debe ser una ruta relativa segura.")
    normalized = candidate.as_posix()
    if not normalized or not _SAFE_RELATIVE_PATH.match(normalized):
        raise InstallerError(
            f"{option_name} solo puede contener letras, números, '.', '_', '-' y separadores."
        )
    return normalized


def _validate_options(options: Mapping[str, object] | None) -> dict[str, object]:
    raw_options = dict(options or {})
    app_path = _validate_relative_path(
        str(raw_options.get("app", "src/main.py")), "app"
    )
    assets_dir = _validate_relative_path(
        str(raw_options.get("assets_dir", "assets")), "assets_dir"
    )
    package_spec = str(raw_options.get("package_spec", "."))
    if package_spec != ".":
        package_spec = _validate_relative_path(package_spec, "package_spec")
    return {
        "app": app_path,
        "assets_dir": assets_dir,
        "package_spec": package_spec,
        "include_bat": bool(raw_options.get("include_bat", False)),
    }


def _targets_for(target_os: str) -> Sequence[str]:
    normalized = target_os.lower()
    if normalized == "all":
        return SUPPORTED_TARGETS
    if normalized not in SUPPORTED_TARGETS:
        raise InstallerError(
            "target_os debe ser uno de: windows, macos, linux, web o all."
        )
    return (normalized,)


def _write_script(path: Path, content: str, *, executable: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _common_header(project_dir: Path) -> str:
    return (
        "# Generado por fletplus installer.\n"
        "# Revisa el contenido antes de ejecutarlo en entornos productivos.\n"
        f"# Proyecto origen: {project_dir}\n"
    )


def _sh_single_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _windows_ps1(project_dir: Path, options: Mapping[str, object]) -> str:
    app = options["app"]
    assets = options["assets_dir"]
    package_spec = options["package_spec"]
    return f"""{_common_header(project_dir)}$ErrorActionPreference = "Stop"
$ProjectDir = {_ps_single_quote(str(project_dir))}
Set-Location $ProjectDir
$VenvDir = Join-Path $ProjectDir ".venv"
$Python = Join-Path $VenvDir "Scripts\\python.exe"
if (-not (Test-Path $Python)) {{
    py -3 -m venv $VenvDir
}}
& $Python -m pip install --upgrade pip
if (Test-Path (Join-Path $ProjectDir "requirements.txt")) {{
    & $Python -m pip install -r (Join-Path $ProjectDir "requirements.txt")
}}
if (Test-Path (Join-Path $ProjectDir "dist")) {{
    $Wheel = Get-ChildItem -Path (Join-Path $ProjectDir "dist") -Filter "*.whl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($Wheel) {{ & $Python -m pip install $Wheel.FullName }} else {{ & $Python -m pip install "{package_spec}" }}
}} else {{
    & $Python -m pip install "{package_spec}"
}}
if (Test-Path (Join-Path $ProjectDir "{assets}")) {{
    New-Item -ItemType Directory -Force -Path (Join-Path $ProjectDir "build\\runtime_assets") | Out-Null
    Copy-Item -Path (Join-Path $ProjectDir "{assets}\\*") -Destination (Join-Path $ProjectDir "build\\runtime_assets") -Recurse -Force
}}
& $Python -m flet run (Join-Path $ProjectDir "{app}")
"""


def _windows_bat() -> str:
    return """@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
endlocal
"""


def _posix_script(project_dir: Path, options: Mapping[str, object], target: str) -> str:
    app = options["app"]
    assets = options["assets_dir"]
    package_spec = options["package_spec"]
    distro = ""
    if target == "linux":
        distro = '\nif [ -r /etc/os-release ]; then . /etc/os-release; echo "Distribución detectada: ${PRETTY_NAME:-$ID}"; fi\n'
    return f"""#!/usr/bin/env sh
{_common_header(project_dir)}set -eu
PROJECT_DIR={_sh_single_quote(str(project_dir))}
cd "$PROJECT_DIR"{distro}
PYTHON_BIN=${{PYTHON:-python3}}
VENV_DIR="$PROJECT_DIR/.venv"
if [ ! -x "$VENV_DIR/bin/python" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
PY="$VENV_DIR/bin/python"
"$PY" -m pip install --upgrade pip
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    "$PY" -m pip install -r "$PROJECT_DIR/requirements.txt"
fi
WHEEL=$(find "$PROJECT_DIR/dist" -maxdepth 1 -name '*.whl' -type f 2>/dev/null | sort | tail -n 1 || true)
if [ -n "$WHEEL" ]; then
    "$PY" -m pip install "$WHEEL"
else
    "$PY" -m pip install "{package_spec}"
fi
if [ -d "$PROJECT_DIR/{assets}" ]; then
    mkdir -p "$PROJECT_DIR/build/runtime_assets"
    cp -R "$PROJECT_DIR/{assets}/." "$PROJECT_DIR/build/runtime_assets/"
fi
"$PY" -m flet run "$PROJECT_DIR/{app}"
"""


def _web_script(project_dir: Path, options: Mapping[str, object]) -> str:
    package_spec = options["package_spec"]
    return f"""#!/usr/bin/env sh
{_common_header(project_dir)}set -eu
PROJECT_DIR={_sh_single_quote(str(project_dir))}
cd "$PROJECT_DIR"
PYTHON_BIN=${{PYTHON:-python3}}
VENV_DIR="$PROJECT_DIR/.venv"
if [ ! -x "$VENV_DIR/bin/python" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
PY="$VENV_DIR/bin/python"
"$PY" -m pip install --upgrade pip
if [ -f "$PROJECT_DIR/requirements.txt" ]; then "$PY" -m pip install -r "$PROJECT_DIR/requirements.txt"; fi
"$PY" -m pip install "{package_spec}"
"$PY" -m flet build web
printf '%s\n' "Artefactos web generados. Sirve dist/ o build/web con un servidor estático seguro."
printf '%s\n' "Ejemplo local: python -m http.server --directory dist 8000"
"""


def generate_installer(
    project_dir: Path | str,
    target_os: str,
    output_dir: Path | str,
    options: Mapping[str, object] | None = None,
) -> list[GeneratedInstaller]:
    """Genera scripts de instalación sin ejecutarlos.

    La función valida rutas, limita los destinos soportados y solo escribe scripts
    con operaciones no destructivas: creación de virtualenv, instalación de
    dependencias/paquete, copia de assets y arranque o build de la app.
    """

    project_path = _resolve_directory(Path(project_dir), must_exist=True)
    output_path = _resolve_directory(Path(output_dir), must_exist=False)
    safe_options = _validate_options(options)

    generated: list[GeneratedInstaller] = []
    for target in _targets_for(target_os):
        target_dir = output_path / target
        if target == "windows":
            generated.append(
                GeneratedInstaller(
                    target,
                    _write_script(
                        target_dir / "install.ps1",
                        _windows_ps1(project_path, safe_options),
                    ),
                )
            )
            if safe_options["include_bat"]:
                generated.append(
                    GeneratedInstaller(
                        target,
                        _write_script(target_dir / "install.bat", _windows_bat()),
                    )
                )
        elif target == "web":
            generated.append(
                GeneratedInstaller(
                    target,
                    _write_script(
                        target_dir / "deploy_static.sh",
                        _web_script(project_path, safe_options),
                        executable=os.name != "nt",
                    ),
                )
            )
        else:
            filename = "install.command" if target == "macos" else "install.sh"
            generated.append(
                GeneratedInstaller(
                    target,
                    _write_script(
                        target_dir / filename,
                        _posix_script(project_path, safe_options, target),
                        executable=os.name != "nt",
                    ),
                )
            )
    return generated
