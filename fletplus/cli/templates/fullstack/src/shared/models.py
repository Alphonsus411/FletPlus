"""Modelos compartidos entre frontend y backend."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectStatus:
    """Estado mínimo del proyecto usado como contrato inicial."""

    name: str
    ready: bool = False
