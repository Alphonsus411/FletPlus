from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/check_ci_workflow_contract.py"
SPEC = importlib.util.spec_from_file_location("check_ci_workflow_contract", MODULE_PATH)
assert SPEC and SPEC.loader
check_ci_workflow_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_ci_workflow_contract)


def test_extract_workflow_references_detects_all_mentions() -> None:
    text = """
    revisar .github/workflows/qa.yml y .github/workflows/quality.yml
    además de .github/workflows/reusable-quality.yml
    """

    refs = check_ci_workflow_contract.extract_workflow_references(text)

    assert refs == {
        ".github/workflows/qa.yml",
        ".github/workflows/quality.yml",
        ".github/workflows/reusable-quality.yml",
    }


def test_load_workflow_commands_reads_run_blocks(tmp_path: Path) -> None:
    workflow = tmp_path / "reusable-quality.yml"
    workflow.write_text(
        """
name: Reusable Quality
jobs:
  quality:
    steps:
      - name: Test
        run: |
          python -m pytest
          python -m ruff check .
      - name: Other
        run: echo done
""",
        encoding="utf-8",
    )

    commands = check_ci_workflow_contract.load_workflow_commands(workflow)

    assert "python -m pytest" in commands
    assert "python -m ruff check ." in commands
