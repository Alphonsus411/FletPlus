"""Helpers de viewport para interfaces responsivas en FletPlus."""

from __future__ import annotations

from typing import Literal, Sequence

import flet as ft

from fletplus.utils.device_profiles import (
    DEFAULT_DEVICE_PROFILES,
    DeviceProfile,
    get_device_profile,
)
from fletplus.utils.flet_compat import get_page_height, get_page_width

Orientation = Literal["portrait", "landscape"]
VisualDensity = Literal["compact", "normal", "comfortable"]


def safe_page_width(page: ft.Page, fallback: int | float = 0) -> int:
    """Devuelve un ancho de página siempre no negativo."""

    try:
        width = get_page_width(page)
    except (AttributeError, TypeError, ValueError):
        width = fallback
    return max(0, int(width or fallback or 0))


def safe_page_height(page: ft.Page, fallback: int | float = 0) -> int:
    """Devuelve un alto de página siempre no negativo."""

    try:
        height = get_page_height(page)
    except (AttributeError, TypeError, ValueError):
        height = fallback
    return max(0, int(height or fallback or 0))


def safe_page_size(
    page: ft.Page,
    fallback_width: int | float = 0,
    fallback_height: int | float = 0,
) -> tuple[int, int]:
    """Devuelve ``(width, height)`` normalizados para un ``ft.Page``."""

    return (
        safe_page_width(page, fallback=fallback_width),
        safe_page_height(page, fallback=fallback_height),
    )


def viewport_orientation(page: ft.Page) -> Orientation:
    """Detecta si el viewport actual está en ``portrait`` o ``landscape``."""

    width, height = safe_page_size(page)
    return "portrait" if height >= width else "landscape"


def active_device_profile(
    page: ft.Page,
    profiles: Sequence[DeviceProfile] | None = None,
    fallback_width: int | float = 0,
) -> DeviceProfile:
    """Resuelve el perfil de dispositivo activo usando el ancho seguro."""

    return get_device_profile(
        safe_page_width(page, fallback=fallback_width),
        profiles if profiles is not None else DEFAULT_DEVICE_PROFILES,
    )


def visual_density_for_page(
    page: ft.Page,
    *,
    profiles: Sequence[DeviceProfile] | None = None,
) -> VisualDensity:
    """Calcula densidad visual sugerida para el viewport actual."""

    profile = active_device_profile(page, profiles=profiles)
    orientation = viewport_orientation(page)
    height = safe_page_height(page)

    if profile.name == "mobile" or height < 520:
        return "compact"
    if profile.name == "tablet" or orientation == "portrait":
        return "normal"
    return "comfortable"


def safe_mobile_padding(
    page: ft.Page,
    base: int = 16,
    *,
    profiles: Sequence[DeviceProfile] | None = None,
) -> ft.Padding:
    """Calcula padding seguro para mobile considerando orientación y densidad."""

    profile = active_device_profile(page, profiles=profiles)
    orientation = viewport_orientation(page)
    density = visual_density_for_page(page, profiles=profiles)

    if density == "compact":
        horizontal = max(8, round(base * 0.75))
        vertical = max(8, round(base * 0.625))
    elif density == "normal":
        horizontal = base
        vertical = max(10, round(base * 0.875))
    else:
        horizontal = round(base * 1.25)
        vertical = base

    if profile.name == "mobile":
        top = vertical + (4 if orientation == "portrait" else 0)
        bottom = vertical + (8 if orientation == "portrait" else 4)
        return ft.Padding(horizontal, top, horizontal, bottom)

    return ft.Padding(horizontal, vertical, horizontal, vertical)


__all__ = [
    "Orientation",
    "VisualDensity",
    "active_device_profile",
    "safe_mobile_padding",
    "safe_page_height",
    "safe_page_size",
    "safe_page_width",
    "viewport_orientation",
    "visual_density_for_page",
]
