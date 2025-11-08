import asyncio
import json
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
            producer_ready = await asyncio.wait_for(producer.recv(), timeout=2)
            consumer_ready = await asyncio.wait_for(consumer.recv(), timeout=2)
            assert producer_ready == consumer_ready == "server:ready"

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
            producer_ready = await asyncio.wait_for(producer.recv(), timeout=2)
            consumer_ready = await asyncio.wait_for(consumer.recv(), timeout=2)
            assert producer_ready == consumer_ready == "server:ready"

            await producer.send(b"binario")

            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(consumer.recv(), timeout=0.2)


@pytest.mark.anyio
async def test_late_client_receives_last_snapshot_immediately():
    server = DevToolsServer()

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as producer:
            ready = await asyncio.wait_for(producer.recv(), timeout=2)
            assert ready == "server:ready"

            snapshot_payload = {"type": "snapshot", "data": {"value": 123}}
            await producer.send(json.dumps(snapshot_payload))

            async with websockets.connect(uri) as late_client:
                ready = await asyncio.wait_for(late_client.recv(), timeout=2)
                assert ready == "server:ready"

                snapshot_raw = await asyncio.wait_for(late_client.recv(), timeout=2)
                received_snapshot = json.loads(snapshot_raw)
                assert received_snapshot["type"].lower().startswith("snapshot")
                assert received_snapshot["data"] == {"value": 123}

