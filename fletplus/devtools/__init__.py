"""Herramientas para depuración y desarrollo en tiempo real.

La clase :class:`DevToolsServer` depende opcionalmente de ``websockets``:
el módulo se puede importar sin esa dependencia, pero al instanciar la clase
se lanzará un ``RuntimeError`` con instrucciones de instalación.
"""

from .server import DevToolsServer

__all__ = ["DevToolsServer"]
