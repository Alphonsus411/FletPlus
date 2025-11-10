"""Controlador de animaciones coordinado mediante contextos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional
import weakref

import flet as ft

from fletplus.context import Context

__all__ = ["AnimationController", "animation_controller_context"]


@dataclass(frozen=True)
class _ListenerKey:
    """Identificador estable para una *callback* almacenada débilmente."""

    owner_id: Optional[int]
    func: object


class _WeakCallback:
    """Envuelve un callable permitiendo resolverlo de forma segura."""

    __slots__ = ("_ref", "key")

    def __init__(self, callback: Callable[[str], None]) -> None:
        if hasattr(callback, "__self__") and hasattr(callback, "__func__"):
            self._ref: Callable[[], Optional[Callable[[str], None]]] = weakref.WeakMethod(callback)  # type: ignore[arg-type]
            owner_id: Optional[int] = id(getattr(callback, "__self__"))
            func = getattr(callback, "__func__")
        else:
            self._ref = weakref.ref(callback)  # type: ignore[arg-type]
            owner_id = None
            func = callback
        object.__setattr__(self, "key", _ListenerKey(owner_id, func))

    def resolve(self) -> Optional[Callable[[str], None]]:
        try:
            return self._ref()
        except TypeError:  # pragma: no cover - refs inválidas en CPython
            return None

    def matches(self, other: Callable[[str], None]) -> bool:
        if hasattr(other, "__self__") and hasattr(other, "__func__"):
            other_key = _ListenerKey(id(getattr(other, "__self__")), getattr(other, "__func__"))
        else:
            other_key = _ListenerKey(None, other)
        return self.key == other_key


animation_controller_context: Context["AnimationController | None"] = Context(
    "animation_controller",
    default=None,
)


class AnimationController:
    """Coordina animaciones declarativas a través de eventos simbólicos."""

    __slots__ = ("page", "_listeners", "_fired")

    def __init__(self, page: ft.Page | None = None) -> None:
        self.page = page
        self._listeners: Dict[str, list[_WeakCallback]] = {}
        self._fired: set[str] = set()

    # ------------------------------------------------------------------
    def bind_page(self, page: ft.Page) -> None:
        """Actualiza la página asociada usada para solicitar repintados."""

        self.page = page

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Elimina todos los listeners registrados y limpia el historial."""

        self._listeners.clear()
        self._fired.clear()

    # ------------------------------------------------------------------
    def add_listener(
        self,
        trigger: str,
        callback: Callable[[str], None],
        *,
        replay_if_fired: bool = False,
    ) -> Callable[[], None]:
        """Suscribe una función a un evento y devuelve un desuscriptor."""

        storage = self._listeners.setdefault(trigger, [])
        wrapper = _WeakCallback(callback)
        storage.append(wrapper)

        if replay_if_fired and trigger in self._fired:
            resolved = wrapper.resolve()
            if resolved is not None:
                resolved(trigger)

        def _unsubscribe() -> None:
            listeners = self._listeners.get(trigger)
            if not listeners:
                return
            self._listeners[trigger] = [item for item in listeners if not item.matches(callback)]
            if not self._listeners[trigger]:
                self._listeners.pop(trigger, None)

        return _unsubscribe

    # ------------------------------------------------------------------
    def remove_listener(self, trigger: str, callback: Callable[[str], None]) -> None:
        listeners = self._listeners.get(trigger)
        if not listeners:
            return
        self._listeners[trigger] = [item for item in listeners if not item.matches(callback)]
        if not self._listeners[trigger]:
            self._listeners.pop(trigger, None)

    # ------------------------------------------------------------------
    def trigger(self, name: str) -> None:
        """Lanza un evento, notificando a todos los listeners registrados."""

        callbacks = list(self._listeners.get(name, ()))
        alive: list[_WeakCallback] = []
        for wrapper in callbacks:
            resolved = wrapper.resolve()
            if resolved is None:
                continue
            try:
                resolved(name)
                alive.append(wrapper)
            except Exception:  # pragma: no cover - errores de usuario
                # Evitamos que un error en un listener bloquee el resto.
                continue
        if alive:
            self._listeners[name] = alive
        else:
            self._listeners.pop(name, None)
        self._fired.add(name)

    # ------------------------------------------------------------------
    def trigger_many(self, names: Iterable[str]) -> None:
        for name in names:
            self.trigger(name)

    # ------------------------------------------------------------------
    def has_fired(self, name: str) -> bool:
        return name in self._fired

    # ------------------------------------------------------------------
    def request_update(self, control: ft.Control | None = None) -> None:
        """Solicita una actualización del control o la página asociada."""

        target = control or None
        if target is not None and hasattr(target, "update"):
            try:
                target.update()
                return
            except Exception:  # pragma: no cover - errores del usuario
                pass
        if self.page is not None and hasattr(self.page, "update"):
            try:
                self.page.update()
            except Exception:  # pragma: no cover - errores del usuario
                pass

