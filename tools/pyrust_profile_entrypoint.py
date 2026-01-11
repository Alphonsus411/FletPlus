"""Punto de entrada para perfilar flujos representativos de FletPlus."""
from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path) -> ModuleType:
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el módulo desde {path}")
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _exercise_device_profiles(module: ModuleType) -> None:
    for width in (320, 480, 640, 800, 1024, 1366, 1600, 1920):
        module.columns_for_width(width)
        module.device_name(width)


def _exercise_breakpoints(module: ModuleType) -> None:
    registry = module.BreakpointRegistry
    registry.configure(xs=0, sm=480, md=768, lg=1024, xl=1280)
    registry.normalize({"xs": 1, "md": 2, 1440: 3})
    registry.collect_breakpoints({"sm": 1, "lg": 2}, {480: 3, "xl": 4})


def main() -> None:
    device_profiles = _load_module(
        "pyrust_device_profiles",
        REPO_ROOT / "fletplus" / "utils" / "device_profiles.py",
    )
    responsive_breakpoints = _load_module(
        "pyrust_responsive_breakpoints",
        REPO_ROOT / "fletplus" / "utils" / "responsive_breakpoints.py",
    )
    _exercise_device_profiles(device_profiles)
    _exercise_breakpoints(responsive_breakpoints)


if __name__ == "__main__":
    main()
