#!/usr/bin/env python3
"""Valida que CI y QA local usan el mismo comando de Bandit."""

from __future__ import annotations

from pathlib import Path
import re
import sys

WORKFLOW_PATH = Path('.github/workflows/reusable-quality.yml')
QA_SCRIPT_PATH = Path('tools/qa.sh')
EXPECTED_BANDIT_COMMAND = 'python -m bandit -c pyproject.toml -r fletplus'
BANDIT_PATTERN = re.compile(r'^\s*python\s+-m\s+bandit\b.*$', re.MULTILINE)


def _extract_bandit_command(path: Path) -> str:
    text = path.read_text(encoding='utf-8')
    match = BANDIT_PATTERN.search(text)
    if not match:
        raise ValueError(f'No se encontró un comando de Bandit en {path}')
    command = re.sub(r'\s+', ' ', match.group(0)).strip()
    return command


def main() -> int:
    workflow_cmd = _extract_bandit_command(WORKFLOW_PATH)
    qa_cmd = _extract_bandit_command(QA_SCRIPT_PATH)

    errors: list[str] = []
    if workflow_cmd != qa_cmd:
        errors.append(
            'Desalineación detectada: el comando Bandit difiere entre CI y QA local\n'
            f'  - {WORKFLOW_PATH}: {workflow_cmd}\n'
            f'  - {QA_SCRIPT_PATH}: {qa_cmd}'
        )

    if workflow_cmd != EXPECTED_BANDIT_COMMAND:
        errors.append(
            'El comando Bandit no coincide con el esperado.\n'
            f'  - esperado: {EXPECTED_BANDIT_COMMAND}\n'
            f'  - encontrado: {workflow_cmd}'
        )

    if errors:
        print('\n\n'.join(errors), file=sys.stderr)
        return 1

    print(f'OK: comando Bandit alineado -> {workflow_cmd}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
