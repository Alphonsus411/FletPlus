#!/usr/bin/env python3
"""Valida que tools/qa.sh mantenga el contrato de Bandit y delegación CI."""

from __future__ import annotations

from pathlib import Path
import re
import sys

WORKFLOW_PATH = Path('.github/workflows/reusable-quality.yml')
QA_SCRIPT_PATH = Path('tools/qa.sh')
EXPECTED_BANDIT_COMMAND = 'python -m bandit -c pyproject.toml -r fletplus'
BANDIT_PATTERN = re.compile(r'^\s*python\s+-m\s+bandit\b.*$', re.MULTILINE)
WORKFLOW_QA_CALL = 'bash tools/qa.sh'


def _normalize_command(command: str) -> str:
    return re.sub(r'\s+', ' ', command.strip())


def _extract_bandit_command(path: Path) -> str:
    text = path.read_text(encoding='utf-8')
    match = BANDIT_PATTERN.search(text)
    if not match:
        raise ValueError(f'No se encontró un comando de Bandit en {path}')
    return _normalize_command(match.group(0))


def _extract_run_commands(path: Path) -> list[str]:
    commands: list[str] = []
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line.startswith('run:'):
            continue
        run_cmd = line.split('run:', 1)[1].strip()
        if run_cmd:
            commands.append(_normalize_command(run_cmd))
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
    if WORKFLOW_QA_CALL not in workflow_commands:
        errors.append(
            "Contrato roto: reusable-quality.yml debe ejecutar exactamente 'bash tools/qa.sh'."
        )

    if errors:
        print('\n\n'.join(errors), file=sys.stderr)
        return 1

    print(f'OK: comando Bandit alineado -> {EXPECTED_BANDIT_COMMAND}')
    print("OK: reusable-quality.yml delega en 'bash tools/qa.sh'")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
