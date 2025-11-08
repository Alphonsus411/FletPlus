from pathlib import Path

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
