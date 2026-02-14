#!/usr/bin/env python3
"""Valida consistencia básica entre documentación, workflows y comandos QA."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REUSABLE_WORKFLOW = REPO_ROOT / ".github/workflows/reusable-quality.yml"
QA_SCRIPT = REPO_ROOT / "tools/qa.sh"
NOXFILE = REPO_ROOT / "noxfile.py"
TOOLING_DOC = REPO_ROOT / "docs/tooling.md"
README_DOC = REPO_ROOT / "README.md"
WRAPPER_WORKFLOWS = (
    REPO_ROOT / ".github/workflows/qa.yml",
    REPO_ROOT / ".github/workflows/quality.yml",
)
DOCS_WORKFLOW = REPO_ROOT / ".github/workflows/docs.yml"
PERF_WORKFLOW = REPO_ROOT / ".github/workflows/perf.yml"
REQUIRED_QA_CHECKS = (
    "python tools/check_package_data_files.py",
    "python tools/check_canonical_repo_links.py",
)

WORKFLOW_REF_PATTERN = re.compile(r"\.github/workflows/[A-Za-z0-9_.-]+\.yml")
RUN_BLOCK_PATTERN = re.compile(r"^\s*(?:-\s*)?run:\s*\|\s*$", re.MULTILINE)
INLINE_RUN_PATTERN = re.compile(r"^\s*(?:-\s*)?run:\s*(.+?)\s*$", re.MULTILINE)
USES_REUSABLE_PATTERN = re.compile(
    r"^\s*uses:\s*\./\.github/workflows/reusable-quality\.yml\s*$", re.MULTILINE
)

OBSOLETE_DOC_PHRASES = (
    "desde la rama `gh-pages`",
    "desde la rama gh-pages",
)

DOC_PAGES_SOURCE_SENTINEL = "Source: GitHub Actions"

CRITICAL_COMMANDS = {
    "test-dependencies": "python tools/check_test_dependencies.py --suite unit --suite cli --suite websocket",
    "package-data": "python tools/check_package_data_files.py",
    "canonical-links": "python tools/check_canonical_repo_links.py",
    "workflow-validation": "python tools/check_github_workflows.py",
    "pytest": "python -m pytest",
    "ruff": "python -m ruff check .",
    "black": "python -m black --check .",
    "mypy": "python -m mypy fletplus",
    "bandit-sync": "python tools/check_bandit_command_sync.py",
    "bandit": "python -m bandit -c pyproject.toml -r fletplus",
    "pip-audit": "python -m pip_audit -r requirements.txt -r requirements-dev.txt --policy pip-audit.policy.json",
    "safety": "python -m safety check -r requirements.txt -r requirements-dev.txt --policy-file safety-policy.yml",
}


def normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def extract_workflow_references(text: str) -> set[str]:
    return set(WORKFLOW_REF_PATTERN.findall(text))


def extract_python_commands_from_text(text: str) -> list[str]:
    commands: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("python "):
            commands.append(normalize_command(line))
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


def load_workflow_run_commands(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    commands: list[str] = []

    for block in _extract_run_blocks(text):
        for raw in block.splitlines():
            line = raw.strip()
            if line:
                commands.append(normalize_command(line))

    for match in INLINE_RUN_PATTERN.finditer(text):
        candidate = match.group(1).strip()
        if candidate == "|":
            continue
        commands.append(normalize_command(candidate))

    return commands


def load_workflow_commands(path: Path) -> set[str]:
    """Compatibilidad con tests existentes: extrae comandos python del workflow."""
    commands = set()
    for command in load_workflow_run_commands(path):
        if command.startswith("python "):
            commands.add(command)
    return commands


def load_nox_qa_commands(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def function_has_qa_session_decorator(node: ast.FunctionDef) -> bool:
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr != "session":
                continue
            for keyword in decorator.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    if keyword.value.value == "qa":
                        return True
        return False

    qa_function = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and function_has_qa_session_decorator(
            node
        ):
            qa_function = node
            break

    if qa_function is None:
        return []

    commands: list[str] = []
    for node in qa_function.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute):
            continue
        if call.func.attr != "run":
            continue

        parts: list[str] = []
        for arg in call.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                parts.append(arg.value)
        if parts:
            commands.append(normalize_command(" ".join(parts)))

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


def _extract_job_block(workflow_text: str, job_name: str) -> str:
    pattern = re.compile(
        rf"(?ms)^  {re.escape(job_name)}:\n(?P<body>(?:^(?:    |\s*$).*(?:\n|$))+)"
    )
    match = pattern.search(workflow_text)
    return match.group("body") if match else ""


def validate_docs_workflow_contract(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    build_block = _extract_job_block(text, "build")
    deploy_block = _extract_job_block(text, "deploy")

    if not build_block:
        errors.append(f"{path}: falta el job obligatorio 'build'.")
    else:
        if "uses: actions/configure-pages@" not in build_block:
            errors.append(
                f"{path}: el job 'build' debe usar actions/configure-pages."
            )
        if "uses: actions/upload-pages-artifact@" not in build_block:
            errors.append(
                f"{path}: el job 'build' debe usar actions/upload-pages-artifact."
            )

    if not deploy_block:
        errors.append(f"{path}: falta el job obligatorio 'deploy'.")
    else:
        if not re.search(r"^\s*needs:\s*build\s*$", deploy_block, re.MULTILINE):
            errors.append(f"{path}: el job 'deploy' debe depender de 'build' (needs: build).")
        if "uses: actions/deploy-pages@" not in deploy_block:
            errors.append(
                f"{path}: el job 'deploy' debe usar actions/deploy-pages."
            )

    return errors


def validate_perf_workflow_contract(path: Path) -> list[str]:
    errors: list[str] = []
    commands = load_workflow_run_commands(path)

    required_commands = (
        "pip install -r requirements-dev.txt",
        "python -m pytest -m perf",
    )
    for required in required_commands:
        if normalize_command(required) not in commands:
            errors.append(
                f"{path}: falta el comando requerido en perf workflow: {required}"
            )

    return errors


def validate_workflow_references() -> list[str]:
    errors: list[str] = []
    referenced: set[str] = set()
    for doc_path in (README_DOC, TOOLING_DOC):
        referenced.update(
            extract_workflow_references(doc_path.read_text(encoding="utf-8"))
        )

    for rel_path in sorted(referenced):
        file_path = REPO_ROOT / rel_path
        if not file_path.exists():
            errors.append(f"Workflow referenciado en docs no existe: {rel_path}")
    return errors


def validate_required_qa_scripts_exist() -> list[str]:
    errors: list[str] = []
    for command in REQUIRED_QA_CHECKS:
        script_path = REPO_ROOT / command.split()[1]
        if not script_path.exists():
            errors.append(
                f"No existe script requerido por QA: {script_path.relative_to(REPO_ROOT)}"
            )
    return errors


def validate_critical_commands_sync() -> list[str]:
    errors: list[str] = []
    workflow_commands = load_workflow_run_commands(REUSABLE_WORKFLOW)
    qa_commands = extract_python_commands_from_text(
        QA_SCRIPT.read_text(encoding="utf-8")
    )
    nox_qa_commands = load_nox_qa_commands(NOXFILE)

    if normalize_command("bash tools/qa.sh") not in workflow_commands:
        errors.append(
            "reusable-quality.yml debe ejecutar exactamente 'bash tools/qa.sh'."
        )

    if normalize_command("bash tools/qa.sh") not in nox_qa_commands:
        errors.append(
            "noxfile.py sesión qa debe ejecutar exactamente 'bash tools/qa.sh'."
        )

    if workflow_commands.count(normalize_command("bash tools/qa.sh")) != 1:
        errors.append("reusable-quality.yml debe invocar tools/qa.sh una única vez.")

    for command in REQUIRED_QA_CHECKS:
        normalized = normalize_command(command)
        if normalized not in qa_commands:
            errors.append(f"tools/qa.sh no incluye verificación requerida: {command}")

    docs_tooling = TOOLING_DOC.read_text(encoding="utf-8")
    docs_readme = README_DOC.read_text(encoding="utf-8")
    for tool, command in CRITICAL_COMMANDS.items():
        normalized = normalize_command(command)
        if normalized not in qa_commands:
            errors.append(
                f"tools/qa.sh no incluye comando crítico de {tool}: {command}"
            )
        if command not in docs_tooling:
            errors.append(
                f"docs/tooling.md no documenta comando crítico de {tool}: {command}"
            )
        if command not in docs_readme:
            errors.append(
                f"README.md no documenta comando crítico de {tool}: {command}"
            )

    return errors


def validate_single_source_of_truth_sync() -> list[str]:
    """Compatibilidad retroactiva con nombre anterior del check integral."""
    return validate_critical_commands_sync()


def validate_pages_docs_wording() -> list[str]:
    errors: list[str] = []
    docs = {
        README_DOC: README_DOC.read_text(encoding="utf-8"),
        TOOLING_DOC: TOOLING_DOC.read_text(encoding="utf-8"),
    }

    for path, content in docs.items():
        lowered = content.lower()
        for phrase in OBSOLETE_DOC_PHRASES:
            if phrase.lower() in lowered:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)} contiene referencia obsoleta de despliegue: {phrase}"
                )

    if DOC_PAGES_SOURCE_SENTINEL not in docs[README_DOC]:
        errors.append(
            "README.md debe indicar explícitamente 'Source: GitHub Actions' como fuente de GitHub Pages."
        )

    if "GitHub Actions" not in docs[TOOLING_DOC]:
        errors.append(
            "docs/tooling.md debe mencionar GitHub Actions como fuente de GitHub Pages."
        )

    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(validate_workflow_references())
    errors.extend(validate_required_qa_scripts_exist())
    errors.extend(validate_critical_commands_sync())
    errors.extend(validate_pages_docs_wording())
    errors.extend(validate_docs_workflow_contract(DOCS_WORKFLOW))
    errors.extend(validate_perf_workflow_contract(PERF_WORKFLOW))

    for wrapper in WRAPPER_WORKFLOWS:
        errors.extend(validate_wrapper_workflow(wrapper))

    if errors:
        print(
            "ERROR: inconsistencias detectadas en contrato CI/docs:\n", file=sys.stderr
        )
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "OK: contrato CI/docs validado (workflow reusable, tools/qa.sh, nox y docs sincronizados)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
