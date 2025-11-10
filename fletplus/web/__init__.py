"""Funciones utilitarias para habilitar PWA en FletPlus."""

from fletplus.web.pwa import (
    generate_manifest,
    generate_service_worker,
    register_pwa,
)

__all__ = [
    "generate_manifest",
    "generate_service_worker",
    "register_pwa",
]