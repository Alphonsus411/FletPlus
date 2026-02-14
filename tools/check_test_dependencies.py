#!/usr/bin/env python3
"""Valida dependencias críticas antes de ejecutar pytest."""

from __future__ import annotations

import importlib
from argparse import ArgumentParser
import sys

SUITE_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "default": (),
    "unit": (),
    "cli": ("watchdog",),
    "websocket": ("websockets",),
    "perf": (),
}


def parse_args() -> tuple[str, ...]:
    parser = ArgumentParser(
        description=(
            "Valida dependencias opcionales por suite antes de ejecutar pytest."
        )
    )
    parser.add_argument(
        "--suite",
        dest="suites",
        action="append",
        choices=tuple(SUITE_DEPENDENCIES.keys()),
        default=None,
        help=(
            "Suite(s) para validar. Se puede repetir el flag para combinar "
            "comprobaciones."
        ),
    )
    args = parser.parse_args()
    suites = args.suites or ["default"]
    return tuple(dict.fromkeys(suites))


def resolve_required_imports(suites: tuple[str, ...]) -> tuple[str, ...]:
    required: dict[str, None] = {}
    for suite in suites:
        for module_name in SUITE_DEPENDENCIES[suite]:
            required[module_name] = None
    return tuple(required.keys())


def main() -> int:
    suites = parse_args()
    required_imports = resolve_required_imports(suites)
    missing: list[str] = []

    for module_name in required_imports:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)

    if missing:
        missing_list = ", ".join(missing)
        suite_list = ", ".join(suites)
        print(
            "ERROR: faltan dependencias críticas para tests "
            f"(suite(s): {suite_list}): "
            f"{missing_list}.\n"
            "Instala el entorno de pruebas antes de ejecutar pytest:\n"
            "  python -m pip install -e .[dev,qa,cli]\n"
            "o\n"
            "  python -m pip install -r requirements-dev.txt",
            file=sys.stderr,
        )
        return 1

    if not required_imports:
        print(
            "OK: no hay dependencias opcionales a validar para "
            f"suite(s): {', '.join(suites)}."
        )
        return 0

    print(
        "OK: dependencias críticas disponibles para "
        f"suite(s): {', '.join(suites)} ({', '.join(required_imports)})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
