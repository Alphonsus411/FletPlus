from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "tools/check_ci_workflow_contract.py"
)
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
permissions:
  contents: read
jobs:
  tests-matrix:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]
    steps:
      - name: Tests scope
        run: bash tools/qa.sh --scope tests-matrix
  static-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Static scope
        run: bash tools/qa.sh --scope static-security
""",
        encoding="utf-8",
    )

    qa_wrapper = workflows_dir / "qa.yml"
    qa_wrapper.write_text(
        """
name: QA
permissions:
  contents: read
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
permissions:
  contents: read
jobs:
  quality:
    uses: ./.github/workflows/reusable-quality.yml
""",
        encoding="utf-8",
    )

    qa_commands = "\n".join(check_ci_workflow_contract.CRITICAL_COMMANDS.values())
    (tools_dir / "qa.sh").write_text(
        f"#!/usr/bin/env bash\n{qa_commands}\n", encoding="utf-8"
    )

    (tmp_path / "noxfile.py").write_text(
        """
import nox


@nox.session(name="qa")
def qa(session):
    session.run("bash", "tools/qa.sh")
""",
        encoding="utf-8",
    )

    docs_workflow = workflows_dir / "docs.yml"
    docs_workflow.write_text(
        """
name: Docs
on:
  pull_request:
    branches:
      - main
      - develop
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/configure-pages@v4
      - run: mkdocs build --strict --site-dir site
      - uses: actions/upload-pages-artifact@v3
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/deploy-pages@v4
""",
        encoding="utf-8",
    )

    perf_workflow = workflows_dir / "perf.yml"
    perf_workflow.write_text(
        """
name: Perf
jobs:
  perf:
    runs-on: ubuntu-latest
    steps:
      - run: |
          pip install -r requirements-dev.txt
      - run: |
          python -m pytest -m perf -o addopts=
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
    monkeypatch.setattr(
        check_ci_workflow_contract, "README_DOC", tmp_path / "README.md"
    )
    monkeypatch.setattr(
        check_ci_workflow_contract, "TOOLING_DOC", docs_dir / "tooling.md"
    )
    pytest_ini = tmp_path / "pytest.ini"
    pytest_ini.write_text('addopts = -m "not perf"\n', encoding="utf-8")

    monkeypatch.setattr(check_ci_workflow_contract, "DOCS_WORKFLOW", docs_workflow)
    monkeypatch.setattr(check_ci_workflow_contract, "PERF_WORKFLOW", perf_workflow)
    monkeypatch.setattr(check_ci_workflow_contract, "PYTEST_INI", pytest_ini)
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
        "docs_workflow": docs_workflow,
        "perf_workflow": perf_workflow,
        "readme": tmp_path / "README.md",
        "tooling": docs_dir / "tooling.md",
    }


def test_extract_workflow_references_detects_all_mentions() -> None:
    text = """
    revisar .github/workflows/qa.yml y .github/workflows/quality.yaml
    además de .github/workflows/reusable-quality.yml y .github/workflows/docs.yaml
    """

    refs = check_ci_workflow_contract.extract_workflow_references(text)

    assert refs == {
        ".github/workflows/qa.yml",
        ".github/workflows/quality.yaml",
        ".github/workflows/reusable-quality.yml",
        ".github/workflows/docs.yaml",
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


def test_load_workflow_run_commands_by_job_scopes_commands_per_job(
    tmp_path: Path,
) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        """
name: Example
jobs:
  build:
    steps:
      - run: |
          mkdocs build --strict
  deploy:
    steps:
      - run: echo deploy
""",
        encoding="utf-8",
    )

    commands = check_ci_workflow_contract.load_workflow_run_commands_by_job(workflow)

    assert commands["build"] == ["mkdocs build --strict"]
    assert commands["deploy"] == ["echo deploy"]


def test_load_workflow_run_commands_for_jobs_filters_requested_jobs(
    tmp_path: Path,
) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        """
name: Example
jobs:
  build:
    steps:
      - run: mkdocs build --strict
  deploy:
    steps:
      - run: echo deploy
  perf:
    steps:
      - run: python -m pytest -m perf
""",
        encoding="utf-8",
    )

    commands = check_ci_workflow_contract.load_workflow_run_commands_for_jobs(
        workflow, ("build", "perf")
    )

    assert commands == {
        "build": ["mkdocs build --strict"],
        "perf": ["python -m pytest -m perf"],
    }


def test_validate_workflow_permissions_passes_with_workflow_level_permissions(
    contract_env: dict[str, Path],
) -> None:
    errors = check_ci_workflow_contract.validate_workflow_permissions(
        contract_env["qa_wrapper"]
    )

    assert errors == []


def test_validate_workflow_permissions_fails_without_permissions(
    contract_env: dict[str, Path],
) -> None:
    workflow = contract_env["workflows_dir"] / "missing-permissions.yml"
    workflow.write_text(
        """
name: Missing Permissions
jobs:
  qa:
    uses: ./.github/workflows/reusable-quality.yml
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_workflow_permissions(workflow)

    assert any("permissions.contents: read" in error for error in errors)


def test_validate_workflow_permissions_fails_if_job_permissions_are_incomplete(
    contract_env: dict[str, Path],
) -> None:
    workflow = contract_env["workflows_dir"] / "job-permissions-incomplete.yml"
    workflow.write_text(
        """
name: Job Permissions Incomplete
jobs:
  qa:
    permissions:
      contents: read
    uses: ./.github/workflows/reusable-quality.yml
  lint:
    uses: ./.github/workflows/reusable-quality.yml
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_workflow_permissions(workflow)

    assert any("jobs ['lint']" in error for error in errors)


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

    assert any(
        "debe delegar en ./.github/workflows/reusable-quality.yml" in error
        for error in errors
    )


def test_validate_wrapper_workflow_fails_with_wrong_uses_and_main_job_broken(
    contract_env: dict[str, Path],
) -> None:
    wrapper = contract_env["workflows_dir"] / "wrapper-wrong-uses.yml"
    wrapper.write_text(
        """
name: Wrapper
jobs:
  qa:
    uses: ./.github/workflows/other.yml
  main:
    runs-on: ubuntu-latest
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_wrapper_workflow(wrapper)

    assert any(
        "debe delegar en ./.github/workflows/reusable-quality.yml" in error
        for error in errors
    )


def test_validate_wrapper_workflow_fails_if_uses_only_in_comment_or_string(
    contract_env: dict[str, Path],
) -> None:
    wrapper = contract_env["workflows_dir"] / "wrapper-comment-string-uses.yml"
    wrapper.write_text(
        """
name: Wrapper
jobs:
  qa:
    name: "uses: ./.github/workflows/reusable-quality.yml"
    runs-on: ubuntu-latest
    # uses: ./.github/workflows/reusable-quality.yml
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_wrapper_workflow(wrapper)

    assert any(
        "debe delegar en ./.github/workflows/reusable-quality.yml" in error
        for error in errors
    )


def test_validate_wrapper_workflow_passes_with_minimal_valid_wrapper(
    contract_env: dict[str, Path],
) -> None:
    wrapper = contract_env["workflows_dir"] / "wrapper-minimal-valid.yml"
    wrapper.write_text(
        """
name: Wrapper
jobs:
  qa:
    uses: ./.github/workflows/reusable-quality.yml
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_wrapper_workflow(wrapper)

    assert errors == []


def test_validate_wrapper_workflow_fails_when_only_one_job_delegates(
    contract_env: dict[str, Path],
) -> None:
    wrapper = contract_env["workflows_dir"] / "wrapper-multi-jobs-partial.yml"
    wrapper.write_text(
        """
name: Wrapper
jobs:
  qa:
    uses: ./.github/workflows/reusable-quality.yml
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: echo local
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_wrapper_workflow(wrapper)

    assert any(
        "debe delegar en ./.github/workflows/reusable-quality.yml" in error
        for error in errors
    )
    assert any("no debe definir steps locales" in error for error in errors)


def test_validate_critical_commands_sync_fails_when_workflow_qa_and_docs_drift(
    contract_env: dict[str, Path],
) -> None:
    contract_env["reusable"].write_text(
        contract_env["reusable"]
        .read_text(encoding="utf-8")
        .replace("run: bash tools/qa.sh --scope tests-matrix", "run: echo skipped"),
        encoding="utf-8",
    )

    missing_command = check_ci_workflow_contract.CRITICAL_COMMANDS["ruff"]
    contract_env["qa_script"].write_text(
        contract_env["qa_script"]
        .read_text(encoding="utf-8")
        .replace(f"{missing_command}\n", ""),
        encoding="utf-8",
    )
    contract_env["tooling"].write_text(
        contract_env["tooling"]
        .read_text(encoding="utf-8")
        .replace(f"{missing_command}\n", ""),
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_critical_commands_sync()

    assert (
        "reusable-quality.yml job 'tests-matrix' debe ejecutar exactamente 'bash tools/qa.sh --scope tests-matrix'."
        in errors
    )
    assert any(
        "tools/qa.sh no incluye comando crítico de ruff" in error for error in errors
    )
    assert any(
        "docs/tooling.md no documenta comando crítico de ruff" in error
        for error in errors
    )


def test_load_workflow_run_commands_supports_inline_and_block_with_spacing_variants(
    contract_env: dict[str, Path],
) -> None:
    workflow = contract_env["workflows_dir"] / "spacing-variants.yml"
    workflow.write_text(
        """
name: Spacing
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - run:   python   -m   pytest
      - run: |
          python  -m  ruff   check .
      -
        run: |
          python -m mypy fletplus
      -
        run:    python   tools/check_github_workflows.py
""",
        encoding="utf-8",
    )

    commands = check_ci_workflow_contract.load_workflow_run_commands(workflow)

    assert "python -m pytest" in commands
    assert "python -m ruff check ." in commands
    assert "python -m mypy fletplus" in commands
    assert "python tools/check_github_workflows.py" in commands


def test_validate_critical_commands_sync_allows_whitespace_normalization_in_qa_script(
    contract_env: dict[str, Path],
) -> None:
    qa_content = contract_env["qa_script"].read_text(encoding="utf-8")
    contract_env["qa_script"].write_text(
        qa_content.replace(
            "python tools/check_github_workflows.py",
            "python    tools/check_github_workflows.py",
        ),
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_critical_commands_sync()

    assert not any(
        "comando crítico de workflow-validation" in error for error in errors
    )


def test_validate_critical_commands_sync_requires_exact_qa_invocation(
    contract_env: dict[str, Path],
) -> None:
    contract_env["reusable"].write_text(
        contract_env["reusable"]
        .read_text(encoding="utf-8")
        .replace(
            "run: bash tools/qa.sh --scope tests-matrix",
            "run: bash ./tools/qa.sh --scope tests-matrix",
        ),
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_critical_commands_sync()

    assert (
        "reusable-quality.yml job 'tests-matrix' debe ejecutar exactamente 'bash tools/qa.sh --scope tests-matrix'."
        in errors
    )


def test_validate_critical_commands_sync_flags_duplicate_qa_invocation(
    contract_env: dict[str, Path],
) -> None:
    contract_env["reusable"].write_text(
        """
name: Reusable Quality
jobs:
  tests-matrix:
    runs-on: ubuntu-latest
    steps:
      - run: bash tools/qa.sh --scope tests-matrix
      - run: echo helper
      - run: bash tools/qa.sh --scope tests-matrix
  static-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: bash tools/qa.sh --scope static-security
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_critical_commands_sync()

    assert (
        "reusable-quality.yml debe invocar 'bash tools/qa.sh --scope tests-matrix' una única vez."
        in errors
    )


def test_validate_critical_commands_sync_accepts_single_qa_invocation_with_aux_steps(
    contract_env: dict[str, Path],
) -> None:
    contract_env["reusable"].write_text(
        """
name: Reusable Quality
jobs:
  tests-matrix:
    runs-on: ubuntu-latest
    steps:
      - run: echo setup
      - run: bash tools/qa.sh --scope tests-matrix
      - run: echo cleanup
  static-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: bash tools/qa.sh --scope static-security
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_critical_commands_sync()

    assert (
        "reusable-quality.yml job 'tests-matrix' debe ejecutar exactamente 'bash tools/qa.sh --scope tests-matrix'."
        not in errors
    )
    assert (
        "reusable-quality.yml debe invocar 'bash tools/qa.sh --scope tests-matrix' una única vez."
        not in errors
    )


def test_validate_critical_commands_sync_requires_static_security_job(
    contract_env: dict[str, Path],
) -> None:
    contract_env["reusable"].write_text(
        """
name: Reusable Quality
jobs:
  tests-matrix:
    runs-on: ubuntu-latest
    steps:
      - run: bash tools/qa.sh --scope tests-matrix
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_critical_commands_sync()

    assert (
        "reusable-quality.yml debe definir el job contractual 'static-security'."
        in errors
    )


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


def test_validate_workflow_references_fails_for_missing_doc_reference_yaml(
    contract_env: dict[str, Path],
) -> None:
    contract_env["readme"].write_text(
        contract_env["readme"].read_text(encoding="utf-8")
        + "\n.github/workflows/missing-workflow.yaml\n",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_workflow_references()

    assert errors == [
        "Workflow referenciado en docs no existe: .github/workflows/missing-workflow.yaml"
    ]


def test_validate_docs_workflow_contract_passes_with_required_jobs_and_actions(
    contract_env: dict[str, Path],
) -> None:
    contract_env["docs_workflow"].write_text(
        """
name: Docs
on:
  pull_request:
    branches:
      - main
      - develop
jobs:
    build:
      runs-on: ubuntu-latest
      steps:
        - name: Setup pages
          uses: actions/configure-pages@v4
        - name: Build docs
          run: mkdocs build --strict --site-dir site
        -
          name: Upload artifact
          uses: actions/upload-pages-artifact@v3
    deploy:
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      runs-on: ubuntu-latest
      needs: build
      steps:
        - name: Deploy
          uses: actions/deploy-pages@v4
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_docs_workflow_contract(
        contract_env["docs_workflow"]
    )

    assert errors == []


def test_validate_docs_workflow_contract_passes_when_deploy_needs_is_list(
    contract_env: dict[str, Path],
) -> None:
    contract_env["docs_workflow"].write_text(
        """
name: Docs
on:
  pull_request:
    branches:
      - main
      - develop
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/configure-pages@v4
      - run: mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs:
      - lint
      - build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/deploy-pages@v4
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_docs_workflow_contract(
        contract_env["docs_workflow"]
    )

    assert errors == []


def test_validate_docs_workflow_contract_fails_when_required_action_is_missing(
    contract_env: dict[str, Path],
) -> None:
    contract_env["docs_workflow"].write_text(
        """
name: Docs
on:
  pull_request:
    branches:
      - main
      - develop
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/configure-pages@v4
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo deploy
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_docs_workflow_contract(
        contract_env["docs_workflow"]
    )

    assert any(
        "build' debe usar actions/upload-pages-artifact" in error for error in errors
    )
    assert any("deploy' debe usar actions/deploy-pages" in error for error in errors)


def test_validate_docs_workflow_contract_fails_when_triggers_or_deploy_guard_are_missing(
    contract_env: dict[str, Path],
) -> None:
    contract_env["docs_workflow"].write_text(
        """
name: Docs
on:
  push:
    branches:
      - main
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/configure-pages@v4
      - run: mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/deploy-pages@v4
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_docs_workflow_contract(
        contract_env["docs_workflow"]
    )

    assert any("debe definir trigger pull_request" in error for error in errors)
    assert any("debe limitarse a push en main" in error for error in errors)


def test_validate_docs_workflow_contract_fails_when_mkdocs_strict_is_in_wrong_job(
    contract_env: dict[str, Path],
) -> None:
    contract_env["docs_workflow"].write_text(
        """
name: Docs
on:
  pull_request:
    branches:
      - main
      - develop
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/configure-pages@v4
      - uses: actions/upload-pages-artifact@v3
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: mkdocs build --strict
      - uses: actions/deploy-pages@v4
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_docs_workflow_contract(
        contract_env["docs_workflow"]
    )

    assert any(
        "job 'build' debe ejecutar mkdocs build --strict" in error for error in errors
    )


def test_validate_docs_workflow_contract_fails_when_build_command_exists_only_in_unknown_job(
    contract_env: dict[str, Path],
) -> None:
    contract_env["docs_workflow"].write_text(
        """
name: Docs
on:
  pull_request:
    branches:
      - main
      - develop
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/configure-pages@v4
      - uses: actions/upload-pages-artifact@v3
  verify:
    runs-on: ubuntu-latest
    steps:
      - run: mkdocs build --strict
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/deploy-pages@v4
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_docs_workflow_contract(
        contract_env["docs_workflow"]
    )

    assert any(
        "job 'build' debe ejecutar mkdocs build --strict" in error for error in errors
    )


def test_validate_perf_workflow_contract_passes_when_deps_and_perf_pytest_exist(
    contract_env: dict[str, Path],
) -> None:
    errors = check_ci_workflow_contract.validate_perf_workflow_contract(
        contract_env["perf_workflow"]
    )

    assert errors == []


def test_validate_perf_workflow_contract_fails_when_required_commands_are_missing(
    contract_env: dict[str, Path],
) -> None:
    contract_env["perf_workflow"].write_text(
        """
name: Perf
jobs:
  perf:
    runs-on: ubuntu-latest
    steps:
      - run: echo no-op
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_perf_workflow_contract(
        contract_env["perf_workflow"]
    )

    assert any("pip install -r requirements-dev.txt" in error for error in errors)
    assert any("python -m pytest -m perf" in error for error in errors)


def test_validate_perf_workflow_contract_fails_when_addopts_override_is_missing(
    contract_env: dict[str, Path],
) -> None:
    contract_env["perf_workflow"].write_text(
        """
name: Perf
jobs:
  perf:
    runs-on: ubuntu-latest
    steps:
      - run: |
          pip install -r requirements-dev.txt
      - run: |
          python -m pytest -m perf
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_perf_workflow_contract(
        contract_env["perf_workflow"]
    )

    assert any("python -m pytest -m perf -o addopts=" in error for error in errors)


def test_validate_perf_workflow_contract_passes_without_addopts_override_when_pytest_ini_does_not_exclude_perf(
    contract_env: dict[str, Path],
) -> None:
    (contract_env["tmp_path"] / "pytest.ini").write_text(
        """
[pytest]
addopts = -ra
""",
        encoding="utf-8",
    )
    contract_env["perf_workflow"].write_text(
        """
name: Perf
jobs:
  perf:
    runs-on: ubuntu-latest
    steps:
      - run: |
          pip install -r requirements-dev.txt
      - run: |
          python -m pytest -m perf
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_perf_workflow_contract(
        contract_env["perf_workflow"]
    )

    assert errors == []


def test_validate_perf_workflow_contract_fails_when_required_commands_are_in_wrong_job(
    contract_env: dict[str, Path],
) -> None:
    contract_env["perf_workflow"].write_text(
        """
name: Perf
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          pip install -r requirements-dev.txt
      - run: |
          pytest -m perf -o addopts=
  perf:
    runs-on: ubuntu-latest
    steps:
      - run: echo only-perf-shell
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_perf_workflow_contract(
        contract_env["perf_workflow"]
    )

    assert any("pip install -r requirements-dev.txt" in error for error in errors)
    assert any(
        "falta el comando requerido en perf workflow: pytest" in error
        for error in errors
    )
    assert any("python -m pytest -m perf" in error for error in errors)


def test_validate_perf_workflow_contract_fails_when_perf_job_is_missing(
    contract_env: dict[str, Path],
) -> None:
    contract_env["perf_workflow"].write_text(
        """
name: Perf
jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - run: |
          pip install -r requirements-dev.txt
      - run: |
          python -m pytest -m perf -o addopts=
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_perf_workflow_contract(
        contract_env["perf_workflow"]
    )

    assert any("pip install -r requirements-dev.txt" in error for error in errors)
    assert any(
        "falta el comando requerido en perf workflow: pytest" in error
        for error in errors
    )
    assert any("python -m pytest -m perf" in error for error in errors)


def test_validate_perf_workflow_contract_fails_when_pytest_exists_only_outside_perf_job(
    contract_env: dict[str, Path],
) -> None:
    contract_env["perf_workflow"].write_text(
        """
name: Perf
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: pytest -m perf -o addopts=
  perf:
    runs-on: ubuntu-latest
    steps:
      - run: pip install -r requirements-dev.txt
      - run: echo benchmark
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_perf_workflow_contract(
        contract_env["perf_workflow"]
    )

    assert any(
        "falta el comando requerido en perf workflow: pytest" in error
        for error in errors
    )
    assert any("python -m pytest -m perf" in error for error in errors)


def test_validate_perf_workflow_contract_fails_when_only_plain_pytest_exists(
    contract_env: dict[str, Path],
) -> None:
    contract_env["perf_workflow"].write_text(
        """
name: Perf
jobs:
  perf:
    runs-on: ubuntu-latest
    steps:
      - run: pip install -r requirements-dev.txt
      - run: pytest
""",
        encoding="utf-8",
    )

    errors = check_ci_workflow_contract.validate_perf_workflow_contract(
        contract_env["perf_workflow"]
    )

    assert not any(
        "falta el comando requerido en perf workflow: pytest" in error
        for error in errors
    )
    assert any("python -m pytest -m perf" in error for error in errors)


def test_validate_flet_baseline_target_contract_passes_when_synced(
    contract_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract_env["reusable"].write_text(
        contract_env["reusable"].read_text(encoding="utf-8")
        + """
  flet-version-matrix:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - label: min-supported
            flet-spec: flet>=0.28,<0.29
            expected-minor: "0.28"
          - label: latest-migration-target
            flet-spec: flet>=0.80,<0.81
            expected-minor: "0.80"
""",
        encoding="utf-8",
    )

    (contract_env["tmp_path"] / "tools" / "flet_version_matrix_config.py").write_text(
        'FLET_MATRIX_MINORS: tuple[str, ...] = ("0.28", "0.80")\n',
        encoding="utf-8",
    )
    (contract_env["tmp_path"] / "docs" / "migration-flet-latest.md").write_text(
        """
**Versión mínima soportada (estado actual)**: `flet>=0.28,<0.29`
**Versión objetivo de migración (estado objetivo)**: `flet>=0.80,<0.81`
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        check_ci_workflow_contract,
        "FLET_MATRIX_CONFIG",
        contract_env["tmp_path"] / "tools" / "flet_version_matrix_config.py",
    )
    monkeypatch.setattr(
        check_ci_workflow_contract,
        "MIGRATION_DOC",
        contract_env["tmp_path"] / "docs" / "migration-flet-latest.md",
    )

    errors = check_ci_workflow_contract.validate_flet_baseline_target_contract()

    assert errors == []


def test_validate_flet_baseline_target_contract_fails_when_docs_drift(
    contract_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract_env["reusable"].write_text(
        contract_env["reusable"].read_text(encoding="utf-8")
        + """
  flet-version-matrix:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - label: min-supported
            flet-spec: flet>=0.28,<0.29
            expected-minor: "0.28"
          - label: latest-migration-target
            flet-spec: flet>=0.80,<0.81
            expected-minor: "0.80"
""",
        encoding="utf-8",
    )

    (contract_env["tmp_path"] / "tools" / "flet_version_matrix_config.py").write_text(
        'FLET_MATRIX_MINORS: tuple[str, ...] = ("0.28", "0.80")\n',
        encoding="utf-8",
    )
    (contract_env["tmp_path"] / "docs" / "migration-flet-latest.md").write_text(
        """
**Versión mínima soportada (estado actual)**: `flet>=0.28,<0.29`
**Versión objetivo de migración (estado objetivo)**: `flet>=0.79,<0.80`
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        check_ci_workflow_contract,
        "FLET_MATRIX_CONFIG",
        contract_env["tmp_path"] / "tools" / "flet_version_matrix_config.py",
    )
    monkeypatch.setattr(
        check_ci_workflow_contract,
        "MIGRATION_DOC",
        contract_env["tmp_path"] / "docs" / "migration-flet-latest.md",
    )

    errors = check_ci_workflow_contract.validate_flet_baseline_target_contract()

    assert any(
        "workflow y docs/migration-flet-latest.md no coinciden" in e for e in errors
    )


def test_validate_flet_baseline_target_contract_fails_when_flet_spec_drift(
    contract_env: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract_env["reusable"].write_text(
        contract_env["reusable"].read_text(encoding="utf-8")
        + """
  flet-version-matrix:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - label: min-supported
            flet-spec: flet>=0.28,<0.30
            expected-minor: "0.28"
          - label: latest-migration-target
            flet-spec: flet>=0.80,<0.81
            expected-minor: "0.80"
""",
        encoding="utf-8",
    )

    (contract_env["tmp_path"] / "tools" / "flet_version_matrix_config.py").write_text(
        'FLET_MATRIX_MINORS: tuple[str, ...] = ("0.28", "0.80")\n',
        encoding="utf-8",
    )
    (contract_env["tmp_path"] / "docs" / "migration-flet-latest.md").write_text(
        """
**Baseline de validación (estado actual en CI)**: `flet>=0.28,<0.29`
**Versión objetivo de migración (estado objetivo en CI)**: `flet>=0.80,<0.81`
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        check_ci_workflow_contract,
        "FLET_MATRIX_CONFIG",
        contract_env["tmp_path"] / "tools" / "flet_version_matrix_config.py",
    )
    monkeypatch.setattr(
        check_ci_workflow_contract,
        "MIGRATION_DOC",
        contract_env["tmp_path"] / "docs" / "migration-flet-latest.md",
    )

    errors = check_ci_workflow_contract.validate_flet_baseline_target_contract()

    assert any("debe derivar flet-spec exactamente" in e for e in errors)
