#!/usr/bin/env python3
"""Verifica que la URL pública del repositorio sea canónica en metadatos y docs."""

from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]

CANONICAL_REPO_URL = "https://github.com/FletPlus/FletPlus"
CANONICAL_OWNER = "fletplus"
CANONICAL_REPO = "fletplus"

PROJECT_URL_EXPECTED = {
    "Homepage": CANONICAL_REPO_URL,
    "Source": CANONICAL_REPO_URL,
    "Documentation": f"{CANONICAL_REPO_URL}#readme",
}

URL_RE = re.compile(r"https?://[^\s)\]>'\"]+")
GITHUB_REPO_RE = re.compile(r"^https://github\.com/([^/]+)/([^/#?]+)")


def _check_pyproject(pyproject_path: Path) -> list[str]:
    errors: list[str] = []
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project_urls = data.get("project", {}).get("urls", {})
    for key, expected in PROJECT_URL_EXPECTED.items():
        current = project_urls.get(key)
        if current != expected:
            errors.append(
                f"{pyproject_path}:{key} -> esperado '{expected}' pero encontrado '{current}'"
            )
    return errors


def _check_mkdocs(mkdocs_path: Path) -> list[str]:
    errors: list[str] = []
    content = mkdocs_path.read_text(encoding="utf-8")
    social_link_found = False
    inside_extra = False
    inside_social = False

    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("extra:"):
            inside_extra = True
            inside_social = False
            continue

        if inside_extra and re.match(r"^[^\s].*:$", line):
            inside_extra = False
            inside_social = False

        if inside_extra and stripped.startswith("social:"):
            inside_social = True
            continue

        if inside_social and "link:" in stripped:
            social_link_found = True
            link = stripped.split("link:", 1)[1].strip().strip("'\"")
            if link != CANONICAL_REPO_URL:
                errors.append(
                    f"{mkdocs_path}:{lineno} -> extra.social.link no canónico: '{link}'"
                )

    if not social_link_found:
        errors.append(f"{mkdocs_path}: no se encontró extra.social.link")

    return errors


def _check_markdown(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        content = path.read_text(encoding="utf-8")
        for match in URL_RE.finditer(content):
            url = match.group(0).rstrip(".,")
            gh_match = GITHUB_REPO_RE.match(url)
            if not gh_match:
                continue

            owner, repo = gh_match.groups()
            if repo.lower() != CANONICAL_REPO:
                continue

            if owner.lower() != CANONICAL_OWNER or repo != "FletPlus":
                lineno = content.count("\n", 0, match.start()) + 1
                errors.append(
                    f"{path}:{lineno} -> URL de repo no canónica: '{url}'"
                )
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    pyproject_path = root / "pyproject.toml"
    mkdocs_path = root / "mkdocs.yml"
    markdown_paths = [root / "README.md", *sorted((root / "docs").glob("*.md"))]

    errors = []
    errors.extend(_check_pyproject(pyproject_path))
    errors.extend(_check_mkdocs(mkdocs_path))
    errors.extend(_check_markdown(markdown_paths))

    if errors:
        print("❌ Se detectaron enlaces de repositorio no canónicos:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("✅ Todos los enlaces del repositorio usan la URL canónica.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
