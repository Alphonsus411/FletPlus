"""Perfiles reutilizables para adaptar interfaces según el ancho disponible."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DeviceProfile:
    """Describe un rango de ancho asociado a un tipo de dispositivo."""

    name: str
    min_width: int
    max_width: int | None
    columns: int
    description: str = ""

    def matches(self, width: int) -> bool:
        """Retorna ``True`` si ``width`` cae dentro del rango del perfil."""

        upper_ok = self.max_width is None or width <= self.max_width
        return width >= self.min_width and upper_ok


DEFAULT_DEVICE_PROFILES: tuple[DeviceProfile, ...] = (
    DeviceProfile(
        name="mobile",
        min_width=0,
        max_width=599,
        columns=4,
        description="Teléfonos y pantallas muy compactas",
    ),
    DeviceProfile(
        name="tablet",
        min_width=600,
        max_width=1023,
        columns=8,
        description="Tabletas, pantallas híbridas o ventanas medianas",
    ),
    DeviceProfile(
        name="desktop",
        min_width=1024,
        max_width=None,
        columns=12,
        description="Escritorios, portátiles o monitores anchos",
    ),
)


EXTENDED_DEVICE_PROFILES: tuple[DeviceProfile, ...] = DEFAULT_DEVICE_PROFILES + (
    DeviceProfile(
        name="large_desktop",
        min_width=1440,
        max_width=None,
        columns=16,
        description="Monitores ultraanchos, proyectores o estaciones profesionales",
    ),
)


def get_device_profile(
    width: int,
    profiles: Sequence[DeviceProfile] | None = None,
) -> DeviceProfile:
    """Devuelve el :class:`DeviceProfile` más adecuado para ``width``."""

    if profiles is not None:
        catalog = tuple(profiles)
        if not catalog:
            raise ValueError("At least one device profile must be provided")
    else:
        catalog = DEFAULT_DEVICE_PROFILES

    ordered = sorted(catalog, key=lambda p: p.min_width, reverse=True)
    for profile in ordered:
        if profile.matches(width):
            return profile
    # Si ningún perfil coincide, devolvemos el de menor ancho
    return ordered[-1]


def iter_device_profiles(
    profiles: Sequence[DeviceProfile] | None = None,
) -> Iterable[DeviceProfile]:
    """Itera perfiles ordenados por ``min_width`` ascendente."""

    catalog = tuple(profiles or DEFAULT_DEVICE_PROFILES)
    return tuple(sorted(catalog, key=lambda p: p.min_width))


def device_name(width: int, profiles: Sequence[DeviceProfile] | None = None) -> str:
    """Conveniencia para obtener solo el nombre del perfil activo."""

    return get_device_profile(width, profiles).name


def columns_for_width(
    width: int,
    profiles: Sequence[DeviceProfile] | None = None,
) -> int:
    """Devuelve el número de columnas sugerido para ``width``."""

    return get_device_profile(width, profiles).columns
