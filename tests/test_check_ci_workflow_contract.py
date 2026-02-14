from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/check_ci_workflow_contract.py"
SPEC = importlib.util.spec_from_file_location("check_ci_workflow_contract", MODULE_PATH)
assert SPEC and SPEC.loader
check_ci_workflow_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_ci_workflow_contract)


@pytest.fixture
def contract_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    workflows_dir = tmp_path / ".github" / "workflows"
    docs_dir = tmp_path / "docs"
    tools_dir = tmp_path / "tools"
    workflows_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)
    tools_dir.mkdir(parents=True)

    reusable = workflows_dir / "reusable-quality.yml"
    reusable.write_text(
        """
name: Reusable Quality
jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - name: QA
        run: bash tools/qa.sh
""",
        encoding="utf-8",
    )

    qa_wrapper = workflows_dir / "qa.yml"
    qa_wrapper.write_text(
        """
name: QA
jobs:
  qa:
    uses: ./.github/workflows/reusable-quality.yml
""",
        encoding="utf-8",
    )

    quality_wrapper = workflows_dir / "quality.yml"
    quality_wrapper.write_text(
        """
name: Quality
jobs:
  quality:
    uses: ./.github/workflows/reusable-quality.yml
""",
        encoding="utf-8",
    )

    qa_commands = "\n".join(check_ci_workflow_contract.CRITICAL_COMMANDS.values())
    (tools_dir / "qa.sh").write_text(f"#!/usr/bin/env bash\n{qa_commands}\n", encoding="utf-8")

    (tmp_path / "noxfile.py").write_text(
        """
import nox


@nox.session(name="qa")
def qa(session):
    session.run("bash", "tools/qa.sh")
""",
        encoding="utf-8",
    )

    docs_content = "\n".join(
        [
            "Referencias:",
            ".github/workflows/qa.yml",
            ".github/workflows/quality.yml",
            ".github/workflows/reusable-quality.yml",
            *check_ci_workflow_contract.CRITICAL_COMMANDS.values(),
            "Source: GitHub Actions",
            "GitHub Actions",
        ]
    )
    (tmp_path / "README.md").write_text(docs_content, encoding="utf-8")
    (docs_dir / "tooling.md").write_text(docs_content, encoding="utf-8")

    monkeypatch.setattr(check_ci_workflow_contract, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(check_ci_workflow_contract, "REUSABLE_WORKFLOW", reusable)
    monkeypatch.setattr(check_ci_workflow_contract, "QA_SCRIPT", tools_dir / "qa.sh")
    monkeypatch.setattr(check_ci_workflow_contract, "NOXFILE", tmp_path / "noxfile.py")
    monkeypatch.setattr(check_ci_workflow_contract, "README_DOC", tmp_path / "README.md")
    monkeypatch.setattr(check_ci_workflow_contract, "TOOLING_DOC", docs_dir / "tooling.md")
    monkeypatch.setattr(
        check_ci_workflow_contract,
        "WRAPPER_WORKFLOWS",
        (qa_wrapper, quality_wrapper),
    )

    return {
        "tmp_path": tmp_path,
        "workflows_dir": workflows_dir,
        "reusable": reusable,
        "qa_wrapper": qa_wrapper,
        "quality_wrapper": quality_wrapper,
        "qa_script": tools_dir / "qa.sh",
        "readme": tmp_path / "README.md",
        "tooling": docs_dir / "tooling.md",
    }


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


def test_validate_wrapper_workflow_fails_if_local_steps_exist(
    contract_env: dict[str, Path],
) -> None:
    wrapper = contract_env["workflows_dir"] / "wrapper-with-steps.yml"
    wrapper.write_text(
        """
name: Wrapper
jobs:
  qa:
    uses: ./.github/workflows/reusable-quality.yml
    steps:
      - run: echo local
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_wrapper_workflow(wrapper)

    assert any("no debe definir steps locales" in error for error in errors)


def test_validate_wrapper_workflow_fails_if_uses_reusable_is_missing(
    contract_env: dict[str, Path],
) -> None:
    wrapper = contract_env["workflows_dir"] / "wrapper-without-uses.yml"
    wrapper.write_text(
        """
name: Wrapper
jobs:
  qa:
    runs-on: ubuntu-latest
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_wrapper_workflow(wrapper)

    assert any("debe delegar en ./.github/workflows/reusable-quality.yml" in error for error in errors)


def test_validate_critical_commands_sync_fails_when_workflow_qa_and_docs_drift(
    contract_env: dict[str, Path],
) -> None:
    contract_env["reusable"].write_text(
        contract_env["reusable"].read_text(encoding="utf-8").replace(
            "run: bash tools/qa.sh", "run: echo skipped"
        ),
        encoding="utf-8",
    )

    missing_command = check_ci_workflow_contract.CRITICAL_COMMANDS["ruff"]
    contract_env["qa_script"].write_text(
        contract_env["qa_script"].read_text(encoding="utf-8").replace(
            f"{missing_command}\n", ""
        ),
        encoding="utf-8",
    )
    contract_env["tooling"].write_text(
        contract_env["tooling"].read_text(encoding="utf-8").replace(
            f"{missing_command}\n", ""
        ),
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_critical_commands_sync()

    assert "reusable-quality.yml debe ejecutar exactamente 'bash tools/qa.sh'." in errors
    assert any("tools/qa.sh no incluye comando crítico de ruff" in error for error in errors)
    assert any("docs/tooling.md no documenta comando crítico de ruff" in error for error in errors)


def test_validate_workflow_references_fails_for_missing_doc_reference(
    contract_env: dict[str, Path],
) -> None:
    contract_env["readme"].write_text(
        contract_env["readme"].read_text(encoding="utf-8")
        + "\n.github/workflows/missing-workflow.yml\n",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_workflow_references()

    assert errors == [
        "Workflow referenciado en docs no existe: .github/workflows/missing-workflow.yml"
    ]
