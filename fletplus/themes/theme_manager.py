# fletplus/themes/theme_manager.py

"""Utilities to manage visual theme tokens for a Flet page.

This module exposes :class:`ThemeManager`, a helper that keeps a dictionary
of design tokens (colors, typography, radii, spacing, borders and shadows)
and applies them to a ``ft.Page`` instance. Tokens can be queried or updated
at runtime using ``get_token`` and ``set_token`` which immediately refresh
the page theme.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
from collections.abc import Callable, Mapping
from copy import deepcopy
import flet as ft

from fletplus.themes.palettes import (
    get_palette_definition,
    has_palette,
    list_palettes,
)
from fletplus.themes.presets import (
    get_preset_definition,
    has_preset,
)
from fletplus.themes.token_merge_rs import merge_token_layers
from fletplus.state import Signal

logger = logging.getLogger(__name__)


def _load_palette_flatten_backend():
    spec = importlib.util.find_spec("fletplus.themes.palette_flatten_rs")
    if spec is None:
        return None
    module = importlib.import_module("fletplus.themes.palette_flatten_rs")
    if getattr(module, "flatten_palette", None) is None:
        return None
    return module


_PALETTE_FLATTEN_RS = _load_palette_flatten_backend()


def _load_theme_merge_backend():
    spec = importlib.util.find_spec("fletplus.themes.theme_merge_rs")
    if spec is None:
        return None
    module = importlib.import_module("fletplus.themes.theme_merge_rs")
    if getattr(module, "merge_token_groups", None) is None:
        return None
    if getattr(module, "merge_variant_overrides", None) is None:
        return None
    return module


_THEME_MERGE_RS = _load_theme_merge_backend()


def _merge_token_groups(
    target: dict[str, dict[str, object]],
    updates: Mapping[str, object],
) -> None:
    if _THEME_MERGE_RS is not None:
        _THEME_MERGE_RS.merge_token_groups(target, updates)
        return
    for group, values in updates.items():
        if not isinstance(values, Mapping):
            continue
        existing = target.setdefault(group, {})
        if not isinstance(existing, dict):
            target[group] = dict(values)
        else:
            existing.update(values)


def _parse_theme_json(file_path: str) -> dict[str, object]:
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        logger.error("Theme file '%s' not found", file_path)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in theme file '%s': %s", file_path, exc)
        return {}

    if not isinstance(data, Mapping):
        logger.error("Theme file '%s' must contain a JSON object", file_path)
        return {}

    preset_name = data.get("preset")
    normalized_preset: str | None = None

    if isinstance(preset_name, str):
        candidate = preset_name.lower()
        if has_preset(candidate):
            normalized_preset = candidate
            definition = get_preset_definition(candidate)
        else:
            logger.error("Preset '%s' referenced in '%s' is not registered", preset_name, file_path)
            definition = {"light": {}, "dark": {}}
    else:
        definition = {"light": {}, "dark": {}}

    common_tokens = data.get("tokens")
    if _THEME_MERGE_RS is not None:
        overrides = {"light": data.get("light"), "dark": data.get("dark")}
        _THEME_MERGE_RS.merge_variant_overrides(
            definition,
            common_tokens if isinstance(common_tokens, Mapping) else None,
            overrides,
        )
    else:
        if isinstance(common_tokens, Mapping):
            for variant in ("light", "dark"):
                variant_mapping = definition.setdefault(variant, {})
                _merge_token_groups(variant_mapping, common_tokens)

        for variant in ("light", "dark"):
            overrides = data.get(variant)
            if isinstance(overrides, Mapping):
                variant_mapping = definition.setdefault(variant, {})
                _merge_token_groups(variant_mapping, overrides)

    mode = data.get("mode")
    mode_value: str | None = None
    if isinstance(mode, str) and mode.lower() in {"light", "dark"}:
        mode_value = mode.lower()

    return {
        "preset": normalized_preset,
        "mode": mode_value,
        "variants": definition,
    }


def load_palette_from_file(file_path: str, mode: str = "light") -> dict[str, object]:
    """Load a color palette from a JSON file.

    Parameters
    ----------
    file_path:
        Path to the JSON file containing palette definitions under "light"
        and/or "dark" keys.
    mode:
        Palette mode to load. Must be ``"light"`` or ``"dark"``.

    Returns
    -------
    dict[str, object]
        Palette dictionary for the requested mode with nested dictionaries
        flattened using underscore-separated keys. If the mode key is
        missing in the file, an empty dictionary is returned.
        Palette dictionary for the requested mode. Nested color groups
        such as ``{"info": {"100": "#BBDEFB"}}`` are flattened into
        ``{"info_100": "#BBDEFB"}``. This works for any semantic group
        (``info``, ``success``, ``warning`` or ``error``).
        If the mode key is missing, the file cannot be opened or contains
        invalid JSON, the error is logged and an empty dictionary is
        returned.

    Raises
    ------
    ValueError
        If ``mode`` is not ``"light"`` or ``"dark"``.
    """

    if mode not in {"light", "dark"}:
        raise ValueError("mode must be 'light' or 'dark'")

    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        logger.error("Palette file '%s' not found", file_path)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in palette file '%s': %s", file_path, exc)
        return {}

    if not isinstance(data, Mapping):
        logger.error("Palette file '%s' must contain a JSON object", file_path)
        return {}

    palette = data.get(mode)
    if not isinstance(palette, Mapping):
        logger.error(
            "Palette mode '%s' in '%s' must be a JSON object, got %s",
            mode,
            file_path,
            type(palette).__name__,
        )
        return {}

    def _flatten(prefix: str, value: object) -> dict[str, object]:
        """Flatten nested dictionaries using underscore-separated keys."""
        if isinstance(value, Mapping):
            flattened: dict[str, object] = {}
            for k, v in value.items():
                new_prefix = f"{prefix}_{k}" if prefix else k
                flattened.update(_flatten(new_prefix, v))
            return flattened
        if not prefix:
            return {}
        return {prefix: value}

    if _PALETTE_FLATTEN_RS is not None:
        return _PALETTE_FLATTEN_RS.flatten_palette(palette)
    return _flatten("", palette)


class ThemeManager:
    """Manage theme tokens and apply them to a Flet page.

    Parameters
    ----------
    page:
        ``ft.Page`` instance whose theme will be managed.
    tokens:
        Optional dictionary of initial tokens grouped by ``"colors"``,
        ``"typography"``, ``"radii"``, ``"spacing"``, ``"borders`` and
        ``"shadows"``. Each group contains key/value pairs representing
        individual design tokens. Missing groups or tokens are filled with
        sensible defaults.
    primary_color:
        Backwards compatible argument used when ``tokens`` does not specify
        ``"colors.primary"``. Defaults to ``ft.Colors.BLUE``.
    palette:
        Nombre de una paleta registrada o un mapeo de tokens agrupados por
        modo (``"light"``/``"dark"``) que se combinarán con los tokens
        principales.
    palette_mode:
        Variante inicial de la paleta (``"light"`` o ``"dark"``). Se ignora
        cuando ``follow_platform_theme`` es ``True`` para respetar la
        preferencia del sistema.
    device_tokens:
        Diccionario de overrides por dispositivo (``"mobile"``, ``"desktop"``,
        etc.). Cada valor contiene los grupos de tokens específicos.
    orientation_tokens:
        Overrides por orientación. Las claves deben ser ``"portrait"`` o
        ``"landscape"`` y los valores contienen los tokens a aplicar.
    breakpoint_tokens:
        Overrides basados en anchos mínimos. Las claves indican el breakpoint y
        cada valor contiene los tokens para esa resolución.
    follow_platform_theme:
        Si es ``True`` (valor por defecto) la instancia sincroniza el modo claro
        u oscuro con ``page.platform_brightness`` o ``page.platform_theme`` y
        se suscribe a ``page.on_platform_brightness_change`` (o APIs
        equivalentes). Establécelo en ``False`` para controlar el modo de forma
        manual.
    """

    def __init__(
        self,
        page: ft.Page,
        tokens: dict | None = None,
        primary_color: str = ft.Colors.BLUE,
        *,
        palette: str | Mapping[str, Mapping[str, object]] | None = None,
        palette_mode: str | None = None,
        device_tokens: Mapping[str, Mapping[str, Mapping[str, object]]] | None = None,
        orientation_tokens: Mapping[str, Mapping[str, Mapping[str, object]]] | None = None,
        breakpoint_tokens: Mapping[int, Mapping[str, Mapping[str, object]]] | None = None,
        follow_platform_theme: bool = True,
    ) -> None:
        self.page = page
        normalized_palette_mode = (
            palette_mode if palette_mode in {"dark", "light"} else None
        )
        self._follow_platform_theme = bool(follow_platform_theme)
        self._platform_theme_unsubscribers: list[Callable[[], None]] = []

        platform_preference = (
            self._read_platform_preference() if self._follow_platform_theme else None
        )

        self.dark_mode = (
            normalized_palette_mode == "dark" if normalized_palette_mode else False
        )
        if platform_preference is not None:
            self.dark_mode = platform_preference

        # Default token structure
        shade_range = range(100, 1000, 100)
        base_colors = {
            "secondary": "PURPLE",
            "tertiary": "TEAL",
            "info": "BLUE",
            "success": "GREEN",
            "warning": "AMBER",
            "error": "RED",
        }

        color_defaults = {
            "primary": primary_color,
            **{
                f"{token}_{n}": getattr(ft.Colors, f"{base}_{n}")
                for token, base in base_colors.items()
                for n in shade_range
            },
        }
        self.tokens: dict[str, dict[str, object]] = {
            "colors": color_defaults,
            "typography": {},
            "radii": {},
            "spacing": {"default": 8},
            "borders": {"default": 1},
            "shadows": {"default": "none"},
            "gradients": {},
        }

        self._palette_definition: dict[str, Mapping[str, object]] | None = None
        self._palette_name: str | None = None
        self._preset_name: str | None = None
        self._device_tokens: dict[str, dict[str, dict[str, object]]] = {}
        self._orientation_tokens: dict[str, dict[str, dict[str, object]]] = {}
        self._breakpoint_tokens: dict[int, dict[str, dict[str, object]]] = {}
        self._active_device: str | None = None
        self._active_orientation: str | None = None
        self._active_width: int | None = None
        self._active_breakpoint: int | None = None
        self._effective_tokens: dict[str, dict[str, object]] = deepcopy(self.tokens)
        self._persistent_overrides: dict[str, dict[str, object]] = {}

        self.mode_signal: Signal[bool] = Signal(self.dark_mode)
        self.tokens_signal: Signal[dict[str, dict[str, object]]] = Signal(
            deepcopy(self._effective_tokens),
            comparer=lambda _old, _new: False,
        )
        self.overrides_signal: Signal[dict[str, dict[str, object]]] = Signal({})

        if palette is not None:
            try:
                palette_variant = (
                    None
                    if self._follow_platform_theme
                    else normalized_palette_mode
                )
                self.apply_palette(palette, mode=palette_variant, refresh=False)
            except Exception as exc:  # pragma: no cover - errores logueados
                logger.error("Failed to apply palette '%s': %s", palette, exc)

        if tokens:
            for group, values in tokens.items():
                if isinstance(values, Mapping):
                    self.tokens.setdefault(group, {}).update(values)

        if device_tokens:
            for device, overrides in device_tokens.items():
                self.set_device_tokens(device, overrides, refresh=False)

        if orientation_tokens:
            for orientation, overrides in orientation_tokens.items():
                self.set_orientation_tokens(orientation, overrides, refresh=False)

        if breakpoint_tokens:
            for breakpoint, overrides in breakpoint_tokens.items():
                self.set_breakpoint_tokens(breakpoint, overrides, refresh=False)

        # Aplicar la variante inicial de la paleta tras fusionar tokens
        if self._palette_definition is not None:
            self._apply_current_palette_variant()

        self._refresh_effective_tokens(
            self._active_device, self._active_orientation, self._active_width
        )
        self._emit_tokens_snapshot()
        if self._follow_platform_theme:
            self._install_platform_theme_listeners()
            self.mode_signal.set(self.dark_mode)

    # ------------------------------------------------------------------
    def apply_theme(
        self,
        *,
        device: str | None = None,
        orientation: str | None = None,
        width: int | float | None = None,
    ) -> None:
        """Apply current tokens to the page theme."""

        if device is not None:
            self._active_device = device.lower()

        if orientation is not None:
            self._active_orientation = orientation.lower()

        if width is not None:
            try:
                self._active_width = int(width)
            except (TypeError, ValueError):
                self._active_width = None

        self._refresh_effective_tokens(
            self._active_device, self._active_orientation, self._active_width
        )

        colors = self._effective_tokens.get("colors", {})
        typography = self._effective_tokens.get("typography", {})
        radii = self._effective_tokens.get("radii", {})
        spacing = self._effective_tokens.get("spacing", {})
        borders = self._effective_tokens.get("borders", {})
        shadows = self._effective_tokens.get("shadows", {})

        self.page.theme = ft.Theme(
            color_scheme_seed=colors.get("primary"),
            font_family=typography.get("font_family"),
        )
        # Store additional tokens that are not directly supported by
        # ``ft.Theme`` as custom attributes.
        self.page.theme.radii = radii
        self.page.theme.spacing = spacing
        self.page.theme.borders = borders
        self.page.theme.shadows = shadows
        self.page.theme_mode = (
            ft.ThemeMode.DARK if self.dark_mode else ft.ThemeMode.LIGHT
        )

        background = colors.get("background")
        if background:
            self.page.bgcolor = background
        surface = colors.get("surface")
        if surface:
            setattr(self.page, "surface_tint_color", surface)

        self.page.update()
        self._emit_tokens_snapshot()

    # ------------------------------------------------------------------
    def set_dark_mode(self, value: bool, *, refresh: bool = True) -> None:
        """Establece el modo oscuro de forma explícita."""

        desired = bool(value)
        if desired == self.dark_mode:
            return
        self.dark_mode = desired
        self._apply_current_palette_variant()
        if refresh:
            self.apply_theme()
        else:
            self._refresh_effective_tokens(
                self._active_device, self._active_orientation, self._active_width
            )
            self._emit_tokens_snapshot()
        self.mode_signal.set(self.dark_mode)

    # ------------------------------------------------------------------
    def toggle_dark_mode(self) -> None:
        """Toggle between light and dark modes."""

        self.set_dark_mode(not self.dark_mode)

    # ------------------------------------------------------------------
    def set_follow_platform_theme(
        self, value: bool, *, apply_current: bool = True
    ) -> None:
        """Activa o desactiva la sincronización automática con el sistema."""

        desired = bool(value)
        if desired == self._follow_platform_theme:
            if desired and apply_current:
                self._sync_with_platform_preference()
            return

        self._follow_platform_theme = desired

        if desired:
            self._install_platform_theme_listeners()
            if apply_current:
                self._sync_with_platform_preference()
        else:
            self._dispose_platform_theme_listeners()

    # ------------------------------------------------------------------
    def apply_palette(
        self,
        palette: str | Mapping[str, Mapping[str, object]],
        *,
        mode: str | None = None,
        refresh: bool = True,
    ) -> None:
        """Carga una paleta predefinida o personalizada y actualiza los tokens."""

        palette_definition: dict[str, Mapping[str, object]] | None

        if isinstance(palette, str):
            if not has_palette(palette):
                raise ValueError(f"Palette '{palette}' is not registered")
            definition = get_palette_definition(palette) or {}
            palette_definition = {
                key: value
                for key, value in definition.items()
                if isinstance(value, Mapping)
            }
            self._palette_name = palette
        elif isinstance(palette, Mapping):
            palette_definition = {
                key: value
                for key, value in palette.items()
                if isinstance(value, Mapping)
            }
            self._palette_name = None
        else:
            raise TypeError("palette must be a name or a mapping of tokens")

        if mode in {"light", "dark"}:
            if self._follow_platform_theme:
                self.set_follow_platform_theme(False, apply_current=False)
            self.dark_mode = mode == "dark"

        self._palette_definition = palette_definition
        self._preset_name = None
        self._apply_current_palette_variant()

        if refresh:
            self.apply_theme()
        self.mode_signal.set(self.dark_mode)

    # ------------------------------------------------------------------
    def set_device_tokens(
        self,
        device: str,
        tokens: Mapping[str, Mapping[str, object]],
        *,
        refresh: bool = True,
    ) -> None:
        """Registra tokens específicos para ``device``."""

        normalized_device = device.lower().strip()
        overrides: dict[str, dict[str, object]] = {}
        for group, values in tokens.items():
            if isinstance(values, Mapping):
                overrides[group] = {key: value for key, value in values.items()}
        if not overrides:
            return

        self._device_tokens[normalized_device] = overrides
        if refresh:
            self.apply_theme(device=self._active_device or normalized_device)

    # ------------------------------------------------------------------
    def clear_device_tokens(self, device: str | None = None) -> None:
        """Elimina tokens adaptativos registrados."""

        if device is None:
            self._device_tokens.clear()
        else:
            self._device_tokens.pop(device.lower().strip(), None)
        self.apply_theme(device=self._active_device)

    # ------------------------------------------------------------------
    def set_orientation_tokens(
        self,
        orientation: str,
        tokens: Mapping[str, Mapping[str, object]],
        *,
        refresh: bool = True,
    ) -> None:
        """Registra tokens específicos para una orientación."""

        normalized = orientation.lower().strip()
        overrides: dict[str, dict[str, object]] = {}
        for group, values in tokens.items():
            if isinstance(values, Mapping):
                overrides[group] = {key: value for key, value in values.items()}
        if not overrides:
            return

        self._orientation_tokens[normalized] = overrides
        if refresh:
            self.apply_theme(orientation=self._active_orientation or normalized)

    # ------------------------------------------------------------------
    def clear_orientation_tokens(self, orientation: str | None = None) -> None:
        """Elimina los tokens registrados para una orientación."""

        if orientation is None:
            self._orientation_tokens.clear()
        else:
            self._orientation_tokens.pop(orientation.lower().strip(), None)
        self.apply_theme(orientation=self._active_orientation)

    # ------------------------------------------------------------------
    def set_breakpoint_tokens(
        self,
        breakpoint: int | float,
        tokens: Mapping[str, Mapping[str, object]],
        *,
        refresh: bool = True,
    ) -> None:
        """Registra tokens para un breakpoint mínimo de ancho."""

        try:
            bp_value = int(breakpoint)
        except (TypeError, ValueError):
            raise ValueError("breakpoint must be an integer value") from None

        overrides: dict[str, dict[str, object]] = {}
        for group, values in tokens.items():
            if isinstance(values, Mapping):
                overrides[group] = {key: value for key, value in values.items()}
        if not overrides:
            return

        self._breakpoint_tokens[bp_value] = overrides
        if refresh:
            self.apply_theme(width=self._active_width or bp_value)

    # ------------------------------------------------------------------
    def clear_breakpoint_tokens(self, breakpoint: int | None = None) -> None:
        """Elimina overrides registrados para breakpoints de ancho."""

        if breakpoint is None:
            self._breakpoint_tokens.clear()
        else:
            self._breakpoint_tokens.pop(int(breakpoint), None)
        self.apply_theme(width=self._active_width)

    # ------------------------------------------------------------------
    @property
    def active_device(self) -> str | None:
        """Devuelve el dispositivo actualmente activo."""

        return self._active_device

    # ------------------------------------------------------------------
    @property
    def active_orientation(self) -> str | None:
        """Devuelve la orientación aplicada actualmente."""

        return self._active_orientation

    # ------------------------------------------------------------------
    @property
    def active_breakpoint(self) -> int | None:
        """Breakpoint de ancho actualmente aplicado."""

        return self._active_breakpoint

    # ------------------------------------------------------------------
    @property
    def effective_tokens(self) -> dict[str, dict[str, object]]:
        """Tokens tras aplicar overrides por dispositivo."""

        return self._effective_tokens

    # ------------------------------------------------------------------
    @staticmethod
    def _split_name(name: str) -> tuple[str, str]:
        """Split a ``group.token`` string into its components.

        This helper only separates on the first dot, allowing tokens to
        contain underscores, numbers or any other characters (e.g.
        ``"colors.warning_500"``).

        Parameters
        ----------
        name:
            Token identifier in ``"group.token"`` format.

        Returns
        -------
        tuple[str, str]
            The ``(group, token)`` pair.

        Raises
        ------
        ValueError
            If ``name`` does not contain a dot separator.
        """

        group, sep, token = name.partition(".")
        if not sep:
            raise ValueError("Token name must be in 'group.token' format")
        return group, token

    # ------------------------------------------------------------------
    def set_token(self, name: str, value: object) -> None:
        """Set a token value and update the theme.

        Parameters
        ----------
        name:
            Name of the token using ``"group.token"`` notation, e.g.
            ``"colors.primary"`` or ``"radii.default"``. Token names may
            contain underscores or numbers such as ``"colors.warning_500"``
            or ``"colors.success_200"``.
        value:
            New value for the token.
        """
        group, token = self._split_name(name)
        self.tokens.setdefault(group, {})[token] = value
        self._persistent_overrides.setdefault(group, {})[token] = value
        self._emit_overrides_snapshot()
        self.apply_theme()

    # ------------------------------------------------------------------
    def get_token(self, name: str) -> object | None:
        """Retrieve a token value.

        Parameters
        ----------
        name:
            Token identifier in ``"group.token"`` format. Token names may
            include underscores or numbers, e.g. ``"colors.info_100"`` or
            ``"colors.error_900"``.

        Returns
        -------
        The token value if present, otherwise ``None``.
        """
        group, token = self._split_name(name)
        return self._effective_tokens.get(group, {}).get(token)

    # ------------------------------------------------------------------
    def set_primary_color(self, color: str) -> None:
        """Backwards compatible helper to set the primary color."""

        self.set_token("colors.primary", color)

    # ------------------------------------------------------------------
    def get_color(self, token: str, default: object | None = None) -> object | None:
        """Recupera un color almacenado en ``tokens.colors``."""

        return self._effective_tokens.get("colors", {}).get(token, default)

    # ------------------------------------------------------------------
    def get_gradient(self, token: str) -> object | None:
        """Devuelve un gradiente preparado para usarse en contenedores."""

        return self._effective_tokens.get("gradients", {}).get(token)

    # ------------------------------------------------------------------
    def list_available_palettes(self) -> list[tuple[str, str]]:
        """Lista las paletas disponibles junto a su descripción."""

        return list(list_palettes())

    # ------------------------------------------------------------------
    def _apply_current_palette_variant(self) -> None:
        if not self._palette_definition:
            return

        mode = "dark" if self.dark_mode else "light"
        variant = self._palette_definition.get(mode)
        if not isinstance(variant, Mapping):
            # Intentar modo alternativo si no existe la variante
            fallback = "light" if mode == "dark" else "dark"
            variant = self._palette_definition.get(fallback)
            if not isinstance(variant, Mapping):
                return

        self._merge_palette_tokens(variant)
        self._refresh_effective_tokens(
            self._active_device, self._active_orientation, self._active_width
        )
        self._emit_tokens_snapshot()

    # ------------------------------------------------------------------
    def _merge_palette_tokens(self, palette_tokens: Mapping[str, object]) -> None:
        for group, values in palette_tokens.items():
            if group == "description":
                continue
            if group == "gradients" and isinstance(values, Mapping):
                gradients = self.tokens.setdefault("gradients", {})
                for name, definition in values.items():
                    gradients[name] = self._build_gradient(definition)
                continue

            if isinstance(values, Mapping):
                target = self.tokens.setdefault(group, {})
                target.update(values)

        self._refresh_effective_tokens(
            self._active_device, self._active_orientation, self._active_width
        )
        self._emit_tokens_snapshot()

    # ------------------------------------------------------------------
    def _refresh_effective_tokens(
        self,
        device: str | None,
        orientation: str | None,
        width: int | None,
    ) -> None:
        device_overrides = self._resolve_device_overrides(device)
        orientation_overrides = self._resolve_orientation_overrides(orientation)
        breakpoint_overrides = self._resolve_breakpoint_overrides(width)

        self._effective_tokens = merge_token_layers(
            self.tokens,
            [
                device_overrides,
                orientation_overrides,
                breakpoint_overrides,
                self._persistent_overrides,
            ],
        )

    # ------------------------------------------------------------------
    def _apply_preset_definition(
        self,
        definition: Mapping[str, Mapping[str, object]],
        *,
        preset_name: str | None,
        mode: str | None,
        refresh: bool,
    ) -> None:
        sanitized: dict[str, dict[str, dict[str, object]]] = {}
        for variant, values in definition.items():
            if not isinstance(values, Mapping):
                continue
            variant_tokens: dict[str, dict[str, object]] = {}
            for group, group_values in values.items():
                if isinstance(group_values, Mapping):
                    variant_tokens[group] = {k: v for k, v in group_values.items()}
            if variant_tokens:
                sanitized[variant] = variant_tokens

        if mode in {"light", "dark"}:
            if self._follow_platform_theme:
                self.set_follow_platform_theme(False, apply_current=False)
            self.dark_mode = mode == "dark"

        self._palette_definition = sanitized
        self._palette_name = None
        self._preset_name = preset_name.lower() if preset_name else None
        self._apply_current_palette_variant()

        if refresh:
            self.apply_theme()

        self.mode_signal.set(self.dark_mode)

    def load_token_overrides(
        self,
        overrides: Mapping[str, Mapping[str, object]] | None,
        *,
        refresh: bool = True,
    ) -> None:
        """Carga y aplica tokens personalizados persistentes."""

        if not overrides:
            return

        updated = False
        for group, values in overrides.items():
            if not isinstance(values, Mapping):
                continue
            target = self.tokens.setdefault(group, {})
            persisted_group = self._persistent_overrides.setdefault(group, {})
            for token, value in values.items():
                target[token] = value
                persisted_group[token] = value
                updated = True

        if not updated:
            return

        if refresh:
            self.apply_theme()
        else:
            self._refresh_effective_tokens(
                self._active_device, self._active_orientation, self._active_width
            )
            self._emit_tokens_snapshot()
        self._emit_overrides_snapshot()

    # ------------------------------------------------------------------
    def _install_platform_theme_listeners(self) -> None:
        if self._platform_theme_unsubscribers:
            return

        for event_name in (
            "on_platform_brightness_change",
            "on_platform_theme_change",
        ):
            unsubscribe = self._attach_page_event_handler(
                event_name, self._handle_platform_theme_event
            )
            if unsubscribe:
                self._platform_theme_unsubscribers.append(unsubscribe)

        # Si no se pudo enlazar a ningún evento, sincronizar igualmente
        if not self._platform_theme_unsubscribers:
            self._sync_with_platform_preference(refresh=False)

    # ------------------------------------------------------------------
    def _dispose_platform_theme_listeners(self) -> None:
        while self._platform_theme_unsubscribers:
            unsubscribe = self._platform_theme_unsubscribers.pop()
            try:
                unsubscribe()
            except Exception:  # pragma: no cover - limpieza defensiva
                logger.exception("Error al cancelar escucha de brillo del sistema")

    # ------------------------------------------------------------------
    def _sync_with_platform_preference(self, *, refresh: bool = True) -> None:
        preference = self._read_platform_preference()
        if preference is None:
            return
        self.set_dark_mode(preference, refresh=refresh)

    # ------------------------------------------------------------------
    def _handle_platform_theme_event(self, event) -> None:
        if not self._follow_platform_theme:
            return

        preference = self._extract_preference_from_event(event)
        if preference is None:
            preference = self._read_platform_preference()
        if preference is None:
            return
        self.set_dark_mode(preference)

    # ------------------------------------------------------------------
    def _read_platform_preference(self) -> bool | None:
        brightness = getattr(self.page, "platform_brightness", None)
        preference = self._normalize_mode_value(brightness)
        if preference is not None:
            return preference
        theme_value = getattr(self.page, "platform_theme", None)
        return self._normalize_mode_value(theme_value)

    # ------------------------------------------------------------------
    def _extract_preference_from_event(self, event) -> bool | None:
        if event is None:
            return None

        candidate = None
        if isinstance(event, Mapping):
            for key in ("brightness", "theme", "value", "data"):
                if key in event and event[key] is not None:
                    candidate = event[key]
                    break
        else:
            for attr in ("brightness", "theme", "value", "data"):
                if hasattr(event, attr):
                    candidate = getattr(event, attr)
                    if candidate is not None:
                        break
            if candidate is None and isinstance(event, str):
                candidate = event

        return self._normalize_mode_value(candidate)

    # ------------------------------------------------------------------
    def _normalize_mode_value(self, value) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value
        else:
            for attr in ("value", "name"):
                attr_value = getattr(value, attr, None)
                if isinstance(attr_value, str):
                    normalized = attr_value
                    break
            else:
                normalized = str(value)

        lowered = normalized.strip().lower()
        if not lowered:
            return None
        if "dark" in lowered:
            return True
        if "light" in lowered:
            return False
        return None

    # ------------------------------------------------------------------
    def _attach_page_event_handler(
        self, event_name: str, callback: Callable[[object], None]
    ) -> Callable[[], None] | None:
        handler = getattr(self.page, event_name, None)

        if hasattr(handler, "subscribe") and callable(handler.subscribe):
            try:
                return handler.subscribe(callback)
            except Exception:  # pragma: no cover - defensivo
                logger.exception(
                    "No se pudo suscribir al evento %s mediante 'subscribe'",
                    event_name,
                )
                return None

        original = handler if callable(handler) else None

        def combined(event):
            if original:
                try:
                    original(event)
                except Exception:  # pragma: no cover - evitar romper callbacks ajenos
                    logger.exception(
                        "Error en el manejador original de %s", event_name
                    )
            callback(event)

        try:
            setattr(self.page, event_name, combined)
        except Exception:  # pragma: no cover - páginas no mutables
            logger.exception(
                "No se pudo asignar el manejador combinado para %s", event_name
            )
            return None

        def restore() -> None:
            try:
                setattr(self.page, event_name, original)
            except Exception:  # pragma: no cover - tolerante a fallos
                logger.exception(
                    "No se pudo restaurar el manejador original de %s", event_name
                )

        return restore

    # ------------------------------------------------------------------
    def get_token_overrides(self) -> dict[str, dict[str, object]]:
        """Devuelve una copia de los tokens personalizados persistentes."""

        return {
            group: dict(values) for group, values in self._persistent_overrides.items()
        }

    # ------------------------------------------------------------------
    def _emit_tokens_snapshot(self) -> None:
        snapshot = deepcopy(self._effective_tokens)
        self.tokens_signal.set(snapshot)

    # ------------------------------------------------------------------
    def _emit_overrides_snapshot(self) -> None:
        overrides = self.get_token_overrides()
        self.overrides_signal.set(overrides)

    # ------------------------------------------------------------------
    def _resolve_device_overrides(
        self, device: str | None
    ) -> dict[str, dict[str, object]]:
        if not device:
            return {}
        overrides = self._device_tokens.get(device.lower())
        if not overrides:
            return {}
        return {group: dict(values) for group, values in overrides.items()}

    # ------------------------------------------------------------------
    def _resolve_orientation_overrides(
        self, orientation: str | None
    ) -> dict[str, dict[str, object]]:
        if not orientation:
            return {}
        overrides = self._orientation_tokens.get(orientation.lower())
        if not overrides:
            return {}
        return {group: dict(values) for group, values in overrides.items()}

    # ------------------------------------------------------------------
    def _resolve_breakpoint_overrides(
        self, width: int | None
    ) -> dict[str, dict[str, object]]:
        if width is None or not self._breakpoint_tokens:
            self._active_breakpoint = None
            return {}

        active_bp: int | None = None
        for bp in sorted(self._breakpoint_tokens):
            if width >= bp:
                active_bp = bp
        self._active_breakpoint = active_bp
        if active_bp is None:
            return {}

        overrides = self._breakpoint_tokens.get(active_bp)
        if not overrides:
            return {}
        return {group: dict(values) for group, values in overrides.items()}

    # ------------------------------------------------------------------
    @staticmethod
    def _build_gradient(definition: object) -> object:
        if isinstance(definition, ft.Gradient):
            return definition
        if not isinstance(definition, Mapping):
            return definition

        colors = list(definition.get("colors", []))
        begin = ThemeManager._as_alignment(definition.get("begin"))
        end = ThemeManager._as_alignment(definition.get("end"))
        return ft.LinearGradient(colors=colors, begin=begin, end=end)

    # ------------------------------------------------------------------
    @staticmethod
    def _as_alignment(value: object) -> ft.Alignment:
        if isinstance(value, ft.Alignment):
            return value
        if isinstance(value, (tuple, list)) and len(value) == 2:
            try:
                return ft.alignment.Alignment(float(value[0]), float(value[1]))
            except (TypeError, ValueError):
                pass
        return ft.alignment.center

    # ------------------------------------------------------------------
    def _apply_preset(
        self,
        preset_name: str,
        *,
        mode: str | None = None,
        refresh: bool = True,
    ) -> None:
        normalized = preset_name.lower()
        if not has_preset(normalized):
            raise ValueError(f"Preset '{preset_name}' is not registered")

        definition = get_preset_definition(normalized)
        self._apply_preset_definition(
            definition,
            preset_name=normalized,
            mode=mode,
            refresh=refresh,
        )

    # ------------------------------------------------------------------
    def apply_material3(
        self,
        *,
        mode: str | None = None,
        refresh: bool = True,
    ) -> None:
        """Fusiona el preset Material Design 3 con los tokens actuales."""

        self._apply_preset("material3", mode=mode, refresh=refresh)

    # ------------------------------------------------------------------
    def apply_fluent(
        self,
        *,
        mode: str | None = None,
        refresh: bool = True,
    ) -> None:
        """Fusiona el preset Fluent Design System con los tokens actuales."""

        self._apply_preset("fluent", mode=mode, refresh=refresh)

    # ------------------------------------------------------------------
    def apply_cupertino(
        self,
        *,
        mode: str | None = None,
        refresh: bool = True,
    ) -> None:
        """Fusiona el preset inspirado en Cupertino con los tokens actuales."""

        self._apply_preset("cupertino", mode=mode, refresh=refresh)

    # ------------------------------------------------------------------
    def load_theme_from_json(
        self,
        file_path: str,
        *,
        refresh: bool = True,
    ) -> None:
        """Carga un tema completo desde un JSON y lo aplica al ``ThemeManager``.

        El archivo debe contener un objeto JSON con la siguiente estructura
        orientativa::

            {
                "preset": "material3",
                "mode": "light",
                "tokens": {"spacing": {"md": 20}},
                "light": {"colors": {"primary": "#6750A4"}},
                "dark": {"colors": {"primary": "#D0BCFF"}}
            }

        Los valores bajo ``"tokens"`` se aplican tanto al modo claro como al
        oscuro, mientras que ``"light"`` y ``"dark"`` permiten ajustar cada
        variante de manera independiente. El campo ``"preset"`` determina el
        preset base que se fusionará antes de los overrides.
        """

        payload = _parse_theme_json(file_path)
        if not payload:
            return

        variants = payload.get("variants")
        if not isinstance(variants, Mapping):
            return

        preset_name = payload.get("preset")
        preset_value = preset_name if isinstance(preset_name, str) else None
        mode_value = payload.get("mode")
        mode_str = mode_value if isinstance(mode_value, str) else None

        self._apply_preset_definition(
            variants,
            preset_name=preset_value,
            mode=mode_str,
            refresh=refresh,
        )


def load_theme_from_json(file_path: str) -> dict[str, object]:
    """Carga un archivo JSON y devuelve la definición de tema normalizada."""

    return _parse_theme_json(file_path)
