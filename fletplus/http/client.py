"""Cliente HTTP reactivo con soporte para hooks, interceptores y caché."""

from __future__ import annotations

import contextlib
import importlib
import inspect
import os
import time
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Awaitable, Callable, Iterable, MutableMapping

import httpx

from .disk_cache_py import DiskCache as _PyDiskCache

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


def _load_disk_cache() -> type[_PyDiskCache]:
    spec = importlib.util.find_spec("fletplus.http.disk_cache")
    if spec is None:
        return _PyDiskCache
    module = importlib.import_module("fletplus.http.disk_cache")
    cache_cls = getattr(module, "DiskCache", None)
    if cache_cls is None:
        return _PyDiskCache
    return cache_cls


DiskCache = _load_disk_cache()


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
                    # DiskCache.get construye un httpx.Response nuevo en cada lectura,
                    # así que los interceptores pueden modificarlo sin necesidad de
                    # clonar ni invalidar la instancia para evitar efectos secundarios
                    # compartidos entre llamadas.
                    for interceptor in reversed(self._interceptors):
                        cached = await interceptor.apply_response(cached)
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
        request = event.request
        try:
            for interceptor in self._interceptors:
                request = await interceptor.apply_request(request)
            event.request = request

            connect_kwargs = dict(kwargs)
            connect_kwargs.pop("headers", None)
            connect_kwargs.pop("params", None)
            websocket = await self._client.websocket_connect(
                str(request.url), headers=request.headers, **connect_kwargs
            )
            response = websocket.response
            for interceptor in reversed(self._interceptors):
                response = await interceptor.apply_response(response)
            websocket.response = response
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
            response=response,
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
