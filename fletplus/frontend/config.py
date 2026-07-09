"""Configuración FrontEnd reutilizable para apps FletPlus."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

import flet as ft

from fletplus.themes import (
    ThemeManager,
    get_palette_tokens,
    get_preset_definition,
    get_preset_metadata,
    has_palette,
    has_preset,
)
from fletplus.utils.device_profiles import (
    DEFAULT_DEVICE_PROFILES,
    DeviceProfile,
    columns_for_width,
    get_device_profile,
)
from fletplus.utils.viewport import visual_density_for_page

TypographyStyle = Mapping[str, int | float | str | None]
TypographyScale = Mapping[str, TypographyStyle | Mapping[str, TypographyStyle]]
FontAssets = Mapping[str, str]
FontWeights = Sequence[str | int]
FontStyles = Sequence[str]

_ALLOWED_MODES = {"light", "dark", "system"}
_ALLOWED_DENSITIES = {"compact", "normal", "comfortable", "spacious"}
_ALLOWED_TARGETS = {
    "web",
    "desktop",
    "mobile",
    "app",
    "all",
    "android-apk",
    "android-aab",
    "ios",
}
_NUMERIC_FIELDS = {
    "page_padding",
    "max_content_width",
    "min_content_width",
    "spacing",
}


_TARGET_LAYOUT_PRESETS: dict[str, dict[str, object]] = {
    "web": {
        "page_padding": 32,
        "max_content_width": 1280,
        "spacing": 20,
        "layout_density": "comfortable",
    },
    "desktop": {
        "page_padding": 28,
        "max_content_width": 1180,
        "spacing": 18,
        "layout_density": "comfortable",
    },
    "mobile": {
        "page_padding": 16,
        "max_content_width": 480,
        "spacing": 12,
        "layout_density": "compact",
    },
    "android-apk": {
        "page_padding": 16,
        "max_content_width": 480,
        "spacing": 12,
        "layout_density": "compact",
    },
    "android-aab": {
        "page_padding": 16,
        "max_content_width": 480,
        "spacing": 12,
        "layout_density": "compact",
    },
    "ios": {
        "page_padding": 16,
        "max_content_width": 480,
        "spacing": 12,
        "layout_density": "compact",
    },
}


def _int_from_mapping_value(
    mapping: Mapping[str, object], *keys: str, default: int
) -> int:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                continue
    return default


def _frontend_values_from_registered_preset(
    preset_name: str, *, target: str | None = None, mode: str | None = None
) -> dict[str, Any]:
    """Deriva valores de FrontEndConfig desde un preset visual registrado."""
    normalized_preset = preset_name.lower()
    if not has_preset(normalized_preset):
        return {"preset": preset_name}

    definition = get_preset_definition(normalized_preset)
    metadata = get_preset_metadata(normalized_preset)
    mode_name = "light" if mode in {None, "system"} else mode
    tokens = definition.get(str(mode_name), {}) or definition.get("light", {})
    spacing_tokens = tokens.get("spacing", {})
    typography_tokens = tokens.get("typography", {})
    target_preset = _TARGET_LAYOUT_PRESETS.get((target or "").lower(), {})
    density = str(
        metadata.get("density")
        or tokens.get("meta", {}).get("density")
        or target_preset.get("layout_density")
        or "comfortable"
    )

    values: dict[str, Any] = {
        "preset": normalized_preset,
        "palette": str(
            metadata.get("palette")
            or tokens.get("meta", {}).get("palette")
            or "material"
        ),
        "layout_density": density,
        "theme_tokens": dict(tokens),
        "typography_tokens": dict(typography_tokens)
        if isinstance(typography_tokens, Mapping)
        else {},
        "page_padding": _int_from_mapping_value(
            spacing_tokens if isinstance(spacing_tokens, Mapping) else {},
            "page",
            default=int(target_preset.get("page_padding", 24)),
        ),
        "max_content_width": int(target_preset.get("max_content_width", 1200)),
        "spacing": _int_from_mapping_value(
            spacing_tokens if isinstance(spacing_tokens, Mapping) else {},
            "md",
            "section",
            default=int(target_preset.get("spacing", 16)),
        ),
    }
    font_family = (
        typography_tokens.get("font_family")
        if isinstance(typography_tokens, Mapping)
        else None
    )
    if isinstance(font_family, str) and font_family:
        values["font_family"] = font_family
    return values


@dataclass(frozen=True, slots=True)
class FrontEndTask:
    """Tarea declarativa para adaptar una app FletPlus por plataforma.

    No ejecuta acciones por sí misma: documenta pasos separados que una app,
    plantilla CLI o equipo de frontend puede aplicar de forma ordenada.
    """

    name: str
    target: str
    description: str
    functions: tuple[str, ...] = ()
    tokens: Mapping[str, object] = field(default_factory=dict)


def _ensure_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(
            f"[tool.fletplus.frontend.{field_name}] debe ser una tabla TOML"
        )
    return value


def _validate_positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"tool.fletplus.frontend.{field_name} debe ser un entero positivo"
        )
    if value < 0:
        raise ValueError(f"tool.fletplus.frontend.{field_name} no puede ser negativo")
    return value


def _validate_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"tool.fletplus.frontend.{field_name} debe ser una cadena no vacía"
        )
    return value.strip()


def _validate_string_sequence(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(
            f"tool.fletplus.frontend.{field_name} debe ser una lista de cadenas"
        )
    return tuple(_validate_string(item, f"{field_name}[]") for item in value)


def _normalize_font_weight(value: str | int) -> str:
    if isinstance(value, int):
        return f"w{value}"
    return str(value)


def _validate_font_weights(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"tool.fletplus.frontend.{field_name} debe ser una lista")
    return tuple(_normalize_font_weight(item) for item in value)


@dataclass(slots=True)
class FontDeclaration:
    """Declaración común de fuentes para FrontEndConfig.

    ``family`` es la familia principal, ``fallback_families`` son las familias
    de respaldo para ``Theme.font_family`` y ``assets`` contiene las fuentes
    locales que se registrarán en ``page.fonts``. ``weights`` y ``styles`` son
    metadatos descriptivos para documentar qué variantes están disponibles.
    """

    family: str | None = None
    fallback_families: Sequence[str] = field(default_factory=tuple)
    assets: FontAssets = field(default_factory=dict)
    weights: FontWeights = field(default_factory=tuple)
    styles: FontStyles = field(default_factory=tuple)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "FontDeclaration":
        return cls(
            family=(
                _validate_string(data["family"], "font.family")
                if data.get("family") is not None
                else None
            ),
            fallback_families=_validate_string_sequence(
                data.get("fallback_families") or data.get("fallbacks"),
                "font.fallback_families",
            ),
            assets=_validate_string_mapping(
                _ensure_mapping(data.get("assets"), "font.assets"), "font.assets"
            ),
            weights=_validate_font_weights(data.get("weights"), "font.weights"),
            styles=_validate_string_sequence(data.get("styles"), "font.styles"),
        )

    def theme_font_family(self, legacy_family: str | None = None) -> str | None:
        family = self.family or legacy_family
        families = [item for item in (family, *self.fallback_families) if item]
        return ", ".join(dict.fromkeys(families)) or None

    def merged_assets(
        self, legacy_assets: Mapping[str, str] | None = None
    ) -> dict[str, str]:
        return {**dict(legacy_assets or {}), **dict(self.assets)}


def _validate_string_mapping(
    value: Mapping[str, Any], field_name: str
) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(
                "Las claves de tool.fletplus.frontend."
                f"{field_name} deben ser cadenas no vacías"
            )
        result[key.strip()] = _validate_string(item, f"{field_name}.{key}")
    return result


DEFAULT_TYPOGRAPHY_TOKENS: dict[str, dict[str, dict[str, int | float | str]]] = {
    "display": {
        "mobile": {"size": 40, "weight": "w700", "line_height": 1.1},
        "tablet": {"size": 48, "weight": "w700", "line_height": 1.08},
        "desktop": {"size": 56, "weight": "w700", "line_height": 1.05},
        "large_desktop": {"size": 64, "weight": "w700", "line_height": 1.03},
    },
    "headline": {
        "mobile": {"size": 28, "weight": "w600", "line_height": 1.18},
        "tablet": {"size": 32, "weight": "w600", "line_height": 1.16},
        "desktop": {"size": 36, "weight": "w600", "line_height": 1.14},
        "large_desktop": {"size": 40, "weight": "w600", "line_height": 1.12},
    },
    "title": {
        "mobile": {"size": 20, "weight": "w600", "line_height": 1.28},
        "tablet": {"size": 22, "weight": "w600", "line_height": 1.25},
        "desktop": {"size": 24, "weight": "w600", "line_height": 1.22},
        "large_desktop": {"size": 28, "weight": "w600", "line_height": 1.18},
    },
    "body": {
        "mobile": {"size": 14, "weight": "w400", "line_height": 1.55},
        "tablet": {"size": 16, "weight": "w400", "line_height": 1.55},
        "desktop": {"size": 18, "weight": "w400", "line_height": 1.5},
        "large_desktop": {"size": 20, "weight": "w400", "line_height": 1.45},
    },
    "label": {
        "mobile": {"size": 12, "weight": "w600", "line_height": 1.35},
        "tablet": {"size": 13, "weight": "w600", "line_height": 1.35},
        "desktop": {"size": 14, "weight": "w600", "line_height": 1.3},
        "large_desktop": {"size": 15, "weight": "w600", "line_height": 1.28},
    },
    "caption": {
        "mobile": {"size": 11, "weight": "w400", "line_height": 1.35},
        "tablet": {"size": 12, "weight": "w400", "line_height": 1.35},
        "desktop": {"size": 13, "weight": "w400", "line_height": 1.32},
        "large_desktop": {"size": 14, "weight": "w400", "line_height": 1.3},
    },
}

_DEVICE_ALIASES = {
    "movil": "mobile",
    "móvil": "mobile",
    "mobile": "mobile",
    "tablet": "tablet",
    "escritorio": "desktop",
    "desktop": "desktop",
    "pantalla_amplia": "large_desktop",
    "wide": "large_desktop",
    "wide_screen": "large_desktop",
    "large_desktop": "large_desktop",
}


def _normalize_device_name(name: str) -> str:
    return _DEVICE_ALIASES.get(name, name)


def _merge_typography_tokens(
    base: Mapping[str, Mapping[str, Mapping[str, int | float | str]]],
    overrides: TypographyScale,
) -> dict[str, dict[str, dict[str, int | float | str | None]]]:
    merged = {
        role: {device: dict(values) for device, values in variants.items()}
        for role, variants in base.items()
    }
    for role, role_values in overrides.items():
        if not isinstance(role_values, Mapping):
            continue
        target = merged.setdefault(role, {})
        if any(key in role_values for key in ("size", "weight", "line_height")):
            target.setdefault("mobile", {}).update(role_values)  # type: ignore[arg-type]
            continue
        for device, values in role_values.items():
            if isinstance(values, Mapping):
                target.setdefault(_normalize_device_name(str(device)), {}).update(
                    values
                )
    return merged


@dataclass(slots=True)
class FrontEndConfig:
    """Agrupa decisiones visuales habituales para una aplicación FletPlus."""

    palette: str = "material"
    mode: str = "light"
    font_family: str | None = None
    font_assets: Mapping[str, str] = field(default_factory=dict)
    font: FontDeclaration = field(default_factory=FontDeclaration)
    font_assets_base_path: Path | None = None
    page_padding: int = 24
    max_content_width: int = 1200
    min_content_width: int = 320
    allow_min_width_overflow: bool = False
    spacing: int = 16
    responsive_profiles: Sequence[DeviceProfile] = DEFAULT_DEVICE_PROFILES
    layout_density: str = "comfortable"
    preset: str | None = None
    theme_tokens: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    typography_tokens: TypographyScale = field(default_factory=dict)
    follow_platform_theme: bool = False
    target: str | None = None
    platform_palettes: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    screen_tokens: Mapping[str, Mapping[str, int | float | str | bool | None]] = field(
        default_factory=dict
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "FrontEndConfig":
        allowed = {
            "palette",
            "mode",
            "font_family",
            "font_assets",
            "fonts",
            "font",
            "page_padding",
            "max_content_width",
            "min_content_width",
            "allow_min_width_overflow",
            "spacing",
            "layout_density",
            "preset",
            "theme_tokens",
            "typography_tokens",
            "tokens",
            "follow_platform_theme",
            "target",
            "platform_palettes",
            "screen_tokens",
        }
        normalized: dict[str, Any] = {}
        for key, value in data.items():
            if key not in allowed:
                continue
            if key in _NUMERIC_FIELDS:
                normalized[key] = _validate_positive_int(value, key)
            elif key in {
                "palette",
                "mode",
                "font_family",
                "layout_density",
                "preset",
                "target",
            }:
                normalized[key] = _validate_string(value, key)
            elif key == "allow_min_width_overflow" or key == "follow_platform_theme":
                if not isinstance(value, bool):
                    raise ValueError(f"tool.fletplus.frontend.{key} debe ser booleano")
                normalized[key] = value
            elif key == "font_assets":
                normalized[key] = _validate_string_mapping(
                    _ensure_mapping(value, key), key
                )
            elif key == "fonts":
                fonts = _validate_string_mapping(_ensure_mapping(value, key), key)
                normalized["font_assets"] = {
                    **fonts,
                    **dict(normalized.get("font_assets", {})),
                }
            elif key == "font":
                normalized["font"] = FontDeclaration.from_mapping(
                    _ensure_mapping(value, key)
                )
            elif key == "tokens":
                tokens = _ensure_mapping(value, key)
                normalized["theme_tokens"] = {
                    **dict(normalized.get("theme_tokens", {})),
                    **dict(tokens),
                }
            elif key in {
                "theme_tokens",
                "typography_tokens",
                "platform_palettes",
                "screen_tokens",
            }:
                normalized[key] = _ensure_mapping(value, key)

        if isinstance(normalized.get("preset"), str):
            preset_defaults = _frontend_values_from_registered_preset(
                normalized["preset"],
                target=normalized.get("target"),
                mode=normalized.get("mode"),
            )
            normalized = {**preset_defaults, **normalized}

        mode = normalized.get("mode")
        if mode is not None and mode not in _ALLOWED_MODES:
            raise ValueError(
                "tool.fletplus.frontend.mode debe ser 'light', 'dark' o 'system'"
            )
        density = normalized.get("layout_density")
        if density is not None and density not in _ALLOWED_DENSITIES:
            raise ValueError(
                "tool.fletplus.frontend.layout_density debe ser uno de "
                f"{sorted(_ALLOWED_DENSITIES)}"
            )
        target = normalized.get("target")
        if target is not None and target not in _ALLOWED_TARGETS:
            raise ValueError(
                "tool.fletplus.frontend.target debe ser uno de "
                f"{sorted(_ALLOWED_TARGETS)}"
            )
        if (
            "min_content_width" in normalized
            and "max_content_width" in normalized
            and normalized["min_content_width"] > normalized["max_content_width"]
        ):
            raise ValueError(
                "tool.fletplus.frontend.min_content_width no puede superar "
                "max_content_width"
            )
        return cls(**normalized)

    @classmethod
    def from_pyproject(cls, path: str | Path = "pyproject.toml") -> "FrontEndConfig":
        pyproject_path = Path(path)
        if not pyproject_path.exists():
            return cls()
        try:
            import tomllib
        except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
            import tomli as tomllib  # type: ignore
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        tool_data = data.get("tool", {}) if isinstance(data, dict) else {}
        fletplus_data = (
            tool_data.get("fletplus", {}) if isinstance(tool_data, dict) else {}
        )
        frontend_data = (
            fletplus_data.get("frontend", {}) if isinstance(fletplus_data, dict) else {}
        )
        if not isinstance(frontend_data, Mapping):
            return cls()
        config = cls.from_mapping(frontend_data)
        config.font_assets_base_path = pyproject_path.parent
        return config

    def preset_for_target(self, target: str | None = None) -> dict[str, object]:
        """Devuelve ajustes base para web, escritorio o móvil sin mutar la config."""
        target_name = (target or self.target or "all").lower()
        if target_name in {"app", "all"}:
            return {}
        return dict(_TARGET_LAYOUT_PRESETS.get(target_name, {}))

    def configured_for_target(self, target: str | None = None) -> "FrontEndConfig":
        """Crea una copia con estructura visual sugerida para la plataforma."""
        preset = self.preset_for_target(target)
        if not preset:
            return self
        values = {
            "palette": self.palette,
            "mode": self.mode,
            "font_family": self.font_family,
            "font_assets": self.font_assets,
            "font": self.font,
            "font_assets_base_path": self.font_assets_base_path,
            "page_padding": preset.get("page_padding", self.page_padding),
            "max_content_width": preset.get(
                "max_content_width", self.max_content_width
            ),
            "min_content_width": self.min_content_width,
            "allow_min_width_overflow": self.allow_min_width_overflow,
            "spacing": preset.get("spacing", self.spacing),
            "responsive_profiles": self.responsive_profiles,
            "layout_density": preset.get("layout_density", self.layout_density),
            "preset": self.preset,
            "theme_tokens": self.theme_tokens,
            "typography_tokens": self.typography_tokens,
            "follow_platform_theme": self.follow_platform_theme,
            "target": target or self.target,
            "platform_palettes": self.platform_palettes,
            "screen_tokens": self.screen_tokens,
        }
        return FrontEndConfig(**values)

    def palette_for_target(self, target: str | None = None) -> dict[str, str]:
        """Fusiona colores base de la paleta activa con overrides de plataforma."""
        palette_tokens = self.palette_tokens()
        base_colors = palette_tokens.get("colors", {})
        palette = {
            str(k): str(v) for k, v in base_colors.items() if isinstance(v, str)
        }
        target_name = (target or self.target or "").lower()
        overrides = self.platform_palettes.get(target_name, {})
        if isinstance(overrides, Mapping):
            palette.update({str(k): str(v) for k, v in overrides.items()})
        return palette

    def screen_tokens_for_page(self, page: ft.Page) -> dict[str, object]:
        """Resuelve tokens de pantalla según perfil, orientación y densidad visual."""
        profile = self.resolve_device_profile(
            int(getattr(page, "width", 0) or self.max_content_width)
        )
        device_name = _normalize_device_name(profile.name)
        tokens: dict[str, object] = {
            "target": self.target or "all",
            "device": device_name,
            "orientation": self.orientation_for_page(page),
            "columns": profile.columns,
            "page_padding": self.page_padding,
            "spacing": self.spacing,
            "content_width": self.content_width_for_page(page),
            "density": visual_density_for_page(page, profiles=self.responsive_profiles),
        }
        for key in ("all", device_name, tokens["orientation"]):
            values = self.screen_tokens.get(str(key), {})
            if isinstance(values, Mapping):
                tokens.update(values)
        return tokens

    def implementation_tasks(
        self, target: str | None = None
    ) -> tuple[FrontEndTask, ...]:
        """Lista tareas separadas para adaptar frontend sin reemplazar código existente."""
        target_name = (target or self.target or "all").lower()
        return (
            FrontEndTask(
                "paleta",
                target_name,
                "Resolver paletas base y overrides por plataforma.",
                ("palette_for_target", "palette_tokens"),
                {"palette": self.palette},
            ),
            FrontEndTask(
                "pantalla",
                target_name,
                "Calcular perfil, orientación, columnas, padding y ancho útil.",
                (
                    "screen_tokens_for_page",
                    "content_width_for_page",
                    "resolve_device_profile",
                ),
                self.preset_for_target(target_name),
            ),
            FrontEndTask(
                "diseño",
                target_name,
                "Aplicar densidad, spacing y contenedores adaptativos existentes.",
                ("configured_for_target", "build_content_shell"),
                {
                    "layout_density": self.configured_for_target(
                        target_name
                    ).layout_density
                },
            ),
            FrontEndTask(
                "fuentes",
                target_name,
                "Registrar fuentes locales/remotas y escala tipográfica responsive.",
                ("apply_to_page", "text_style", "resolved_typography_tokens"),
                {"font_family": self.font.theme_font_family(self.font_family)},
            ),
        )

    def palette_tokens(self) -> dict[str, object]:
        if has_palette(self.palette):
            return dict(
                get_palette_tokens(
                    self.palette, "light" if self.mode == "system" else self.mode
                )
            )
        return {}

    def resolved_typography_tokens(
        self,
    ) -> dict[str, dict[str, dict[str, int | float | str | None]]]:
        """Devuelve la escala tipográfica base fusionada con overrides."""
        return _merge_typography_tokens(
            DEFAULT_TYPOGRAPHY_TOKENS, self.typography_tokens
        )

    def resolve_device_profile(self, width: int) -> DeviceProfile:
        return get_device_profile(width, self.responsive_profiles)

    def columns_for_width(self, width: int) -> int:
        return columns_for_width(width, self.responsive_profiles)

    def resolve_typography(
        self, role: str, width: int
    ) -> dict[str, int | float | str | None]:
        """Resuelve tamaño, peso y altura de línea de un rol para un ancho."""
        tokens = self.resolved_typography_tokens()
        role_tokens = tokens.get(role) or tokens["body"]
        device = _normalize_device_name(self.resolve_device_profile(width).name)
        if width >= 1440 and "large_desktop" in role_tokens:
            device = "large_desktop"
        selected = (
            role_tokens.get(device)
            or role_tokens.get("desktop")
            or role_tokens.get("mobile")
            or {}
        )
        return dict(selected)

    def typography_size(self, role: str, width: int) -> int | float | None:
        return self.resolve_typography(role, width).get("size")  # type: ignore[return-value]

    def typography_weight(self, role: str, width: int) -> str | None:
        value = self.resolve_typography(role, width).get("weight")
        return str(value) if value is not None else None

    def typography_line_height(self, role: str, width: int) -> int | float | None:
        return self.resolve_typography(role, width).get("line_height")  # type: ignore[return-value]

    def text_style(self, role: str, width: int) -> ft.TextStyle:
        """Construye un ``ft.TextStyle`` para el rol y ancho indicados."""
        values = self.resolve_typography(role, width)
        return ft.TextStyle(
            size=values.get("size"),
            weight=values.get("weight"),
            height=values.get("line_height"),
        )

    def content_width_for_page(self, page: ft.Page) -> int:
        width = int(page.width or self.max_content_width)
        available_width = max(0, width - (self.page_padding * 2))
        content_width = min(available_width, self.max_content_width)
        if self.allow_min_width_overflow:
            return max(self.min_content_width, content_width)
        return content_width

    def apply_to_page(self, page: ft.Page) -> ThemeManager:
        font_assets = self.font.merged_assets(self.font_assets)
        if font_assets:
            self._warn_missing_font_assets(font_assets)
            page.fonts = {**getattr(page, "fonts", {}), **font_assets}
        theme_font_family = self.font.theme_font_family(self.font_family)
        if theme_font_family:
            theme = page.theme or ft.Theme()
            try:
                theme.font_family = theme_font_family
            except AttributeError:
                theme = ft.Theme(font_family=theme_font_family)
            page.theme = theme
        theme = page.theme or ft.Theme()
        try:
            if getattr(theme, "visual_density", None) is None:
                theme.visual_density = self.layout_density
        except AttributeError:
            pass
        page.theme = theme
        page.padding = self.page_padding
        theme_manager = ThemeManager(
            page,
            palette=self.palette,
            palette_mode="light" if self.mode == "system" else self.mode,
            follow_platform_theme=self.follow_platform_theme or self.mode == "system",
        )
        for group, values in self.theme_tokens.items():
            for key, value in values.items():
                theme_manager.set_token(f"{group}.{key}", value)
        theme_manager.tokens.setdefault("typography", {}).update(
            self.resolved_typography_tokens()
        )
        theme_manager.apply_theme(
            device=self.resolve_device_profile(
                int(getattr(page, "width", 0) or self.max_content_width)
            ).name,
            orientation=self.orientation_for_page(page),
            width=getattr(page, "width", None),
        )
        return theme_manager

    def _warn_missing_font_assets(self, font_assets: Mapping[str, str]) -> None:
        """Emite avisos claros si una fuente local declarada no existe."""
        base_path = self.font_assets_base_path or Path.cwd()
        for family, asset_path in font_assets.items():
            if self._is_remote_font_asset(asset_path):
                continue
            path = Path(asset_path)
            candidates = [path] if path.is_absolute() else [base_path / path, path]
            if not any(candidate.exists() for candidate in candidates):
                warnings.warn(
                    "Fuente local no encontrada para "
                    f"'{family}': '{asset_path}'. Coloca el archivo .ttf/.otf en "
                    "assets/fonts/ o corrige la ruta declarada en FrontEndConfig.",
                    stacklevel=2,
                )

    @staticmethod
    def _is_remote_font_asset(asset_path: str) -> bool:
        parsed = urlparse(asset_path)
        return parsed.scheme in {"http", "https", "data"}

    def orientation_for_page(self, page: ft.Page) -> str:
        width = int(getattr(page, "width", 0) or 0)
        height = int(getattr(page, "height", 0) or 0)
        return "portrait" if height >= width else "landscape"

    def build_content_shell(self, control: ft.Control, page: ft.Page) -> ft.Container:
        return ft.Container(
            content=control,
            width=self.content_width_for_page(page),
            padding=self.page_padding,
            alignment=getattr(getattr(ft, "alignment", object()), "center", None),
        )
