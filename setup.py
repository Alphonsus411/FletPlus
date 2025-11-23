import json
from pathlib import Path

from setuptools import Extension, find_packages, setup


CONFIG_FILENAMES = ("build_config.yaml", "build_config.yml", "build_config.json")
DEFAULT_CYTHON_MODULES = (
    ("fletplus.router.router_cy", Path("fletplus/router/router_cy.pyx")),
    ("fletplus.http.disk_cache", Path("fletplus/http/disk_cache.pyx")),
    ("fletplus.state.state", Path("fletplus/state/state.pyx")),
)


def _load_module_config() -> list[tuple[str, Path]]:
    base_dir = Path(__file__).parent
    for filename in CONFIG_FILENAMES:
        config_path = base_dir / filename
        if not config_path.exists():
            continue

        try:
            if config_path.suffix in {".yaml", ".yml"}:
                import yaml  # type: ignore

                data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            else:
                data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        modules = []
        for entry in data.get("cython_modules", ()):  # type: ignore[arg-type]
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            path_str = entry.get("path")
            if not name or not path_str:
                continue
            path = Path(str(path_str))
            modules.append((str(name), path if path.is_absolute() else base_dir / path))

        if modules:
            return modules

    modules = []
    for name, path in DEFAULT_CYTHON_MODULES:
        modules.append((name, path if path.is_absolute() else base_dir / path))
    return modules


def _build_extensions():
    modules = _load_module_config()
    try:
        from Cython.Build import cythonize

        extensions = [Extension(name, sources=[str(path)]) for name, path in modules]
        return cythonize(extensions, language_level="3", annotate=False)
    except Exception:
        extensions: list[Extension] = []
        for name, path in modules:
            c_path = path.with_suffix(".c")
            if c_path.exists():
                extensions.append(Extension(name, sources=[str(c_path)]))
        return extensions

setup(
    name="fletplus",
    version="0.2.5",
    author="Adolfo González Hernández",
    author_email="adolfogonzal@gmail.com",
    description="Componentes avanzados y utilidades para apps Flet en Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Alphonsus411/fletplus",  # Cambia esto si lo subes a GitHub
    project_urls={
        "Bug Tracker": "https://github.com/Alphonsus411/fletplus/issues",
    },
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "fletplus.router": ["router_cy.c", "router_cy.pyx", "router_cy.pxd"],
        "fletplus.http": ["disk_cache.c", "disk_cache.pyx", "disk_cache.pxd"],
        "fletplus.state": ["state.c", "state.pyx", "state.pxd"],
    },
    install_requires=[
        "flet>=0.27.0",
    ],
    entry_points={
        "console_scripts": [
            # Nuevo alias con guion para lanzar la demo desde la terminal.
            "fletplus-demo=fletplus_demo:main",
            # Alias existente con guion bajo para mantener compatibilidad.
            "fletplus_demo=fletplus_demo:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: User Interfaces",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    ext_modules=_build_extensions(),
)
