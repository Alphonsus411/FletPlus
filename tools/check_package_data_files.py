#!/usr/bin/env python3
"""Valida que `tool.setuptools.package-data` no tenga referencias huérfanas."""

from __future__ import annotations

import glob
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _load_package_data() -> dict[str, list[str]]:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    tool = pyproject.get("tool", {})
    setuptools = tool.get("setuptools", {})
    package_data = setuptools.get("package-data", {})
    return {
        package: [str(pattern) for pattern in patterns]
        for package, patterns in package_data.items()
    }


def _resolve_matches(package_dir: Path, pattern: str) -> list[Path]:
    expression = str(package_dir / pattern)
    return [
        Path(path)
        for path in glob.glob(expression, recursive=True)
        if Path(path).is_file()
    ]


def main() -> int:
    missing_entries: list[tuple[str, str, str]] = []

    for package, patterns in sorted(_load_package_data().items()):
        package_dir = REPO_ROOT / package.replace(".", "/")
        if not package_dir.is_dir():
            missing_entries.append((package, "<package>", str(package_dir.relative_to(REPO_ROOT))))
            continue

        for pattern in patterns:
            matches = _resolve_matches(package_dir, pattern)
            if not matches:
                missing_entries.append((package, pattern, str((package_dir / pattern).relative_to(REPO_ROOT))))

    if missing_entries:
        print("Se encontraron referencias huérfanas en [tool.setuptools.package-data]:")
        for package, pattern, resolved in missing_entries:
            print(f"- {package}: {pattern} -> {resolved}")
        print("\nCorrige el patrón o agrega los archivos referenciados.")
        return 1

    print("OK: todas las entradas de package-data apuntan a archivos existentes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
