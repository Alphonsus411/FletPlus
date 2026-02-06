"""Compatibilidad con importaciones previas del shim de listeners.

Si el módulo nativo existe, Python debería priorizarlo frente a este archivo.
"""
from __future__ import annotations

from .listeners_backend import ListenerContainer

__all__ = ["ListenerContainer"]
