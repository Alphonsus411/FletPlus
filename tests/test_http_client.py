import importlib
from pathlib import Path
from typing import Any

import httpx
import pytest

from fletplus.http import DiskCache, HttpClient, HttpInterceptor
from fletplus.http.client import _build_websocket_response


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
async def test_http_client_does_not_cache_sensitive_headers_by_default(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"value": call_count})

    transport = httpx.MockTransport(handler)
    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=transport)

    headers = {"Authorization": "Bearer token"}
    respuesta1 = await client.get("https://example.org/secure", headers=headers, cache=True)
    respuesta2 = await client.get("https://example.org/secure", headers=headers, cache=True)

    await client.aclose()

    assert respuesta1.json() == {"value": 1}
    assert respuesta2.json() == {"value": 2}
    assert call_count == 2


@pytest.mark.anyio
async def test_http_client_allows_sensitive_cache_with_explicit_flag(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"value": call_count})

    transport = httpx.MockTransport(handler)
    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=transport)

    headers = {"Authorization": "Bearer token"}
    respuesta1 = await client.get(
        "https://example.org/secure",
        headers=headers,
        cache=True,
        allow_sensitive_cache=True,
    )
    respuesta2 = await client.get(
        "https://example.org/secure",
        headers=headers,
        cache=True,
        allow_sensitive_cache=True,
    )

    await client.aclose()

    assert respuesta1.json() == {"value": 1}
    assert respuesta2.json() == {"value": 1}
    assert call_count == 1


@pytest.mark.anyio
async def test_http_client_keeps_cache_behavior_without_credentials(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"value": call_count})

    transport = httpx.MockTransport(handler)
    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=transport)

    respuesta1 = await client.get("https://example.org/public", cache=True)
    respuesta2 = await client.get("https://example.org/public", cache=True)

    await client.aclose()

    assert respuesta1.json() == {"value": 1}
    assert respuesta2.json() == {"value": 1}
    assert call_count == 1


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

    async def fake_websocket_connect(url: str, additional_headers: Any = None, **kwargs: Any):
        headers = additional_headers or {}
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


def test_build_websocket_response_with_legacy_metadata():
    class LegacyWebSocket:
        response_status = 204
        response_headers = [("X-Legacy", "ok"), (b"X-Bytes", b"1")]

    request = httpx.Request("GET", "https://example.org/socket")

    response = _build_websocket_response(request, LegacyWebSocket())

    assert response.status_code == 204
    assert response.headers["X-Legacy"] == "ok"
    assert response.headers["X-Bytes"] == "1"


def test_build_websocket_response_with_modern_metadata():
    class ModernHandshakeResponse:
        status_code = 202
        headers = {"X-Modern": "ok"}

    class ModernWebSocket:
        response = ModernHandshakeResponse()

    request = httpx.Request("GET", "https://example.org/socket")

    response = _build_websocket_response(request, ModernWebSocket())

    assert response.status_code == 202
    assert response.headers["X-Modern"] == "ok"


@pytest.mark.anyio
async def test_http_client_websocket_interceptors_receive_modern_response(monkeypatch: pytest.MonkeyPatch):
    class ModernHandshakeResponse:
        status_code = 201
        headers = httpx.Headers({"X-Modern": "1"})

    class DummyWebSocket:
        response = ModernHandshakeResponse()

        async def close(self) -> None:
            return None

    async def fake_websocket_connect(url: str, additional_headers: Any = None, **kwargs: Any):
        return DummyWebSocket()

    client = HttpClient()
    monkeypatch.setattr("fletplus.http.client._load_websocket_connect", lambda: fake_websocket_connect)

    intercepted: list[tuple[int, str | None]] = []

    def after(response: httpx.Response) -> httpx.Response:
        intercepted.append((response.status_code, response.headers.get("X-Modern")))
        return response

    client.add_interceptor(HttpInterceptor(after_response=after))

    websocket = await client.ws_connect("https://example.org/socket")
    await websocket.aclose()
    await client.aclose()

    assert intercepted == [(201, "1")]
    assert websocket.response.status_code == 201
    assert websocket.response.headers["X-Modern"] == "1"


@pytest.mark.anyio
async def test_http_client_websocket_headers_use_additional_headers(monkeypatch: pytest.MonkeyPatch):
    captured_headers = {}

    class DummyWebSocket:
        response_headers = {}
        response_status = 101

        async def close(self) -> None:
            return None

    async def modern_connect(url: str, additional_headers: Any = None, **kwargs: Any):
        assert "extra_headers" not in kwargs
        captured_headers["request"] = {k.lower(): v for k, v in dict(additional_headers or []).items()}
        return DummyWebSocket()

    client = HttpClient()
    monkeypatch.setattr("fletplus.http.client._load_websocket_connect", lambda: modern_connect)

    ws = await client.ws_connect(
        "https://example.org/ws",
        headers={"X-From-Request": "1"},
        additional_headers={"X-From-Arg": "2"},
    )
    await ws.aclose()
    await client.aclose()

    assert captured_headers["request"]["x-from-request"] == "1"
    assert captured_headers["request"]["x-from-arg"] == "2"


@pytest.mark.anyio
async def test_http_client_ws_connect_forwards_headers_and_params(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    class DummyWebSocket:
        response_headers = {}
        response_status = 101

        async def close(self) -> None:
            return None

    async def modern_connect(url: str, additional_headers: Any = None, **kwargs: Any):
        captured["url"] = url
        captured["headers"] = {k.lower(): v for k, v in dict(additional_headers or []).items()}
        return DummyWebSocket()

    client = HttpClient()
    monkeypatch.setattr("fletplus.http.client._load_websocket_connect", lambda: modern_connect)

    ws = await client.ws_connect(
        "https://example.org/ws",
        headers={"X-From-Request": "1"},
        params={"channel": "chat"},
    )
    await ws.aclose()
    await client.aclose()

    assert captured["url"] == "https://example.org/ws?channel=chat"
    assert captured["headers"]["x-from-request"] == "1"


@pytest.mark.anyio
async def test_http_client_ws_connect_forwards_auth_and_cookies(monkeypatch: pytest.MonkeyPatch):
    captured_headers = {}

    class DummyWebSocket:
        response_headers = {}
        response_status = 101

        async def close(self) -> None:
            return None

    async def modern_connect(url: str, additional_headers: Any = None, **kwargs: Any):
        captured_headers.update({k.lower(): v for k, v in dict(additional_headers or []).items()})
        return DummyWebSocket()

    client = HttpClient()
    monkeypatch.setattr("fletplus.http.client._load_websocket_connect", lambda: modern_connect)

    ws = await client.ws_connect(
        "https://example.org/ws",
        auth=("alice", "secret"),
        cookies={"session": "abc123"},
    )
    await ws.aclose()
    await client.aclose()

    assert captured_headers["authorization"].startswith("Basic ")
    assert captured_headers["cookie"] == "session=abc123"


@pytest.mark.anyio
async def test_http_client_ws_connect_additional_headers_override_extra_headers(monkeypatch: pytest.MonkeyPatch):
    captured_headers = {}

    class DummyWebSocket:
        response_headers = {}
        response_status = 101

        async def close(self) -> None:
            return None

    async def modern_connect(url: str, additional_headers: Any = None, **kwargs: Any):
        captured_headers.update({k.lower(): v for k, v in dict(additional_headers or []).items()})
        return DummyWebSocket()

    client = HttpClient()
    monkeypatch.setattr("fletplus.http.client._load_websocket_connect", lambda: modern_connect)

    ws = await client.ws_connect(
        "https://example.org/ws",
        headers={"X-Conflict": "request"},
        extra_headers={"X-Conflict": "legacy"},
        additional_headers={"X-Conflict": "additional"},
    )
    await ws.aclose()
    await client.aclose()

    assert captured_headers["x-conflict"] == "additional"


@pytest.mark.anyio
async def test_http_client_websocket_headers_use_extra_headers_fallback(monkeypatch: pytest.MonkeyPatch):
    captured_headers = {}

    class DummyWebSocket:
        response_headers = {}
        response_status = 101

        async def close(self) -> None:
            return None

    async def legacy_connect(url: str, extra_headers: Any = None, **kwargs: Any):
        assert "additional_headers" not in kwargs
        captured_headers["request"] = {k.lower(): v for k, v in dict(extra_headers or []).items()}
        return DummyWebSocket()

    client = HttpClient()
    monkeypatch.setattr("fletplus.http.client._load_websocket_connect", lambda: legacy_connect)

    ws = await client.ws_connect(
        "https://example.org/ws",
        headers={"X-From-Request": "1"},
        additional_headers={"X-From-Arg": "2"},
    )
    await ws.aclose()
    await client.aclose()

    assert captured_headers["request"]["x-from-request"] == "1"
    assert captured_headers["request"]["x-from-arg"] == "2"


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
async def test_http_client_ws_connect_closes_websocket_when_after_hook_fails(monkeypatch: pytest.MonkeyPatch):
    class DummyWebSocket:
        response_headers = {}
        response_status = 101

        def __init__(self) -> None:
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    created: dict[str, DummyWebSocket] = {}

    async def fake_websocket_connect(url: str, additional_headers: Any = None, **kwargs: Any):
        websocket = DummyWebSocket()
        created["ws"] = websocket
        return websocket

    client = HttpClient()
    monkeypatch.setattr("fletplus.http.client._load_websocket_connect", lambda: fake_websocket_connect)

    def after_hook(_event: Any) -> None:
        raise RuntimeError("hook after failed")

    client.add_after_hook(after_hook)

    with pytest.raises(RuntimeError, match="hook after failed"):
        await client.ws_connect("https://example.org/socket")

    await client.aclose()

    assert created["ws"].closed is True


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
    assert list(tmp_path.glob("*.json")) == []


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
    cached_entries = list(tmp_path.glob("*.json"))
    assert len(cached_entries) == 1


@pytest.mark.anyio
async def test_http_client_no_cache_persists_metadata_without_serving_from_cache(tmp_path: Path):
    call_count = 0
    seen_if_none_match: list[str | None] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        seen_if_none_match.append(request.headers.get("If-None-Match"))
        return httpx.Response(
            200,
            headers={
                "Cache-Control": "no-cache",
                "ETag": '"abc123"',
                "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT",
            },
            json={"count": call_count},
        )

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get("https://example.org/no-cache-metadata")
    second = await client.get("https://example.org/no-cache-metadata")

    await client.aclose()

    assert first.json() == {"count": 1}
    assert second.json() == {"count": 2}
    assert call_count == 2
    assert seen_if_none_match == [None, '"abc123"']

    last_event = client.after_request.get()
    assert last_event is not None
    assert last_event.from_cache is False

    cache_files = list(tmp_path.glob("*.json"))
    assert len(cache_files) == 1
    cached_response = cache.get(cache_files[0].stem, request=httpx.Request("GET", "https://example.org/no-cache-metadata"))
    assert cached_response is not None
    assert cached_response.headers["ETag"] == '"abc123"'
    assert cached_response.headers["Last-Modified"] == "Wed, 21 Oct 2015 07:28:00 GMT"


@pytest.mark.anyio
async def test_http_client_revalidates_no_cache_with_etag_and_uses_cached_body(tmp_path: Path):
    call_count = 0
    seen_if_none_match: list[str | None] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        seen_if_none_match.append(request.headers.get("If-None-Match"))
        if call_count == 1:
            return httpx.Response(
                200,
                headers={
                    "Cache-Control": "no-cache",
                    "ETag": '"etag-v1"',
                    "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT",
                    "X-Version": "v1",
                },
                json={"count": 1, "value": "cached"},
            )
        return httpx.Response(
            304,
            headers={
                "ETag": '"etag-v1"',
                "X-Version": "v2",
            },
        )

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get("https://example.org/revalidate-etag")
    second = await client.get("https://example.org/revalidate-etag")

    await client.aclose()

    assert call_count == 2
    assert seen_if_none_match == [None, '"etag-v1"']
    assert first.json() == {"count": 1, "value": "cached"}
    assert second.status_code == 200
    assert second.json() == {"count": 1, "value": "cached"}
    assert second.headers["X-Version"] == "v2"

    last_event = client.after_request.get()
    assert last_event is not None
    assert last_event.from_cache is True


@pytest.mark.anyio
async def test_http_client_revalidates_no_cache_with_last_modified_when_no_etag(tmp_path: Path):
    call_count = 0
    seen_if_modified_since: list[str | None] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        seen_if_modified_since.append(request.headers.get("If-Modified-Since"))
        if call_count == 1:
            return httpx.Response(
                200,
                headers={
                    "Cache-Control": "no-cache",
                    "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT",
                    "X-Version": "lm-v1",
                },
                json={"count": 1, "value": "cached"},
            )
        return httpx.Response(
            304,
            headers={
                "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT",
                "X-Version": "lm-v2",
            },
        )

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get("https://example.org/revalidate-last-modified")
    second = await client.get("https://example.org/revalidate-last-modified")

    await client.aclose()

    assert call_count == 2
    assert seen_if_modified_since == [None, "Wed, 21 Oct 2015 07:28:00 GMT"]
    assert first.json() == {"count": 1, "value": "cached"}
    assert second.status_code == 200
    assert second.json() == {"count": 1, "value": "cached"}
    assert second.headers["X-Version"] == "lm-v2"

    last_event = client.after_request.get()
    assert last_event is not None
    assert last_event.from_cache is True


@pytest.mark.anyio
async def test_http_client_no_cache_without_validators_does_full_fetch(tmp_path: Path):
    call_count = 0
    seen_conditional_headers: list[tuple[str | None, str | None]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        seen_conditional_headers.append(
            (request.headers.get("If-None-Match"), request.headers.get("If-Modified-Since"))
        )
        return httpx.Response(
            200,
            headers={
                "Cache-Control": "no-cache",
            },
            json={"count": call_count},
        )

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get("https://example.org/no-validators")
    second = await client.get("https://example.org/no-validators")

    await client.aclose()

    assert call_count == 2
    assert seen_conditional_headers == [(None, None), (None, None)]
    assert first.json() == {"count": 1}
    assert second.json() == {"count": 2}

    last_event = client.after_request.get()
    assert last_event is not None
    assert last_event.from_cache is False


@pytest.mark.anyio
async def test_http_client_preserves_network_error_when_after_hook_fails(caplog: pytest.LogCaptureFixture):
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("network down", request=request)

    client = HttpClient(transport=httpx.MockTransport(handler))

    async def broken_after(_event):
        raise RuntimeError("after-hook-boom")

    client.add_after_hook(broken_after)

    with pytest.raises(httpx.ConnectError, match="network down"):
        await client.get("https://example.org/fail")

    await client.aclose()

    assert "Fallo al ejecutar hooks 'after' de HttpClient." in caplog.text


@pytest.mark.anyio
async def test_http_client_raises_after_hook_error_when_request_succeeds(caplog: pytest.LogCaptureFixture):
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    client = HttpClient(transport=httpx.MockTransport(handler))

    async def broken_after(_event):
        raise RuntimeError("after-hook-boom")

    client.add_after_hook(broken_after)

    with pytest.raises(RuntimeError, match="after-hook-boom"):
        await client.get("https://example.org/ok")

    await client.aclose()

    assert "Fallo al ejecutar hooks 'after' de HttpClient." in caplog.text


@pytest.mark.anyio
async def test_http_client_preserves_before_hook_error_when_after_hook_fails(caplog: pytest.LogCaptureFixture):
    client = HttpClient(transport=httpx.MockTransport(lambda _request: httpx.Response(200)))

    def broken_before(_event):
        raise ValueError("before-hook-boom")

    async def broken_after(_event):
        raise RuntimeError("after-hook-boom")

    client.add_before_hook(broken_before)
    client.add_after_hook(broken_after)

    with pytest.raises(ValueError, match="before-hook-boom"):
        await client.get("https://example.org/fail-before")

    await client.aclose()

    assert "Fallo al ejecutar hooks 'after' de HttpClient." in caplog.text


@pytest.mark.anyio
async def test_http_client_request_cache_control_substring_does_not_disable_cache(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"count": call_count})

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get(
        "https://example.org/request-substring",
        headers={"Cache-Control": "x-no-cache, x-no-store"},
    )
    second = await client.get(
        "https://example.org/request-substring",
        headers={"Cache-Control": "x-no-cache, x-no-store"},
    )

    await client.aclose()

    assert first.json() == {"count": 1}
    assert second.json() == {"count": 1}
    assert call_count == 1


@pytest.mark.anyio
async def test_http_client_response_cache_control_substring_does_not_disable_cache(tmp_path: Path):
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            headers={"Cache-Control": "x-no-cache, x-no-store, nonprivate"},
            json={"count": call_count},
        )

    cache = DiskCache(tmp_path)
    client = HttpClient(cache=cache, transport=httpx.MockTransport(handler))

    first = await client.get("https://example.org/response-substring")
    second = await client.get("https://example.org/response-substring")

    await client.aclose()

    assert first.json() == {"count": 1}
    assert second.json() == {"count": 1}
    assert call_count == 1


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
