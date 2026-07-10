"""Infraestructura de compilación para el comando ``fletplus build``."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, List

import click

from fletplus.rendering import RenderStrategy, strategy_for_target

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - compatibilidad
    import tomli as tomllib  # type: ignore


class PackagingError(RuntimeError):
    """Error de alto nivel al empaquetar la aplicación."""


DEFAULT_BUILD_TIMEOUT_SECONDS = 900.0

# Variables base permitidas para cualquier comando de build.
BUILD_ENV_BASE_WHITELIST = (
    "PATH",
    "SystemRoot",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "TEMP",
    "TMP",
    "HOME",
    "USERPROFILE",
)

# Perfiles mínimos por tipo de comando para evitar sobreexposición del entorno.
BUILD_ENV_PROFILES: dict[str, tuple[str, ...]] = {
    "flet_build": (
        *BUILD_ENV_BASE_WHITELIST,
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONUTF8",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONUNBUFFERED",
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
    ),
    "flet_mobile": (
        *BUILD_ENV_BASE_WHITELIST,
        "APPDATA",
        "LOCALAPPDATA",
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONUTF8",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONUNBUFFERED",
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
        "FLETPLUS_METADATA",
        "FLETPLUS_ICON",
        "FLETPLUS_PACKAGE",
    ),
    "pyinstaller": (
        *BUILD_ENV_BASE_WHITELIST,
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONUTF8",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONUNBUFFERED",
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
    ),
}


class BuildTarget(str, Enum):
    """Objetivos soportados por el comando de compilación."""

    WEB = "web"
    DESKTOP = "desktop"
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID_APK = "android-apk"
    ANDROID_AAB = "android-aab"
    IOS = "ios"

    @classmethod
    def parse_option(cls, value: str) -> List["BuildTarget"]:
        normalized = value.lower()
        aliases = {
            "mobile": cls.ANDROID_APK,
            "apk": cls.ANDROID_APK,
            "aab": cls.ANDROID_AAB,
        }
        if normalized == "all":
            return [cls.WEB, cls.DESKTOP, cls.ANDROID_APK]
        if normalized == "desktop-all":
            return [cls.WINDOWS, cls.MACOS, cls.LINUX]
        if normalized == "desktop":
            return [cls(_desktop_platform_target())]
        if normalized in aliases:
            return [aliases[normalized]]
        try:
            return [cls(normalized)]
        except ValueError as exc:  # pragma: no cover - validado por Click
            raise PackagingError(str(exc)) from exc


@dataclass(slots=True)
class FletPlusProjectConfig:
    """Configuración leída de ``[tool.fletplus]`` en proyectos generados."""

    app_path: Path | None = None
    default_target: str | None = None
    assets_dir: Path | None = None
    icon_path: Path | None = None
    backend_app: Path | None = None
    frontend_app: Path | None = None
    docs_dir: Path | None = None
    config_dir: Path | None = None
    deployment_dir: Path | None = None
    include_python_packages: list[Path] = field(default_factory=list)
    build_timeout: float | None = None
    frontend: dict[str, Any] = field(default_factory=dict)
    web: dict[str, Any] = field(default_factory=dict)
    desktop: dict[str, Any] = field(default_factory=dict)
    mobile: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BuildMetadata:
    """Metadatos del proyecto normalizados para compilación.

    El nombre se normaliza en `_load_metadata` para usar solo letras, números,
    guiones y guiones bajos; los separadores de ruta (`/`, `\\`) y espacios se
    reemplazan por guiones, y el resto de caracteres inseguros se elimina.
    """

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
    build_timeout: float
    project_config: FletPlusProjectConfig
    render_strategy: RenderStrategy | None = None

    @classmethod
    def from_project(
        cls,
        project_dir: Path,
        app_path: Path,
        build_timeout: float = DEFAULT_BUILD_TIMEOUT_SECONDS,
    ) -> "BuildContext":
        return FullStackBuildContext.from_project(project_dir, app_path, build_timeout)


@dataclass(slots=True)
class FullStackBuildContext(BuildContext):
    """Contexto ampliado para preparar proyectos full-stack antes del build."""

    backend_app: Path | None = None
    frontend_app: Path | None = None
    docs_dir: Path | None = None
    config_dir: Path | None = None
    deployment_dir: Path | None = None
    include_python_packages: list[Path] = field(default_factory=list)

    @classmethod
    def from_project(
        cls,
        project_dir: Path,
        app_path: Path,
        build_timeout: float = DEFAULT_BUILD_TIMEOUT_SECONDS,
    ) -> "FullStackBuildContext":
        project_dir = project_dir.resolve()
        if not project_dir.exists():
            raise PackagingError(f"No se encontró el proyecto en {project_dir}.")

        project_config = _load_fletplus_config(project_dir)
        if str(app_path) == "src/main.py" and project_config.app_path is not None:
            app_path = project_config.app_path
        app_path = app_path if app_path.is_absolute() else project_dir / app_path
        if not app_path.exists():
            raise PackagingError(f"No se encontró la aplicación principal: {app_path}.")
        if not app_path.is_file():
            raise PackagingError(
                f"La ruta de la aplicación principal debe ser un archivo: {app_path}."
            )

        dist_dir = project_dir / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        build_dir = project_dir / "build"
        build_dir.mkdir(parents=True, exist_ok=True)

        metadata = _load_metadata(project_dir)
        assets_dir = _detect_assets(project_dir, project_config)
        icon_path = _detect_icon(project_dir, assets_dir, project_config)
        effective_timeout = project_config.build_timeout or build_timeout

        return cls(
            project_dir=project_dir,
            app_path=app_path,
            dist_dir=dist_dir,
            build_dir=build_dir,
            metadata=metadata,
            assets_dir=assets_dir,
            icon_path=icon_path,
            build_timeout=effective_timeout,
            project_config=project_config,
            backend_app=_resolve_project_path(project_dir, project_config.backend_app),
            frontend_app=_resolve_project_path(
                project_dir, project_config.frontend_app
            ),
            docs_dir=_resolve_project_path(project_dir, project_config.docs_dir),
            config_dir=_resolve_project_path(project_dir, project_config.config_dir),
            deployment_dir=_resolve_project_path(
                project_dir, project_config.deployment_dir
            ),
            include_python_packages=[
                resolved
                for package in project_config.include_python_packages
                if (resolved := _resolve_project_path(project_dir, package)) is not None
            ],
        )


def _load_pyproject(project_dir: Path) -> dict[str, Any]:
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.exists():
        return {}
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))


def _load_fletplus_config(project_dir: Path) -> FletPlusProjectConfig:
    data = _load_pyproject(project_dir)
    tool_data = data.get("tool", {}) if isinstance(data, dict) else {}
    raw_config = tool_data.get("fletplus", {}) if isinstance(tool_data, dict) else {}
    if not isinstance(raw_config, dict):
        return FletPlusProjectConfig()

    def optional_path(name: str) -> Path | None:
        value = raw_config.get(name)
        if isinstance(value, str) and value.strip():
            return Path(value)
        return None

    timeout_value = raw_config.get("build_timeout")
    try:
        build_timeout = float(timeout_value) if timeout_value is not None else None
    except (TypeError, ValueError):
        raise PackagingError("[tool.fletplus].build_timeout debe ser numérico.")

    default_target = raw_config.get("default_target")

    def optional_dict(name: str) -> dict[str, Any]:
        value = raw_config.get(name, {})
        return dict(value) if isinstance(value, dict) else {}

    return FletPlusProjectConfig(
        app_path=optional_path("app"),
        default_target=default_target if isinstance(default_target, str) else None,
        assets_dir=optional_path("assets_dir"),
        icon_path=optional_path("icon"),
        backend_app=optional_path("backend_app"),
        frontend_app=optional_path("frontend_app"),
        docs_dir=optional_path("docs_dir"),
        config_dir=optional_path("config_dir"),
        deployment_dir=optional_path("deployment_dir"),
        include_python_packages=_parse_python_packages(raw_config),
        build_timeout=build_timeout,
        frontend=optional_dict("frontend"),
        web=optional_dict("web"),
        desktop=optional_dict("desktop"),
        mobile=optional_dict("mobile"),
    )


def _parse_python_packages(raw_config: dict[str, Any]) -> list[Path]:
    value = raw_config.get("include_python_packages", [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise PackagingError(
            "[tool.fletplus].include_python_packages debe ser una lista de rutas."
        )
    return [Path(item) for item in value]


def _load_metadata(project_dir: Path) -> BuildMetadata:
    data = _load_pyproject(project_dir)
    project_data = data.get("project", {}) if isinstance(data, dict) else {}

    raw_name = project_data.get("name") or project_dir.name
    name = _normalize_build_name(raw_name)
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

    return BuildMetadata(
        name=name, version=version, author=author, description=description
    )


def _normalize_build_name(value: str) -> str:
    normalized = re.sub(r"[\\/\s]+", "-", value)
    normalized = re.sub(r"[^A-Za-z0-9_-]", "", normalized)
    normalized = normalized.strip("-_")
    return normalized or "app"


def _resolve_project_path(project_dir: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else project_dir / path


def _detect_assets(
    project_dir: Path, config: FletPlusProjectConfig | None = None
) -> Path | None:
    configured_assets = _resolve_project_path(
        project_dir, config.assets_dir if config else None
    )
    candidates = [configured_assets] if configured_assets else []
    candidates.extend([project_dir / "assets", project_dir / "static"])
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _detect_icon(
    project_dir: Path,
    assets_dir: Path | None,
    config: FletPlusProjectConfig | None = None,
) -> Path | None:
    configured_icon = _resolve_project_path(
        project_dir, config.icon_path if config else None
    )
    candidates = [configured_icon] if configured_icon else []
    if assets_dir:
        candidates.append(assets_dir / "icon.png")
        candidates.append(assets_dir / "icons" / "app.png")
    candidates.extend([project_dir / "icon.png", project_dir / "app.png"])
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _copy_assets(source: Path | None, destination: Path) -> None:
    if not source or not source.exists():
        return
    target = destination / source.name
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    for root, dirs, files in os.walk(source, followlinks=False):
        root_path = Path(root)
        relative_root = root_path.relative_to(source)
        target_root = target / relative_root
        target_root.mkdir(parents=True, exist_ok=True)

        for dirname in list(dirs):
            source_dir = root_path / dirname
            if source_dir.is_symlink():
                click.echo(f"Advertencia: se omitió el enlace simbólico {source_dir}.")
                dirs.remove(dirname)

        for filename in files:
            source_file = root_path / filename
            if source_file.is_symlink():
                click.echo(f"Advertencia: se omitió el enlace simbólico {source_file}.")
                continue
            shutil.copy2(source_file, target_root / filename)


def _copy_path(source: Path | None, destination: Path, label: str) -> Path | None:
    if source is None or not source.exists():
        return None
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / label
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    if source.is_dir():
        shutil.copytree(source, target, symlinks=False)
    else:
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target / source.name)
    return target


def _prepare_full_stack_components(
    context: BuildContext, destination: Path
) -> dict[str, Path | None]:
    if not isinstance(context, FullStackBuildContext):
        return {}
    prepared: dict[str, Path | None] = {
        "backend": _copy_path(context.backend_app, destination, "backend"),
        "frontend": _copy_path(context.frontend_app, destination, "frontend"),
        "docs": _copy_path(context.docs_dir, destination, "docs"),
        "config": _copy_path(context.config_dir, destination, "config"),
        "deployment": _copy_path(context.deployment_dir, destination, "deployment"),
    }
    packages_dir = destination / "python-packages"
    copied_packages: list[str] = []
    for package in context.include_python_packages:
        copied = _copy_path(package, packages_dir, package.name)
        if copied is not None:
            copied_packages.append(str(copied))
    if copied_packages:
        prepared["python_packages"] = packages_dir
        manifest = destination / "fullstack.json"
        manifest.write_text(
            json.dumps({"python_packages": copied_packages}, indent=2),
            encoding="utf-8",
        )
        prepared["manifest"] = manifest
    return prepared


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


def _run_command(
    command: List[str],
    *,
    cwd: Path | None = None,
    timeout: float | None = None,
    env_overrides: dict[str, str] | None = None,
    env_profile: str,
) -> None:
    click.echo(f"Ejecutando: {' '.join(command)}")
    whitelist = BUILD_ENV_PROFILES.get(env_profile)
    if whitelist is None:
        raise PackagingError(f"Perfil de entorno no soportado: {env_profile}.")

    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    try:
        from fletplus.utils.safe_subprocess import safe_run

        safe_run(
            command,
            cwd=str(cwd) if cwd else None,
            check=True,
            timeout=timeout,
            env=env,
            env_whitelist=whitelist,
        )
    except FileNotFoundError as exc:  # pragma: no cover - depende del entorno
        missing_tool = command[0]
        raise PackagingError(
            f"No se encontró la herramienta requerida: {missing_tool}. "
            "Asegúrate de que esté instalada y disponible en el PATH."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        executed_command = " ".join(str(part) for part in command)
        cwd_label = str(cwd) if cwd else os.getcwd()
        timeout_label = exc.timeout if exc.timeout is not None else timeout
        raise PackagingError(
            "El subproceso de compilación excedió el tiempo límite "
            f"({timeout_label}s, cwd={cwd_label}, comando='{executed_command}')."
        ) from exc
    except (
        subprocess.CalledProcessError
    ) as exc:  # pragma: no cover - manejado en adaptador
        executed_command = " ".join(str(part) for part in (exc.cmd or command))
        cwd_label = str(cwd) if cwd else os.getcwd()
        raise PackagingError(
            "El subproceso de compilación falló "
            f"(código={exc.returncode}, cwd={cwd_label}, comando='{executed_command}')."
        ) from exc


class _BaseAdapter:
    target: BuildTarget

    def __init__(self, context: BuildContext) -> None:
        self.context = context
        self.output_dir = context.dist_dir / self.target.value
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir = context.build_dir / self.target.value
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def prepare(self) -> dict[str, Path | str | None]:
        metadata_path = _write_metadata(self.context.metadata, self.staging_dir)
        _copy_assets(self.context.assets_dir, self.staging_dir)
        full_stack = _prepare_full_stack_components(self.context, self.staging_dir)
        icon_target = _copy_icon(self.context.icon_path, self.staging_dir)
        strategy_target = (
            "desktop" if self.target in DESKTOP_PLATFORM_TARGETS else self.target.value
        )
        strategy = strategy_for_target(strategy_target)
        self.context.render_strategy = strategy
        strategy_path = self.staging_dir / "render_strategy.json"
        strategy_path.write_text(
            json.dumps(strategy.build_metadata(), indent=2), encoding="utf-8"
        )
        return {
            "metadata": metadata_path,
            "icon": icon_target,
            "render_strategy": strategy_path,
            **full_stack,
        }

    def build(self, prepared: dict[str, Path | str | None]) -> None:
        raise NotImplementedError

    def run(self) -> Path:
        prepared = self.prepare()
        self.build(prepared)
        return self.output_dir


class WebAdapter(_BaseAdapter):
    target = BuildTarget.WEB

    def build(
        self, prepared: dict[str, Path | str | None]
    ) -> None:  # pragma: no cover - invocado por run()
        command = [
            sys.executable,
            "-m",
            "flet",
            "build",
            "web",
            str(self.context.app_path),
            "--output",
            str(self.output_dir),
        ]
        base_url = self.context.project_config.web.get("base_url")
        if isinstance(base_url, str) and base_url:
            command.extend(["--base-url", base_url])
        _run_command(
            command,
            cwd=self.context.project_dir,
            timeout=self.context.build_timeout,
            env_profile="flet_build",
        )


def _desktop_platform_target() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


DESKTOP_PLATFORM_TARGETS = {BuildTarget.WINDOWS, BuildTarget.MACOS, BuildTarget.LINUX}


class DesktopAdapter(_BaseAdapter):
    target = BuildTarget.LINUX

    def __init__(
        self, context: BuildContext, platform_target: BuildTarget | None = None
    ) -> None:
        if platform_target is not None:
            self.target = platform_target
        super().__init__(context)

    def build(self, prepared: dict[str, Path | str | None]) -> None:
        command = [
            sys.executable,
            "-m",
            "flet",
            "build",
            self.target.value,
            str(self.context.app_path),
            "--output",
            str(self.output_dir),
        ]
        product_name = self.context.project_config.desktop.get("product_name")
        if isinstance(product_name, str) and product_name:
            command.extend(["--product", product_name])
        _run_command(
            command,
            cwd=self.context.project_dir,
            timeout=self.context.build_timeout,
            env_profile="flet_build",
        )


class FletMobileAdapter(_BaseAdapter):
    flet_target: str = "apk"

    def build(self, prepared: dict[str, Path | str | None]) -> None:
        icon_path = prepared.get("icon")
        metadata_path = prepared.get("metadata")

        env = {}
        if metadata_path:
            env["FLETPLUS_METADATA"] = str(metadata_path)
        if icon_path:
            env["FLETPLUS_ICON"] = str(icon_path)
        mobile_config = self.context.project_config.mobile
        package_name = mobile_config.get("package")
        if isinstance(package_name, str) and package_name:
            env["FLETPLUS_PACKAGE"] = package_name

        command = [
            sys.executable,
            "-m",
            "flet",
            "build",
            self.flet_target,
            str(self.context.app_path),
            "--output",
            str(self.output_dir),
        ]
        click.echo(f"Preparando paquete móvil con Flet ({self.flet_target})")
        _run_command(
            command,
            cwd=self.context.project_dir,
            timeout=self.context.build_timeout,
            env_overrides=env,
            env_profile="flet_mobile",
        )


class AndroidApkAdapter(FletMobileAdapter):
    target = BuildTarget.ANDROID_APK
    flet_target = "apk"


class AndroidAabAdapter(FletMobileAdapter):
    target = BuildTarget.ANDROID_AAB
    flet_target = "aab"


class IosAdapter(FletMobileAdapter):
    target = BuildTarget.IOS
    flet_target = "ipa"


def create_adapter(target: BuildTarget, context: BuildContext) -> _BaseAdapter:
    if target is BuildTarget.WEB:
        return WebAdapter(context)
    if target is BuildTarget.DESKTOP:
        return DesktopAdapter(context, BuildTarget(_desktop_platform_target()))
    if target in DESKTOP_PLATFORM_TARGETS:
        return DesktopAdapter(context, target)
    if target is BuildTarget.ANDROID_APK:
        return AndroidApkAdapter(context)
    if target is BuildTarget.ANDROID_AAB:
        return AndroidAabAdapter(context)
    if target is BuildTarget.IOS:
        return IosAdapter(context)
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

    def select_render_strategy(self, target: BuildTarget) -> RenderStrategy:
        """Selecciona y registra la estrategia de renderizado para un BuildTarget."""
        strategy_target = (
            "desktop" if target in DESKTOP_PLATFORM_TARGETS else target.value
        )
        strategy = strategy_for_target(strategy_target)
        self.context.render_strategy = strategy
        return strategy

    def build(self, targets: Iterable[BuildTarget]) -> List[BuildReport]:
        reports: List[BuildReport] = []
        for target in targets:
            self.select_render_strategy(target)
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
                reports.append(
                    BuildReport(target=target, success=False, message=str(exc))
                )
        return reports


def run_build(
    project_dir: Path,
    app_path: Path,
    target: str,
    build_timeout: float = DEFAULT_BUILD_TIMEOUT_SECONDS,
) -> List[BuildReport]:
    project_config = _load_fletplus_config(project_dir.resolve())
    effective_target = target
    if target == "all" and project_config.default_target:
        effective_target = project_config.default_target
    context = BuildContext.from_project(
        project_dir, app_path, build_timeout=build_timeout
    )
    targets = BuildTarget.parse_option(effective_target)
    manager = BuildManager(context)
    return manager.build(targets)
