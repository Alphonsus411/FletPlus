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


def test_reusable_workflow_is_valid_when_declaring_workflow_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    reusable = """
name: Reusable
on:
  workflow_call:
    inputs:
      environment:
        required: false
        type: string
    secrets:
      token:
        required: false
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: echo reusable
"""
    wrapper = """
name: Wrapper
on:
  push:
jobs:
  call-reusable:
    uses: ./.github/workflows/reusable.yml
    with:
      environment: dev
    secrets: inherit
"""

    (workflows_dir / "reusable.yml").write_text(reusable, encoding="utf-8")
    (workflows_dir / "wrapper.yml").write_text(wrapper, encoding="utf-8")

    monkeypatch.setattr(check_github_workflows, "WORKFLOWS_DIR", workflows_dir)

    exit_code = check_github_workflows.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "OK: 2 workflows validados" in captured.out


def test_reusable_workflow_is_invalid_without_workflow_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    reusable_without_workflow_call = """
name: Reusable Invalid
on:
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo invalid
"""
    wrapper = """
name: Wrapper
on:
  pull_request:
jobs:
  call-reusable:
    uses: ./.github/workflows/reusable.yml
"""

    (workflows_dir / "reusable.yml").write_text(
        reusable_without_workflow_call, encoding="utf-8"
    )
    (workflows_dir / "wrapper.yml").write_text(wrapper, encoding="utf-8")

    monkeypatch.setattr(check_github_workflows, "WORKFLOWS_DIR", workflows_dir)

    exit_code = check_github_workflows.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "debe declarar 'on.workflow_call'" in captured.err


def test_wrapper_that_references_non_existing_reusable_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    wrapper = """
name: Wrapper Invalid
on:
  push:
jobs:
  call-missing:
    uses: ./.github/workflows/missing-reusable.yaml
"""

    (workflows_dir / "wrapper.yaml").write_text(wrapper, encoding="utf-8")

    monkeypatch.setattr(check_github_workflows, "WORKFLOWS_DIR", workflows_dir)

    exit_code = check_github_workflows.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "referencia reusable inexistente" in captured.err
