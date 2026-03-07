#!/usr/bin/env python3
"""Valida que tools/qa.sh mantenga el contrato de Bandit y delegación CI."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

WORKFLOW_PATH = Path('.github/workflows/reusable-quality.yml')
QA_SCRIPT_PATH = Path('tools/qa.sh')
EXPECTED_BANDIT_COMMAND = 'python -m bandit -c pyproject.toml -r fletplus'
BANDIT_PATTERN = re.compile(r'^\s*python\s+-m\s+bandit\b.*$', re.MULTILINE)
WORKFLOW_QA_CALL_PREFIX = 'bash tools/qa.sh'


def _normalize_command(command: str) -> str:
    return re.sub(r'\s+', ' ', command.strip())


def _extract_bandit_command(path: Path) -> str:
    text = path.read_text(encoding='utf-8')
    match = BANDIT_PATTERN.search(text)
    if not match:
        raise ValueError(f'No se encontró un comando de Bandit en {path}')
    return _normalize_command(match.group(0))


def _extract_run_commands(path: Path) -> list[str]:
    try:
        content = yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError:
        return []

    jobs = content.get('jobs') if isinstance(content, dict) else None
    if not isinstance(jobs, dict):
        return []

    commands: list[str] = []
    for job in jobs.values():
        if not isinstance(job, dict):
            continue

        steps = job.get('steps')
        if not isinstance(steps, list):
            continue

        for step in steps:
            if not isinstance(step, dict):
                continue

            run_value = step.get('run')
            if not isinstance(run_value, str):
                continue

            for raw_line in run_value.splitlines():
                line = raw_line.strip()
                if line:
                    commands.append(_normalize_command(line))

    return commands


def main() -> int:
    errors: list[str] = []

    try:
        qa_cmd = _extract_bandit_command(QA_SCRIPT_PATH)
    except ValueError as exc:
        errors.append(str(exc))
        qa_cmd = None

    if qa_cmd and qa_cmd != EXPECTED_BANDIT_COMMAND:
        errors.append(
            'Desalineación detectada: el comando Bandit de tools/qa.sh no coincide con el canónico.\n'
            f'  - esperado: {EXPECTED_BANDIT_COMMAND}\n'
            f'  - encontrado: {qa_cmd}'
        )

    workflow_commands = _extract_run_commands(WORKFLOW_PATH)
    if not any(
        command == WORKFLOW_QA_CALL_PREFIX
        or command.startswith(f"{WORKFLOW_QA_CALL_PREFIX} ")
        for command in workflow_commands
    ):
        errors.append(
            "Contrato roto: reusable-quality.yml debe delegar en tools/qa.sh (con o sin --scope)."
        )

    if errors:
        print('\n\n'.join(errors), file=sys.stderr)
        return 1

    print(f'OK: comando Bandit alineado -> {EXPECTED_BANDIT_COMMAND}')
    print("OK: reusable-quality.yml delega en tools/qa.sh")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
