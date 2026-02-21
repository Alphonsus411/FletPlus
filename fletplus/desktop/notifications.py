from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from typing import Callable

logger = logging.getLogger(__name__)

_MAX_LOG_BODY_LEN = 80


def _sanitize_for_log(value: str, max_len: int = _MAX_LOG_BODY_LEN) -> str:
    """Sanitiza texto para logs, evitando multilinea y exceso de longitud."""

    compact = " ".join(value.split())
    if len(compact) <= max_len:
        return compact
    return f"{compact[: max_len - 3]}..."


def _is_verbose_logging_enabled(verbose: bool | None = None) -> bool:
    """Habilita logging verboso solo en modo desarrollo."""

    if verbose is False:
        return False

    dev_mode = os.environ.get("FLETPLUS_ENV", "").lower() in {"dev", "development"}
    env_verbose = os.environ.get("FLETPLUS_NOTIFICATION_VERBOSE", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if verbose is True:
        return dev_mode

    return dev_mode and env_verbose


def _escape_powershell(text: str) -> str:
    s = text.replace("\r", " ").replace("\n", " ").replace("\x00", "")
    s = s.replace("'", "''")
    return s


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
                timeout=4,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired as err:
            logger.debug("PowerShell agotó el tiempo de espera: %s", err)
            return False
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
            timeout=4,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired as err:
        logger.debug("osascript agotó el tiempo de espera: %s", err)
        return False
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
                timeout=4,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired as err:
            logger.debug("notify-send agotó el tiempo de espera: %s", err)
            return False
        except OSError:
            logger.debug("notify-send no está disponible")
        except Exception as err:  # pragma: no cover - dependiente de entorno
            logger.debug("notify-send falló: %s", err)

    return False


def _notify_in_page(title: str, body: str, *, verbose: bool | None = None) -> bool:
    """Muestra una notificación dentro de la página como fallback."""

    logger.info("Notificación en página activada (fallback).")
    if _is_verbose_logging_enabled(verbose):
        logger.debug(
            "Fallback notificación | title=%s | body=%s",
            _sanitize_for_log(title),
            _sanitize_for_log(body),
        )
    return True


def show_notification(title: str, body: str, *, verbose: bool | None = None) -> None:
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
        _notify_in_page(title, body, verbose=verbose)
