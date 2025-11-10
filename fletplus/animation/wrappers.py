"""Controles animados que reaccionan a eventos del :class:`AnimationController`."""

from __future__ import annotations

from typing import Any, Callable, Mapping

import flet as ft

from .controller import AnimationController, animation_controller_context

__all__ = ["FadeIn", "SlideTransition", "Scale", "AnimatedContainer"]


def _resolve_controller(explicit: AnimationController | None = None) -> AnimationController | None:
    if explicit is not None:
        return explicit
    try:
        controller = animation_controller_context.get()
    except LookupError:
        controller = None
    return controller


class _BaseAnimatedContainer(ft.Container):
    """Base que registra listeners en un :class:`AnimationController`."""

    def __init__(
        self,
        *,
        trigger: str = "mount",
        reverse_trigger: str | None = "unmount",
        controller: AnimationController | None = None,
        replay_if_fired: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._controller = _resolve_controller(controller)
        self._trigger = trigger
        self._reverse_trigger = reverse_trigger
        self._unsubscribers: list[Callable[[], None]] = []
        if self._controller is not None and self._trigger:
            self._unsubscribers.append(
                self._controller.add_listener(self._trigger, self._handle_forward, replay_if_fired=replay_if_fired)
            )
        if self._controller is not None and self._reverse_trigger:
            self._unsubscribers.append(
                self._controller.add_listener(self._reverse_trigger, self._handle_reverse)
            )

    # ------------------------------------------------------------------
    def _handle_forward(self, _event: str) -> None:
        self._play_forward()
        if self._controller is not None:
            self._controller.request_update(self)

    # ------------------------------------------------------------------
    def _handle_reverse(self, _event: str) -> None:
        self._play_reverse()
        if self._controller is not None:
            self._controller.request_update(self)

    # ------------------------------------------------------------------
    def _play_forward(self) -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------
    def _play_reverse(self) -> None:
        pass


class FadeIn(_BaseAnimatedContainer):
    """Control que aparece con una animación de opacidad."""

    def __init__(
        self,
        content: ft.Control,
        *,
        duration: int = 350,
        curve: ft.AnimationCurve = ft.AnimationCurve.EASE_OUT,
        start: float = 0.0,
        end: float = 1.0,
        trigger: str = "mount",
        reverse_trigger: str | None = "unmount",
        controller: AnimationController | None = None,
        replay_if_fired: bool = True,
        **kwargs: Any,
    ) -> None:
        self._start = start
        self._end = end
        animation = ft.Animation(duration, curve=curve)
        super().__init__(
            content=content,
            opacity=start,
            animate_opacity=animation,
            trigger=trigger,
            reverse_trigger=reverse_trigger,
            controller=controller,
            replay_if_fired=replay_if_fired,
            **kwargs,
        )
        

    def _play_forward(self) -> None:
        self.opacity = self._end

    def _play_reverse(self) -> None:
        self.opacity = self._start


class SlideTransition(_BaseAnimatedContainer):
    """Desplaza el contenido desde un desplazamiento inicial."""

    def __init__(
        self,
        content: ft.Control,
        *,
        duration: int = 300,
        curve: ft.AnimationCurve = ft.AnimationCurve.DECELERATE,
        begin: ft.transform.Offset = ft.transform.Offset(0, 0.1),
        end: ft.transform.Offset = ft.transform.Offset(0, 0),
        trigger: str = "mount",
        reverse_trigger: str | None = "unmount",
        controller: AnimationController | None = None,
        replay_if_fired: bool = True,
        **kwargs: Any,
    ) -> None:
        self._begin = begin
        self._end = end
        animation = ft.Animation(duration, curve=curve)
        super().__init__(
            content=content,
            offset=begin,
            animate_offset=animation,
            trigger=trigger,
            reverse_trigger=reverse_trigger,
            controller=controller,
            replay_if_fired=replay_if_fired,
            **kwargs,
        )
        

    def _play_forward(self) -> None:
        self.offset = self._end

    def _play_reverse(self) -> None:
        self.offset = self._begin


class Scale(_BaseAnimatedContainer):
    """Escala el contenido desde un valor inicial."""

    def __init__(
        self,
        content: ft.Control,
        *,
        duration: int = 260,
        curve: ft.AnimationCurve = ft.AnimationCurve.EASE_OUT_BACK,
        begin: ft.transform.Scale = ft.transform.Scale(0.92, 0.92),
        end: ft.transform.Scale = ft.transform.Scale(1, 1),
        trigger: str = "mount",
        reverse_trigger: str | None = "unmount",
        controller: AnimationController | None = None,
        replay_if_fired: bool = True,
        **kwargs: Any,
    ) -> None:
        self._begin = begin
        self._end = end
        animation = ft.Animation(duration, curve=curve)
        super().__init__(
            content=content,
            scale=begin,
            animate_scale=animation,
            trigger=trigger,
            reverse_trigger=reverse_trigger,
            controller=controller,
            replay_if_fired=replay_if_fired,
            **kwargs,
        )
        

    def _play_forward(self) -> None:
        self.scale = self._end

    def _play_reverse(self) -> None:
        self.scale = self._begin


class AnimatedContainer(_BaseAnimatedContainer):
    """Anima propiedades arbitrarias del contenedor."""

    def __init__(
        self,
        content: ft.Control,
        *,
        duration: int = 280,
        curve: ft.AnimationCurve = ft.AnimationCurve.EASE_IN_OUT,
        begin: Mapping[str, Any] | None = None,
        end: Mapping[str, Any] | None = None,
        trigger: str = "mount",
        reverse_trigger: str | None = "unmount",
        controller: AnimationController | None = None,
        replay_if_fired: bool = True,
        **kwargs: Any,
    ) -> None:
        self._end_style = dict(end or {})
        self._begin_style = dict(begin or {})
        animation = ft.Animation(duration, curve=curve)
        merged_kwargs = {"content": content, "animate": animation}
        merged_kwargs.update(kwargs)
        if begin:
            merged_kwargs.update(begin)
        super().__init__(
            trigger=trigger,
            reverse_trigger=reverse_trigger,
            controller=controller,
            replay_if_fired=replay_if_fired,
            **merged_kwargs,
        )

    def _apply_style(self, style: Mapping[str, Any]) -> None:
        for name, value in style.items():
            setattr(self, name, value)

    def _play_forward(self) -> None:
        if self._end_style:
            self._apply_style(self._end_style)

    def _play_reverse(self) -> None:
        if self._begin_style:
            self._apply_style(self._begin_style)

