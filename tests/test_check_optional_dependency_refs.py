from __future__ import annotations

from tools.check_optional_dependency_refs import _find_referenced_extras


def test_find_referenced_extras_simple_valid() -> None:
    content = "pip install .[build]"
    assert _find_referenced_extras(content) == {"build"}


def test_find_referenced_extras_multiple_valid() -> None:
    content = "python -m pip install .[dev,qa,cli]"
    assert _find_referenced_extras(content) == {"dev", "qa", "cli"}


def test_find_referenced_extras_with_invalid_combination() -> None:
    content = "pip install .[dev,does-not-exist,cli]"
    assert _find_referenced_extras(content) == {"dev", "does-not-exist", "cli"}


def test_find_referenced_extras_with_quotes_and_editable() -> None:
    content = "\n".join(
        [
            'pip install ".[dev, qa]"',
            'pip install "fletplus[dev]"',
            "pip install -e .[cli]",
        ]
    )
    assert _find_referenced_extras(content) == {"dev", "qa", "cli"}
