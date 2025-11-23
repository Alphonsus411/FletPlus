from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from typing import Callable

logger = logging.getLogger(__name__)


def _escape_powershell(text: str) -> str:
    """Escapa cadenas para scripts de PowerShell."""

    return text.replace("'", "''")


def _notify_windows(title: str, body: str) -> bool:
    """Muestra una notificación en Windows."""

    try:
        from win10toast import ToastNotifier

        try:
            toaster = ToastNotifier()
            return bool(toaster.show_toast(title, body, threaded=True))
        except Exception as err:  # pragma: no cover - dependiente de entorno
            logger.debug("win10toast falló: %s", err)
    except ImportError:
        logger.debug("win10toast no está disponible")

    for powershell in ("powershell", "pwsh"):
        ps_executable = shutil.which(powershell)
        if not ps_executable:
            continue

        script = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime];"
            "$template=[Windows.UI.Notifications.ToastTemplateType]::ToastText02;"
            "$xml=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template);"
            "$texts=$xml.GetElementsByTagName('text');"
            f"$texts.Item(0).AppendChild($xml.CreateTextNode('{_escape_powershell(title)}'))> $null;"
            f"$texts.Item(1).AppendChild($xml.CreateTextNode('{_escape_powershell(body)}'))> $null;"
            "$toast=[Windows.UI.Notifications.ToastNotification]::new($xml);"
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('FletPlus').Show($toast);"
        )

        try:
            result = subprocess.run(
                [ps_executable, "-NoProfile", "-Command", script],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return result.returncode == 0
        except OSError:
            logger.debug("PowerShell no está disponible")
        except Exception as err:  # pragma: no cover - dependiente de entorno
            logger.debug("Error al usar PowerShell para notificaciones: %s", err)

    return False


def _notify_macos(title: str, body: str) -> bool:
    """Muestra una notificación en macOS."""

    try:
        import pync

        try:
            pync.notify(body, title=title)
            return True
        except Exception as err:  # pragma: no cover - dependiente de entorno
            logger.debug("pync falló: %s", err)
    except ImportError:
        logger.debug("pync no está disponible")

    osa = shutil.which("osascript")
    if not osa:
        return False

    script = f"display notification {json.dumps(body)} with title {json.dumps(title)}"

    try:
        result = subprocess.run(
            [osa, "-e", script],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except OSError:
        logger.debug("osascript no está disponible")
    except Exception as err:  # pragma: no cover - dependiente de entorno
        logger.debug("osascript falló: %s", err)

    return False


def _notify_linux(title: str, body: str) -> bool:
    """Muestra una notificación en Linux."""

    try:
        from gi.repository import Notify

        try:
            if not Notify.is_initted():
                Notify.init("FletPlus")
            notification = Notify.Notification.new(title, body)
            notification.show()
            return True
        except Exception as err:  # pragma: no cover - dependiente de entorno
            logger.debug("gi Notify falló: %s", err)
    except ImportError:
        logger.debug("gi.repository.Notify no está disponible")

    notify_send = shutil.which("notify-send")
    if notify_send:
        try:
            result = subprocess.run(
                [notify_send, title, body],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return result.returncode == 0
        except OSError:
            logger.debug("notify-send no está disponible")
        except Exception as err:  # pragma: no cover - dependiente de entorno
            logger.debug("notify-send falló: %s", err)

    return False


def _notify_in_page(title: str, body: str) -> bool:
    """Muestra una notificación dentro de la página como fallback."""

    print(f"Notificación: {title} - {body}")
    return True


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

    delivered = False
    try:
        delivered = bool(notifier(title, body))
    except Exception as err:
        logger.error("Error al mostrar la notificación: %s", err)

    if not delivered:
        _notify_in_page(title, body)
