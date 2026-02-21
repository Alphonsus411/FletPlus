from __future__ import annotations

import asyncio
import hmac
import ipaddress
import json
import logging
from collections import OrderedDict
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse

try:
    from websockets.asyncio.server import ServerProtocol, serve
    from websockets.exceptions import ConnectionClosed
except ImportError as exc:  # pragma: no cover - exercised via optional-dep tests
    ServerProtocol = Any  # type: ignore[assignment]
    serve = None
    ConnectionClosed = Exception
    _WEBSOCKETS_IMPORT_ERROR: ImportError | None = exc
else:
    _WEBSOCKETS_IMPORT_ERROR = None


_LOGGER = logging.getLogger(__name__)

_DEFAULT_PORTS_BY_SCHEME: dict[str, int] = {
    "http": 80,
    "https": 443,
    "ws": 80,
    "wss": 443,
}


class DevToolsServer:
    """Servidor WebSocket simple para reenviar eventos entre clientes.

    Requiere la dependencia opcional ``websockets`` para crear instancias.
    """

    def __init__(
        self,
        *,
        max_initial_payloads: int | None = 50,
        max_payload_size: int | None = 256 * 1024,
        allowed_snapshot_types: set[str] | None = None,
        auth_token: str | None = None,
        allowed_origins: set[str] | None = None,
    ) -> None:
        if _WEBSOCKETS_IMPORT_ERROR is not None:
            raise RuntimeError(
                "DevToolsServer requiere la dependencia opcional 'websockets'. "
                "Instálala con: pip install websockets"
            ) from _WEBSOCKETS_IMPORT_ERROR

        self._clients: set[ServerProtocol] = set()
        self._lock = asyncio.Lock()
        self._initial_payloads_lock = asyncio.Lock()
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
        self._allowed_origins = self._normalize_allowed_origins(allowed_origins)

    def listen(self, host: str = "127.0.0.1", port: int = 0):
        """Crea el servidor y comienza a escuchar conexiones.

        Si se configura ``auth_token`` o ``allowed_origins``, las conexiones
        entrantes deben incluir el token en un header dedicado
        (``Authorization: Bearer <token>`` o ``X-DevTools-Token: <token>``) y/o
        un header ``Origin`` permitido; en caso contrario se rechazan con un
        cierre de política.

        Para exponer el servidor fuera de loopback (por ejemplo ``0.0.0.0``,
        ``::`` o una IP pública) es obligatorio configurar ``auth_token``.
        ``allowed_origins`` puede añadirse como capa extra, pero no reemplaza
        al token para exposición remota.
        """
        if not self._is_loopback_host(host) and self._auth_token is None:
            raise RuntimeError(
                "No se puede iniciar DevTools fuera de loopback sin auth_token. "
                "allowed_origins por sí solo no es suficiente para exposición remota."
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

        await self._remember_initial_payload(message)

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
        _, headers = self._get_request_path_and_headers(websocket)

        if self._auth_token is not None:
            if headers is None:
                _LOGGER.warning(
                    "No se pudieron leer headers del request para validar token"
                )
                return False

            token = self._extract_token_from_headers(headers)

            try:
                # Comparación en tiempo constante para evitar ataques de timing
                match = hmac.compare_digest(
                    token.encode("utf-8"), self._auth_token.encode("utf-8")
                )
            except Exception:
                match = False
            if not match:
                _LOGGER.warning("Token inválido o ausente al conectar DevTools")
                return False

        if self._allowed_origins is not None:
            if headers is None:
                _LOGGER.warning("No se pudieron leer headers del request para validar Origin")
                return False

            origin = headers.get("Origin")
            normalized_origin = self._normalize_origin(origin)
            if normalized_origin is None:
                _LOGGER.warning("Origin inválido al conectar DevTools: %s", origin)
                return False

            if normalized_origin not in self._allowed_origins:
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

    @classmethod
    def _normalize_allowed_origins(
        cls,
        allowed_origins: set[str] | None,
    ) -> set[str] | None:
        if allowed_origins is None:
            return None

        normalized_origins: set[str] = set()
        for origin in allowed_origins:
            normalized_origin = cls._normalize_origin(origin)
            if normalized_origin is None:
                _LOGGER.warning(
                    "Se ignoró allowed_origin inválido en configuración: %s", origin
                )
                continue

            normalized_origins.add(normalized_origin)

        if allowed_origins and not normalized_origins:
            raise ValueError(
                "allowed_origins contiene solo orígenes inválidos. "
                "Usa formatos como 'https://host', 'https://host:443', "
                "'http://host' o 'http://host:80' (esquema obligatorio; "
                "puerto implícito o explícito)."
            )

        return normalized_origins

    @staticmethod
    def _normalize_origin(origin: str | None) -> str | None:
        if not origin:
            return None

        parsed = urlparse(origin)
        scheme = parsed.scheme.lower()
        host = parsed.hostname
        if not scheme or host is None:
            return None

        if parsed.path.rstrip("/"):
            return None

        if parsed.params or parsed.query or parsed.fragment:
            return None

        try:
            port = parsed.port
        except ValueError:
            return None

        if port is None:
            port = _DEFAULT_PORTS_BY_SCHEME.get(scheme)

        if port is None:
            return None

        return f"{scheme}://{host.lower()}:{port}"

    async def _send_initial_payloads(self, websocket: ServerProtocol) -> None:
        async with self._initial_payloads_lock:
            messages = list(self._initial_payloads.values())

        for message in messages:
            await self._safe_send(websocket, message)

    async def _remember_initial_payload(self, message: str) -> None:
        async with self._initial_payloads_lock:
            self._remember_initial_payload_unlocked(message)

    def _remember_initial_payload_unlocked(self, message: str) -> None:
        """Guarda snapshots por tipo en forma case-insensitive.

        La clave interna se normaliza a minúsculas para evitar duplicados cuando
        llegan mensajes del mismo tipo con distinto casing (por ejemplo
        ``snapshot`` y ``SNAPSHOT``). El valor almacenado conserva el mensaje
        original más reciente recibido para ese tipo normalizado.
        """
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

        if payload_type_lower in self._initial_payloads:
            self._initial_payloads.move_to_end(payload_type_lower)

        self._initial_payloads[payload_type_lower] = message
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
