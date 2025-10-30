"""Utilidades comunes para ejecutar los ejemplos de FletPlus."""

from __future__ import annotations

from pathlib import Path
import sys


def ensure_project_root() -> None:
    """Asegura que la raíz del repositorio esté presente en ``sys.path``.

    Esto permite importar ``fletplus`` sin instalar el paquete cuando los
    ejemplos se ejecutan directamente con ``python`` o ``flet run``.
    """

    project_root = Path(__file__).resolve().parent.parent
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)


__all__ = ["ensure_project_root"]
