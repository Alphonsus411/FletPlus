"""Validate that docs references to optional extras match pyproject definitions."""
from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
DOC_PATHS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "tooling.md",
    REPO_ROOT / "docs" / "building.md",
)
EXTRA_REF_PATTERN = re.compile(
    r"(?:pip\s+install\s+(?:\.|\"?fletplus)\[(?P<extra>[A-Za-z0-9_.-]+)\]\"?)"
)


def _load_defined_extras() -> set[str]:
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    optional = data.get("project", {}).get("optional-dependencies", {})
    return set(optional.keys())


def _find_referenced_extras(content: str) -> set[str]:
    return {match.group("extra") for match in EXTRA_REF_PATTERN.finditer(content)}


def main() -> int:
    defined_extras = _load_defined_extras()
    missing_refs: list[tuple[Path, str]] = []

    for path in DOC_PATHS:
        content = path.read_text(encoding="utf-8")
        for extra in sorted(_find_referenced_extras(content)):
            if extra not in defined_extras:
                missing_refs.append((path, extra))

    if missing_refs:
        print("Se encontraron referencias a extras inexistentes:")
        for path, extra in missing_refs:
            rel = path.relative_to(REPO_ROOT)
            print(f"- {rel}: [{extra}]")
        print("\nDefine esos extras en pyproject.toml o corrige la documentación.")
        return 1

    print("OK: todas las referencias a extras documentadas existen en pyproject.toml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
