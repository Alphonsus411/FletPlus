"""Servicios Python y lógica de dominio para {{ project_name }}."""

from __future__ import annotations

from shared.models import ProjectStatus


def get_project_status() -> ProjectStatus:
    """Devuelve un estado inicial consumible por la interfaz."""
    return ProjectStatus(name="{{ project_name }}", ready=True)
