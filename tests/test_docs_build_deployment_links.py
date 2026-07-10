from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_build_installer_deployment_docs_are_indexed() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    docs_index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")

    expected = {
        "docs/building.md": "building.md",
        "docs/installer.md": "installer.md",
        "docs/deployment.md": "deployment.md",
    }

    for path, relative_link in expected.items():
        assert (ROOT / path).is_file()
        assert relative_link in readme
        assert relative_link in docs_index


def test_building_doc_covers_required_build_targets() -> None:
    building = (ROOT / "docs" / "building.md").read_text(encoding="utf-8")

    for heading in (
        "## Build full-stack",
        "## Build Windows",
        "## Build macOS",
        "## Build Linux",
        "## Build web",
        "## Limitaciones de cross-compilation",
    ):
        assert heading in building

    for command in (
        "fletplus build --target web",
        "fletplus build --target windows",
        "fletplus build --target macos",
        "fletplus build --target linux",
        "fletplus create my-saas --template fullstack",
    ):
        assert command in building


def test_installer_and_deployment_docs_include_cli_examples() -> None:
    installer = (ROOT / "docs" / "installer.md").read_text(encoding="utf-8")
    deployment = (ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")

    for command in (
        "fletplus installer --target linux",
        "fletplus installer --target macos",
        "fletplus installer --target windows --include-bat",
        "fletplus installer --target web",
    ):
        assert command in installer or command in deployment

    assert "fletplus create my-product --template fullstack" in deployment
    assert "fletplus build --target web" in deployment
