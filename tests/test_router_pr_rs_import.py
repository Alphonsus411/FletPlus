from __future__ import annotations

import os

import pytest


REQUIRE_NATIVE = os.getenv("FLETPPLUS_REQUIRE_ROUTER_PR_RS_NATIVE", "0") == "1"

if not REQUIRE_NATIVE:
    pytest.skip(
        "No se exige router_pr_rs._native en este entorno.",
        allow_module_level=True,
    )


def test_router_pr_rs_native_module_available() -> None:
    try:
        import fletplus.router.router_pr_rs._native as native  # type: ignore
    except Exception as exc:  # pragma: no cover - el fallo se reporta en release
        pytest.fail(
            f"No se pudo importar fletplus.router.router_pr_rs._native: {exc}"
        )

    assert hasattr(native, "_match")
