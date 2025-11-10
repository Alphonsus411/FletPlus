"""Sistema de contextos reactivos para FletPlus.

Este paquete introduce dos primitivas principales:

* :class:`Context`: representa un canal de comunicación nombrado cuyo valor se
  resuelve dinámicamente según el proveedor más cercano en la jerarquía
  actual. Puede obtenerse el valor actual mediante :meth:`Context.get`,
  suscribirse a cambios con :meth:`Context.subscribe` o utilizarlo como gestor
  de contexto (``with Context("tema") as provider: ...``) para crear un
  proveedor temporal.
* :class:`ContextProvider`: administra el valor concreto de un contexto dentro
  de un bloque o durante la vida útil de un componente. Internamente utiliza
  las señales reactivas de :mod:`fletplus.state` para notificar cambios a
  controles de Flet.

Los contextos están respaldados por :mod:`contextvars`, lo que permite anidar
proveedores sin interferencias entre hilos o *coroutines*. Cuando se resuelve
el valor de un contexto se toma el proveedor más interno disponible; si no hay
ninguno activo se devuelve el valor por defecto.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
import contextvars
from typing import Any, Callable, Generic, Optional, Tuple, TypeVar

from fletplus.state import Signal

__all__ = [
    "Context",
    "ContextProvider",
    "theme_context",
    "user_context",
    "locale_context",
]

_T = TypeVar("_T")


class _Missing:
    """Sentinela para detectar argumentos opcionales no proporcionados."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - representación trivial
        return "<MISSING>"


MISSING = _Missing()


class Context(Generic[_T], AbstractContextManager["ContextProvider[_T]"]):
    """Canal reactivo identificado por un nombre.

    Args:
        name:
            Nombre lógico del contexto. Se utiliza como clave para todos los
            proveedores pertenecientes al mismo canal.
        default:
            Valor devuelto cuando no existe ningún proveedor activo. Este valor
            también se utilizará como punto de partida para el primer proveedor
            que no especifique un valor inicial propio.
        comparer:
            Función opcional utilizada por los proveedores para determinar si
            un nuevo valor es diferente del actual. Si no se indica se utiliza
            la comparación por igualdad estándar.
    """

    _registry: dict[str, "Context[Any]"] = {}

    def __new__(
        cls,
        name: str,
        *,
        default: _T | _Missing = MISSING,
        comparer: Callable[[Any, Any], bool] | None = None,
    ) -> "Context[_T]":
        existing = cls._registry.get(name)
        if existing is not None:
            return existing  # type: ignore[return-value]
        self = super().__new__(cls)
        cls._registry[name] = self  # type: ignore[assignment]
        return self  # type: ignore[return-value]

    def __init__(
        self,
        name: str,
        *,
        default: _T | _Missing = MISSING,
        comparer: Callable[[Any, Any], bool] | None = None,
    ) -> None:
        if hasattr(self, "_initialized"):
            return
        self.name = name
        self.default: _T | _Missing = default
        self._comparer = comparer
        self._providers_var: contextvars.ContextVar[Tuple[ContextProvider[Any], ...]] = (
            contextvars.ContextVar(f"fletplus.context.{name}", default=())
        )
        self._auto_stack_var: contextvars.ContextVar[
            Tuple[ContextProvider[Any], ...]
        ] = contextvars.ContextVar(f"fletplus.context.auto.{name}", default=())
        self._initialized = True

    # ------------------------------------------------------------------
    def _push_provider(self, provider: "ContextProvider[_T]") -> contextvars.Token:
        stack = self._providers_var.get()
        return self._providers_var.set(stack + (provider,))

    # ------------------------------------------------------------------
    def _pop_provider(self, provider: "ContextProvider[_T]", token: contextvars.Token) -> None:
        stack = self._providers_var.get()
        if not stack or stack[-1] is not provider:
            raise RuntimeError(
                f"Intento de cerrar un proveedor de contexto '{self.name}' fuera de orden"
            )
        self._providers_var.reset(token)

    # ------------------------------------------------------------------
    def current_provider(self) -> "ContextProvider[_T] | None":
        stack = self._providers_var.get()
        return stack[-1] if stack else None

    # ------------------------------------------------------------------
    def get(self, default: _T | _Missing = MISSING) -> _T:
        provider = self.current_provider()
        if provider is not None:
            return provider.get()
        if default is not MISSING:
            return default
        if self.default is not MISSING:
            return self.default  # type: ignore[return-value]
        raise LookupError(
            f"No existe un proveedor activo para el contexto '{self.name}'"
        )

    # ------------------------------------------------------------------
    def set(self, value: _T) -> _T:
        provider = self.current_provider()
        if provider is None:
            raise LookupError(
                f"No existe un proveedor activo para el contexto '{self.name}'"
            )
        return provider.set(value)

    # ------------------------------------------------------------------
    def subscribe(
        self,
        callback: Callable[["_T"], None],
        *,
        immediate: bool = False,
    ) -> Callable[[], None]:
        provider = self.current_provider()
        if provider is None:
            raise LookupError(
                f"No existe un proveedor activo para el contexto '{self.name}'"
            )
        return provider.subscribe(callback, immediate=immediate)

    # ------------------------------------------------------------------
    def bind_control(self, control: Any, **kwargs: Any) -> Callable[[], None]:
        provider = self.current_provider()
        if provider is None:
            raise LookupError(
                f"No existe un proveedor activo para el contexto '{self.name}'"
            )
        return provider.bind_control(control, **kwargs)

    # ------------------------------------------------------------------
    def provide(
        self,
        value: _T | _Missing = MISSING,
        *,
        inherit: bool = True,
    ) -> "ContextProvider[_T]":
        """Crea un proveedor explícito sin activar el *context manager* aún."""

        return ContextProvider(self, value=value, inherit=inherit)

    # ------------------------------------------------------------------
    def __enter__(self) -> "ContextProvider[_T]":
        provider = ContextProvider(self)
        provider.__enter__()
        stack = self._auto_stack_var.get()
        self._auto_stack_var.set(stack + (provider,))
        return provider

    # ------------------------------------------------------------------
    def __exit__(self, exc_type, exc, tb) -> Optional[bool]:
        stack = self._auto_stack_var.get()
        if not stack:
            return None
        provider = stack[-1]
        self._auto_stack_var.set(stack[:-1])
        provider.__exit__(exc_type, exc, tb)
        return None


class ContextProvider(Generic[_T]):
    """Gestiona el valor de un :class:`Context` concreto."""

    __slots__ = (
        "context",
        "inherit",
        "_value",
        "_signal",
        "_token",
        "_parent",
    )

    def __init__(
        self,
        context: Context[_T],
        *,
        value: _T | _Missing = MISSING,
        inherit: bool = True,
    ) -> None:
        self.context = context
        self.inherit = inherit
        self._value = value
        self._signal: Signal[_T] | None = None
        self._token: contextvars.Token | None = None
        self._parent: ContextProvider[_T] | None = None

    # ------------------------------------------------------------------
    def __enter__(self) -> "ContextProvider[_T]":
        if self._token is not None:
            raise RuntimeError("El proveedor de contexto ya está activo")
        self._parent = self.context.current_provider()
        if self._value is not MISSING:
            initial = self._value
        elif self._parent is not None and self.inherit:
            initial = self._parent.get()
        elif self.context.default is not MISSING:
            initial = self.context.default  # type: ignore[assignment]
        else:
            initial = None  # type: ignore[assignment]
        self._signal = Signal(initial, comparer=self.context._comparer)
        self._token = self.context._push_provider(self)
        return self

    # ------------------------------------------------------------------
    def __exit__(self, exc_type, exc, tb) -> Optional[bool]:
        self.close()
        return None

    # ------------------------------------------------------------------
    def close(self) -> None:
        if self._token is None:
            return
        self.context._pop_provider(self, self._token)
        self._token = None
        self._signal = None

    # ------------------------------------------------------------------
    def get(self) -> _T:
        if self._signal is None:
            raise RuntimeError("El proveedor de contexto no está activo")
        return self._signal.get()

    # ------------------------------------------------------------------
    def set(self, value: _T) -> _T:
        if self._signal is None:
            raise RuntimeError("El proveedor de contexto no está activo")
        return self._signal.set(value)

    # ------------------------------------------------------------------
    @property
    def value(self) -> _T:
        return self.get()

    @value.setter
    def value(self, new_value: _T) -> None:
        self.set(new_value)

    # ------------------------------------------------------------------
    def subscribe(
        self,
        callback: Callable[["_T"], None],
        *,
        immediate: bool = False,
    ) -> Callable[[], None]:
        if self._signal is None:
            raise RuntimeError("El proveedor de contexto no está activo")
        return self._signal.subscribe(callback, immediate=immediate)

    # ------------------------------------------------------------------
    def bind_control(self, control: Any, **kwargs: Any) -> Callable[[], None]:
        if self._signal is None:
            raise RuntimeError("El proveedor de contexto no está activo")
        return self._signal.bind_control(control, **kwargs)


# Contextos principales expuestos por la librería

theme_context: Context[Any] = Context("theme")
user_context: Context[Any] = Context("user", default=None)
locale_context: Context[str] = Context("locale", default="es")
