"""Cliente HTTP reactivo con soporte para hooks, interceptores y caché."""

from __future__ import annotations

import base64
import contextlib
import hashlib
import inspect
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Awaitable, Callable, Iterable, MutableMapping

import httpx

from fletplus.state import Signal

RequestHook = Callable[["RequestEvent"], Awaitable[None] | None]
ResponseHook = Callable[["ResponseEvent"], Awaitable[None] | None]
RequestInterceptor = Callable[[httpx.Request], Awaitable[httpx.Request | None] | httpx.Request | None]
ResponseInterceptor = Callable[[httpx.Response], Awaitable[httpx.Response | None] | httpx.Response | None]


@dataclass(slots=True)
class RequestEvent:
    """Información emitida antes de enviar una petición."""

    request: httpx.Request
    context: MutableMapping[str, Any] = field(default_factory=dict)
    cache_key: str | None = None
    timestamp: float = field(default_factory=time.time)

    @property
    def method(self) -> str:
        return self.request.method

    @property
    def url(self) -> str:
        return str(self.request.url)

    @property
    def headers(self) -> MappingProxyType[str, str]:
        return MappingProxyType(dict(self.request.headers))


@dataclass(slots=True)
class ResponseEvent:
    """Información emitida tras completar una petición."""

    request_event: RequestEvent
    response: httpx.Response | None
    context: MutableMapping[str, Any]
    from_cache: bool = False
    error: Exception | None = None
    timestamp: float = field(default_factory=time.time)

    @property
    def status_code(self) -> int | None:
        return self.response.status_code if self.response is not None else None

    @property
    def elapsed(self) -> float | None:
        if self.response is None:
            return None
        return self.response.elapsed.total_seconds() if self.response.elapsed else None


@dataclass(slots=True)
class HttpInterceptor:
    """Interceptor configurable para peticiones HTTP."""

    before_request: RequestInterceptor | None = None
    after_response: ResponseInterceptor | None = None

    async def apply_request(self, request: httpx.Request) -> httpx.Request:
        if self.before_request is None:
            return request
        result = self.before_request(request)
        if inspect.isawaitable(result):
            result = await result  # type: ignore[assignment]
        return result or request

    async def apply_response(self, response: httpx.Response) -> httpx.Response:
        if self.after_response is None:
            return response
        result = self.after_response(response)
        if inspect.isawaitable(result):
            result = await result  # type: ignore[assignment]
        return result or response


@dataclass(slots=True)
class _CacheEntry:
    status_code: int
    headers: list[tuple[str, str]]
    content: bytes
    http_version: str | None
    reason_phrase: str | None
    timestamp: float


class DiskCache:
    """Caché persistente sencilla para respuestas HTTP."""

    def __init__(self, directory: str | os.PathLike[str], *, max_entries: int = 128) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries

    # ------------------------------------------------------------------
    def build_key(self, request: httpx.Request) -> str:
        body = request.content or b""
        headers = sorted((k.lower(), v) for k, v in request.headers.items())
        payload = json.dumps(
            {
                "method": request.method,
                "url": str(request.url),
                "headers": headers,
                "body": base64.b64encode(body).decode("ascii"),
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    def _path_for(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    # ------------------------------------------------------------------
    def get(self, key: str, *, request: httpx.Request | None = None) -> httpx.Response | None:
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text("utf-8"))
            entry = _CacheEntry(
                status_code=data["status_code"],
                headers=[(item[0], item[1]) for item in data["headers"]],
                content=base64.b64decode(data["content"]),
                http_version=data.get("http_version"),
                reason_phrase=data.get("reason_phrase"),
                timestamp=data["timestamp"],
            )
        except Exception:
            path.unlink(missing_ok=True)
            return None

        headers = [(name.encode("latin-1"), value.encode("latin-1")) for name, value in entry.headers]
        response = httpx.Response(
            entry.status_code,
            headers=headers,
            content=entry.content,
            request=request,
            extensions={},
        )
        if entry.http_version:
            response.extensions["http_version"] = entry.http_version
        if entry.reason_phrase:
            response.extensions["reason_phrase"] = entry.reason_phrase
        os.utime(path, None)
        return response

    # ------------------------------------------------------------------
    def set(self, key: str, response: httpx.Response) -> None:
        path = self._path_for(key)
        headers = [(name.decode("latin-1"), value.decode("latin-1")) for name, value in response.headers.raw]
        entry = {
            "status_code": response.status_code,
            "headers": headers,
            "content": base64.b64encode(response.content).decode("ascii"),
            "http_version": response.extensions.get("http_version"),
            "reason_phrase": response.reason_phrase,
            "timestamp": time.time(),
        }
        path.write_text(json.dumps(entry), "utf-8")
        self._enforce_limit()

    # ------------------------------------------------------------------
    def _enforce_limit(self) -> None:
        files = sorted(self.directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for extra in files[self.max_entries :]:
            with contextlib.suppress(OSError):
                extra.unlink()

    # ------------------------------------------------------------------
    def clear(self) -> None:
        for file in self.directory.glob("*.json"):
            with contextlib.suppress(OSError):
                file.unlink()


class _HookManager:
    """Gestiona los hooks y señales asociados a las peticiones."""

    def __init__(self) -> None:
        self._before_callbacks: list[RequestHook] = []
        self._after_callbacks: list[ResponseHook] = []
        self.before_signal: Signal[RequestEvent | None] = Signal(None)
        self.after_signal: Signal[ResponseEvent | None] = Signal(None)

    # ------------------------------------------------------------------
    def add_before(self, callback: RequestHook) -> Callable[[], None]:
        self._before_callbacks.append(callback)

        def unsubscribe() -> None:
            with contextlib.suppress(ValueError):
                self._before_callbacks.remove(callback)

        return unsubscribe

    # ------------------------------------------------------------------
    def add_after(self, callback: ResponseHook) -> Callable[[], None]:
        self._after_callbacks.append(callback)

        def unsubscribe() -> None:
            with contextlib.suppress(ValueError):
                self._after_callbacks.remove(callback)

        return unsubscribe

    # ------------------------------------------------------------------
    async def emit_before(self, event: RequestEvent) -> None:
        self.before_signal.set(event)
        for callback in list(self._before_callbacks):
            result = callback(event)
            if inspect.isawaitable(result):
                await result

    # ------------------------------------------------------------------
    async def emit_after(self, event: ResponseEvent) -> None:
        self.after_signal.set(event)
        for callback in list(self._after_callbacks):
            result = callback(event)
            if inspect.isawaitable(result):
                await result


class HttpClient:
    """Cliente HTTP asincrónico con integración reactiva."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: httpx.Timeout | float | None = None,
        cache: DiskCache | None = None,
        interceptors: Iterable[HttpInterceptor] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        client_kwargs: dict[str, Any] = {
            "timeout": timeout,
            "transport": transport,
        }
        if base_url is not None:
            client_kwargs["base_url"] = base_url
        self._client = httpx.AsyncClient(**client_kwargs)
        self._cache = cache
        self._hooks = _HookManager()
        self._interceptors: list[HttpInterceptor] = list(interceptors or [])

    # ------------------------------------------------------------------
    @property
    def before_request(self) -> Signal[RequestEvent | None]:
        return self._hooks.before_signal

    # ------------------------------------------------------------------
    @property
    def after_request(self) -> Signal[ResponseEvent | None]:
        return self._hooks.after_signal

    # ------------------------------------------------------------------
    def add_before_hook(self, callback: RequestHook) -> Callable[[], None]:
        return self._hooks.add_before(callback)

    # ------------------------------------------------------------------
    def add_after_hook(self, callback: ResponseHook) -> Callable[[], None]:
        return self._hooks.add_after(callback)

    # ------------------------------------------------------------------
    def add_interceptor(self, interceptor: HttpInterceptor) -> None:
        self._interceptors.append(interceptor)

    # ------------------------------------------------------------------
    async def request(
        self,
        method: str,
        url: str,
        *,
        cache: bool | None = None,
        context: MutableMapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        request = self._client.build_request(method, url, **kwargs)
        request_context: MutableMapping[str, Any] = context or {}
        use_cache = cache if cache is not None else True
        event = RequestEvent(request=request, context=request_context, cache_key=None)
        await self._hooks.emit_before(event)
        request = event.request
        cache_key: str | None = None
        response: httpx.Response | None = None
        from_cache = False
        error: Exception | None = None

        try:
            for interceptor in self._interceptors:
                request = await interceptor.apply_request(request)
            event.request = request

            if self._cache and use_cache and request.method.upper() == "GET":
                cache_key = self._cache.build_key(request)
                event.cache_key = cache_key

            if cache_key and self._cache:
                cached = self._cache.get(cache_key, request=request)
                if cached is not None:
                    response = cached
                    from_cache = True
            if response is None:
                response = await self._client.send(request)
                for interceptor in reversed(self._interceptors):
                    response = await interceptor.apply_response(response)
                if cache_key and self._cache:
                    await response.aread()
                    self._cache.set(cache_key, response)
        except Exception as exc:  # pragma: no cover - rutas excepcionales
            error = exc
            raise
        finally:
            response_event = ResponseEvent(
                request_event=event,
                response=response,
                context=request_context,
                from_cache=from_cache,
                error=error,
            )
            await self._hooks.emit_after(response_event)
        assert response is not None
        return response

    # ------------------------------------------------------------------
    async def get(
        self,
        url: str,
        *,
        params: MutableMapping[str, Any] | None = None,
        headers: MutableMapping[str, str] | None = None,
        cache: bool | None = None,
        context: MutableMapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return await self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            cache=cache,
            context=context,
            **kwargs,
        )

    # ------------------------------------------------------------------
    async def post(
        self,
        url: str,
        *,
        data: Any = None,
        json_data: Any = None,
        headers: MutableMapping[str, str] | None = None,
        context: MutableMapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        payload = dict(kwargs)
        if data is not None:
            payload["data"] = data
        if json_data is not None:
            payload["json"] = json_data
        if headers is not None:
            payload["headers"] = headers
        return await self.request("POST", url, cache=False, context=context, **payload)

    # ------------------------------------------------------------------
    async def ws_connect(self, url: str, *, context: MutableMapping[str, Any] | None = None, **kwargs: Any):
        request = self._client.build_request("GET", url, **{k: v for k, v in kwargs.items() if k in {"headers", "params"}})
        request_context: MutableMapping[str, Any] = context or {}
        request_context.setdefault("websocket", True)
        event = RequestEvent(request=request, context=request_context, cache_key=None)
        await self._hooks.emit_before(event)
        try:
            websocket = await self._client.websocket_connect(url, **kwargs)
        except Exception as exc:  # pragma: no cover - rutas excepcionales
            response_event = ResponseEvent(
                request_event=event,
                response=None,
                context=request_context,
                from_cache=False,
                error=exc,
            )
            await self._hooks.emit_after(response_event)
            raise
        response_event = ResponseEvent(
            request_event=event,
            response=websocket.response,
            context=request_context,
            from_cache=False,
            error=None,
        )
        await self._hooks.emit_after(response_event)
        return websocket

    # ------------------------------------------------------------------
    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    async def __aenter__(self) -> "HttpClient":
        await self._client.__aenter__()
        return self

    # ------------------------------------------------------------------
    async def __aexit__(self, *exc_info: Any) -> None:
        await self._client.__aexit__(*exc_info)


__all__ = [
    "DiskCache",
    "HttpClient",
    "HttpInterceptor",
    "RequestEvent",
    "ResponseEvent",
]
