"""Pruebas para la fusión de capas de tokens en Rust y Python."""

from __future__ import annotations

from fletplus.state import Signal
from fletplus.themes.theme_manager import ThemeManager
from fletplus.themes.token_merge_rs import merge_token_layers


def _reference_merge(base, layers):
    merged = {group: dict(values) for group, values in base.items()}
    for layer in layers:
        for group, values in layer.items():
            target = merged.setdefault(group, {})
            target.update(values)
    return merged


def test_merge_token_layers_matches_previous_logic():
    base = {
        "colors": {"primary": "red", "secondary": "blue"},
        "spacing": {"xs": 2},
    }
    layers = [
        {"colors": {"primary": "green", "accent": "yellow"}},
        {"spacing": {"xs": 4, "md": 12}},
        {"shadows": {"soft": 2}},
        {"colors": {"secondary": "orange"}},
    ]

    expected = _reference_merge(base, layers)
    result = merge_token_layers(base, layers)

    assert result == expected
    assert base["colors"]["primary"] == "red"
    assert "shadows" not in base


class _MergeHarness(ThemeManager):
    def __init__(
        self,
        tokens,
        device_overrides,
        orientation_overrides,
        breakpoint_overrides,
        persistent_overrides,
    ) -> None:
        # No invocamos a ThemeManager.__init__ para aislar la fusión
        self.tokens = tokens
        self._persistent_overrides = persistent_overrides
        self._device_overrides = device_overrides
        self._orientation_overrides = orientation_overrides
        self._breakpoint_overrides = breakpoint_overrides
        self._effective_tokens = {}
        self.overrides_signal = Signal(dict)
        self.tokens_signal = Signal(dict)

    def _resolve_device_overrides(self, _device):
        return {group: dict(values) for group, values in self._device_overrides.items()}

    def _resolve_orientation_overrides(self, _orientation):
        return {
            group: dict(values) for group, values in self._orientation_overrides.items()
        }

    def _resolve_breakpoint_overrides(self, _width):
        return {
            group: dict(values) for group, values in self._breakpoint_overrides.items()
        }


def test_refresh_effective_tokens_uses_merge_layers():
    base = {
        "colors": {"primary": "red", "secondary": "blue"},
        "spacing": {"xs": 2},
    }
    device_overrides = {"colors": {"primary": "green", "accent": "yellow"}}
    orientation_overrides = {"spacing": {"xs": 4, "md": 12}}
    breakpoint_overrides = {"shadows": {"soft": 2}}
    persistent_overrides = {"colors": {"secondary": "orange"}}

    harness = _MergeHarness(
        base,
        device_overrides,
        orientation_overrides,
        breakpoint_overrides,
        persistent_overrides,
    )

    harness._refresh_effective_tokens("desktop", "portrait", 1024)

    expected = _reference_merge(
        base,
        [
            device_overrides,
            orientation_overrides,
            breakpoint_overrides,
            persistent_overrides,
        ],
    )
    assert harness._effective_tokens == expected
