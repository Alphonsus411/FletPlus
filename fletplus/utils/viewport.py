"""Helpers de viewport para interfaces responsivas en FletPlus."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class ViewportInfo:
    """Snapshot normalizado del viewport activo.

    El snapshot evita recalcular ancho, alto, orientación, perfil y densidad en
    varios widgets dentro del mismo ciclo de resize. Es especialmente útil en
    callbacks de ``ResponsiveManager`` y plantillas generadas por la CLI.
    """

    width: int
    height: int
    orientation: Orientation
    profile: DeviceProfile
    density: VisualDensity
    padding: ft.Padding


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


def orientation_from_size(width: int | float, height: int | float) -> Orientation:
    """Detecta orientación a partir de dimensiones ya normalizadas."""

    return "portrait" if height >= width else "landscape"


def viewport_orientation(page: ft.Page) -> Orientation:
    """Detecta si el viewport actual está en ``portrait`` o ``landscape``."""

    width, height = safe_page_size(page)
    return orientation_from_size(width, height)


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


def density_for_viewport(
    width: int | float,
    height: int | float,
    profile: DeviceProfile,
) -> VisualDensity:
    """Calcula densidad visual a partir de tamaño y perfil ya resueltos."""

    orientation = orientation_from_size(width, height)
    if profile.name == "mobile" or height < 520:
        return "compact"
    if profile.name == "tablet" or orientation == "portrait":
        return "normal"
    return "comfortable"


def visual_density_for_page(
    page: ft.Page,
    *,
    profiles: Sequence[DeviceProfile] | None = None,
) -> VisualDensity:
    """Calcula densidad visual sugerida para el viewport actual."""

    width, height = safe_page_size(page)
    profile = get_device_profile(width, profiles or DEFAULT_DEVICE_PROFILES)
    return density_for_viewport(width, height, profile)


def padding_for_viewport(
    profile: DeviceProfile,
    orientation: Orientation,
    density: VisualDensity,
    base: int = 16,
) -> ft.Padding:
    """Calcula padding seguro desde perfil, orientación y densidad resueltos."""

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
    return padding_for_viewport(profile, orientation, density, base=base)


def viewport_info(
    page: ft.Page,
    *,
    profiles: Sequence[DeviceProfile] | None = None,
    fallback_width: int | float = 0,
    fallback_height: int | float = 0,
    padding_base: int = 16,
) -> ViewportInfo:
    """Devuelve un snapshot completo y consistente del viewport actual."""

    width, height = safe_page_size(page, fallback_width, fallback_height)
    profile = get_device_profile(width, profiles or DEFAULT_DEVICE_PROFILES)
    orientation = orientation_from_size(width, height)
    density = density_for_viewport(width, height, profile)
    padding = padding_for_viewport(profile, orientation, density, base=padding_base)
    return ViewportInfo(width, height, orientation, profile, density, padding)


__all__ = [
    "Orientation",
    "VisualDensity",
    "ViewportInfo",
    "active_device_profile",
    "density_for_viewport",
    "orientation_from_size",
    "padding_for_viewport",
    "safe_mobile_padding",
    "safe_page_height",
    "safe_page_size",
    "safe_page_width",
    "viewport_info",
    "viewport_orientation",
    "visual_density_for_page",
]
