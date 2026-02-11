from __future__ import annotations

import asyncio
import json
import logging
import ipaddress
from collections import OrderedDict
from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.server import ServerProtocol, serve
from websockets.exceptions import ConnectionClosed


_LOGGER = logging.getLogger(__name__)


class DevToolsServer:
    """Servidor WebSocket simple para reenviar eventos entre clientes."""

    def __init__(
        self,
        *,
        max_initial_payloads: int | None = 50,
        max_payload_size: int | None = 256 * 1024,
        allowed_snapshot_types: set[str] | None = None,
        auth_token: str | None = None,
        allowed_origins: set[str] | None = None,
    ) -> None:
        self._clients: set[ServerProtocol] = set()
        self._lock = asyncio.Lock()
        self._initial_payloads: OrderedDict[str, str] = OrderedDict()
        self._max_initial_payloads = max_initial_payloads
        self._max_payload_size = max_payload_size
        self._allowed_snapshot_types = allowed_snapshot_types
        self._normalized_allowed_snapshot_types = (
            {snapshot_type.lower() for snapshot_type in allowed_snapshot_types}
            if allowed_snapshot_types is not None
            else None
        )
        self._auth_token = auth_token
        self._allowed_origins = allowed_origins

    def listen(self, host: str = "127.0.0.1", port: int = 0):
        """Crea el servidor y comienza a escuchar conexiones.

        Si se configura ``auth_token`` o ``allowed_origins``, las conexiones
        entrantes deben incluir el token en un header dedicado
        (``Authorization: Bearer <token>`` o ``X-DevTools-Token: <token>``) y/o
        un header ``Origin`` permitido; en caso contrario se rechazan con un
        cierre de política. Durante una ventana de deprecación, también se
        admite ``?token=...`` como fallback legacy.

        Para exponer el servidor fuera de loopback (por ejemplo ``0.0.0.0``,
        ``::`` o una IP pública) es obligatorio configurar ``auth_token`` o
        ``allowed_origins``. Esta restricción evita exponer el canal de DevTools
        sin control de acceso.
        """
        if (
            not self._is_loopback_host(host)
            and self._auth_token is None
            and self._allowed_origins is None
        ):
            raise RuntimeError(
                "No se puede iniciar DevTools sin auth_token ni allowed_origins "
                "cuando se expone fuera de loopback."
            )

        return serve(
            self._handle_client,
            host,
            port,
            max_size=self._max_payload_size,
        )

    async def _register(self, websocket: ServerProtocol) -> None:
        async with self._lock:
            self._clients.add(websocket)

    async def _unregister(self, websocket: ServerProtocol) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def _broadcast(
        self,
        message: str,
        *,
        sender: ServerProtocol | None = None,
    ) -> None:
        """Reenvía ``message`` a los clientes conectados, excluyendo ``sender``."""

        self._remember_initial_payload(message)

        async with self._lock:
            targets: Iterable[ServerProtocol] = (
                client for client in self._clients if client != sender
            )
            clients_snapshot = list(targets)

        if not clients_snapshot:
            return

        await asyncio.gather(
            *(self._safe_send(client, message) for client in clients_snapshot),
            return_exceptions=True,
        )

    async def _safe_send(self, websocket: ServerProtocol, message: str) -> None:
        try:
            await websocket.send(message)
        except ConnectionClosed:
            _LOGGER.debug("Cliente desconectado durante broadcast", exc_info=True)
        except Exception:  # pragma: no cover - errores inesperados
            _LOGGER.exception("Error enviando mensaje a un cliente")

    @staticmethod
    def _payload_size_bytes(text: str) -> int:
        return len(text.encode("utf-8"))

    async def _handle_client(self, websocket: ServerProtocol) -> None:
        if not self._is_authorized(websocket):
            await websocket.close(code=1008, reason="unauthorized")
            return
        await self._register(websocket)
        try:
            await self._safe_send(websocket, "server:ready")
            await self._send_initial_payloads(websocket)
            async for frame in websocket:
                if not isinstance(frame, str):
                    _LOGGER.warning(
                        "Se recibió un frame no textual: %s", type(frame).__name__
                    )
                    continue
                if (
                    self._max_payload_size is not None
                    and self._payload_size_bytes(frame) > self._max_payload_size
                ):
                    _LOGGER.warning(
                        "Frame excede el tamaño máximo permitido (%s bytes)",
                        self._max_payload_size,
                    )
                    await websocket.close(code=1009, reason="message too big")
                    break

                try:
                    await self._broadcast(frame, sender=websocket)
                except Exception:
                    _LOGGER.exception("Error reenviando frame a los clientes")
        except ConnectionClosed:
            _LOGGER.debug("Conexión cerrada por el cliente")
        except Exception:
            _LOGGER.exception("Error manejando cliente")
        finally:
            await self._unregister(websocket)

    def _is_authorized(self, websocket: ServerProtocol) -> bool:
        path, headers = self._get_request_path_and_headers(websocket)

        if self._auth_token is not None:
            if headers is None:
                _LOGGER.warning(
                    "No se pudieron leer headers del request para validar token"
                )
                return False

            token = self._extract_token_from_headers(headers)

            if token is None:
                if path is None:
                    _LOGGER.warning(
                        "No se pudo leer path del request para validar token legacy"
                    )
                    return False

                parsed = urlparse(path)
                token = parse_qs(parsed.query).get("token", [None])[0]
                if token is not None:
                    _LOGGER.warning(
                        "Se usó token por query string (?token=...): método deprecado; "
                        "usa Authorization Bearer o X-DevTools-Token"
                    )

            if token != self._auth_token:
                _LOGGER.warning("Token inválido o ausente al conectar DevTools")
                return False

        if self._allowed_origins is not None:
            if headers is None:
                _LOGGER.warning("No se pudieron leer headers del request para validar Origin")
                return False

            origin = headers.get("Origin")
            if origin not in self._allowed_origins:
                _LOGGER.warning("Origen no permitido al conectar DevTools: %s", origin)
                return False

        return True

    @staticmethod
    def _get_request_path_and_headers(
        websocket: ServerProtocol,
    ) -> tuple[str | None, Any | None]:
        request = getattr(websocket, "request", None)

        path = getattr(request, "path", None)
        if path is None:
            path = getattr(websocket, "path", None)

        headers = getattr(request, "headers", None)
        if headers is None:
            headers = getattr(websocket, "request_headers", None)

        return path, headers

    @staticmethod
    def _extract_token_from_headers(headers: Any) -> str | None:
        auth_header = headers.get("Authorization")
        if auth_header:
            scheme, _, value = auth_header.partition(" ")
            if scheme.lower() == "bearer" and value:
                return value.strip()

        token_header = headers.get("X-DevTools-Token")
        if token_header:
            return token_header.strip()

        return None

    async def _send_initial_payloads(self, websocket: ServerProtocol) -> None:
        for message in self._initial_payloads.values():
            await self._safe_send(websocket, message)

    def _remember_initial_payload(self, message: str) -> None:
        if (
            self._max_payload_size is not None
            and self._payload_size_bytes(message) > self._max_payload_size
        ):
            return

        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return

        payload_type = self._extract_payload_type(payload)
        if payload_type is None:
            return

        payload_type_lower = payload_type.lower()
        if "snapshot" not in payload_type_lower:
            return

        if (
            self._normalized_allowed_snapshot_types is not None
            and payload_type_lower not in self._normalized_allowed_snapshot_types
        ):
            return

        if payload_type in self._initial_payloads:
            self._initial_payloads.move_to_end(payload_type)

        self._initial_payloads[payload_type] = message
        if (
            self._max_initial_payloads is not None
            and len(self._initial_payloads) > self._max_initial_payloads
        ):
            self._initial_payloads.popitem(last=False)

    def _extract_payload_type(self, payload: object) -> str | None:
        if not isinstance(payload, dict):
            return None

        payload_type = payload.get("type")
        if isinstance(payload_type, str):
            return payload_type

        inner = payload.get("payload")
        if isinstance(inner, dict):
            inner_type = inner.get("type")
            if isinstance(inner_type, str):
                return inner_type

        return None

    @staticmethod
    def _is_loopback_host(host: str) -> bool:
        if host == "localhost":
            return True
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return False
        return address.is_loopback
