"""Utilidades para gestionar alias de breakpoints consistentes en toda la librería."""

from __future__ import annotations

from typing import Dict, Mapping, Tuple, TypeVar

T = TypeVar("T")


class BreakpointRegistry:
    """Mantiene un registro global de breakpoints simbólicos."""

    _aliases: Dict[str, int] = {"xs": 0, "md": 768, "xl": 1280}

    @classmethod
    def configure(cls, **aliases: int) -> None:
        """Actualiza los valores asociados a alias simbólicos."""

        for name, value in aliases.items():
            cls._aliases[name.strip().lower()] = max(0, int(value))

    @classmethod
    def resolve(cls, key: int | str) -> int:
        """Convierte ``key`` en un breakpoint numérico."""

        if isinstance(key, str):
            alias = key.strip().lower()
            if alias not in cls._aliases:
                raise KeyError(f"Alias de breakpoint desconocido: {key!r}")
            return cls._aliases[alias]
        return int(key)

    @classmethod
    def normalize(cls, mapping: Mapping[int | str, T]) -> Dict[int, T]:
        """Normaliza un ``mapping`` sustituyendo alias simbólicos por enteros."""

        normalized: Dict[int, T] = {}
        for key, value in mapping.items():
            normalized[cls.resolve(key)] = value
        return normalized

    @classmethod
    def collect_breakpoints(
        cls, *mappings: Mapping[int | str, object] | None
    ) -> Tuple[int, ...]:
        """Devuelve un conjunto ordenado de breakpoints presentes en ``mappings``."""

        values: set[int] = set()
        for mapping in mappings:
            if not mapping:
                continue
            normalized = cls.normalize(mapping)
            values.update(normalized.keys())
        return tuple(sorted(values))


__all__ = ["BreakpointRegistry"]
