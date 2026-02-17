"""Smoke tests para verificar firmas públicas de plantilla CLI y demo."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(module_name, None)


def test_cli_template_main_smoke_signature() -> None:
    template_main = (
        PROJECT_ROOT / "fletplus" / "cli" / "templates" / "app" / "src" / "main.py"
    )
    module = _load_module_from_path("_fletplus_template_main", template_main)

    assert hasattr(module, "main")
    signature = inspect.signature(module.main)
    params = list(signature.parameters.values())

    assert len(params) == 1
    assert params[0].name == "page"


def test_demo_app_exports_and_signatures_smoke() -> None:
    demo_module = _load_module_from_path(
        "_fletplus_demo_app", PROJECT_ROOT / "fletplus_demo" / "app.py"
    )

    assert hasattr(demo_module, "DEMO_ROUTES")
    assert hasattr(demo_module, "create_app")
    assert hasattr(demo_module, "main")
    assert hasattr(demo_module, "run")

    create_app_sig = inspect.signature(demo_module.create_app)
    create_app_params = list(create_app_sig.parameters.values())
    assert len(create_app_params) == 1
    assert create_app_params[0].name == "page"

    main_sig = inspect.signature(demo_module.main)
    main_params = list(main_sig.parameters.values())
    assert len(main_params) == 1
    assert main_params[0].name == "page"

    run_sig = inspect.signature(demo_module.run)
    run_params = list(run_sig.parameters.values())
    assert len(run_params) == 1
    assert run_params[0].name == "argv"


def test_demo_module_importable_as_package_submodule() -> None:
    sys.modules.pop("fletplus_demo.app", None)
    imported = __import__("fletplus_demo.app", fromlist=["*"])

    assert imported.__name__ == "fletplus_demo.app"
    assert callable(imported.main)
