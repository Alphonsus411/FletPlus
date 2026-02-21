import asyncio
import inspect
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("websockets")
import websockets

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fletplus.devtools import DevToolsServer


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _connect_with_headers(uri: str, headers: dict[str, str] | None = None):
    if not headers:
        return websockets.connect(uri)

    params = inspect.signature(websockets.connect).parameters
    header_kw = "additional_headers" if "additional_headers" in params else "extra_headers"
    return websockets.connect(uri, **{header_kw: headers})


@pytest.mark.anyio
async def test_broadcast_excludes_sender_and_reaches_peers():
    server = DevToolsServer(allow_unauthenticated_loopback=True)

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
    server = DevToolsServer(allow_unauthenticated_loopback=True)

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
    server = DevToolsServer(allow_unauthenticated_loopback=True)

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


@pytest.mark.anyio
async def test_authorizes_connection_with_token_in_authorization_header():
    server = DevToolsServer(auth_token="secret")

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        async with _connect_with_headers(
            uri,
            {"Authorization": "Bearer secret"},
        ) as allowed_client:
            ready = await asyncio.wait_for(allowed_client.recv(), timeout=2)
            assert ready == "server:ready"


@pytest.mark.anyio
async def test_rejects_connection_with_invalid_header_token():
    server = DevToolsServer(auth_token="secret")

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        with pytest.raises(websockets.exceptions.ConnectionClosedError) as denied:
            async with _connect_with_headers(
                uri,
                {"X-DevTools-Token": "invalid"},
            ) as denied_client:
                await denied_client.recv()

        assert denied.value.rcvd.code == 1008


@pytest.mark.anyio
async def test_rejects_connection_with_token_only_in_query_string():
    server = DevToolsServer(auth_token="secret")

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}?token=secret"

        with pytest.raises(websockets.exceptions.ConnectionClosedError) as denied:
            async with websockets.connect(uri) as denied_client:
                await denied_client.recv()

        assert denied.value.rcvd.code == 1008


@pytest.mark.anyio
async def test_authorizes_connection_with_allowed_origin():
    server = DevToolsServer(allowed_origins={"https://trusted.example"})

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        async with _connect_with_headers(
            uri,
            {"Origin": "https://trusted.example"},
        ) as allowed_client:
            ready = await asyncio.wait_for(allowed_client.recv(), timeout=2)
            assert ready == "server:ready"

        with pytest.raises(websockets.exceptions.ConnectionClosedError) as denied:
            async with _connect_with_headers(
                uri,
                {"Origin": "https://blocked.example"},
            ) as denied_client:
                await denied_client.recv()

        assert denied.value.rcvd.code == 1008


@pytest.mark.anyio
async def test_authorizes_semantically_equivalent_origin_with_trailing_slash_and_uppercase_host():
    server = DevToolsServer(allowed_origins={"https://trusted.example"})

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        async with _connect_with_headers(
            uri,
            {"Origin": "https://TRUSTED.EXAMPLE/"},
        ) as allowed_client:
            ready = await asyncio.wait_for(allowed_client.recv(), timeout=2)
            assert ready == "server:ready"


@pytest.mark.anyio
async def test_authorizes_semantically_equivalent_origin_when_allowed_origin_has_trailing_slash():
    server = DevToolsServer(allowed_origins={"https://trusted.example/"})

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        async with _connect_with_headers(
            uri,
            {"Origin": "https://trusted.example"},
        ) as allowed_client:
            ready = await asyncio.wait_for(allowed_client.recv(), timeout=2)
            assert ready == "server:ready"


def test_allowed_origins_with_only_invalid_entries_fails_fast():
    with pytest.raises(ValueError, match="contiene solo orígenes inválidos"):
        DevToolsServer(
            allowed_origins={
                "trusted.example",
                "ftp://trusted.example",
                "https://trusted.example/path",
            }
        )


def test_allowed_origins_normalizes_valid_origin_with_implicit_port():
    server = DevToolsServer(allowed_origins={"https://host/"})
    assert server._allowed_origins == {"https://host:443"}


def test_listen_rejects_remote_host_with_only_allowed_origins():
    server = DevToolsServer(allowed_origins={"https://trusted.example"})

    with pytest.raises(
        RuntimeError,
        match="allowed_origins por sí solo no es suficiente para exposición remota",
    ):
        server.listen("0.0.0.0", 0)


def test_listen_rejects_loopback_without_auth_or_origins_by_default():
    server = DevToolsServer()

    with pytest.raises(
        RuntimeError,
        match="loopback sin autenticación u orígenes permitidos",
    ):
        server.listen("127.0.0.1", 0)


def test_listen_allows_loopback_when_auth_token_is_configured():
    server = DevToolsServer(auth_token="secret")

    listener = server.listen("127.0.0.1", 0)
    assert listener is not None


def test_listen_allows_loopback_when_allowed_origins_are_configured():
    server = DevToolsServer(allowed_origins={"https://trusted.example"})

    listener = server.listen("127.0.0.1", 0)
    assert listener is not None


def test_listen_allows_unauthenticated_loopback_only_in_explicit_insecure_mode():
    server = DevToolsServer(allow_unauthenticated_loopback=True)

    listener = server.listen("127.0.0.1", 0)
    assert listener is not None


def test_listen_allows_remote_host_when_auth_token_is_configured():
    server = DevToolsServer(auth_token="secret")

    listener = server.listen("0.0.0.0", 0)
    assert listener is not None


def test_listen_allows_remote_host_when_auth_token_and_allowed_origins_are_configured():
    server = DevToolsServer(
        auth_token="secret",
        allowed_origins={"https://trusted.example"},
    )

    listener = server.listen("0.0.0.0", 0)
    assert listener is not None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "origin",
    [
        "https://trusted.example:444",
        "http://trusted.example",
    ],
)
async def test_rejects_origins_with_different_port_or_scheme(origin: str):
    server = DevToolsServer(allowed_origins={"https://trusted.example"})

    async with server.listen("127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        with pytest.raises(websockets.exceptions.ConnectionClosedError) as denied:
            async with _connect_with_headers(
                uri,
                {"Origin": origin},
            ) as denied_client:
                await denied_client.recv()

        assert denied.value.rcvd.code == 1008


def test_is_authorized_rejects_when_request_metadata_is_missing():
    server = DevToolsServer(
        auth_token="secret",
        allowed_origins={"https://trusted.example"},
    )

    class WebSocketWithoutMetadata:
        pass

    assert server._is_authorized(WebSocketWithoutMetadata()) is False


@pytest.mark.anyio
async def test_remember_initial_payload_handles_case_insensitive_allowed_snapshot_types():
    server = DevToolsServer(
        allowed_snapshot_types={"SNAPSHOT", "Snapshot:Node"},
    )

    await server._remember_initial_payload(
        json.dumps({"type": "snapshot", "data": {"value": 1}})
    )
    await server._remember_initial_payload(
        json.dumps({"type": "SNAPSHOT:NODE", "data": {"id": "n1"}})
    )

    assert "snapshot" in server._initial_payloads
    assert "snapshot:node" in server._initial_payloads

    await server._remember_initial_payload(
        json.dumps({"type": "sNaPsHoT:Edge", "data": {"id": "e1"}})
    )

    assert "sNaPsHoT:Edge" not in server._initial_payloads


@pytest.mark.anyio
async def test_remember_initial_payload_overwrites_same_type_with_different_casing():
    server = DevToolsServer()

    first_message = json.dumps({"type": "snapshot:node", "data": {"value": 1}})
    second_message = json.dumps({"type": "SNAPSHOT:NODE", "data": {"value": 2}})

    await server._remember_initial_payload(first_message)
    await server._remember_initial_payload(second_message)

    assert list(server._initial_payloads.keys()) == ["snapshot:node"]
    assert server._initial_payloads["snapshot:node"] == second_message


@pytest.mark.anyio
async def test_initial_payload_snapshot_is_stable_during_concurrent_updates():
    server = DevToolsServer()

    await server._remember_initial_payload(
        json.dumps({"type": "snapshot", "data": {"value": 0}})
    )

    class SlowWebSocket:
        def __init__(self) -> None:
            self.messages: list[str] = []
            self.first_send_started = asyncio.Event()
            self.allow_first_send = asyncio.Event()

        async def send(self, message: str) -> None:
            if not self.messages:
                self.first_send_started.set()
                await self.allow_first_send.wait()
            self.messages.append(message)

    websocket = SlowWebSocket()

    send_task = asyncio.create_task(server._send_initial_payloads(websocket))

    await asyncio.wait_for(websocket.first_send_started.wait(), timeout=1)

    await server._remember_initial_payload(
        json.dumps({"type": "snapshot:node", "data": {"value": 1}})
    )

    websocket.allow_first_send.set()

    await asyncio.wait_for(send_task, timeout=1)

    assert websocket.messages == [
        json.dumps({"type": "snapshot", "data": {"value": 0}})
    ]
