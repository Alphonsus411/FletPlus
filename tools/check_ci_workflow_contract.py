#!/usr/bin/env python3
"""Valida consistencia básica entre documentación, workflows y comandos QA."""

from __future__ import annotations

import ast
import configparser
import re
import sys
from pathlib import Path

import yaml

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
WORKFLOWS_REQUIRING_CONTENTS_READ = WRAPPER_WORKFLOWS + (REUSABLE_WORKFLOW,)
DOCS_WORKFLOW = REPO_ROOT / ".github/workflows/docs.yml"
PERF_WORKFLOW = REPO_ROOT / ".github/workflows/perf.yml"
PYTEST_INI = REPO_ROOT / "pytest.ini"
REQUIRED_QA_CHECKS = (
    "python tools/check_package_data_files.py",
    "python tools/check_canonical_repo_links.py",
)

REUSABLE_JOB_NAMES = ("tests-matrix", "static-security")
REUSABLE_JOB_QA_SCOPE_COMMANDS = {
    "tests-matrix": "bash tools/qa.sh --scope tests-matrix",
    "static-security": "bash tools/qa.sh --scope static-security",
}

WORKFLOW_REF_PATTERN = re.compile(r"\.github/workflows/[A-Za-z0-9_.-]+\.(?:yml|yaml)")
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


def _extract_step_run_commands(step: object) -> list[str]:
    if not isinstance(step, dict):
        return []

    run_value = step.get("run")
    if not isinstance(run_value, str):
        return []

    commands: list[str] = []
    for raw in run_value.splitlines():
        line = raw.strip()
        if line:
            commands.append(normalize_command(line))
    return commands


def load_workflow_run_commands_by_job(path: Path) -> dict[str, list[str]]:
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return {}

    jobs = content.get("jobs") if isinstance(content, dict) else None
    if not isinstance(jobs, dict):
        return {}

    commands_by_job: dict[str, list[str]] = {}
    for job_name, job_def in jobs.items():
        if not isinstance(job_name, str) or not isinstance(job_def, dict):
            continue
        steps = job_def.get("steps")
        if not isinstance(steps, list):
            commands_by_job[job_name] = []
            continue

        job_commands: list[str] = []
        for step in steps:
            job_commands.extend(_extract_step_run_commands(step))
        commands_by_job[job_name] = job_commands

    return commands_by_job


def load_workflow_run_commands(path: Path) -> list[str]:
    commands: list[str] = []
    for job_commands in load_workflow_run_commands_by_job(path).values():
        commands.extend(job_commands)
    return commands


def load_workflow_run_commands_for_jobs(
    path: Path, job_names: tuple[str, ...]
) -> dict[str, list[str]]:
    """Extrae comandos run únicamente para los jobs indicados."""
    commands_by_job = load_workflow_run_commands_by_job(path)
    return {job_name: commands_by_job.get(job_name, []) for job_name in job_names}


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
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"{path}: YAML inválido ({exc})."]

    jobs = content.get("jobs") if isinstance(content, dict) else None
    if not isinstance(jobs, dict) or not jobs:
        errors.append(
            f"{path}: debe delegar en ./.github/workflows/reusable-quality.yml"
        )
        return errors

    for job_def in jobs.values():
        if not isinstance(job_def, dict):
            errors.append(
                f"{path}: debe delegar en ./.github/workflows/reusable-quality.yml"
            )
            continue

        if job_def.get("uses") != "./.github/workflows/reusable-quality.yml":
            errors.append(
                f"{path}: debe delegar en ./.github/workflows/reusable-quality.yml"
            )
        if "steps" in job_def:
            errors.append(f"{path}: no debe definir steps locales (wrapper mínimo)")

    return errors


def validate_workflow_permissions(path: Path) -> list[str]:
    """Exige permisos explícitos mínimos en workflows de QA/Quality."""
    errors: list[str] = []

    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"{path}: YAML inválido ({exc})."]

    if not isinstance(content, dict):
        return [f"{path}: el workflow debe ser un objeto YAML válido."]

    jobs = content.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        errors.append(
            f"{path}: debe definir permissions: {{contents: read}} a nivel workflow o job."
        )
        return errors

    workflow_permissions = content.get("permissions")
    has_workflow_permissions = isinstance(workflow_permissions, dict)
    if has_workflow_permissions and workflow_permissions.get("contents") != "read":
        errors.append(
            f"{path}: permissions a nivel workflow debe definir contents: read."
        )

    missing_jobs: list[str] = []
    invalid_overrides: list[str] = []
    for job_name, job_def in jobs.items():
        if not isinstance(job_name, str):
            continue
        if not isinstance(job_def, dict):
            if not has_workflow_permissions:
                missing_jobs.append(job_name)
            continue

        job_permissions = job_def.get("permissions")

        if job_permissions is None:
            if not has_workflow_permissions:
                missing_jobs.append(job_name)
            continue

        if not isinstance(job_permissions, dict):
            invalid_overrides.append(job_name)
            continue

        if job_permissions.get("contents") != "read":
            invalid_overrides.append(job_name)

    if missing_jobs:
        errors.append(
            f"{path}: los jobs {missing_jobs} deben definir permissions.contents: read o declararlo a nivel workflow."
        )

    if invalid_overrides:
        errors.append(
            f"{path}: los jobs {invalid_overrides} definen un override inválido; permissions.contents debe ser read."
        )

    return errors


def _extract_job_block(workflow_text: str, job_name: str) -> str:
    pattern = re.compile(
        rf"(?ms)^  {re.escape(job_name)}:\n(?P<body>(?:^(?:    |\s*$).*(?:\n|$))+)"
    )
    match = pattern.search(workflow_text)
    return match.group("body") if match else ""


def validate_docs_workflow_contract(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"{path}: YAML inválido ({exc})."]

    workflow_on = (
        content.get("on", content.get(True)) if isinstance(content, dict) else None
    )
    if not isinstance(workflow_on, dict):
        errors.append(f"{path}: falta la sección de triggers 'on'.")
    else:
        pull_request = workflow_on.get("pull_request")
        if not isinstance(pull_request, dict):
            errors.append(
                f"{path}: debe definir trigger pull_request para validar docs en PR."
            )
        else:
            branches = pull_request.get("branches")
            if isinstance(branches, list):
                branch_items = {item for item in branches if isinstance(item, str)}
            elif isinstance(branches, str):
                branch_items = {branches}
            else:
                branch_items = set()
            missing_branches = {"main", "develop"} - branch_items
            if missing_branches:
                errors.append(
                    f"{path}: pull_request debe incluir ramas {sorted(missing_branches)}."
                )

    jobs = content.get("jobs") if isinstance(content, dict) else None
    if not isinstance(jobs, dict):
        return [f"{path}: falta la sección 'jobs' en el workflow."]

    def _job_step_uses(job_def: object) -> set[str]:
        if not isinstance(job_def, dict):
            return set()
        steps = job_def.get("steps")
        if not isinstance(steps, list):
            return set()

        uses_values: set[str] = set()
        for step in steps:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if isinstance(uses, str):
                uses_values.add(uses.split("@", maxsplit=1)[0])
        return uses_values

    docs_job_commands = load_workflow_run_commands_for_jobs(path, ("build", "deploy"))

    build_job = jobs.get("build")
    if not isinstance(build_job, dict):
        errors.append(f"{path}: falta el job obligatorio 'build'.")
    else:
        build_uses = _job_step_uses(build_job)
        build_commands = docs_job_commands["build"]
        if not any(
            command.startswith("mkdocs build") and "--strict" in command
            for command in build_commands
        ):
            errors.append(
                f"{path}: el job 'build' debe ejecutar mkdocs build --strict."
            )
        if "actions/configure-pages" not in build_uses:
            errors.append(f"{path}: el job 'build' debe usar actions/configure-pages.")
        if "actions/upload-pages-artifact" not in build_uses:
            errors.append(
                f"{path}: el job 'build' debe usar actions/upload-pages-artifact."
            )

    deploy_job = jobs.get("deploy")
    if not isinstance(deploy_job, dict):
        errors.append(f"{path}: falta el job obligatorio 'deploy'.")
    else:
        deploy_if = deploy_job.get("if")
        expected_if = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
        if deploy_if != expected_if:
            errors.append(
                f"{path}: el job 'deploy' debe limitarse a push en main con if: {expected_if}"
            )

        deploy_needs = deploy_job.get("needs")
        if isinstance(deploy_needs, str):
            needs_items = [deploy_needs]
        elif isinstance(deploy_needs, list):
            needs_items = [item for item in deploy_needs if isinstance(item, str)]
        else:
            needs_items = []

        if "build" not in needs_items:
            errors.append(
                f"{path}: el job 'deploy' debe depender de 'build' (needs: build)."
            )

        deploy_uses = _job_step_uses(deploy_job)
        if "actions/deploy-pages" not in deploy_uses:
            errors.append(f"{path}: el job 'deploy' debe usar actions/deploy-pages.")

    return errors


def validate_perf_workflow_contract(path: Path) -> list[str]:
    errors: list[str] = []
    commands = load_workflow_run_commands_for_jobs(path, ("perf",))["perf"]

    required_commands = ["pip install -r requirements-dev.txt"]

    for required in required_commands:
        if normalize_command(required) not in commands:
            errors.append(
                f"{path}: falta el comando requerido en perf workflow: {required}"
            )

    if not any(re.search(r"(?:^|\s)pytest(?:\s|$)", command) for command in commands):
        errors.append(f"{path}: falta el comando requerido en perf workflow: pytest")

    perf_pytest_base = normalize_command("python -m pytest -m perf")
    if not any(
        command == perf_pytest_base or command.startswith(f"{perf_pytest_base} ")
        for command in commands
    ):
        errors.append(
            f"{path}: falta el comando requerido en perf workflow: python -m pytest -m perf"
        )

    pytest_ini_text = ""
    if PYTEST_INI.exists():
        pytest_ini_text = PYTEST_INI.read_text(encoding="utf-8")

    if pytest_ini_has_global_perf_exclusion(pytest_ini_text):
        override_command = normalize_command("python -m pytest -m perf -o addopts=")
        if override_command not in commands:
            errors.append(
                f"{path}: falta el comando requerido en perf workflow: python -m pytest -m perf -o addopts="
            )

    return errors


def pytest_ini_has_global_perf_exclusion(pytest_ini_text: str) -> bool:
    """Detecta si pytest.ini excluye globalmente el marker perf vía addopts."""
    if not pytest_ini_text.strip():
        return False

    parser = configparser.ConfigParser()
    addopts = ""
    try:
        parser.read_string(pytest_ini_text)
        if parser.has_option("pytest", "addopts"):
            addopts = parser.get("pytest", "addopts")
    except configparser.Error:
        addopts = ""

    if not addopts:
        addopts_match = re.search(
            r"^\s*addopts\s*=\s*(?P<value>.+)$", pytest_ini_text, re.MULTILINE
        )
        if addopts_match:
            addopts = addopts_match.group("value")

    return bool(re.search(r"\bnot\s+perf\b", addopts))


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
    workflow_commands_by_job = load_workflow_run_commands_for_jobs(
        REUSABLE_WORKFLOW, REUSABLE_JOB_NAMES
    )
    qa_commands = extract_python_commands_from_text(
        QA_SCRIPT.read_text(encoding="utf-8")
    )
    nox_qa_commands = load_nox_qa_commands(NOXFILE)

    try:
        reusable_content = yaml.safe_load(REUSABLE_WORKFLOW.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        reusable_content = {}
    reusable_jobs = (
        reusable_content.get("jobs", {}) if isinstance(reusable_content, dict) else {}
    )

    for job_name in REUSABLE_JOB_NAMES:
        job_commands = workflow_commands_by_job.get(job_name, [])
        if not job_commands:
            errors.append(
                f"reusable-quality.yml debe definir el job contractual '{job_name}'."
            )

    tests_job = (
        reusable_jobs.get("tests-matrix") if isinstance(reusable_jobs, dict) else None
    )
    tests_matrix = (
        tests_job.get("strategy", {}).get("matrix", {}).get("python-version")
        if isinstance(tests_job, dict)
        else None
    )
    if not isinstance(tests_matrix, list) or set(tests_matrix) != {
        "3.9",
        "3.10",
        "3.11",
    }:
        errors.append(
            "reusable-quality.yml job 'tests-matrix' debe usar matriz python-version: [3.9, 3.10, 3.11]."
        )

    static_job = (
        reusable_jobs.get("static-security")
        if isinstance(reusable_jobs, dict)
        else None
    )
    static_steps = static_job.get("steps") if isinstance(static_job, dict) else None
    setup_python_311 = False
    if isinstance(static_steps, list):
        for step in static_steps:
            if not isinstance(step, dict):
                continue
            uses_value = step.get("uses")
            if not isinstance(uses_value, str) or not uses_value.startswith(
                "actions/setup-python"
            ):
                continue
            with_values = step.get("with")
            if (
                isinstance(with_values, dict)
                and str(with_values.get("python-version")) == "3.11"
            ):
                setup_python_311 = True
                break
    if not setup_python_311:
        errors.append(
            "reusable-quality.yml job 'static-security' debe fijar python-version 3.11 en actions/setup-python."
        )

    for job_name, command in REUSABLE_JOB_QA_SCOPE_COMMANDS.items():
        normalized = normalize_command(command)
        if normalized not in workflow_commands_by_job.get(job_name, []):
            errors.append(
                f"reusable-quality.yml job '{job_name}' debe ejecutar exactamente '{command}'."
            )
        if workflow_commands.count(normalized) != 1:
            errors.append(
                f"reusable-quality.yml debe invocar '{command}' una única vez."
            )

    if normalize_command("bash tools/qa.sh") not in nox_qa_commands:
        errors.append(
            "noxfile.py sesión qa debe ejecutar exactamente 'bash tools/qa.sh'."
        )

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

    for workflow in WORKFLOWS_REQUIRING_CONTENTS_READ:
        errors.extend(validate_workflow_permissions(workflow))

    if errors:
        print(
            "ERROR: inconsistencias detectadas en contrato CI/docs:\n", file=sys.stderr
        )
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "OK: contrato CI/docs validado (workflow reusable por jobs, tools/qa.sh, nox y docs sincronizados)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
