from setuptools import setup, find_packages

setup(
    name="fletplus",
    version="0.2.3",
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
        "flet>=0.8.0",  # Ajusta según versión actual de Flet
    ],
    entry_points={
        "console_scripts": [
            "fletplus-demo=fletplus_demo.app:run",
            "fletplus_demo=fletplus_demo.app:run",
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
    python_requires='>=3.8',
)
