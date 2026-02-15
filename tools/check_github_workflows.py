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

    if errors:
        print("ERROR: validación de workflows falló:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(workflow_files)} workflows validados (YAML + reglas GitHub Actions).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
