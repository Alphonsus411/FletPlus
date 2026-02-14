#!/usr/bin/env python3
"""Valida consistencia básica entre documentación, workflows y comandos QA."""

from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
REUSABLE_WORKFLOW = REPO_ROOT / ".github/workflows/reusable-quality.yml"
QA_SCRIPT = REPO_ROOT / "tools/qa.sh"
TOOLING_DOC = REPO_ROOT / "docs/tooling.md"
README_DOC = REPO_ROOT / "README.md"
WRAPPER_WORKFLOWS = (
    REPO_ROOT / ".github/workflows/qa.yml",
    REPO_ROOT / ".github/workflows/quality.yml",
)

WORKFLOW_REF_PATTERN = re.compile(r"\.github/workflows/[A-Za-z0-9_.-]+\.yml")
RUN_BLOCK_PATTERN = re.compile(r"^\s*run:\s*\|\s*$", re.MULTILINE)
USES_REUSABLE_PATTERN = re.compile(
    r"^\s*uses:\s*\./\.github/workflows/reusable-quality\.yml\s*$", re.MULTILINE
)

CRITICAL_COMMANDS = {
    "pytest": "python -m pytest",
    "ruff": "python -m ruff check .",
    "black": "python -m black --check .",
    "mypy": "python -m mypy fletplus",
    "bandit": "python -m bandit -c pyproject.toml -r fletplus",
    "pip-audit": "python -m pip_audit -r requirements.txt -r requirements-dev.txt --policy pip-audit.policy.json",
    "safety": "python -m safety check -r requirements.txt -r requirements-dev.txt --policy-file safety-policy.yml",
}


def normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def extract_workflow_references(text: str) -> set[str]:
    return set(WORKFLOW_REF_PATTERN.findall(text))


def extract_python_commands_from_text(text: str) -> set[str]:
    commands: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("python "):
            commands.add(normalize_command(line))
    return commands


def _extract_run_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    run_blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not RUN_BLOCK_PATTERN.match(line):
            i += 1
            continue

        run_indent = len(line) - len(line.lstrip(" "))
        block_lines: list[str] = []
        i += 1
        while i < len(lines):
            current = lines[i]
            if not current.strip():
                block_lines.append("")
                i += 1
                continue
            current_indent = len(current) - len(current.lstrip(" "))
            if current_indent <= run_indent:
                break
            block_lines.append(current.strip())
            i += 1
        run_blocks.append("\n".join(block_lines))
    return run_blocks


def load_workflow_commands(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    commands: set[str] = set()
    for block in _extract_run_blocks(text):
        commands.update(extract_python_commands_from_text(block))
    return commands


def validate_wrapper_workflow(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    if not USES_REUSABLE_PATTERN.search(text):
        errors.append(
            f"{path}: debe delegar en ./.github/workflows/reusable-quality.yml"
        )
    if re.search(r"^\s*steps:\s*$", text, re.MULTILINE):
        errors.append(f"{path}: no debe definir steps locales (wrapper mínimo)")

    return errors


def validate_workflow_references() -> list[str]:
    errors: list[str] = []
    referenced: set[str] = set()
    for doc_path in (README_DOC, TOOLING_DOC):
        referenced.update(extract_workflow_references(doc_path.read_text(encoding="utf-8")))

    for rel_path in sorted(referenced):
        file_path = REPO_ROOT / rel_path
        if not file_path.exists():
            errors.append(f"Workflow referenciado en docs no existe: {rel_path}")
    return errors


def validate_critical_commands_sync() -> list[str]:
    errors: list[str] = []
    workflow_commands = load_workflow_commands(REUSABLE_WORKFLOW)
    qa_commands = extract_python_commands_from_text(QA_SCRIPT.read_text(encoding="utf-8"))
    docs_tooling = TOOLING_DOC.read_text(encoding="utf-8")
    docs_readme = README_DOC.read_text(encoding="utf-8")

    for tool, command in CRITICAL_COMMANDS.items():
        normalized = normalize_command(command)
        if normalized not in workflow_commands:
            errors.append(f"reusable-quality.yml no incluye comando crítico de {tool}: {command}")
        if normalized not in qa_commands:
            errors.append(f"tools/qa.sh no incluye comando crítico de {tool}: {command}")
        if command not in docs_tooling:
            errors.append(f"docs/tooling.md no documenta comando crítico de {tool}: {command}")
        if command not in docs_readme:
            errors.append(f"README.md no documenta comando crítico de {tool}: {command}")

    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(validate_workflow_references())
    errors.extend(validate_critical_commands_sync())

    for wrapper in WRAPPER_WORKFLOWS:
        errors.extend(validate_wrapper_workflow(wrapper))

    if errors:
        print("ERROR: inconsistencias detectadas en contrato CI/docs:\n", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("OK: contrato CI/docs validado (workflows y comandos críticos sincronizados).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
