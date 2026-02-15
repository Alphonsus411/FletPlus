from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
QA_SCRIPT = REPO_ROOT / "tools" / "qa.sh"
TOOLING_DOC = REPO_ROOT / "docs" / "tooling.md"
WORKFLOW_VALIDATION_COMMAND = "python tools/check_github_workflows.py"
CHECK_WORKFLOWS_PATH = REPO_ROOT / "tools" / "check_github_workflows.py"


SPEC = importlib.util.spec_from_file_location("check_github_workflows", CHECK_WORKFLOWS_PATH)
assert SPEC and SPEC.loader
check_github_workflows = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_github_workflows)


def test_workflow_validation_command_is_in_qa_script() -> None:
    qa_content = QA_SCRIPT.read_text(encoding="utf-8")

    assert WORKFLOW_VALIDATION_COMMAND in qa_content


def test_workflow_validation_command_is_documented_in_tooling_doc() -> None:
    tooling_content = TOOLING_DOC.read_text(encoding="utf-8")

    assert WORKFLOW_VALIDATION_COMMAND in tooling_content


@pytest.mark.parametrize(
    "workflow_files",
    [
        ("only-yml.yml",),
        ("only-yaml.yaml",),
        ("mixed-yml.yml", "mixed-yaml.yaml"),
    ],
)
def test_workflow_validation_contract_accepts_yml_and_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    workflow_files: tuple[str, ...],
) -> None:
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    valid_workflow = """
name: Test Workflow
on:
  push:
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
"""
    for file_name in workflow_files:
        (workflows_dir / file_name).write_text(valid_workflow, encoding="utf-8")

    monkeypatch.setattr(check_github_workflows, "WORKFLOWS_DIR", workflows_dir)

    exit_code = check_github_workflows.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"OK: {len(workflow_files)} workflows validados" in captured.out
