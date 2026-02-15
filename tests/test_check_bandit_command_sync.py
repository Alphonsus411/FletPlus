from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / 'tools/check_bandit_command_sync.py'
SPEC = importlib.util.spec_from_file_location('check_bandit_command_sync', MODULE_PATH)
assert SPEC and SPEC.loader
check_bandit_command_sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_bandit_command_sync)


@pytest.fixture
def checker_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    workflow_path = tmp_path / '.github' / 'workflows' / 'reusable-quality.yml'
    qa_path = tmp_path / 'tools' / 'qa.sh'
    workflow_path.parent.mkdir(parents=True)
    qa_path.parent.mkdir(parents=True)

    workflow_path.write_text(
        """
name: Reusable Quality
jobs:
  tests-matrix:
    steps:
      - name: QA tests
        run: bash tools/qa.sh --scope tests-matrix
  static-security:
    steps:
      - name: QA static
        run: bash tools/qa.sh --scope static-security
""",
        encoding='utf-8',
    )

    qa_path.write_text(
        """
#!/usr/bin/env bash
python -m bandit -c pyproject.toml -r fletplus
""",
        encoding='utf-8',
    )

    monkeypatch.setattr(check_bandit_command_sync, 'WORKFLOW_PATH', workflow_path)
    monkeypatch.setattr(check_bandit_command_sync, 'QA_SCRIPT_PATH', qa_path)
    return {'workflow': workflow_path, 'qa': qa_path}


def test_main_ok_when_bandit_is_aligned(
    checker_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    result = check_bandit_command_sync.main()

    captured = capsys.readouterr()
    assert result == 0
    assert 'OK: comando Bandit alineado' in captured.out


def test_main_fails_when_bandit_command_is_misaligned(
    checker_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    checker_env['qa'].write_text(
        """
#!/usr/bin/env bash
python -m bandit -c pyproject.toml -r src
""",
        encoding='utf-8',
    )

    result = check_bandit_command_sync.main()

    captured = capsys.readouterr()
    assert result == 1
    assert 'Desalineación detectada' in captured.err


def test_main_fails_when_bandit_command_is_missing(
    checker_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    checker_env['qa'].write_text(
        """
#!/usr/bin/env bash
python -m pytest
""",
        encoding='utf-8',
    )

    result = check_bandit_command_sync.main()

    captured = capsys.readouterr()
    assert result == 1
    assert 'No se encontró un comando de Bandit' in captured.err


def test_main_ok_when_workflow_run_is_multiline_with_qa_call(
    checker_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    checker_env['workflow'].write_text(
        """
name: Reusable Quality
jobs:
  static-security:
    steps:
      - name: QA
        run: |
          echo "pre-check"
          bash tools/qa.sh --scope static-security
""",
        encoding='utf-8',
    )

    result = check_bandit_command_sync.main()

    captured = capsys.readouterr()
    assert result == 0
    assert "OK: reusable-quality.yml delega en tools/qa.sh" in captured.out


def test_main_fails_when_workflow_run_is_multiline_without_qa_call(
    checker_env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    checker_env['workflow'].write_text(
        """
name: Reusable Quality
jobs:
  static-security:
    steps:
      - name: QA
        run: |
          echo "pre-check"
          python -m pytest
""",
        encoding='utf-8',
    )

    result = check_bandit_command_sync.main()

    captured = capsys.readouterr()
    assert result == 1
    assert (
        "Contrato roto: reusable-quality.yml debe delegar en tools/qa.sh (con o sin --scope)."
        in captured.err
    )
