"""Utilidades reactivas para gestionar el estado de aplicaciones FletPlus.

Este módulo proporciona primitivas de estado inmutables similares a *signals* y
*stores* que permiten desacoplar la lógica de negocio de la interfaz. Las
clases :class:`Signal` y :class:`Store` implementan notificaciones
sincrónicas que se integran de forma sencilla con controles de Flet mediante
el método :meth:`Signal.bind_control`.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Callable, Dict, Generic, MutableMapping, TypeVar

_T = TypeVar("_T")
_S = TypeVar("_S")

Subscriber = Callable[["_T"], None]


class _BaseSignal(Generic[_T]):
    """Implementación base compartida por señales mutables y derivadas."""

    __slots__ = ("_value", "_comparer", "_subscribers", "_next_token")

    def __init__(
        self,
        value: _T,
        *,
        comparer: Callable[["_T", "_T"], bool] | None = None,
    ) -> None:
        self._value = value
        self._comparer = comparer or (lambda old, new: old == new)
        self._subscribers: Dict[int, Subscriber] = {}
        self._next_token = 0

    # ------------------------------------------------------------------
    def get(self) -> _T:
        """Devuelve el valor actual de la señal."""

        return self._value

    # ------------------------------------------------------------------
    def _set_value(self, value: _T) -> bool:
        if self._comparer(self._value, value):
            return False
        self._value = value
        return True

    # ------------------------------------------------------------------
    def _notify(self) -> None:
        for callback in list(self._subscribers.values()):
            callback(self._value)

    # ------------------------------------------------------------------
    def subscribe(self, callback: Subscriber, *, immediate: bool = False) -> Callable[[], None]:
        """Registra un *callback* que se ejecutará cuando cambie el valor.

        Args:
            callback: función que recibirá el nuevo valor.
            immediate: si es ``True`` se ejecuta inmediatamente con el valor
                actual.

        Returns:
            Función que elimina la subscripción cuando se ejecuta.
        """

        token = self._next_token
        self._next_token += 1
        self._subscribers[token] = callback
        if immediate:
            callback(self._value)

        def unsubscribe() -> None:
            self._subscribers.pop(token, None)

        return unsubscribe

    # ------------------------------------------------------------------
    def bind_control(
        self,
        control,
        *,
        attr: str = "value",
        transform: Callable[["_T"], object] | None = None,
        update: bool = True,
        immediate: bool = True,
    ) -> Callable[[], None]:
        """Sincroniza la señal con un control de Flet.

        El atributo indicado se actualiza con cada cambio y, si el control
        implementa ``update()``, se invoca automáticamente.
        """

        def apply(value: _T) -> None:
            transformed = transform(value) if transform else value
            setattr(control, attr, transformed)
            if update and hasattr(control, "update"):
                control.update()

        return self.subscribe(apply, immediate=immediate)

    # ------------------------------------------------------------------
    def effect(self, func: Callable[["_T"], None] | None = None, *, immediate: bool = True):
        """Registra efectos secundarios utilizando un decorador."""

        def decorator(callback: Callable[["_T"], None]):
            self.subscribe(callback, immediate=immediate)
            return callback

        if func is None:
            return decorator
        return decorator(func)

    # ------------------------------------------------------------------
    def __call__(self) -> _T:
        return self.get()


class Signal(_BaseSignal[_T]):
    """Señal mutable que notifica cambios a sus subscriptores."""

    __slots__ = ()

    def set(self, value: _T) -> _T:
        if self._set_value(value):
            self._notify()
        return self._value

    @property
    def value(self) -> _T:
        return self.get()

    @value.setter
    def value(self, new_value: _T) -> None:
        self.set(new_value)


class DerivedSignal(_BaseSignal[_T]):
    """Señal derivada de solo lectura."""

    __slots__ = ("_source", "_selector", "_unsubscribe")

    def __init__(
        self,
        source: _BaseSignal[_S],
        selector: Callable[["_S"], "_T"],
        *,
        comparer: Callable[["_T", "_T"], bool] | None = None,
    ) -> None:
        self._source = source
        self._selector = selector
        super().__init__(selector(source.get()), comparer=comparer)
        self._unsubscribe = source.subscribe(self._propagate)

    def _propagate(self, source_value: _S) -> None:
        projected = self._selector(source_value)
        if self._set_value(projected):
            self._notify()

    def set(self, _: _T) -> _T:  # pragma: no cover - comportamiento defensivo
        raise TypeError("Las señales derivadas son de solo lectura")

    @property
    def value(self) -> _T:
        return self.get()

    def close(self) -> None:
        """Detiene la escucha del valor de origen."""

        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None


class Store:
    """Contenedor de señales nombradas con helpers reactivos."""

    __slots__ = ("_signals", "_children", "_root")

    _MISSING = object()

    def __init__(self, initial: MutableMapping[str, object] | None = None) -> None:
        self._signals: Dict[str, Signal] = {}
        self._children: Dict[str, Callable[[], None]] = {}
        self._root: Signal = Signal(self._create_snapshot())

        if initial:
            for key, value in initial.items():
                self._signals[key] = Signal(value)
        for name, signal in self._signals.items():
            self._link_child(name, signal)
        self._sync_root()

    # ------------------------------------------------------------------
    def _create_snapshot(self) -> MappingProxyType:
        data = {name: signal.get() for name, signal in self._signals.items()}
        return MappingProxyType(data)

    # ------------------------------------------------------------------
    def _sync_root(self) -> None:
        self._root.set(self._create_snapshot())

    # ------------------------------------------------------------------
    def _link_child(self, name: str, signal: Signal) -> None:
        if name in self._children:
            return

        def propagate(_: object) -> None:
            self._sync_root()

        self._children[name] = signal.subscribe(propagate)

    # ------------------------------------------------------------------
    def signal(self, name: str, default: object = _MISSING) -> Signal:
        """Obtiene o crea una señal nombrada dentro del *store*."""

        if name in self._signals:
            return self._signals[name]
        if default is self._MISSING:
            raise KeyError(f"La señal '{name}' no existe")
        signal = Signal(default)
        self._signals[name] = signal
        self._link_child(name, signal)
        self._sync_root()
        return signal

    # ------------------------------------------------------------------
    def has(self, name: str) -> bool:
        return name in self._signals

    # ------------------------------------------------------------------
    def __getitem__(self, name: str):
        return self.signal(name).get()

    # ------------------------------------------------------------------
    def __setitem__(self, name: str, value) -> None:
        self.signal(name, default=value).set(value)

    # ------------------------------------------------------------------
    def update(self, name: str, reducer: Callable[[object], object]) -> object:
        current = self.signal(name).get()
        new_value = reducer(current)
        self.signal(name).set(new_value)
        return new_value

    # ------------------------------------------------------------------
    def subscribe(self, callback: Subscriber, *, immediate: bool = False) -> Callable[[], None]:
        """Observa el *snapshot* inmutable del estado completo."""

        return self._root.subscribe(callback, immediate=immediate)

    # ------------------------------------------------------------------
    def snapshot(self) -> MappingProxyType:
        """Devuelve una vista inmutable del estado actual."""

        return self._root.get()

    # ------------------------------------------------------------------
    def derive(
        self,
        selector: Callable[[MappingProxyType], _T],
        *,
        comparer: Callable[["_T", "_T"], bool] | None = None,
    ) -> DerivedSignal[_T]:
        """Crea una señal derivada a partir del estado completo."""

        return DerivedSignal(self._root, selector, comparer=comparer)

    # ------------------------------------------------------------------
    def bind(
        self,
        name: str,
        control,
        *,
        attr: str = "value",
        transform: Callable[[object], object] | None = None,
        update: bool = True,
        immediate: bool = True,
        default: object = _MISSING,
    ) -> Callable[[], None]:
        signal = self.signal(name, default=default)
        return signal.bind_control(
            control,
            attr=attr,
            transform=transform,
            update=update,
            immediate=immediate,
        )


__all__ = [
    "Signal",
    "DerivedSignal",
    "Store",
]
