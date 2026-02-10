#!/usr/bin/env python3
"""Valida dependencias críticas antes de ejecutar pytest."""

from __future__ import annotations

import importlib
import sys

REQUIRED_IMPORTS: tuple[str, ...] = ("websockets", "watchdog")


def main() -> int:
    missing: list[str] = []

    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)

    if missing:
        missing_list = ", ".join(missing)
        print(
            "ERROR: faltan dependencias críticas para tests: "
            f"{missing_list}.\n"
            "Instala el entorno de pruebas antes de ejecutar pytest:\n"
            "  python -m pip install -e .[dev,qa,cli]\n"
            "o\n"
            "  python -m pip install -r requirements-dev.txt",
            file=sys.stderr,
        )
        return 1

    print(
        "OK: dependencias críticas disponibles "
        f"({', '.join(REQUIRED_IMPORTS)})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
