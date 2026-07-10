from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PROFILE_EXTRAS = {"fullstack", "installer", "web-deploy", "desktop-build"}


def _pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_documented_profile_extras_exist_in_pyproject() -> None:
    optional = _pyproject()["project"]["optional-dependencies"]
    building = (ROOT / "docs" / "building.md").read_text(encoding="utf-8")

    assert REQUIRED_PROFILE_EXTRAS <= set(optional)
    for extra in REQUIRED_PROFILE_EXTRAS:
        assert f"`{extra}`" in building
        assert optional[extra], f"El extra {extra} no debe quedar vacío"


def test_rust_modules_declared_in_pyproject_are_covered_by_makefile() -> None:
    pyproject = _pyproject()
    manifests = {
        module["manifest-path"]
        for module in pyproject["tool"]["pyrust-native"]["modules"]
    }
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    missing = sorted(manifest for manifest in manifests if manifest not in makefile)
    assert missing == []


def test_cython_package_data_is_covered_by_build_config() -> None:
    pyproject = _pyproject()
    package_data = pyproject["tool"]["setuptools"]["package-data"]
    cython_c_files = {
        f"{package.replace('.', '/')}/{filename}"
        for package, filenames in package_data.items()
        for filename in filenames
        if filename.endswith(".c")
    }
    build_config = (ROOT / "build_config.yaml").read_text(encoding="utf-8")
    pyx_files = {path.replace(".c", ".pyx") for path in cython_c_files}

    missing = sorted(path for path in pyx_files if path not in build_config)
    assert missing == []
