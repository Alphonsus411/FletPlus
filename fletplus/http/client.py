"""Cliente HTTP reactivo con soporte para hooks, interceptores y caché."""

from __future__ import annotations

import contextlib
import email.utils
import importlib
import inspect
import logging
import time
from dataclasses import dataclass, field
from datetime import timezone
from types import MappingProxyType
from typing import Any, Awaitable, Callable, Iterable, MutableMapping

import httpx

from fletplus.state import Signal

from .disk_cache_py import DiskCache as _PyDiskCache

RequestHook = Callable[["RequestEvent"], Awaitable[None] | None]
ResponseHook = Callable[["ResponseEvent"], Awaitable[None] | None]
RequestInterceptor = Callable[[httpx.Request], Awaitable[httpx.Request | None] | httpx.Request | None]
ResponseInterceptor = Callable[[httpx.Response], Awaitable[httpx.Response | None] | httpx.Response | None]

logger = logging.getLogger(__name__)

_WS_REQUEST_KWARGS = {"headers", "params", "cookies", "auth"}
_WS_BUILD_REQUEST_KWARGS = {"headers", "params", "cookies"}
_WS_UNSUPPORTED_HTTPX_KWARGS = {
    "content",
    "data",
    "files",
    "json",
    "method",
    "url",
}

_DEFAULT_SENSITIVE_QUERY_PARAMS = frozenset(
    {"token", "access_token", "api_key", "apikey", "auth", "signature", "sig"}
)


def _parse_cache_control_max_age(cache_control: str) -> int | None:
    if not cache_control:
        return None
    for directive in cache_control.split(","):
        directive = directive.strip().lower()
        if not directive.startswith("max-age"):
            continue
        parts = directive.split("=", 1)
        if len(parts) != 2:
            continue
        value = parts[1].strip().strip('"')
        if not value:
            continue
        try:
            max_age = int(value)
        except ValueError:
            continue
        return max_age
    return None


def _parse_cache_control_tokens(*header_values: str) -> set[str]:
    """Parsea directivas Cache-Control/Pragma en un set normalizado de tokens."""
    tokens: set[str] = set()
    for header_value in header_values:
        if not header_value:
            continue
        for directive in header_value.split(","):
            normalized = directive.strip().lower()
            if not normalized:
                continue
            token, _, _value = normalized.partition("=")
            token = token.strip()
            if token:
                tokens.add(token)
    return tokens


def _parse_expires_timestamp(expires: str) -> float | None:
    if not expires:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(expires)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


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
    try:
        module = importlib.import_module("fletplus.http.disk_cache")
    except ImportError:
        return _PyDiskCache
    except Exception:
        return _PyDiskCache
    cache_cls = getattr(module, "DiskCache", None)
    if cache_cls is None:
        return _PyDiskCache
    return cache_cls


DiskCache = _load_disk_cache()


class _WebSocketConnection:
    def __init__(self, websocket: Any, response: httpx.Response) -> None:
        self._websocket = websocket
        self.response = response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._websocket, name)

    async def aclose(self) -> None:
        close = getattr(self._websocket, "close", None)
        if close is None:
            close = getattr(self._websocket, "aclose", None)
        if close is None:
            return
        result = close()
        if inspect.isawaitable(result):
            await result

    async def __aenter__(self) -> "_WebSocketConnection":
        enter = getattr(self._websocket, "__aenter__", None)
        if enter is not None:
            result = enter()
            if inspect.isawaitable(result):
                await result
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        exit_method = getattr(self._websocket, "__aexit__", None)
        if exit_method is not None:
            result = exit_method(*exc_info)
            if inspect.isawaitable(result):
                await result
            return
        await self.aclose()


def _load_websocket_connect() -> Callable[..., Awaitable[Any]]:
    spec = importlib.util.find_spec("websockets")
    if spec is None:
        raise RuntimeError(
            "La dependencia 'websockets' no está disponible. Instala 'websockets' para usar ws_connect()."
        )
    try:
        module = importlib.import_module("websockets")
    except Exception as exc:  # pragma: no cover - import dependiente
        raise RuntimeError(
            "No se pudo importar 'websockets'. Instala la dependencia para usar ws_connect()."
        ) from exc
    connect = getattr(module, "connect", None)
    if connect is None:
        raise RuntimeError(
            "No se encontró websockets.connect. Actualiza la dependencia 'websockets' para usar ws_connect()."
        )
    return connect


def _build_websocket_response(request: httpx.Request, websocket: Any) -> httpx.Response:
    status_code: int | None = getattr(websocket, "response_status", None)
    response_headers = getattr(websocket, "response_headers", None)

    websocket_response = getattr(websocket, "response", None)
    if websocket_response is not None:
        if status_code is None:
            status_code = getattr(websocket_response, "status_code", None)
        if response_headers is None:
            response_headers = getattr(websocket_response, "headers", None)

    headers: dict[str, str] = {}
    if response_headers:
        items = getattr(response_headers, "items", None)

        def _as_text(value: Any) -> str:
            if isinstance(value, bytes):
                return value.decode("latin1")
            return str(value)

        try:
            iterable = items() if callable(items) else response_headers
            headers = {_as_text(key): _as_text(value) for key, value in iterable}
        except Exception:
            headers = {}

    resolved_status = status_code if status_code is not None else 101
    return httpx.Response(status_code=resolved_status, headers=headers, request=request)


def _resolve_websocket_headers_arg(connect: Callable[..., Awaitable[Any]]) -> str:
    """Devuelve el nombre del argumento de headers para websockets.connect.

    Compatibilidad soportada:
    - websockets modernos (v14+): `additional_headers`
    - websockets anteriores: `extra_headers`

    Si la firma no puede inspeccionarse, se prioriza `additional_headers`.
    """

    preferred_arg = "additional_headers"
    fallback_arg = "extra_headers"
    with contextlib.suppress(TypeError, ValueError):
        parameters = inspect.signature(connect).parameters
        if preferred_arg in parameters:
            return preferred_arg
        if fallback_arg in parameters:
            return fallback_arg
    return preferred_arg


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
        sensitive_query_params: Iterable[str] | None = None,
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
        if sensitive_query_params is None:
            self._sensitive_query_params = _DEFAULT_SENSITIVE_QUERY_PARAMS
        else:
            self._sensitive_query_params = frozenset(
                key.strip().lower() for key in sensitive_query_params if key and key.strip()
            )

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
        allow_sensitive_cache: bool = False,
        context: MutableMapping[str, Any] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> httpx.Response:
        """Construye y envía una petición HTTP.

        Contrato de errores de hooks:
        - Si `emit_after` falla y ya existe un error principal de la petición,
          se conserva ese error principal y el fallo del hook solo se registra en logs.
        - Si `emit_after` falla y no existe error principal, el error del hook se propaga.

        Nota sobre caché: si los headers incluyen credenciales (`authorization`,
        `cookie` o `x-api-key`) o la URL contiene parámetros sensibles
        (p. ej. `api_key`, `token`), la caché se desactiva automáticamente para evitar
        persistir respuestas sensibles. Para permitirlo debes habilitarlo
        explícitamente con `allow_sensitive_cache=True`. También se respetan
        las cabeceras
        de la petición `Cache-Control`/`Pragma` con `no-store` o `no-cache`
        (a menos que se pase `cache=True`), y en la respuesta se consideran
        `Cache-Control`/`Pragma` con `no-store` o `private`, la presencia de
        `Set-Cookie` y solo se cachean respuestas exitosas (2xx). Si la respuesta
        llega con `no-cache`, se persiste en disco (incluyendo ETag/Last-Modified
        en headers) pero no se sirve directamente sin una futura revalidación.
        Si `stream=True`,
        se desactiva la caché para no cargar el cuerpo completo en memoria.
        """
        stream = kwargs.pop("stream", stream)
        request = self._client.build_request(method, url, **kwargs)
        request_context: MutableMapping[str, Any] = context if context is not None else {}
        event = RequestEvent(request=request, context=request_context, cache_key=None)
        try:
            await self._hooks.emit_before(event)
        except Exception as exc:  # pragma: no cover - rutas excepcionales
            response_event = ResponseEvent(
                request_event=event,
                response=None,
                context=request_context,
                from_cache=False,
                error=exc,
            )
            await self._emit_after_with_guard(response_event, primary_error=exc)
            raise
        request = event.request
        cache_key: str | None = None
        response: httpx.Response | None = None
        from_cache = False
        error: Exception | None = None
        cached_for_revalidation: httpx.Response | None = None

        try:
            for interceptor in self._interceptors:
                request = await interceptor.apply_request(request)
            event.request = request

            use_cache = cache if cache is not None else True
            if stream:
                use_cache = False
            cache_control = request.headers.get("cache-control", "")
            pragma = request.headers.get("pragma", "")
            request_directives = _parse_cache_control_tokens(cache_control, pragma)
            has_no_cache = "no-cache" in request_directives
            has_no_store = "no-store" in request_directives
            if cache is not True and (has_no_cache or has_no_store):
                use_cache = False

            credential_headers = {"authorization", "cookie", "x-api-key"}
            has_credentials = any(request.headers.get(name) is not None for name in credential_headers)
            has_sensitive_query_params = any(
                key.lower() in self._sensitive_query_params for key in request.url.params.keys()
            )
            if (has_credentials or has_sensitive_query_params) and not allow_sensitive_cache:
                use_cache = False

            if self._cache and use_cache and request.method.upper() == "GET":
                cache_key = self._cache.build_key(request)
                event.cache_key = cache_key

            if cache_key and self._cache:
                cached = self._cache.get(cache_key, request=request)
                cached_for_revalidation = cached
                if cached is not None:
                    cached_directives = _parse_cache_control_tokens(
                        cached.headers.get("cache-control", ""),
                        cached.headers.get("pragma", ""),
                    )
                    should_revalidate = "no-cache" in cached_directives
                    if not should_revalidate:
                        cached_for_revalidation = None
                else:
                    should_revalidate = False
                if cached is not None:
                    if should_revalidate:
                        etag = cached.headers.get("etag")
                        last_modified = cached.headers.get("last-modified")
                        if etag:
                            request.headers["If-None-Match"] = etag
                        elif last_modified:
                            request.headers["If-Modified-Since"] = last_modified
                    else:
                        # DiskCache.get construye un httpx.Response nuevo en cada lectura,
                        # así que los interceptores pueden modificarlo sin necesidad de
                        # clonar ni invalidar la instancia para evitar efectos secundarios
                        # compartidos entre llamadas.
                        for interceptor in reversed(self._interceptors):
                            cached = await interceptor.apply_response(cached)
                        response = cached
                        from_cache = True
            if response is None:
                response = await self._client.send(request, stream=stream)
                if (
                    response.status_code == 304
                    and cache_key
                    and self._cache
                    and request.method.upper() == "GET"
                    and cached_for_revalidation is not None
                ):
                    merged_headers = dict(cached_for_revalidation.headers)
                    merged_headers.update(dict(response.headers))
                    response = httpx.Response(
                        cached_for_revalidation.status_code,
                        headers=merged_headers,
                        content=cached_for_revalidation.content,
                        request=request,
                        extensions=dict(cached_for_revalidation.extensions),
                    )
                    from_cache = True
                for interceptor in reversed(self._interceptors):
                    response = await interceptor.apply_response(response)
                if cache_key and self._cache and not stream:
                    cache_control = response.headers.get("cache-control", "")
                    pragma = response.headers.get("pragma", "")
                    response_directives = _parse_cache_control_tokens(cache_control, pragma)
                    has_no_store = "no-store" in response_directives
                    has_private = "private" in response_directives
                    has_set_cookie = response.headers.get("set-cookie") is not None
                    is_success = 200 <= response.status_code <= 299
                    # Respeta no-store/private/set-cookie y evita cachear contenido sensible.
                    # `no-cache` se persiste para futura revalidación.
                    should_cache = not (has_no_store or has_private or has_set_cookie)
                    max_age = _parse_cache_control_max_age(cache_control)
                    now = time.time()
                    expires_at: float | None = None
                    if max_age is not None:
                        if max_age <= 0:
                            should_cache = False
                        else:
                            expires_at = now + max_age
                    else:
                        expires_at = _parse_expires_timestamp(response.headers.get("expires", ""))
                        if expires_at is not None and expires_at <= now:
                            should_cache = False
                    if should_cache and is_success:
                        await response.aread()
                        self._cache.set(cache_key, response, expires_at=expires_at)
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
            await self._emit_after_with_guard(response_event, primary_error=error)
        if response is None:
            raise RuntimeError("La respuesta HTTP es None después de ejecutar la petición.")
        return response

    # ------------------------------------------------------------------
    async def _emit_after_with_guard(
        self,
        response_event: ResponseEvent,
        *,
        primary_error: Exception | None,
    ) -> None:
        try:
            await self._hooks.emit_after(response_event)
        except Exception:
            logger.exception("Fallo al ejecutar hooks 'after' de HttpClient.")
            if primary_error is None:
                raise

    # ------------------------------------------------------------------
    async def get(
        self,
        url: str,
        *,
        params: MutableMapping[str, Any] | None = None,
        headers: MutableMapping[str, str] | None = None,
        cache: bool | None = None,
        allow_sensitive_cache: bool = False,
        context: MutableMapping[str, Any] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> httpx.Response:
        """Atajo para peticiones GET con soporte opcional de streaming."""
        return await self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            cache=cache,
            allow_sensitive_cache=allow_sensitive_cache,
            context=context,
            stream=stream,
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
        allow_sensitive_cache: bool = False,
        context: MutableMapping[str, Any] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> httpx.Response:
        """Atajo para peticiones POST con soporte opcional de streaming."""
        payload = dict(kwargs)
        if data is not None:
            payload["data"] = data
        if json_data is not None:
            payload["json"] = json_data
        if headers is not None:
            payload["headers"] = headers
        return await self.request(
            "POST",
            url,
            cache=False,
            allow_sensitive_cache=allow_sensitive_cache,
            context=context,
            stream=stream,
            **payload,
        )

    # ------------------------------------------------------------------
    async def ws_connect(self, url: str, *, context: MutableMapping[str, Any] | None = None, **kwargs: Any):
        unsupported_httpx_kwargs = sorted(key for key in kwargs if key in _WS_UNSUPPORTED_HTTPX_KWARGS)
        if unsupported_httpx_kwargs:
            supported = ", ".join(sorted(_WS_REQUEST_KWARGS))
            unsupported = ", ".join(unsupported_httpx_kwargs)
            raise TypeError(
                "ws_connect() no soporta payload HTTP tradicional para el handshake websocket. "
                f"Argumentos no soportados: {unsupported}. Usa solamente kwargs de request compatibles "
                f"({supported}) y opciones nativas de websockets.connect."
            )

        request_kwargs = {key: value for key, value in kwargs.items() if key in _WS_REQUEST_KWARGS}
        build_request_kwargs = {key: value for key, value in request_kwargs.items() if key in _WS_BUILD_REQUEST_KWARGS}
        request = self._client.build_request("GET", url, **build_request_kwargs)

        auth = request_kwargs.get("auth")
        if auth is not None:
            if isinstance(auth, tuple) and len(auth) == 2:
                auth = httpx.BasicAuth(auth[0], auth[1])
            if isinstance(auth, httpx.BasicAuth):
                auth_request_flow = auth.auth_flow(request)
                request = next(auth_request_flow)
            else:
                raise TypeError(
                    "ws_connect() solo soporta auth de tipo Basic para preparar el handshake. "
                    "Usa una tupla (usuario, contraseña) o httpx.BasicAuth."
                )
        request_context: MutableMapping[str, Any] = context if context is not None else {}
        request_context.setdefault("websocket", True)
        event = RequestEvent(request=request, context=request_context, cache_key=None)
        websocket: Any | None = None
        try:
            await self._hooks.emit_before(event)
        except Exception as exc:  # pragma: no cover - rutas excepcionales
            response_event = ResponseEvent(
                request_event=event,
                response=None,
                context=request_context,
                from_cache=False,
                error=exc,
            )
            await self._emit_after_with_guard(response_event, primary_error=exc)
            raise
        request = event.request
        try:
            for interceptor in self._interceptors:
                request = await interceptor.apply_request(request)
            event.request = request

            connect_kwargs = dict(kwargs)
            connect_kwargs.pop("headers", None)
            connect_kwargs.pop("params", None)
            additional_headers = connect_kwargs.pop("additional_headers", None)
            legacy_headers = connect_kwargs.pop("extra_headers", None)
            # Precedencia determinística: request.headers < extra_headers < additional_headers
            merged_headers = httpx.Headers(request.headers)
            if legacy_headers is not None:
                merged_headers.update(legacy_headers)
            if additional_headers is not None:
                merged_headers.update(additional_headers)

            websocket_connect = _load_websocket_connect()
            headers_arg = _resolve_websocket_headers_arg(websocket_connect)
            websocket = await websocket_connect(
                str(request.url),
                **{headers_arg: list(merged_headers.multi_items())},
                **connect_kwargs,
            )
            response = _build_websocket_response(request, websocket)
            try:
                for interceptor in reversed(self._interceptors):
                    response = await interceptor.apply_response(response)
                websocket = _WebSocketConnection(websocket, response)
            except Exception:
                await self._close_websocket_with_guard(websocket)
                raise
        except Exception as exc:  # pragma: no cover - rutas excepcionales
            response_event = ResponseEvent(
                request_event=event,
                response=None,
                context=request_context,
                from_cache=False,
                error=exc,
            )
            await self._emit_after_with_guard(response_event, primary_error=exc)
            raise
        response_event = ResponseEvent(
            request_event=event,
            response=response,
            context=request_context,
            from_cache=False,
            error=None,
        )
        try:
            await self._emit_after_with_guard(response_event, primary_error=None)
        except Exception:
            if websocket is not None:
                await self._close_websocket_with_guard(websocket, suppress_errors=True)
            raise
        return websocket

    # ------------------------------------------------------------------
    async def _close_websocket_with_guard(self, websocket: Any, *, suppress_errors: bool = False) -> None:
        try:
            close = getattr(websocket, "close", None)
            if close is None:
                close = getattr(websocket, "aclose", None)
            if close is None:
                return
            result = close()
            if inspect.isawaitable(result):
                await result
        except Exception:
            if suppress_errors:
                logger.exception("Fallo al cerrar websocket durante la limpieza defensiva.")
                return
            raise

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
