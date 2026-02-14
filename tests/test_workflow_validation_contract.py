from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
QA_SCRIPT = REPO_ROOT / "tools" / "qa.sh"
TOOLING_DOC = REPO_ROOT / "docs" / "tooling.md"
WORKFLOW_VALIDATION_COMMAND = "python tools/check_github_workflows.py"


def test_workflow_validation_command_is_in_qa_script() -> None:
    qa_content = QA_SCRIPT.read_text(encoding="utf-8")

    assert WORKFLOW_VALIDATION_COMMAND in qa_content


def test_workflow_validation_command_is_documented_in_tooling_doc() -> None:
    tooling_content = TOOLING_DOC.read_text(encoding="utf-8")

    assert WORKFLOW_VALIDATION_COMMAND in tooling_content
