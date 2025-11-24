"""Infraestructura de compilación para el comando ``fletplus build``."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, List

import click

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - compatibilidad
    import tomli as tomllib  # type: ignore


class PackagingError(RuntimeError):
    """Error de alto nivel al empaquetar la aplicación."""


class BuildTarget(str, Enum):
    """Objetivos soportados por el comando de compilación."""

    WEB = "web"
    DESKTOP = "desktop"
    MOBILE = "mobile"

    @classmethod
    def parse_option(cls, value: str) -> List["BuildTarget"]:
        if value == "all":
            return list(cls)
        try:
            return [cls(value)]
        except ValueError as exc:  # pragma: no cover - validado por Click
            raise PackagingError(str(exc)) from exc


@dataclass(slots=True)
class BuildMetadata:
    name: str
    version: str
    author: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, str]:
        data = {"name": self.name, "version": self.version}
        if self.author:
            data["author"] = self.author
        if self.description:
            data["description"] = self.description
        return data


@dataclass(slots=True)
class BuildContext:
    """Información común compartida por los adaptadores."""

    project_dir: Path
    app_path: Path
    dist_dir: Path
    build_dir: Path
    metadata: BuildMetadata
    assets_dir: Path | None
    icon_path: Path | None

    @classmethod
    def from_project(cls, project_dir: Path, app_path: Path) -> "BuildContext":
        project_dir = project_dir.resolve()
        if not project_dir.exists():
            raise PackagingError(f"No se encontró el proyecto en {project_dir}.")

        app_path = app_path if app_path.is_absolute() else project_dir / app_path
        if not app_path.exists():
            raise PackagingError(f"No se encontró la aplicación principal: {app_path}.")

        dist_dir = project_dir / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        build_dir = project_dir / "build"
        build_dir.mkdir(parents=True, exist_ok=True)

        metadata = _load_metadata(project_dir)
        assets_dir = _detect_assets(project_dir)
        icon_path = _detect_icon(project_dir, assets_dir)

        return cls(
            project_dir=project_dir,
            app_path=app_path,
            dist_dir=dist_dir,
            build_dir=build_dir,
            metadata=metadata,
            assets_dir=assets_dir,
            icon_path=icon_path,
        )


def _load_metadata(project_dir: Path) -> BuildMetadata:
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        project_data = data.get("project", {}) if isinstance(data, dict) else {}
    else:
        project_data = {}

    name = project_data.get("name") or project_dir.name
    version = project_data.get("version", "0.0.0")
    author = None
    authors = project_data.get("authors")
    if isinstance(authors, list) and authors:
        first = authors[0]
        if isinstance(first, dict):
            author = first.get("name")
        elif isinstance(first, str):
            author = first
    description = project_data.get("description")

    return BuildMetadata(name=name, version=version, author=author, description=description)


def _detect_assets(project_dir: Path) -> Path | None:
    candidates = [project_dir / "assets", project_dir / "static"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _detect_icon(project_dir: Path, assets_dir: Path | None) -> Path | None:
    candidates = []
    if assets_dir:
        candidates.append(assets_dir / "icon.png")
        candidates.append(assets_dir / "icons" / "app.png")
    candidates.extend([project_dir / "icon.png", project_dir / "app.png"])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _copy_assets(source: Path | None, destination: Path) -> None:
    if not source or not source.exists():
        return
    target = destination / source.name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def _copy_icon(icon_path: Path | None, destination: Path) -> Path | None:
    if not icon_path or not icon_path.exists():
        return None
    destination.mkdir(parents=True, exist_ok=True)
    target_icon = destination / icon_path.name
    shutil.copy2(icon_path, target_icon)
    return target_icon


def _write_metadata(metadata: BuildMetadata, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    metadata_path = destination / "metadata.json"
    metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2), encoding="utf-8")
    return metadata_path


def _run_command(command: List[str], cwd: Path | None = None) -> None:
    click.echo(f"Ejecutando: {' '.join(command)}")
    try:
        subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)
    except FileNotFoundError as exc:  # pragma: no cover - depende del entorno
        missing_tool = command[0]
        raise PackagingError(
            f"No se encontró la herramienta requerida: {missing_tool}. "
            "Asegúrate de que esté instalada y disponible en el PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:  # pragma: no cover - manejado en adaptador
        raise PackagingError(f"El comando {' '.join(command)} falló con código {exc.returncode}") from exc


class _BaseAdapter:
    target: BuildTarget

    def __init__(self, context: BuildContext) -> None:
        self.context = context
        self.output_dir = context.dist_dir / self.target.value
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir = context.build_dir / self.target.value
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def prepare(self) -> dict[str, Path | None]:
        metadata_path = _write_metadata(self.context.metadata, self.staging_dir)
        _copy_assets(self.context.assets_dir, self.staging_dir)
        icon_target = _copy_icon(self.context.icon_path, self.staging_dir)
        return {"metadata": metadata_path, "icon": icon_target}

    def build(self, prepared: dict[str, Path | None]) -> None:
        raise NotImplementedError

    def run(self) -> Path:
        prepared = self.prepare()
        self.build(prepared)
        return self.output_dir


class WebAdapter(_BaseAdapter):
    target = BuildTarget.WEB

    def build(self, prepared: dict[str, Path | None]) -> None:  # pragma: no cover - invocado por run()
        command = [
            sys.executable,
            "-m",
            "flet",
            "build",
            "web",
            "--output",
            str(self.output_dir),
            str(self.context.app_path),
        ]
        _run_command(command, cwd=self.context.project_dir)


class DesktopAdapter(_BaseAdapter):
    target = BuildTarget.DESKTOP

    def build(self, prepared: dict[str, Path | None]) -> None:
        add_data_args: list[str] = []
        assets_dir = self.context.assets_dir
        if assets_dir and assets_dir.exists():
            staging_assets = self.staging_dir / assets_dir.name
            if staging_assets.exists():
                add_data_args.extend(
                    [
                        "--add-data",
                        f"{staging_assets}{os.pathsep}{assets_dir.name}",
                    ]
                )

        icon_arg: list[str] = []
        icon_path = prepared.get("icon")
        if icon_path:
            icon_arg = ["--icon", str(icon_path)]

        command = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--name",
            self.context.metadata.name,
            "--distpath",
            str(self.output_dir),
            "--workpath",
            str(self.context.build_dir / "pyinstaller"),
            "--specpath",
            str(self.context.build_dir / "pyinstaller"),
            *icon_arg,
            *add_data_args,
            str(self.context.app_path),
        ]
        _run_command(command, cwd=self.context.project_dir)


class MobileAdapter(_BaseAdapter):
    target = BuildTarget.MOBILE

    def build(self, prepared: dict[str, Path | None]) -> None:
        icon_path = prepared.get("icon")
        metadata_path = prepared.get("metadata")

        env = os.environ.copy()
        if metadata_path:
            env["FLETPLUS_METADATA"] = str(metadata_path)
        if icon_path:
            env["FLETPLUS_ICON"] = str(icon_path)

        command = [
            "briefcase",
            "package",
            "android",
            "--no-input",
            "--output",
            str(self.output_dir),
        ]
        click.echo("Preparando paquete móvil (android)")
        try:
            subprocess.run(command, cwd=str(self.context.project_dir), check=True, env=env)
        except FileNotFoundError as exc:  # pragma: no cover - depende del entorno
            missing_tool = command[0]
            raise PackagingError(
                f"No se encontró la herramienta requerida: {missing_tool}. "
                "Asegúrate de que esté instalada y disponible en el PATH."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise PackagingError(
                f"El comando {' '.join(command)} falló con código {exc.returncode}"
            ) from exc


def create_adapter(target: BuildTarget, context: BuildContext) -> _BaseAdapter:
    if target is BuildTarget.WEB:
        return WebAdapter(context)
    if target is BuildTarget.DESKTOP:
        return DesktopAdapter(context)
    if target is BuildTarget.MOBILE:
        return MobileAdapter(context)
    raise PackagingError(f"Objetivo no soportado: {target}")


@dataclass(slots=True)
class BuildReport:
    target: BuildTarget
    success: bool
    message: str
    output_dir: Path | None = None


class BuildManager:
    """Gestiona la ejecución de los adaptadores para cada objetivo."""

    def __init__(self, context: BuildContext) -> None:
        self.context = context

    def build(self, targets: Iterable[BuildTarget]) -> List[BuildReport]:
        reports: List[BuildReport] = []
        for target in targets:
            adapter = create_adapter(target, self.context)
            try:
                output_dir = adapter.run()
                reports.append(
                    BuildReport(
                        target=target,
                        success=True,
                        message=f"Artefactos disponibles en {output_dir}",
                        output_dir=output_dir,
                    )
                )
            except PackagingError as exc:
                reports.append(BuildReport(target=target, success=False, message=str(exc)))
        return reports


def run_build(project_dir: Path, app_path: Path, target: str) -> List[BuildReport]:
    context = BuildContext.from_project(project_dir, app_path)
    targets = BuildTarget.parse_option(target)
    manager = BuildManager(context)
    return manager.build(targets)

