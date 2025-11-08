"""Punto de entrada para la CLI de FletPlus."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
import threading
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Callable, Dict, Iterable

import click
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


EXCLUDED_DIRS = {".git", "__pycache__", "build", "dist", "node_modules", ".venv", "venv"}
TEMPLATE_PACKAGE = "fletplus.cli"


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

    proyecto = directorio_base / nombre
    if proyecto.exists() and any(proyecto.iterdir()):
        raise click.ClickException(f"El directorio '{proyecto}' ya existe y no está vacío.")

    proyecto.mkdir(parents=True, exist_ok=True)

    paquete = nombre.lower().replace("-", "_").replace(" ", "_")
    contexto = {"project_name": nombre, "package_name": paquete}

    plantilla_base = resources.files(TEMPLATE_PACKAGE).joinpath("templates", "app")
    _copy_template_tree(plantilla_base, proyecto, contexto)

    click.echo(f"Proyecto creado en {proyecto}")


def _should_ignore(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


class _ReloadHandler(FileSystemEventHandler):
    def __init__(self, trigger: Callable[[], None], patterns: Iterable[str] | None = None) -> None:
        self._trigger = trigger
        self._patterns = tuple(patterns or ())

    def on_any_event(self, event: FileSystemEvent) -> None:  # pragma: no cover - interactivo
        if event.is_directory:
            return

        path = Path(event.src_path)
        if _should_ignore(path):
            return

        if self._patterns and path.suffix not in self._patterns:
            return

        self._trigger()


def _launch_flet_process(app_path: Path, port: int, devtools: bool) -> subprocess.Popen:
    command = [sys.executable, "-m", "flet", "run", str(app_path)]
    if port:
        command.extend(["--port", str(port)])
    if devtools:
        command.append("--devtools")

    env = os.environ.copy()
    if devtools:
        env.setdefault("FLET_DEVTOOLS", "1")

    click.echo(f"Iniciando servidor: {' '.join(command)}")
    return subprocess.Popen(command, env=env, cwd=str(app_path.parent))


def _stop_process(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@app.command()
@click.option(
    "--app",
    "app_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default="src/main.py",
    help="Ruta al archivo principal de la app.",
)
@click.option("--port", default=8550, show_default=True, help="Puerto del servidor web.")
@click.option("--no-devtools", "devtools", flag_value=False, default=True, help="Desactiva DevTools.")
@click.option(
    "--watch",
    "watch_path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Ruta a monitorear para recarga automática.",
)
def run(app_path: Path, port: int, devtools: bool, watch_path: Path | None) -> None:
    """Inicia el servidor de desarrollo con recarga automática."""

    if watch_path is None:
        watch_path = Path.cwd()

    if not watch_path.exists():
        raise click.ClickException(f"La ruta a monitorear no existe: {watch_path}")

    app_path = (watch_path / app_path) if not app_path.is_absolute() else app_path
    if not app_path.exists():
        raise click.ClickException(f"No se encontró el archivo de la aplicación: {app_path}")

    reinicio_evento = threading.Event()

    def solicitar_reinicio() -> None:
        if not reinicio_evento.is_set():
            click.echo("Cambios detectados, reiniciando servidor...")
        reinicio_evento.set()

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

            if proceso.poll() is not None:
                click.echo("El servidor se detuvo.")
                break
    except KeyboardInterrupt:  # pragma: no cover - interactivo
        click.echo("Deteniendo servidor...")
    finally:
        observer.stop()
        observer.join()
        _stop_process(proceso)


@app.command()
def build() -> None:
    """Compila la aplicación para distribución."""

    mensaje = textwrap.dedent(
        """
        La fase de construcción aún no está implementada.
        Puedes utilizar `flet pack` o tu herramienta preferida hasta que este comando esté disponible.
        """
    ).strip()
    click.echo(mensaje)


if __name__ == "__main__":  # pragma: no cover - punto de entrada manual
    app()
