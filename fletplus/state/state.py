"""Utilidades reactivas para gestionar el estado de aplicaciones FletPlus.

Este módulo proporciona primitivas de estado inmutables similares a *signals* y
*stores* que permiten desacoplar la lógica de negocio de la interfaz. Las
clases :class:`Signal` y :class:`Store` implementan notificaciones
sincrónicas que se integran de forma sencilla con controles de Flet mediante
el método :meth:`Signal.bind_control`.
"""
from __future__ import annotations

import importlib
import importlib.util
from types import MappingProxyType
from typing import Callable, MutableMapping, TypeVar

from . import signal_pr_rs

_T = TypeVar("_T")
_S = TypeVar("_S")

SubscriberType = Callable[["_T"], None]

_spec = importlib.util.find_spec("fletplus.state._native")
if _spec is None:
    _native = None
else:
    _native = importlib.import_module("fletplus.state._native")

if _native is not None and all(
    hasattr(_native, name) for name in ("Signal", "DerivedSignal", "Store")
):
    Signal = _native.Signal
    DerivedSignal = _native.DerivedSignal
    Store = _native.Store
else:
    _signal_native = signal_pr_rs._native

    class _BaseSignal:
        """Implementación base compartida por señales mutables y derivadas."""

        def __init__(
            self,
            value: _T,
            *,
            comparer: Callable[["_T", "_T"], bool] | None = None,
        ) -> None:
            self._value = value
            self._comparer = comparer or (lambda old, new: old == new)
            if _signal_native is not None:
                self._subscribers = _signal_native.SignalState()
            else:
                self._subscribers: dict[int, SubscriberType] = {}
            self._next_token = 0

        # ------------------------------------------------------------------
        def get(self) -> _T:
            """Devuelve el valor actual de la señal."""

            return self._value

        # ------------------------------------------------------------------
        def _set_value(self, value: _T) -> bool:
            comparer = self._comparer
            current = self._value
            if comparer(current, value):
                return False
            self._value = value
            return True

        # ------------------------------------------------------------------
        def _notify(self) -> None:
            if _signal_native is not None:
                _signal_native.notify(self._subscribers, self._value)
                return
            subscribers = self._subscribers
            value = self._value
            for callback in list(subscribers.values()):
                callback(value)

        # ------------------------------------------------------------------
        def subscribe(self, callback: SubscriberType, *, immediate: bool = False):
            """Registra un *callback* que se ejecutará cuando cambie el valor.

            Args:
                callback: función que recibirá el nuevo valor.
                immediate: si es ``True`` se ejecuta inmediatamente con el valor
                    actual.

            Returns:
                Función que elimina la subscripción cuando se ejecuta.
            """

            token = self._next_token
            self._next_token = token + 1
            if _signal_native is not None:
                self._subscribers.add(token, callback)
            else:
                self._subscribers[token] = callback
            if immediate:
                callback(self._value)

            def unsubscribe() -> None:
                if _signal_native is not None:
                    self._subscribers.remove(token)
                else:
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
        ):
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

    class Signal(_BaseSignal):
        """Señal mutable que notifica cambios a sus subscriptores."""

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

    class DerivedSignal(_BaseSignal):
        """Señal derivada de solo lectura."""

        def __init__(
            self,
            source: _BaseSignal,
            selector: Callable[["_S"], "_T"],
            *,
            comparer: Callable[["_T", "_T"], bool] | None = None,
        ) -> None:
            self._source = source
            self._selector = selector
            super().__init__(selector(source.get()), comparer=comparer)
            self._unsubscribe = source.subscribe(self._propagate)

        # ------------------------------------------------------------------
        def _propagate(self, source_value: _S) -> None:
            selector = self._selector
            projected = selector(source_value)
            if self._set_value(projected):
                self._notify()

        # ------------------------------------------------------------------
        def set(self, _value: _T) -> None:  # pragma: no cover - comportamiento defensivo
            raise TypeError("Las señales derivadas son de solo lectura")

        @property
        def value(self) -> _T:
            return self.get()

        def close(self) -> None:
            """Detiene la escucha del valor de origen."""

            unsubscribe = self._unsubscribe
            if unsubscribe:
                unsubscribe()
                self._unsubscribe = None

    class Store:
        """Contenedor de señales nombradas con helpers reactivos."""

        _MISSING = object()

        def __init__(self, initial: MutableMapping[str, object] | None = None) -> None:
            self._signals: dict[str, Signal] = {}
            self._children: dict[str, Callable[[], None]] = {}
            self._root = Signal(self._create_snapshot())

            if initial:
                for key, value in initial.items():
                    self._signals[key] = Signal(value)
            for name, signal in self._signals.items():
                self._link_child(name, signal)
            self._sync_root()

        # ------------------------------------------------------------------
        def _create_snapshot(self) -> MappingProxyType:
            if _signal_native is not None:
                return MappingProxyType(_signal_native.snapshot(self._signals))
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
        def subscribe(self, callback: SubscriberType, *, immediate: bool = False):
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
        ) -> DerivedSignal:
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
        ):
            signal = self.signal(name, default=default)
            return signal.bind_control(
                control,
                attr=attr,
                transform=transform,
                update=update,
                immediate=immediate,
            )


__all__ = ["Signal", "DerivedSignal", "Store"]
