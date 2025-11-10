from setuptools import setup, find_packages

setup(
    name="fletplus",
    version="0.2.4",
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
)
