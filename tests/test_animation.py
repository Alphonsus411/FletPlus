from __future__ import annotations

import flet as ft
import pytest

from fletplus.animation import (
    AnimatedContainer,
    AnimationController,
    FadeIn,
    Scale,
    SlideTransition,
    animation_controller_context,
)


@pytest.fixture()
def controller() -> AnimationController:
    return AnimationController()


def test_fade_in_plays_on_mount(controller: AnimationController) -> None:
    with animation_controller_context.provide(controller, inherit=False):
        fade = FadeIn(
            ft.Text("Hola"),
            duration=420,
            curve=ft.AnimationCurve.LINEAR,
        )
    assert isinstance(fade.animate_opacity, ft.Animation)
    assert fade.animate_opacity.duration == 420
    assert fade.animate_opacity.curve == ft.AnimationCurve.LINEAR
    assert fade.opacity == pytest.approx(0.0)

    controller.trigger("mount")
    assert fade.opacity == pytest.approx(1.0)


def test_slide_transition_updates_offset(controller: AnimationController) -> None:
    begin = ft.transform.Offset(-0.5, 0)
    end = ft.transform.Offset(0, 0)
    with animation_controller_context.provide(controller, inherit=False):
        slide = SlideTransition(
            ft.Container(),
            duration=515,
            curve=ft.AnimationCurve.EASE_IN_OUT,
            begin=begin,
            end=end,
        )
    assert isinstance(slide.animate_offset, ft.Animation)
    assert slide.animate_offset.duration == 515
    assert slide.animate_offset.curve == ft.AnimationCurve.EASE_IN_OUT
    assert slide.offset == begin

    controller.trigger("mount")
    assert slide.offset == end


def test_scale_reacts_to_unmount(controller: AnimationController) -> None:
    with animation_controller_context.provide(controller, inherit=False):
        scale = Scale(ft.Container(), begin=ft.transform.Scale(1.0, 1.0), end=ft.transform.Scale(1.2, 1.2))
    controller.trigger("mount")
    assert scale.scale == ft.transform.Scale(1.2, 1.2)

    controller.trigger("unmount")
    assert scale.scale == ft.transform.Scale(1.0, 1.0)


def test_animated_container_switches_styles(controller: AnimationController) -> None:
    begin = {"padding": ft.Padding(4, 4, 4, 4), "bgcolor": "#111111"}
    end = {"padding": ft.Padding(12, 12, 12, 12), "bgcolor": "#222222"}
    with animation_controller_context.provide(controller, inherit=False):
        animated = AnimatedContainer(
            ft.Text("Demo"),
            duration=300,
            curve=ft.AnimationCurve.BOUNCE_OUT,
            begin=begin,
            end=end,
        )
    assert isinstance(animated.animate, ft.Animation)
    assert animated.animate.duration == 300
    assert animated.animate.curve == ft.AnimationCurve.BOUNCE_OUT
    assert animated.padding == begin["padding"]
    assert animated.bgcolor == begin["bgcolor"]

    controller.trigger("mount")
    assert animated.padding == end["padding"]
    assert animated.bgcolor == end["bgcolor"]


def test_replay_if_trigger_already_fired(controller: AnimationController) -> None:
    controller.trigger("mount")

    with animation_controller_context.provide(controller, inherit=False):
        fade = FadeIn(ft.Text("Hola"), replay_if_fired=True)

    assert fade.opacity == pytest.approx(1.0)
