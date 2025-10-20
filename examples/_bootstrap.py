"""Utilidades para ejecutar ejemplos sin instalar el paquete."""

from __future__ import annotations

from pathlib import Path
import sys


def ensure_project_root() -> None:
    """Garantiza que la raíz del repositorio esté en ``sys.path``.

    Esto permite ejecutar los ejemplos directamente con ``python examples/...``
    sin requerir una instalación previa del paquete ``fletplus``.
    """

    project_root = Path(__file__).resolve().parents[1]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
