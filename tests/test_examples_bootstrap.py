"""Pruebas para verificar que los ejemplos funcionan sin instalar el paquete."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_EXAMPLES = [
    ("examples.buttons_examples", "buttons_examples.py"),
    ("examples.layouts_examples", "layouts_examples.py"),
    ("examples.responsive_container_example", "responsive_container_example.py"),
]


def _load_example(module_name: str, file_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec and spec.loader  # Asegura que el módulo es cargable
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules.pop(module_name, None)


@pytest.mark.parametrize("module_name, relative_path", _EXAMPLES)
def test_examples_bootstrap_adds_project_root(monkeypatch, module_name, relative_path):
    project_root = Path(__file__).resolve().parent.parent
    example_dir = project_root / "examples"

    filtered_path = [
        entry
        for entry in sys.path
        if Path(entry or ".").resolve() != project_root
    ]
    filtered_path.insert(0, str(example_dir))

    monkeypatch.setattr(sys, "path", filtered_path, raising=False)

    _load_example(module_name, example_dir / relative_path)

    assert str(project_root) in sys.path
