import json
from pathlib import Path

from setuptools import Extension, find_packages, setup


CONFIG_FILENAMES = ("build_config.yaml", "build_config.yml", "build_config.json")
DEFAULT_CYTHON_MODULES = (
    ("fletplus.router.router_cy", Path("fletplus/router/router_cy.pyx")),
    ("fletplus.http.disk_cache", Path("fletplus/http/disk_cache.pyx")),
    ("fletplus.state.state", Path("fletplus/state/state.pyx")),
    ("fletplus.utils.responsive_manager", Path("fletplus/utils/responsive_manager.pyx")),
)


def _load_module_config() -> list[tuple[str, Path]]:
    base_dir = Path(__file__).parent
    modules = []

    # Intento de config externa
    for filename in CONFIG_FILENAMES:
        config_path = base_dir / filename
        if config_path.exists():
            try:
                if config_path.suffix in {".yaml", ".yml"}:
                    import yaml
                    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                else:
                    data = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            if isinstance(data, dict):
                for entry in data.get("cython_modules", []):
                    if isinstance(entry, dict):
                        name = entry.get("name")
                        path_str = entry.get("path")
                        if name and path_str:
                            p = Path(path_str)
                            if p.is_absolute():
                                # Convertir a ruta relativa correcta
                                p = p.relative_to(base_dir)
                            modules.append((name, p))

                if modules:
                    return modules

    # Config por defecto
    for name, path in DEFAULT_CYTHON_MODULES:
        if path.is_absolute():
            path = path.relative_to(base_dir)
        modules.append((name, path))

    return modules


def _build_extensions():
    modules = _load_module_config()
    try:
        from Cython.Build import cythonize

        extensions = [
            Extension(name, sources=[str(path).replace("\\", "/")])
            for name, path in modules
        ]
        return cythonize(extensions, language_level="3", annotate=False)

    except Exception:
        # Fallback a archivos .c si Cython no está disponible
        extensions = []
        for name, path in modules:
            c_path = path.with_suffix(".c")
            if c_path.exists():
                extensions.append(
                    Extension(name, sources=[str(c_path).replace("\\", "/")])
                )
        return extensions


setup(
    name="fletplus",
    version="0.2.6",
    author="Adolfo González Hernández",
    author_email="adolfogonzal@gmail.com",
    description="Componentes avanzados y utilidades para apps Flet en Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Alphonsus411/fletplus",
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
        "fletplus.utils": [
            "responsive_manager.c",
            "responsive_manager.pyx",
            "responsive_manager.pxd",
        ],
    },
    install_requires=[
        "flet>=0.27.0",
        "click>=8.1",
        "watchdog>=3.0",
        "websockets>=12.0",
        "httpx>=0.28",
    ],
    extras_require={
        "build": ["Cython>=3.0"],
    },
    entry_points={
        "console_scripts": [
            "fletplus-demo=fletplus_demo:main",
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
