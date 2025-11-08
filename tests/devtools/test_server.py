import asyncio
import sys
from pathlib import Path

import pytest
import websockets

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fletplus.devtools import DevToolsServer


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_broadcast_excludes_sender_and_reaches_peers():
    server = DevToolsServer()

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as producer, websockets.connect(uri) as consumer:
            await producer.send("hola")

            received = await asyncio.wait_for(consumer.recv(), timeout=2)
            assert received == "hola"

            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(producer.recv(), timeout=0.2)


@pytest.mark.anyio
async def test_ignores_binary_messages():
    server = DevToolsServer()

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as producer, websockets.connect(uri) as consumer:
            await producer.send(b"binario")

            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(consumer.recv(), timeout=0.2)

