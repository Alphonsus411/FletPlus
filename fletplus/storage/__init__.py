"""Proveedores de almacenamiento con interfaz unificada y señales reactivas."""

from __future__ import annotations

from collections.abc import Callable
from types import MappingProxyType
from typing import Any, Dict, Generic, Iterable, Mapping, TypeVar

from fletplus.state import Signal

__all__ = [
    "StorageProvider",
    "Serializer",
    "Deserializer",
]

_T = TypeVar("_T")

Serializer = Callable[[Any], Any]
Deserializer = Callable[[Any], Any]


class _Missing:
    __slots__ = ()


MISSING = _Missing()
MISSING_VALUE = object()


class StorageProvider(Generic[_T]):
    """Interfaz base para proveedores de almacenamiento sincronizados con la UI.

    Los proveedores envuelven diferentes mecanismos de persistencia
    (almacenamiento local, de sesión o archivos) y exponen operaciones comunes
    para manipular claves. Además, generan señales de :mod:`fletplus.state`
    para que los controles reactivos puedan reflejar automáticamente los
    cambios.

    Args:
        serializer:
            Función encargada de transformar los valores Python antes de
            persistirlos en el backend concreto. Por defecto se utiliza la
            identidad, asumiendo que el backend admite tipos JSON serializables.
        deserializer:
            Función que invierte la operación anterior recuperando el valor
            original. Por defecto también es la identidad.
    """

    def __init__(
        self,
        *,
        serializer: Serializer | None = None,
        deserializer: Deserializer | None = None,
    ) -> None:
        self._serialize: Serializer = serializer or (lambda value: value)
        self._deserialize: Deserializer = deserializer or (lambda value: value)
        self._signals: Dict[str, Signal[Any]] = {}
        self._defaults: Dict[str, Any] = {}
        self._snapshot_signal: Signal[Mapping[str, Any]] = Signal(
            self._build_snapshot()
        )

    # ------------------------------------------------------------------
    def _build_snapshot(self) -> MappingProxyType[str, Any]:
        data: Dict[str, Any] = {}
        for key in self._iter_keys():
            data[key] = self.get(key)
        return MappingProxyType(data)

    # ------------------------------------------------------------------
    def _refresh_snapshot(self) -> None:
        self._snapshot_signal.set(self._build_snapshot())

    # Métodos que deben implementar los proveedores concretos --------------
    def _iter_keys(self) -> Iterable[str]:  # pragma: no cover - abstracto
        raise NotImplementedError

    def _read_raw(self, key: str) -> Any:  # pragma: no cover - abstracto
        raise NotImplementedError

    def _write_raw(self, key: str, value: Any) -> None:  # pragma: no cover
        raise NotImplementedError

    def _remove_raw(self, key: str) -> None:  # pragma: no cover - abstracto
        raise NotImplementedError

    def _clear_raw(self) -> None:  # pragma: no cover - abstracto
        raise NotImplementedError

    # Operaciones públicas -------------------------------------------------
    def get(self, key: str, default: _T | None = None) -> _T | None:
        """Recupera un valor aplicando la función de deserialización."""

        try:
            raw = self._read_raw(key)
        except KeyError:
            return default
        if raw is MISSING_VALUE:
            return default
        return self._deserialize(raw)

    # ------------------------------------------------------------------
    def set(self, key: str, value: _T) -> _T:
        """Persiste un valor y notifica a las señales asociadas."""

        serialized = self._serialize(value)
        self._write_raw(key, serialized)
        if key in self._signals:
            self._signals[key].set(value)
        self._refresh_snapshot()
        return value

    # ------------------------------------------------------------------
    def remove(self, key: str) -> None:
        """Elimina una clave del almacenamiento."""

        if key not in self:
            return
        try:
            self._remove_raw(key)
        except KeyError:
            return
        if key in self._signals:
            default = self._defaults.get(key)
            self._signals[key].set(default)
        self._refresh_snapshot()

    # ------------------------------------------------------------------
    def clear(self) -> None:
        """Limpia todas las claves disponibles."""

        self._clear_raw()
        for key, signal in self._signals.items():
            signal.set(self._defaults.get(key))
        self._refresh_snapshot()

    # ------------------------------------------------------------------
    def keys(self) -> Iterable[str]:
        """Devuelve un iterador sobre las claves conocidas."""

        return tuple(self._iter_keys())

    # ------------------------------------------------------------------
    def snapshot(self) -> Mapping[str, Any]:
        """Retorna una vista inmutable de todas las claves y valores."""

        return self._snapshot_signal.get()

    # ------------------------------------------------------------------
    def snapshot_signal(self) -> Signal[Mapping[str, Any]]:
        """Señal reactiva del estado completo del almacenamiento."""

        return self._snapshot_signal

    # ------------------------------------------------------------------
    def signal(self, key: str, *, default: Any | _Missing = MISSING) -> Signal[Any]:
        """Obtiene una señal asociada a una clave concreta."""

        if key not in self._signals:
            if default is MISSING:
                value = self.get(key)
                stored_default = None
            else:
                value = self.get(key, default)
                stored_default = default
            signal = Signal(value)
            self._signals[key] = signal
            self._defaults[key] = stored_default
        else:
            if default is not MISSING:
                self._defaults[key] = default
        return self._signals[key]

    # ------------------------------------------------------------------
    def subscribe(
        self,
        key: str,
        callback: Callable[[Any], None],
        *,
        immediate: bool = True,
        default: Any | _Missing = MISSING,
    ) -> Callable[[], None]:
        """Conveniencia para registrar *callbacks* sobre una clave."""

        return self.signal(key, default=default).subscribe(
            callback, immediate=immediate
        )

    # ------------------------------------------------------------------
    def bind_control(self, key: str, control: Any, **kwargs: Any) -> Callable[[], None]:
        """Enlaza el valor de una clave con un control de Flet."""

        return self.signal(key).bind_control(control, **kwargs)

    # ------------------------------------------------------------------
    def __contains__(self, key: str) -> bool:
        try:
            raw = self._read_raw(key)
        except KeyError:
            return False
        return raw is not MISSING_VALUE

    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return len(tuple(self._iter_keys()))
