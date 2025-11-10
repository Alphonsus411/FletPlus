"""Catálogo de iconos reutilizables para FletPlus.

El módulo expone utilidades para resolver nombres de iconos a partir de los
catálogos incluidos de Material y Lucide. También permite registrar iconos
personalizados en tiempo de ejecución y construir instancias de
:class:`flet.Icon` listas para usar.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Dict, Iterable, Mapping, MutableMapping

import flet as ft

DEFAULT_ICON_SET = "material"
_DEFAULT_FALLBACK_ICON = "help"

_CATALOG_FILES: Mapping[str, str] = {
    "material": "material.json",
    "lucide": "lucide.json",
}

# Registro en memoria para catálogos personalizados y sobre-escrituras.
_CUSTOM_CATALOGS: MutableMapping[str, Dict[str, str]] = {}


def _normalise_name(name: str) -> str:
    """Normaliza un nombre de icono para facilitar las búsquedas."""

    return name.replace("-", "_").replace(" ", "_").lower()


@lru_cache(maxsize=None)
def _load_base_catalog(icon_set: str) -> Dict[str, str]:
    """Carga el catálogo base de un set de iconos desde los recursos."""

    if icon_set not in _CATALOG_FILES:
        raise KeyError(f"El set de iconos '{icon_set}' no está disponible")

    resource = resources.files(__package__).joinpath(_CATALOG_FILES[icon_set])
    with resource.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    return {_normalise_name(key): value for key, value in data.items()}


def _merge_catalogs(icon_set: str) -> Dict[str, str]:
    catalog: Dict[str, str] = {}
    if icon_set in _CATALOG_FILES:
        catalog.update(_load_base_catalog(icon_set))
    if icon_set in _CUSTOM_CATALOGS:
        catalog.update(_CUSTOM_CATALOGS[icon_set])
    if not catalog:
        raise KeyError(f"No existe el set de iconos '{icon_set}'")
    return catalog


def available_icon_sets() -> Iterable[str]:
    """Devuelve los sets de iconos disponibles, incluidos los personalizados."""

    return sorted(set(_CATALOG_FILES) | set(_CUSTOM_CATALOGS))


def list_icons(icon_set: str = DEFAULT_ICON_SET) -> Iterable[str]:
    """Lista los identificadores disponibles para un set determinado."""

    catalog = _merge_catalogs(icon_set)
    return sorted(catalog)


def has_icon(name: str, icon_set: str = DEFAULT_ICON_SET) -> bool:
    """Indica si un icono existe dentro del catálogo indicado."""

    normalised = _normalise_name(name)
    try:
        catalog = _merge_catalogs(icon_set)
    except KeyError:
        return False
    return normalised in catalog


@lru_cache(maxsize=1024)
def _resolve_icon_name(name: str, icon_set: str) -> str:
    catalog = _merge_catalogs(icon_set)
    normalised = _normalise_name(name)
    if normalised not in catalog:
        raise KeyError(name)
    return catalog[normalised]


def resolve_icon_name(
    name: str,
    icon_set: str = DEFAULT_ICON_SET,
    *,
    fallback: str | None = _DEFAULT_FALLBACK_ICON,
    fallback_set: str | None = None,
) -> str:
    """Resuelve el nombre final del icono a utilizar."""

    try:
        return _resolve_icon_name(name, icon_set)
    except KeyError:
        if fallback is None:
            raise ValueError(
                f"El icono '{name}' no existe en el set '{icon_set}'"
            ) from None

    fallback_set = fallback_set or icon_set
    try:
        return _resolve_icon_name(fallback, fallback_set)
    except KeyError as exc:
        raise ValueError(
            f"Ni el icono '{name}' ni el fallback '{fallback}' existen en los sets"
            f" '{icon_set}'/'{fallback_set}'"
        ) from exc


def icon(
    name: str,
    *,
    icon_set: str = DEFAULT_ICON_SET,
    fallback: str | None = _DEFAULT_FALLBACK_ICON,
    fallback_set: str | None = None,
    **icon_kwargs,
) -> ft.Icon:
    """Crea una instancia de :class:`flet.Icon` para el icono indicado."""

    resolved_name = resolve_icon_name(
        name,
        icon_set=icon_set,
        fallback=fallback,
        fallback_set=fallback_set,
    )
    return ft.Icon(name=resolved_name, **icon_kwargs)


@dataclass(slots=True)
class Icon:
    """Helper orientado a objetos para construir instancias de :class:`flet.Icon`."""

    name: str
    icon_set: str = DEFAULT_ICON_SET
    fallback: str | None = _DEFAULT_FALLBACK_ICON
    fallback_set: str | None = None
    kwargs: Dict[str, object] | None = None

    def build(self) -> ft.Icon:
        """Construye el icono configurado."""

        resolved_name = resolve_icon_name(
            self.name,
            icon_set=self.icon_set,
            fallback=self.fallback,
            fallback_set=self.fallback_set,
        )
        return ft.Icon(name=resolved_name, **(self.kwargs or {}))

    def __call__(self) -> ft.Icon:
        return self.build()


def register_icon(
    name: str,
    value: str,
    icon_set: str = DEFAULT_ICON_SET,
) -> None:
    """Registra o sobreescribe un icono dentro de un set."""

    icon_set = icon_set.lower()
    normalised = _normalise_name(name)
    catalog = _CUSTOM_CATALOGS.setdefault(icon_set, {})
    catalog[normalised] = value
    _resolve_icon_name.cache_clear()


def register_icon_set(icon_set: str, catalog: Mapping[str, str]) -> None:
    """Registra un set de iconos completo a partir de un *mapping*."""

    icon_set = icon_set.lower()
    normalised_catalog = {
        _normalise_name(name): value for name, value in catalog.items()
    }
    existing = _CUSTOM_CATALOGS.setdefault(icon_set, {})
    existing.update(normalised_catalog)
    _resolve_icon_name.cache_clear()


__all__ = [
    "DEFAULT_ICON_SET",
    "available_icon_sets",
    "has_icon",
    "icon",
    "Icon",
    "list_icons",
    "register_icon",
    "register_icon_set",
    "resolve_icon_name",
]
