"""Benchmarks ligeros para validar `_match` en Rust frente a Python."""

from __future__ import annotations

import time

import pytest

from fletplus.router import Route, Router
from fletplus.router import router as router_mod

router_rs = pytest.importorskip("fletplus.router.router_rs")

if router_rs._match is None:  # pragma: no cover - entorno sin compilación Rust
    pytest.skip("backend Rust no disponible", allow_module_level=True)


def _build_branching_router() -> Router:
    return Router(
        [
            Route(path="/", view=lambda match: match.path),
            Route(
                path="/library",
                children=[
                    Route(path="books/<book_id>", view=lambda match: match.path),
                    Route(
                        path="books/<book_id>/chapters/<chapter_id>",
                        view=lambda match: match.path,
                    ),
                ],
            ),
            Route(path="/authors/<author_id>", view=lambda match: match.path),
        ]
    )


def _normalize(results):
    return [(node.full_path, params) for node, params in results[0]] if results else []


@pytest.mark.perf
@pytest.mark.parametrize("repeats", [200])
def test_rust_match_benchmark_against_python(repeats: int, capsys: pytest.CaptureFixture[str]):
    router = _build_branching_router()
    paths = [
        "/library/books/10",
        "/library/books/10/chapters/3",
        "/authors/99",
    ]

    # Validación de que ambos backends producen el mismo resultado
    for path in paths:
        assert _normalize(router_rs._match(router._root, path)) == _normalize(
            router_mod._match_py(router._root, path)
        )

    def measure(func):
        start = time.perf_counter()
        for _ in range(repeats):
            for path in paths:
                func(router._root, path)
        return (time.perf_counter() - start) / (repeats * len(paths))

    rust_avg = measure(router_rs._match)
    python_avg = measure(router_mod._match_py)

    assert rust_avg > 0 and python_avg > 0
    assert rust_avg <= python_avg * 1.5

    print(
        "Rust vs Python match (s):",
        {"rust_avg": rust_avg, "python_avg": python_avg, "paths": len(paths), "repeats": repeats},
    )
    captured = capsys.readouterr()
    assert "rust_avg" in captured.out
