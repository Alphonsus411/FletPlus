"""Helpers reactivos basados en :mod:`fletplus.state`.

Este módulo implementa utilidades ligeras de estilo *hooks* para asociar
renderizados con señales existentes. Los helpers mantienen compatibilidad con
las primitivas ya disponibles (:class:`~fletplus.state.Signal`) y proporcionan
un patrón declarativo para observar y reaccionar a los cambios.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, Dict, List
from weakref import WeakKeyDictionary, ref

from . import Signal

Subscriber = Callable[[object], None]


@dataclass(slots=True)
class _WatchRegistration:
    signals: tuple[Signal, ...]
    callback: Callable[..., None]
    subscriptions: list[Callable[[], None]] = field(default_factory=list)

    def emit(self) -> None:
        values = [sig.get() for sig in self.signals]
        if len(values) == 1:
            self.callback(values[0])
        else:
            self.callback(*values)

    def stop(self) -> None:
        for unsubscribe in list(self.subscriptions):
            with suppress(Exception):
                unsubscribe()
        self.subscriptions.clear()


def _ensure_signal(obj: object) -> Signal:
    if not hasattr(obj, "subscribe") or not hasattr(obj, "get"):
        raise TypeError("Se esperaba una señal compatible con subscribe/get")
    return obj  # type: ignore[return-value]


class _ReactiveRuntimeError(RuntimeError):
    pass


_context_stack: list["_ReactiveInstance"] = []


def _current_context(required: bool = False) -> "_ReactiveInstance | None":
    if not _context_stack:
        if required:
            raise _ReactiveRuntimeError(
                "Los hooks reactivos solo pueden utilizarse dentro de un render decorado con @reactive",
            )
        return None
    return _context_stack[-1]


def reactive(func: Callable) -> Callable:
    """Decorador que habilita *hooks* reactivos para un render.

    El decorador memoriza el estado por instancia cuando se aplica sobre un
    método. Los cambios en las señales observadas provocarán que el contenedor
    asociado ejecute ``update()``.
    """

    descriptor_cache: "WeakKeyDictionary[object, _ReactiveInstance]" = WeakKeyDictionary()

    def _resolve_instance(owner: object | None) -> _ReactiveInstance:
        if owner is None:
            return _ReactiveInstance(func, None)
        instance = descriptor_cache.get(owner)
        if instance is None:
            instance = _ReactiveInstance(func, owner)
            descriptor_cache[owner] = instance
        return instance

    def wrapper(*args, **kwargs):
        owner = args[0] if args else None
        instance = _resolve_instance(owner)
        return instance(*args, **kwargs)

    return wrapper


@dataclass(slots=True)
class _ReactiveInstance:
    func: Callable
    owner: object | None = None
    _states: List[Signal] = field(default_factory=list)
    _subscriptions: Dict[Signal, Callable[[], None]] = field(default_factory=dict)
    _active_signals: set[Signal] = field(default_factory=set)
    _watchers: list[_WatchRegistration | None] = field(default_factory=list)
    _active_watchers: set[int] = field(default_factory=set)
    _cleanups: list[Callable[[], None]] = field(default_factory=list)
    _hook_index: int = 0
    _watch_index: int = 0
    _invalidated: bool = False
    _owner_ref: Callable[[], object | None] = field(default=lambda: None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.owner is not None:
            register = getattr(self.owner, "_register_reactive_render", None)
            if callable(register):
                register(self)
        self._owner_ref = ref(self.owner) if self.owner is not None else lambda: None

    # ------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        owner = self._owner_ref() if callable(self._owner_ref) else None
        if owner is None and self.owner is not None:
            owner = self.owner
        self.owner = owner
        _context_stack.append(self)
        self._active_signals = set()
        self._active_watchers = set()
        self._hook_index = 0
        self._watch_index = 0
        try:
            result = self.func(*args, **kwargs)
        finally:
            _context_stack.pop()
            self._cleanup_unused_signals()
            self._cleanup_unused_watchers()
        return result

    # ------------------------------------------------------------------
    def _cleanup_unused_signals(self) -> None:
        for signal, unsubscribe in list(self._subscriptions.items()):
            if signal not in self._active_signals:
                unsubscribe()
                self._subscriptions.pop(signal, None)

    # ------------------------------------------------------------------
    def _cleanup_unused_watchers(self) -> None:
        for index, watcher in enumerate(self._watchers):
            if watcher is None:
                continue
            if index in self._active_watchers:
                continue
            watcher.stop()
            self._watchers[index] = None

    # ------------------------------------------------------------------
    def next_state(self, initial: Any) -> Signal:
        if self._hook_index < len(self._states):
            signal = self._states[self._hook_index]
        else:
            value = initial() if callable(initial) else initial
            signal = Signal(value)
            self._states.append(signal)
        self._hook_index += 1
        self.track(signal)
        return signal

    # ------------------------------------------------------------------
    def track(self, signal: Signal) -> None:
        signal = _ensure_signal(signal)
        self._active_signals.add(signal)
        if signal not in self._subscriptions:
            self._subscriptions[signal] = signal.subscribe(self._invalidate)

    # ------------------------------------------------------------------
    def _invalidate(self, _value: object) -> None:
        if self._invalidated:
            return
        self._invalidated = True
        owner = self._owner_ref() if callable(self._owner_ref) else None
        if owner is None:
            owner = self.owner
        trigger = None
        if owner is not None:
            trigger = getattr(owner, "_reactive_trigger", None)
            if not callable(trigger):
                page = getattr(owner, "page", None)
                trigger = getattr(page, "update", None)
            if not callable(trigger):
                trigger = getattr(owner, "update", None)
        if callable(trigger):
            try:
                trigger()
            finally:
                # Restablece el flag incluso si el trigger falla.
                self._invalidated = False
        else:
            self._invalidated = False

    # ------------------------------------------------------------------
    def add_cleanup(self, callback: Callable[[], None]) -> None:
        self._cleanups.append(callback)

    # ------------------------------------------------------------------
    def watch(self, signals: list[Signal], callback: Callable[..., None], *, immediate: bool = True) -> Callable[[], None]:
        index = self._watch_index
        self._watch_index += 1
        self._active_watchers.add(index)

        while len(self._watchers) <= index:
            self._watchers.append(None)

        expected = tuple(signals)
        watcher = self._watchers[index]

        if watcher is not None and watcher.signals != expected:
            watcher.stop()
            watcher = None

        if watcher is None:
            watcher = _WatchRegistration(signals=expected, callback=callback)

            for sig in expected:

                def _handler(_value: object, *, _watcher=watcher) -> None:
                    _watcher.emit()

                watcher.subscriptions.append(sig.subscribe(_handler))

            self._watchers[index] = watcher
            if immediate:
                watcher.emit()
        else:
            watcher.callback = callback
            if not watcher.subscriptions:
                for sig in watcher.signals:

                    def _handler(_value: object, *, _watcher=watcher) -> None:
                        _watcher.emit()

                    watcher.subscriptions.append(sig.subscribe(_handler))
                if immediate:
                    watcher.emit()

        return watcher.stop

    # ------------------------------------------------------------------
    def dispose(self) -> None:
        for unsubscribe in list(self._subscriptions.values()):
            with suppress(Exception):
                unsubscribe()
        self._subscriptions.clear()
        for watcher in list(self._watchers):
            if watcher is None:
                continue
            watcher.stop()
        self._watchers.clear()
        for cleanup in list(self._cleanups):
            with suppress(Exception):
                cleanup()
        self._cleanups.clear()


def use_state(initial: Any) -> Signal:
    """Crea o recupera una señal local asociada al render actual."""

    context = _current_context(required=True)
    if context is None:  # defensivo
        raise _ReactiveRuntimeError(
            "Hooks reactivos requieren un contexto activo (@reactive)."
        )
    return context.next_state(initial)


def use_signal(signal: Signal) -> Signal:
    """Registra una señal externa como dependencia del render actual."""

    context = _current_context(required=True)
    if context is None:  # defensivo
        raise _ReactiveRuntimeError(
            "Hooks reactivos requieren un contexto activo (@reactive)."
        )
    context.track(signal)
    return signal


def watch(signals: Signal | Iterable[Signal], callback: Callable[..., None], *, immediate: bool = True) -> Callable[[], None]:
    """Observa una o varias señales ejecutando ``callback`` cuando cambian."""

    context = _current_context(required=False)
    if isinstance(signals, Iterable) and not isinstance(signals, Signal):
        signal_list = [_ensure_signal(sig) for sig in signals]
    else:
        signal_list = [_ensure_signal(signals)]

    if context is not None:
        for sig in signal_list:
            context.track(sig)
        return context.watch(signal_list, callback, immediate=immediate)

    watcher = _WatchRegistration(signals=tuple(signal_list), callback=callback)

    for sig in signal_list:

        def _handler(_value: object, *, _watcher=watcher) -> None:
            _watcher.emit()

        watcher.subscriptions.append(sig.subscribe(_handler))

    if immediate:
        watcher.emit()

    return watcher.stop


__all__ = ["reactive", "use_state", "use_signal", "watch"]
