import logging
import sys  # Se utiliza para detectar la plataforma en tiempo de ejecución
from typing import Callable


def _notify_windows(title: str, body: str) -> None:
    """Muestra una notificación en Windows."""
    # Aquí se integraría la API de notificaciones de Windows
    raise NotImplementedError("Las notificaciones en Windows no están implementadas")


def _notify_macos(title: str, body: str) -> None:
    """Muestra una notificación en macOS."""
    # Aquí se integraría la API de notificaciones de macOS
    raise NotImplementedError("Las notificaciones en macOS no están implementadas")


def _notify_linux(title: str, body: str) -> None:
    """Muestra una notificación en Linux."""
    # Aquí se integraría la API de notificaciones de Linux
    raise NotImplementedError("Las notificaciones en Linux no están implementadas")


def _notify_in_page(title: str, body: str) -> None:
    """Muestra una notificación dentro de la página como fallback."""
    print(f"Notificación: {title} - {body}")


def show_notification(title: str, body: str) -> None:
    """Muestra una notificación nativa o una interna si la plataforma no la soporta."""
    plat = sys.platform
    if plat.startswith("win"):
        notifier: Callable[[str, str], None] = _notify_windows
    elif plat == "darwin":
        notifier = _notify_macos
    elif plat.startswith("linux"):
        notifier = _notify_linux
    else:
        notifier = _notify_in_page

    try:
        notifier(title, body)
    except (OSError, NotImplementedError) as err:
        logging.error("Error al mostrar la notificación: %s", err)
        _notify_in_page(title, body)
