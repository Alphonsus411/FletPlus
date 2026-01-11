import importlib
from pathlib import Path
from typing import Any

import httpx
import pytest

from fletplus.http import DiskCache, HttpClient, HttpInterceptor


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_http_client_hooks_and_cache(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"value": call_count})

    transport = httpx.MockTransport(handler)
    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=transport)

    before_events = []
    after_events = []

    client.add_before_hook(lambda event: before_events.append((event.method, event.url)))
    client.add_after_hook(
        lambda event: after_events.append((event.status_code, event.from_cache, event.error))
    )

    respuesta1 = await client.get("https://example.org/items")
    assert respuesta1.json() == {"value": 1}
    assert call_count == 1

    respuesta2 = await client.get("https://example.org/items")
    assert respuesta2.json() == {"value": 1}
    assert call_count == 1  # La caché evita la segunda llamada

    await client.aclose()

    assert len(before_events) == 2
    assert before_events[0][1] == "https://example.org/items"
    assert before_events[1][1] == "https://example.org/items"

    assert len(after_events) == 2
    assert after_events[0] == (200, False, None)
    assert after_events[1] == (200, True, None)

    ultimo_evento = client.after_request.get()
    assert ultimo_evento is not None
    assert ultimo_evento.from_cache is True


@pytest.mark.anyio
async def test_http_client_interceptors(tmp_path: Path):
    captured_header = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_header["X-Test"] = request.headers.get("X-Test")
        return httpx.Response(200, json={"value": "ok"})

    transport = httpx.MockTransport(handler)
    client = HttpClient(transport=transport)

    async def before(request: httpx.Request) -> httpx.Request:
        request.headers["X-Test"] = "intercepted"
        return request

    async def after(response: httpx.Response) -> httpx.Response:
        response.headers["X-Intercepted"] = "1"
        return response

    client.add_interceptor(HttpInterceptor(before_request=before, after_response=after))

    respuesta = await client.get("https://example.org/secure")
    await client.aclose()

    assert captured_header["X-Test"] == "intercepted"
    assert respuesta.headers["X-Intercepted"] == "1"


@pytest.mark.anyio
async def test_http_client_websocket_interceptors(monkeypatch: pytest.MonkeyPatch):
    captured_headers = {}

    class DummyWebSocket:
        response_headers = {"X-Original": "1"}
        response_status = 101

        def __init__(self) -> None:
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    async def fake_websocket_connect(url: str, **kwargs: Any):
        headers = kwargs.get("extra_headers") or {}
        captured_headers["request"] = {key.lower(): value for key, value in dict(headers).items()}
        return DummyWebSocket()

    client = HttpClient()
    monkeypatch.setattr("fletplus.http.client._load_websocket_connect", lambda: fake_websocket_connect)

    def before(request: httpx.Request) -> httpx.Request:
        request.headers["X-Test"] = "intercepted"
        return request

    def after(response: httpx.Response) -> httpx.Response:
        response.headers["X-Intercepted"] = "1"
        return response

    client.add_interceptor(HttpInterceptor(before_request=before, after_response=after))

    websocket = await client.ws_connect(
        "https://example.org/socket", headers={"X-Initial": "1"}
    )
    await websocket.aclose()
    await client.aclose()

    assert captured_headers["request"]["x-test"] == "intercepted"
    assert captured_headers["request"]["x-initial"] == "1"
    assert websocket.response.headers["X-Intercepted"] == "1"
    assert websocket.response.headers["X-Original"] == "1"


@pytest.mark.anyio
async def test_http_client_websocket_missing_dependency(monkeypatch: pytest.MonkeyPatch):
    client = HttpClient()

    def fake_find_spec(name: str):
        if name == "websockets":
            return None
        return importlib.util.find_spec(name)

    monkeypatch.setattr("fletplus.http.client.importlib.util.find_spec", fake_find_spec)

    with pytest.raises(RuntimeError, match="websockets"):
        await client.ws_connect("https://example.org/socket")
    await client.aclose()


@pytest.mark.anyio
async def test_http_client_response_interceptors_with_cache(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json={"value": call_count},
            headers={"X-Call": str(call_count)},
        )

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    intercepted_headers: list[str | None] = []

    def after(response: httpx.Response) -> httpx.Response:
        intercepted_headers.append(response.headers.get("X-Call"))
        response.headers["X-Intercepted"] = str(len(intercepted_headers))
        return response

    client.add_interceptor(HttpInterceptor(after_response=after))

    primera_respuesta = await client.get("https://example.org/data")
    segunda_respuesta = await client.get("https://example.org/data")

    await client.aclose()

    assert call_count == 1
    assert primera_respuesta.headers["X-Intercepted"] == "1"
    assert segunda_respuesta.headers["X-Intercepted"] == "2"
    assert intercepted_headers == ["1", "1"]


@pytest.mark.anyio
async def test_http_client_cache_key_after_request_modifications(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"url": str(request.url), "count": call_count})

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    def before_hook(event):
        suffix = event.context.get("suffix")
        if suffix is None:
            return
        params = dict(event.request.url.params)
        params["suffix"] = suffix
        event.request.url = event.request.url.copy_with(params=params)

    client.add_before_hook(before_hook)

    resp_one = await client.get("https://example.org/items", context={"suffix": "one"})
    resp_two = await client.get("https://example.org/items", context={"suffix": "two"})
    resp_one_cached = await client.get(
        "https://example.org/items", context={"suffix": "one"}
    )

    await client.aclose()

    assert call_count == 2
    assert resp_one.json() == {"url": "https://example.org/items?suffix=one", "count": 1}
    assert resp_two.json() == {"url": "https://example.org/items?suffix=two", "count": 2}
    assert resp_one_cached.json() == {
        "url": "https://example.org/items?suffix=one",
        "count": 1,
    }


@pytest.mark.anyio
async def test_http_client_cache_respects_no_store(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, headers={"Cache-Control": "no-store"}, json={"count": call_count})

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get("https://example.org/no-store")
    second = await client.get("https://example.org/no-store")

    await client.aclose()

    assert first.json() == {"count": 1}
    assert second.json() == {"count": 2}
    assert call_count == 2


@pytest.mark.anyio
async def test_http_client_cache_respects_no_cache(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, headers={"Cache-Control": "no-cache"}, json={"count": call_count})

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get("https://example.org/no-cache")
    second = await client.get("https://example.org/no-cache")

    await client.aclose()

    assert first.json() == {"count": 1}
    assert second.json() == {"count": 2}
    assert call_count == 2


@pytest.mark.anyio
async def test_http_client_cache_skips_set_cookie(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, headers={"Set-Cookie": "session=abc"}, json={"count": call_count})

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get("https://example.org/set-cookie")
    second = await client.get("https://example.org/set-cookie")

    await client.aclose()

    assert first.json() == {"count": 1}
    assert second.json() == {"count": 2}
    assert call_count == 2


@pytest.mark.anyio
async def test_http_client_cache_success_response(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"count": call_count})

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get("https://example.org/cache-ok")
    second = await client.get("https://example.org/cache-ok")

    await client.aclose()

    assert first.json() == {"count": 1}
    assert second.json() == {"count": 1}
    assert call_count == 1


@pytest.mark.anyio
async def test_http_client_disables_cache_when_interceptor_adds_auth(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"count": call_count})

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    def before(request: httpx.Request) -> httpx.Request:
        request.headers["Authorization"] = "Bearer token"
        return request

    client.add_interceptor(HttpInterceptor(before_request=before))

    primera = await client.get("https://example.org/secure")
    segunda = await client.get("https://example.org/secure")

    await client.aclose()

    assert primera.json() == {"count": 1}
    assert segunda.json() == {"count": 2}
    assert call_count == 2


def test_disk_cache_rejects_invalid_max_entries(tmp_path: Path):
    with pytest.raises(ValueError, match="max_entries debe ser un entero mayor o igual a 1"):
        DiskCache(tmp_path, max_entries=0)
    with pytest.raises(ValueError, match="max_entries debe ser un entero mayor o igual a 1"):
        DiskCache(tmp_path, max_entries=-5)
    with pytest.raises(ValueError, match="max_entries debe ser un entero mayor o igual a 1"):
        DiskCache(tmp_path, max_entries=1.5)
    with pytest.raises(ValueError, match="max_entries debe ser un entero mayor o igual a 1"):
        DiskCache(tmp_path, max_entries="10")  # type: ignore[arg-type]


def test_disk_cache_rejects_invalid_max_age(tmp_path: Path):
    with pytest.raises(ValueError, match="max_age debe ser None o un número positivo"):
        DiskCache(tmp_path, max_age=0)
    with pytest.raises(ValueError, match="max_age debe ser None o un número positivo"):
        DiskCache(tmp_path, max_age=-1)
    with pytest.raises(ValueError, match="max_age debe ser None o un número positivo"):
        DiskCache(tmp_path, max_age="30")  # type: ignore[arg-type]
