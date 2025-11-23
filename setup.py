from pathlib import Path

from setuptools import Extension, find_packages, setup


def _build_extensions():
    module_path = Path("fletplus/router/router_cy.pyx")
    source = "router_cy.pyx"
    sources = [str(module_path)]
    try:
        from Cython.Build import cythonize

        return cythonize(
            [Extension("fletplus.router.router_cy", sources=sources)],
            language_level="3",
            annotate=False,
        )
    except Exception:
        c_path = module_path.with_suffix(".c")
        if c_path.exists():
            return [Extension("fletplus.router.router_cy", sources=[str(c_path)])]
        # Sin Cython ni archivo C generado, no añadimos la extensión
        return []

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
