"""Punto de entrada para la CLI de FletPlus."""

from __future__ import annotations

import cProfile
import io
import os
import pstats
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from importlib import resources, util
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Callable, Dict, Iterable

import click

from .build import PackagingError, run_build


def _watchdog_available() -> bool:
    try:
        return util.find_spec("watchdog") is not None
    except (ImportError, ValueError):
        return sys.modules.get("watchdog") is not None


WATCHDOG_AVAILABLE = _watchdog_available()
if WATCHDOG_AVAILABLE:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
else:  # pragma: no cover - depende de watchdog opcional
    FileSystemEvent = object  # type: ignore[assignment]

    class FileSystemEventHandler:  # type: ignore[no-redef]
        """Fallback cuando watchdog no está instalado."""

    Observer = None  # type: ignore[assignment]

EXCLUDED_DIRS = {".git", "__pycache__", "build", "dist", "node_modules", ".venv", "venv"}
TEMPLATE_PACKAGE = "fletplus.cli"
PACKAGE_NAME_REGEX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@click.group()
def app() -> None:
    """Herramientas de línea de comandos para proyectos FletPlus."""


def _render_template(content: str, context: Dict[str, str]) -> str:
    rendered = content
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{ {key} }}}}", value)
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def _copy_template_tree(template_root: Traversable, destination: Path, context: Dict[str, str]) -> None:
    for entry in template_root.iterdir():
        target_path = destination / entry.name
        if entry.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            _copy_template_tree(entry, target_path, context)
        else:
            try:
                content = entry.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Binarios: copiar tal cual.
                with entry.open("rb") as source, target_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
            else:
                target_path.write_text(_render_template(content, context), encoding="utf-8")


def _profile_router_navigation() -> None:
    import flet as ft

    from fletplus.router import Route, Router

    router = Router(
        routes=[
            Route(path="/", view=lambda _: ft.Text("inicio")),
            Route(path="/dashboard", view=lambda _: ft.Text("dashboard")),
            Route(
                # La sintaxis de parámetros del router usa <>.
                path="/usuarios/<user_id>",
                view=lambda match: ft.Text(
                    f"usuario {match.params.get('user_id')}",
                    key=match.params.get("user_id"),
                ),
            ),
        ]
    )
    router.observe(lambda _match, _view: None)
    for path in ("/", "/dashboard", "/usuarios/42", "/usuarios/99", "/dashboard", "/"):
        router.go(path)


def _profile_scaffold_generation() -> None:
    template_root = resources.files(TEMPLATE_PACKAGE).joinpath("templates", "app")
    context = {"project_name": "Perfil", "package_name": "perfil"}
    with tempfile.TemporaryDirectory() as tmp_dir:
        destino = Path(tmp_dir) / "demo"
        destino.mkdir(parents=True, exist_ok=True)
        _copy_template_tree(template_root, destino, context)


def _profile_responsive_utils() -> None:
    from fletplus.utils.device_profiles import columns_for_width, iter_device_profiles

    profiles = tuple(iter_device_profiles())
    for width in (320, 480, 640, 800, 1024, 1366, 1600, 1920):
        columns_for_width(width, profiles)


PROFILE_FLOWS: dict[str, Callable[[], None]] = {
    "router": _profile_router_navigation,
    "scaffold": _profile_scaffold_generation,
    "responsive": _profile_responsive_utils,
}


def _run_profile(flows: Iterable[Callable[[], None]], *, sort: str, limit: int) -> str:
    profiler = cProfile.Profile()
    for flow in flows:
        profiler.runcall(flow)

    output = io.StringIO()
    stats = pstats.Stats(profiler, stream=output).sort_stats(sort)
    stats.print_stats(limit)
    return output.getvalue()


def _normalize_package_name(nombre: str) -> str:
    paquete = nombre.lower().replace("-", "_").replace(" ", "_")
    if paquete and paquete[0].isdigit():
        paquete = f"_{paquete}"
    return paquete


def _validate_package_name(paquete: str) -> None:
    if not PACKAGE_NAME_REGEX.match(paquete):
        raise click.ClickException(
            "El nombre del paquete debe ser un identificador Python válido: "
            "solo letras, números y guiones bajos, y debe iniciar con letra o '_'.\n"
            "Ejemplos válidos: mi_app, app2, _demo.\n"
            "Ejemplos inválidos: 1app, mi-app, app!."
        )


def _validate_project_name(nombre: str) -> None:
    if "/" in nombre or "\\" in nombre:
        raise click.ClickException(
            "El nombre del proyecto no puede incluir separadores de ruta Unix ('/') ni Windows ('\\\\')."
        )

    separators = {os.sep}
    if os.altsep:
        separators.add(os.altsep)

    if any(sep in nombre for sep in separators):
        raise click.ClickException(
            "El nombre del proyecto no puede incluir separadores de ruta Unix ('/') ni Windows ('\\\\')."
        )

    if ".." in Path(nombre).parts:
        raise click.ClickException(
            "El nombre del proyecto no puede incluir segmentos '..'."
        )

    if Path(nombre).name != nombre:
        raise click.ClickException(
            "El nombre del proyecto debe ser un nombre simple sin rutas."
        )


@app.command()
@click.argument("nombre")
@click.option(
    "--directorio",
    "directorio_base",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Ruta donde se creará la nueva aplicación.",
)
def create(nombre: str, directorio_base: Path | None) -> None:
    """Genera la estructura base de una aplicación FletPlus."""

    if directorio_base is None:
        directorio_base = Path.cwd()

    _validate_project_name(nombre)

    paquete = _normalize_package_name(nombre)
    _validate_package_name(paquete)
    proyecto = directorio_base / nombre
    if proyecto.exists() and not proyecto.is_dir():
        raise click.ClickException(
            f"La ruta '{proyecto}' ya existe y no es un directorio."
        )

    if proyecto.is_dir() and any(proyecto.iterdir()):
        raise click.ClickException(f"El directorio '{proyecto}' ya existe y no está vacío.")

    proyecto.mkdir(parents=True, exist_ok=True)
    contexto = {"project_name": nombre, "package_name": paquete}

    plantilla_base = resources.files(TEMPLATE_PACKAGE).joinpath("templates", "app")
    _copy_template_tree(plantilla_base, proyecto, contexto)

    click.echo(f"Proyecto creado en {proyecto}")


def _should_ignore(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


class _ReloadHandler(FileSystemEventHandler):
    def __init__(
        self,
        trigger: Callable[[], None],
        patterns: Iterable[str] | None = None,
        debounce_window_seconds: float = 0.3,
    ) -> None:
        self._trigger = trigger
        self._patterns = tuple(patterns or ())
        self._debounce_window_seconds = debounce_window_seconds
        self._last_event_by_path: dict[str, float] = {}

    def on_any_event(self, event: FileSystemEvent) -> None:  # pragma: no cover - interactivo
        if event.is_directory:
            return

        path = Path(event.src_path)
        if _should_ignore(path):
            return

        if self._patterns and path.suffix not in self._patterns:
            return

        now = time.monotonic()
        path_key = event.src_path
        last_event_time = self._last_event_by_path.get(path_key)
        if (
            last_event_time is not None
            and now - last_event_time < self._debounce_window_seconds
        ):
            return

        self._last_event_by_path[path_key] = now

        self._trigger()


def _launch_flet_process(app_path: Path, port: int | None, devtools: bool) -> subprocess.Popen:
    command = [sys.executable, "-m", "flet", "run", str(app_path)]
    if port is not None:
        command.extend(["--port", str(port)])
    if devtools:
        command.append("--devtools")

    env = os.environ.copy()
    devtools_env_removed = False
    if devtools:
        env.setdefault("FLET_DEVTOOLS", "1")
    else:
        if env.pop("FLET_DEVTOOLS", None) is not None:
            devtools_env_removed = True

    mensaje_arranque = f"Iniciando servidor: {' '.join(command)}"
    if devtools_env_removed:
        mensaje_arranque += " (FLET_DEVTOOLS eliminado del entorno porque --no-devtools está activo)"
    click.echo(mensaje_arranque)
    return subprocess.Popen(command, env=env, cwd=str(app_path.parent))


def _stop_process(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def _resolve_app_path(app_path: Path, watch_path: Path) -> Path:
    """Resuelve --app priorizando --watch para rutas relativas.

    Regla de precedencia:
    1) Si --app es absoluto, se usa tal cual.
    2) Si --app es relativo, se intenta primero `watch_path / app_path`.
    3) Como compatibilidad, si no existe, se intenta `Path.cwd() / app_path`.
    4) Si no existe en ninguna, se devuelve el candidato primario para el error final.
    """

    if app_path.is_absolute():
        return app_path

    watch_candidate = watch_path / app_path
    if watch_candidate.exists():
        return watch_candidate

    cwd_candidate = Path.cwd() / app_path
    if cwd_candidate.exists():
        return cwd_candidate

    return watch_candidate


@app.command()
@click.option(
    "--app",
    "app_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default="src/main.py",
    help=(
        "Ruta al archivo principal de la app. Si es relativa, se resuelve primero "
        "contra --watch y, si no existe, contra el directorio actual."
    ),
)
@click.option("--port", default=8550, show_default=True, help="Puerto del servidor web.")
@click.option("--no-devtools", "devtools", flag_value=False, default=True, help="Desactiva DevTools.")
@click.option(
    "--watch",
    "watch_path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Directorio a monitorear y base primaria para resolver --app relativo.",
)
def run(app_path: Path, port: int, devtools: bool, watch_path: Path | None) -> None:
    """Inicia el servidor de desarrollo con recarga automática."""

    if watch_path is None:
        watch_path = Path.cwd()
    watch_path = watch_path.resolve()

    if not watch_path.exists():
        raise click.ClickException(f"La ruta a monitorear no existe: {watch_path}")

    app_path = _resolve_app_path(app_path, watch_path)
    if not app_path.exists():
        raise click.ClickException(f"No se encontró el archivo de la aplicación: {app_path}")
    if not app_path.is_file():
        raise click.ClickException(
            f"La ruta de la aplicación debe ser un archivo: {app_path}"
        )

    reinicio_evento = threading.Event()

    def solicitar_reinicio() -> None:
        if not reinicio_evento.is_set():
            click.echo("Cambios detectados, reiniciando servidor...")
        reinicio_evento.set()

    if not WATCHDOG_AVAILABLE:
        click.echo(
            "watchdog no está instalado; se ejecuta sin recarga automática. "
            "Instálalo con 'pip install fletplus[cli]' (o 'pip install watchdog') para habilitarla."
        )
        proceso = _launch_flet_process(app_path.resolve(), port, devtools)
        try:
            while True:
                returncode = proceso.poll()
                if returncode is not None:
                    if returncode != 0:
                        click.echo(
                            f"El servidor terminó con error (código {returncode}).",
                            err=True,
                        )
                        raise click.ClickException(
                            f"La ejecución de la app finalizó con código {returncode}."
                        )
                    click.echo("El servidor se detuvo.")
                    break
                time.sleep(0.5)
        except KeyboardInterrupt:  # pragma: no cover - interactivo
            click.echo("Deteniendo servidor...")
        finally:
            _stop_process(proceso)
        return

    observer = Observer()
    handler = _ReloadHandler(solicitar_reinicio, patterns={".py", ".json", ".yaml", ".yml"})
    observer.schedule(handler, str(watch_path), recursive=True)
    observer.start()

    proceso = _launch_flet_process(app_path.resolve(), port, devtools)

    try:
        while True:
            if reinicio_evento.wait(timeout=0.5):
                reinicio_evento.clear()
                _stop_process(proceso)
                proceso = _launch_flet_process(app_path.resolve(), port, devtools)

            returncode = proceso.poll()
            if returncode is not None:
                if returncode != 0:
                    click.echo(
                        f"El servidor terminó con error (código {returncode}).",
                        err=True,
                    )
                    raise click.ClickException(
                        f"La ejecución de la app finalizó con código {returncode}."
                    )
                click.echo("El servidor se detuvo.")
                break
    except KeyboardInterrupt:  # pragma: no cover - interactivo
        click.echo("Deteniendo servidor...")
    finally:
        observer.stop()
        observer.join()
        _stop_process(proceso)


@app.command()
@click.option(
    "--flow",
    "flow_names",
    multiple=True,
    type=click.Choice(sorted(PROFILE_FLOWS)),
    help="Flujos a ejecutar (por defecto todos).",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("profile-report.txt"),
    show_default=True,
    help="Archivo donde se almacenará el reporte.",
)
@click.option(
    "--sort",
    type=click.Choice(["tottime", "cumtime", "ncalls", "calls"], case_sensitive=False),
    default="tottime",
    show_default=True,
    help="Columna por la que se ordenará el reporte de pstats.",
)
@click.option(
    "--limit",
    type=int,
    default=40,
    show_default=True,
    help="Número de filas a mostrar en el reporte impreso.",
)
def profile(flow_names: tuple[str, ...], output_path: Path, sort: str, limit: int) -> None:
    """Ejecuta flujos clave con cProfile y genera un reporte."""

    if limit <= 0:
        raise click.ClickException("--limit debe ser un entero positivo.")

    selected_names = flow_names or tuple(PROFILE_FLOWS)
    flows = [PROFILE_FLOWS[name] for name in selected_names]
    click.echo(f"Ejecutando {len(flows)} flujo(s): {', '.join(selected_names)}")
    report = _run_profile(flows, sort=sort, limit=limit)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    click.echo(f"Reporte almacenado en {output_path}")
    click.echo(report)


@app.command()
@click.option(
    "--target",
    type=click.Choice(["web", "desktop", "mobile", "all"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Objetivo de compilación (web, desktop, mobile o all).",
)
@click.option(
    "--app",
    "app_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("src/main.py"),
    show_default=True,
    help="Ruta al archivo principal de la aplicación.",
)
def build(target: str, app_path: Path) -> None:
    """Compila la aplicación para los objetivos seleccionados."""

    try:
        reports = run_build(Path.cwd(), app_path, target.lower())
    except PackagingError as exc:
        raise click.ClickException(str(exc)) from exc

    failed = False
    for report in reports:
        prefix = "✅" if report.success else "❌"
        click.echo(f"{prefix} {report.target.value}: {report.message}")
        failed = failed or not report.success

    if failed:
        raise click.ClickException("La compilación terminó con errores.")


if __name__ == "__main__":  # pragma: no cover - punto de entrada manual
    app()
