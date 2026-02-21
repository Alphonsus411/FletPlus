#!/usr/bin/env python3
"""Actualiza baseline/target de matriz Flet en workflow, config y docs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/reusable-quality.yml"
CONFIG_PATH = REPO_ROOT / "tools/flet_version_matrix_config.py"
DOC_PATH = REPO_ROOT / "docs/migration-flet-latest.md"


def _minor_to_upper_bound(minor: str) -> str:
    major_str, minor_str = minor.split(".")
    return f"{major_str}.{int(minor_str) + 1}"


def _replace_once(pattern: str, repl: str, text: str) -> str:
    updated, count = re.subn(pattern, repl, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Patrón no encontrado o ambiguo: {pattern}")
    return updated


def update_workflow(text: str, baseline_minor: str, target_minor: str) -> str:
    baseline_upper = _minor_to_upper_bound(baseline_minor)
    target_upper = _minor_to_upper_bound(target_minor)

    text = _replace_once(
        r'(- label: min-supported\n\s*flet-spec:\s*)flet>=[^\n]+(\n\s*expected-minor:\s*)"[^"]+"',
        rf'\g<1>flet>={baseline_minor},<{baseline_upper}\g<2>"{baseline_minor}"',
        text,
    )
    text = _replace_once(
        r'(- label: latest-migration-target\n\s*flet-spec:\s*)flet>=[^\n]+(\n\s*expected-minor:\s*)"[^"]+"',
        rf'\g<1>flet>={target_minor},<{target_upper}\g<2>"{target_minor}"',
        text,
    )
    return text


def update_config(text: str, baseline_minor: str, target_minor: str) -> str:
    return _replace_once(
        r'FLET_MATRIX_MINORS: tuple\[str, \.\.\.\] = \("[^"]+", "[^"]+"\)',
        f'FLET_MATRIX_MINORS: tuple[str, ...] = ("{baseline_minor}", "{target_minor}")',
        text,
    )


def _replace_first_matching(patterns: tuple[str, ...], repl: str, text: str) -> str:
    for pattern in patterns:
        updated, count = re.subn(pattern, repl, text, count=1, flags=re.MULTILINE)
        if count == 1:
            return updated
    raise ValueError(f"Ningún patrón encontrado para reemplazo: {patterns}")


def update_docs(text: str, baseline_minor: str, target_minor: str) -> str:
    baseline_upper = _minor_to_upper_bound(baseline_minor)
    target_upper = _minor_to_upper_bound(target_minor)

    text = _replace_first_matching(
        (
            r"\*\*Versión mínima soportada \(estado actual\)\*\*: `flet>=[^`]+`",
            r"\*\*Baseline de validación \(estado actual en CI\)\*\*: `flet>=[^`]+`",
        ),
        f"**Baseline de validación (estado actual en CI)**: `flet>={baseline_minor},<{baseline_upper}`",
        text,
    )
    text = _replace_first_matching(
        (
            r"\*\*Versión objetivo de migración \(estado objetivo\)\*\*: `flet>=[^`]+`",
            r"\*\*Versión objetivo de migración \(estado objetivo en CI\)\*\*: `flet>=[^`]+`",
        ),
        f"**Versión objetivo de migración (estado objetivo en CI)**: `flet>={target_minor},<{target_upper}`",
        text,
    )

    text = _replace_once(
        r"(\| CI baseline \(`flet-version-matrix`\) \| `flet>=)[^`]+(` \(`min-supported`\) \|)",
        rf"\g<1>{baseline_minor},<{baseline_upper}\g<2>",
        text,
    )
    text = _replace_once(
        r"(\| CI target \(`flet-version-matrix`\) \| `flet>=)[^`]+(` \(`latest-migration-target`\) \|)",
        rf"\g<1>{target_minor},<{target_upper}\g<2>",
        text,
    )
    return text


def write_if_changed(path: Path, content: str) -> bool:
    current = path.read_text(encoding="utf-8")
    if current == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-minor", required=True)
    parser.add_argument("--target-minor", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    baseline_minor = args.baseline_minor.strip()
    target_minor = args.target_minor.strip()

    for name, value in {"baseline": baseline_minor, "target": target_minor}.items():
        if not re.fullmatch(r"\d+\.\d+", value):
            raise ValueError(
                f"Formato inválido para {name}: '{value}'. Usa MAJOR.MINOR."
            )

    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    doc_text = DOC_PATH.read_text(encoding="utf-8")

    new_workflow = update_workflow(workflow_text, baseline_minor, target_minor)
    new_config = update_config(config_text, baseline_minor, target_minor)
    new_doc = update_docs(doc_text, baseline_minor, target_minor)

    if args.check:
        if (
            workflow_text == new_workflow
            and config_text == new_config
            and doc_text == new_doc
        ):
            print("OK: workflow/config/docs ya están sincronizados.")
            return 0
        print("ERROR: workflow/config/docs no están sincronizados.")
        return 1

    changed = 0
    changed += int(write_if_changed(WORKFLOW_PATH, new_workflow))
    changed += int(write_if_changed(CONFIG_PATH, new_config))
    changed += int(write_if_changed(DOC_PATH, new_doc))
    print(
        f"Actualización completada: baseline={baseline_minor} target={target_minor} archivos_modificados={changed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
