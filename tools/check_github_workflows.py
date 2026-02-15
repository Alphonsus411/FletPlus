#!/usr/bin/env python3
"""Valida workflows de GitHub Actions (YAML + reglas contractuales básicas)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_step(workflow: Path, job_name: str, step: object, index: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(step, dict):
        return [
            f"{workflow}: job '{job_name}' step #{index} debe ser un objeto YAML."
        ]

    has_uses = _is_non_empty_string(step.get("uses"))
    has_run = _is_non_empty_string(step.get("run"))

    if has_uses and has_run:
        errors.append(
            f"{workflow}: job '{job_name}' step #{index} no puede definir simultáneamente 'uses' y 'run'."
        )
    if not has_uses and not has_run:
        errors.append(
            f"{workflow}: job '{job_name}' step #{index} debe definir 'uses' o 'run'."
        )

    return errors


def _normalize_local_workflow_use(value: str) -> str | None:
    prefix = "./.github/workflows/"
    if not value.startswith(prefix):
        return None
    return value.split("@", maxsplit=1)[0]


def _validate_reusable_trigger(path: Path, content: dict[object, object]) -> list[str]:
    on_value = content.get("on")
    if on_value is None and True in content:
        on_value = content.get(True)

    if not isinstance(on_value, dict) or "workflow_call" not in on_value:
        return [
            f"{path}: al ser invocado vía 'uses: ./.github/workflows/...', debe declarar 'on.workflow_call'."
        ]

    workflow_call = on_value.get("workflow_call")
    if workflow_call is None:
        return []

    if not isinstance(workflow_call, dict):
        return [f"{path}: 'on.workflow_call' debe ser un objeto YAML."]

    errors: list[str] = []
    for key in ("inputs", "secrets"):
        block = workflow_call.get(key)
        if block is None:
            continue
        if not isinstance(block, dict):
            errors.append(f"{path}: 'on.workflow_call.{key}' debe ser un objeto YAML.")
            continue
        for item_name, item_def in block.items():
            if not isinstance(item_def, dict):
                errors.append(
                    f"{path}: 'on.workflow_call.{key}.{item_name}' debe ser un objeto YAML."
                )

    return errors


def validate_workflow(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"{path}: YAML inválido ({exc})."]

    if not isinstance(content, dict):
        return [f"{path}: el archivo debe tener un objeto YAML en raíz."]

    has_on_key = "on" in content or True in content
    if not has_on_key:
        errors.append(f"{path}: falta clave obligatoria 'on'.")

    jobs = content.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        errors.append(f"{path}: falta bloque 'jobs' o está vacío.")
        return errors

    for job_name, job_def in jobs.items():
        if not isinstance(job_def, dict):
            errors.append(f"{path}: job '{job_name}' debe ser un objeto YAML.")
            continue

        has_uses = _is_non_empty_string(job_def.get("uses"))
        has_runs_on = "runs-on" in job_def

        if has_uses and has_runs_on:
            errors.append(
                f"{path}: job '{job_name}' no puede definir 'uses' y 'runs-on' a la vez."
            )
        if not has_uses and not has_runs_on:
            errors.append(
                f"{path}: job '{job_name}' debe definir 'uses' (reusable) o 'runs-on'."
            )

        if has_uses and "steps" in job_def:
            errors.append(
                f"{path}: job '{job_name}' reusable no debe declarar 'steps' locales."
            )

        if has_uses:
            with_value = job_def.get("with")
            if with_value is not None and not isinstance(with_value, dict):
                errors.append(f"{path}: job '{job_name}' reusable debe declarar 'with' como objeto YAML.")

            secrets_value = job_def.get("secrets")
            if secrets_value is not None and not (
                isinstance(secrets_value, dict)
                or (_is_non_empty_string(secrets_value) and secrets_value == "inherit")
            ):
                errors.append(
                    f"{path}: job '{job_name}' reusable debe declarar 'secrets' como objeto YAML o 'inherit'."
                )

        if has_runs_on:
            steps = job_def.get("steps")
            if not isinstance(steps, list) or not steps:
                errors.append(
                    f"{path}: job '{job_name}' con 'runs-on' debe declarar una lista no vacía de 'steps'."
                )
                continue
            for index, step in enumerate(steps, start=1):
                errors.extend(_validate_step(path, str(job_name), step, index))

    return errors


def validate_reusable_workflow_references(workflow_files: list[Path]) -> list[str]:
    errors: list[str] = []
    indexed_files = {
        f"./.github/workflows/{workflow_file.name}": workflow_file for workflow_file in workflow_files
    }

    for workflow in workflow_files:
        try:
            content = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue

        if not isinstance(content, dict):
            continue

        jobs = content.get("jobs")
        if not isinstance(jobs, dict):
            continue

        for job_def in jobs.values():
            if not isinstance(job_def, dict):
                continue

            use_value = job_def.get("uses")
            if not _is_non_empty_string(use_value):
                continue

            normalized_use = _normalize_local_workflow_use(use_value)
            if normalized_use is None:
                continue

            target_workflow = indexed_files.get(normalized_use)
            if target_workflow is None:
                errors.append(
                    f"{workflow}: referencia reusable inexistente '{normalized_use}'."
                )
                continue

            try:
                target_content = yaml.safe_load(target_workflow.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            if not isinstance(target_content, dict):
                continue

            errors.extend(_validate_reusable_trigger(target_workflow, target_content))

    return errors


def main() -> int:
    if not WORKFLOWS_DIR.exists():
        print(f"ERROR: no existe directorio de workflows: {WORKFLOWS_DIR}", file=sys.stderr)
        return 1

    workflow_files = sorted(
        {
            *WORKFLOWS_DIR.glob("*.yml"),
            *WORKFLOWS_DIR.glob("*.yaml"),
        },
        key=lambda path: path.name,
    )
    if not workflow_files:
        print(f"ERROR: no se encontraron workflows en {WORKFLOWS_DIR}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for workflow in workflow_files:
        errors.extend(validate_workflow(workflow))
    errors.extend(validate_reusable_workflow_references(workflow_files))

    if errors:
        print("ERROR: validación de workflows falló:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(workflow_files)} workflows validados (YAML + reglas GitHub Actions).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
