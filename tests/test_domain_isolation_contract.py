"""Contrato de aislamiento por dominio (core moderna vs core legacy).

Motivación: la revisión de ingeniería documentó una regresión por *imports
cruzados*: tests que ejercitaban la API legacy (`build()`, `theme`, rutas,
sidebar) obteniendo `FletPlusApp` de la core moderna (`fletplus.core`), cuya
firma es incompatible.

Este meta-test verifica de forma estática:

1. `pytest.ini` declara los markers `domain_core` y `domain_legacy`.
2. Cada módulo de test que ejercita **una única** core declara el marker que
   le corresponde vía `pytestmark`.
3. Un módulo que importa ambas cores está listado explícitamente en
   `CROSS_DOMAIN_MODULES` (cruce deliberado y revisable).
"""

from __future__ import annotations

import ast
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
PYTEST_INI = TESTS_ROOT.parent / "pytest.ini"
LEGACY_PACKAGE = "fletplus.core_legacy"
CORE_PACKAGE = "fletplus.core"
MARKER_BY_DOMAIN = {"legacy": "domain_legacy", "core": "domain_core"}
DOMAIN_MARKERS = frozenset(MARKER_BY_DOMAIN.values())
CROSS_DOMAIN_MODULES = frozenset({"test_all.py", "test_fletplus_app.py"})


def _test_files() -> list[Path]:
    return sorted(
        path for path in TESTS_ROOT.rglob("test_*.py") if path.name != Path(__file__).name
    )


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imported_roots(tree: ast.Module) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module)
    return roots


def _domains(roots: set[str]) -> set[str]:
    domains: set[str] = set()
    for root in roots:
        if root == LEGACY_PACKAGE or root.startswith(f"{LEGACY_PACKAGE}."):
            domains.add("legacy")
        elif root == CORE_PACKAGE or root.startswith(f"{CORE_PACKAGE}."):
            domains.add("core")
    return domains


def _marker_names(value: ast.expr) -> set[str]:
    elements = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
    names: set[str] = set()
    for element in elements:
        if (
            isinstance(element, ast.Attribute)
            and isinstance(element.value, ast.Attribute)
            and element.value.attr == "mark"
        ):
            names.add(element.attr)
    return names


def _declared_markers(tree: ast.Module) -> set[str]:
    markers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark"
            for target in node.targets
        ):
            markers |= _marker_names(node.value)
    return markers


def test_domain_markers_are_declared_in_pytest_ini() -> None:
    config = PYTEST_INI.read_text(encoding="utf-8")
    missing = [f"{marker}:" for marker in sorted(DOMAIN_MARKERS) if f"{marker}:" not in config]
    assert not missing, f"Faltan markers en pytest.ini: {missing}"


def test_single_domain_modules_declare_their_marker() -> None:
    problems: list[str] = []
    for path in _test_files():
        tree = _tree(path)
        domains = _domains(_imported_roots(tree))
        if len(domains) != 1:
            continue
        expected = MARKER_BY_DOMAIN[next(iter(domains))]
        declared = _declared_markers(tree) & DOMAIN_MARKERS
        if declared != {expected}:
            problems.append(
                f"{path.name}: esperaba `{expected}`, declaró {sorted(declared) or '[]'}"
            )
    assert not problems, "Módulos de dominio sin etiquetar correctamente:\n" + "\n".join(
        problems
    )


def test_cross_domain_modules_are_explicit() -> None:
    detected: dict[str, set[str]] = {}
    for path in _test_files():
        tree = _tree(path)
        domains = _domains(_imported_roots(tree))
        if len(domains) > 1:
            detected[path.name] = _declared_markers(tree) & DOMAIN_MARKERS
    assert set(detected) == set(CROSS_DOMAIN_MODULES), (
        "Los cruces de dominio deben ser explícitos: "
        f"detectados={sorted(detected)}, declarados={sorted(CROSS_DOMAIN_MODULES)}"
    )
    con_marker = {name for name, markers in detected.items() if markers}
    assert not con_marker, f"Los módulos de cruce no deben declarar marker de dominio: {sorted(con_marker)}"
