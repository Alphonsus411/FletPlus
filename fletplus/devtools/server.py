from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterable

from websockets.asyncio.server import ServerProtocol, serve
from websockets.exceptions import ConnectionClosed


_LOGGER = logging.getLogger(__name__)


class DevToolsServer:
    """Servidor WebSocket simple para reenviar eventos entre clientes."""

    def __init__(self) -> None:
        self._clients: set[ServerProtocol] = set()
        self._lock = asyncio.Lock()
        self._initial_payloads: dict[str, str] = {}

    def listen(self, host: str = "127.0.0.1", port: int = 0):
        """Crea el servidor y comienza a escuchar conexiones."""

        return serve(self._handle_client, host, port)

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

    async def _handle_client(self, websocket: ServerProtocol) -> None:
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

    async def _send_initial_payloads(self, websocket: ServerProtocol) -> None:
        async with self._lock:
            initial_payloads = list(self._initial_payloads.values())

        for message in initial_payloads:
            await self._safe_send(websocket, message)

    async def _remember_initial_payload(self, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return

        payload_type = self._extract_payload_type(payload)
        if payload_type is None:
            return

        if any(keyword in payload_type.lower() for keyword in {"snapshot"}):
            async with self._lock:
                self._initial_payloads[payload_type] = message

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

