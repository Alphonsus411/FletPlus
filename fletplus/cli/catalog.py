"""Catálogo declarativo de comandos de la CLI de FletPlus.

El catálogo permite reutilizar los comandos oficiales tanto desde la terminal
como desde interfaces gráficas, sin ejecutar procesos desde la UI por defecto.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CliCommandInfo:
    """Describe un comando público de la CLI sin ejecutarlo."""

    name: str
    command: str
    description: str
    category: str = "general"


def get_cli_command_catalog() -> tuple[CliCommandInfo, ...]:
    """Devuelve los comandos principales disponibles en ``fletplus``."""

    return (
        CliCommandInfo(
            name="Crear proyecto",
            command="fletplus create <nombre>",
            description="Genera una aplicación FletPlus desde una plantilla.",
            category="proyecto",
        ),
        CliCommandInfo(
            name="Ejecutar en desarrollo",
            command="fletplus run",
            description="Inicia la app con recarga y DevTools opcionales.",
            category="desarrollo",
        ),
        CliCommandInfo(
            name="Listar tareas frontend",
            command="fletplus frontend-tasks --format markdown",
            description="Muestra tareas declarativas para adaptar FrontEndConfig.",
            category="frontend",
        ),
        CliCommandInfo(
            name="Perfilar FletPlus",
            command="fletplus profile --limit 40",
            description="Ejecuta perfiles internos con cProfile.",
            category="diagnostico",
        ),
        CliCommandInfo(
            name="Compilar app",
            command="fletplus build --target desktop",
            description="Construye artefactos para el target indicado.",
            category="build",
        ),
    )


__all__ = ["CliCommandInfo", "get_cli_command_catalog"]
