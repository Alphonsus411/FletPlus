"""Auditoría informativa de contraste WCAG 2.1 sobre las paletas incluidas.

El objetivo es *documentar* qué pares de tokens no alcanzan los umbrales AA.
La prueba no bloquea CI ante pares por debajo del umbral: los registra como
advertencia (deuda conocida) y solo valida que los cálculos sean coherentes.
"""

from __future__ import annotations

import warnings

import pytest

from fletplus.themes.contrast import (
    WCAG_AA_TEXT,
    WCAG_AA_UI,
    contrast_ratio,
    parse_hex_color,
    relative_luminance,
)
from fletplus.themes.palettes import (
    get_palette_definition,
    get_palette_tokens,
    list_palettes,
)

MODES = ("light", "dark")

# Pares (fondo, primer plano) de texto con umbral AA de texto normal.
TEXT_CONTRAST_PAIRS = (
    ("background", "on_background"),
    ("surface", "on_surface"),
    ("surface_variant", "on_surface_variant"),
    ("primary", "on_primary"),
)
# Pares (fondo, primer plano) de componentes de UI y estados interactivos.
UI_CONTRAST_PAIRS = (
    ("surface", "outline"),
    ("surface", "focus_ring"),
    ("surface", "success"),
    ("surface", "error"),
)


def test_contrast_ratio_matches_wcag_reference_values() -> None:
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#336699", "#336699") == pytest.approx(1.0)


def test_relative_luminance_bounds() -> None:
    assert relative_luminance("#000000") == pytest.approx(0.0)
    assert relative_luminance("#FFFFFF") == pytest.approx(1.0)


def test_parse_hex_color_accepts_alpha_and_rejects_invalid() -> None:
    assert parse_hex_color("#0B57D0") == (0x0B, 0x57, 0xD0)
    assert parse_hex_color("#0B57D0FF") == (0x0B, 0x57, 0xD0)
    with pytest.raises(ValueError):
        parse_hex_color("rgb(1, 2, 3)")


def test_palette_contrast_audit_is_reported_without_gating() -> None:
    """Reporta el contraste de cada paleta; los pares bajos no rompen la suite."""
    findings: list[str] = []

    for palette_name, _description in list_palettes():
        definition = get_palette_definition(palette_name) or {}
        for mode in MODES:
            if mode not in definition:
                continue
            colors = get_palette_tokens(palette_name, mode).get("colors", {})
            for threshold, pairs in (
                (WCAG_AA_TEXT, TEXT_CONTRAST_PAIRS),
                (WCAG_AA_UI, UI_CONTRAST_PAIRS),
            ):
                for background, foreground in pairs:
                    if background not in colors or foreground not in colors:
                        continue
                    ratio = contrast_ratio(
                        str(colors[background]), str(colors[foreground])
                    )
                    assert 1.0 <= ratio <= 21.0
                    if ratio < threshold:
                        findings.append(
                            f"{palette_name}/{mode}: {foreground} sobre "
                            f"{background} = {ratio:.2f} (< {threshold:g})"
                        )

    if findings:
        warnings.warn(
            "Contraste AA no alcanzado (deuda registrada en el roadmap, no bloquea CI):\n"
            + "\n".join(findings),
            stacklevel=1,
        )
