"""Generate Cython module config from profiling data."""
from __future__ import annotations

import argparse
import pstats
from pathlib import Path
from typing import Iterable, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODULES: tuple[tuple[str, Path], ...] = (
    ("fletplus.router.router_cy", REPO_ROOT / "fletplus/router/router_cy.pyx"),
    ("fletplus.http.disk_cache", REPO_ROOT / "fletplus/http/disk_cache.pyx"),
    ("fletplus.state.state", REPO_ROOT / "fletplus/state/state.pyx"),
    (
        "fletplus.utils.responsive_manager",
        REPO_ROOT / "fletplus/utils/responsive_manager.pyx",
    ),
)


def _iter_profile_entries(profile_path: Path) -> Iterable[tuple[Path, float]]:
    stats = pstats.Stats(str(profile_path)).sort_stats("cumtime")
    for (filename, _lineno, _funcname), (_cc, _nc, _tt, cumtime, _callers) in stats.stats.items():
        file_path = Path(filename)
        try:
            file_path = file_path.resolve()
        except FileNotFoundError:
            # Skip entries we cannot resolve (e.g. <string> or generated code).
            continue

        if REPO_ROOT not in file_path.parents and file_path != REPO_ROOT:
            continue

        relative = file_path.relative_to(REPO_ROOT)
        if relative.parts and relative.parts[0] not in {"fletplus", "fletplus_demo"}:
            continue

        yield relative, float(cumtime)


def _module_for_path(relative: Path) -> Tuple[str, Path]:
    module_name = relative.with_suffix("")
    dotted = ".".join(module_name.parts)

    cython_candidate = (REPO_ROOT / relative).with_suffix(".pyx")
    module_path = cython_candidate if cython_candidate.exists() else REPO_ROOT / relative
    return dotted, module_path


def _render_config(modules: list[tuple[str, Path]]) -> str:
    lines: list[str] = ["cython_modules:"]
    for name, path in modules:
        rel_path = path if path.is_absolute() else path
        try:
            rel_path = path.relative_to(REPO_ROOT)
        except ValueError:
            rel_path = path
        lines.append(f"  - name: {name}")
        lines.append(f"    path: {rel_path.as_posix()}")
    return "\n".join(lines) + "\n"


def select_modules(profile_path: Path, limit: int) -> list[tuple[str, Path]]:
    aggregates: dict[Path, float] = {}
    for relative, cumtime in _iter_profile_entries(profile_path):
        aggregates[relative] = aggregates.get(relative, 0.0) + cumtime

    sorted_entries = sorted(aggregates.items(), key=lambda item: item[1], reverse=True)

    selected: list[tuple[str, Path]] = []
    for relative, _cumtime in sorted_entries[:limit]:
        selected.append(_module_for_path(relative))

    if not selected:
        selected.extend(DEFAULT_MODULES)

    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Select hottest modules for Cython build")
    parser.add_argument(
        "--profile",
        default=REPO_ROOT / "build/profile.txt",
        type=Path,
        help="Ruta del archivo de perfil generado con cProfile (formato Stats)",
    )
    parser.add_argument(
        "--config",
        default=REPO_ROOT / "build_config.yaml",
        type=Path,
        help="Archivo YAML a generar/actualizar",
    )
    parser.add_argument(
        "--limit",
        default=4,
        type=int,
        help="Número de módulos a incluir ordenados por tiempo acumulado",
    )

    args = parser.parse_args()
    profile_path: Path = args.profile
    config_path: Path = args.config
    limit: int = max(1, args.limit)

    if not profile_path.exists():
        raise SystemExit(f"No se encontró el perfil en {profile_path}")

    modules = select_modules(profile_path, limit)
    config_path.write_text(_render_config(modules), encoding="utf-8")

    print(f"Configuración actualizada en {config_path} con {len(modules)} módulos.")
    for name, path in modules:
        try:
            rel = path.relative_to(REPO_ROOT)
        except ValueError:
            rel = path
        print(f"- {name} -> {rel}")


if __name__ == "__main__":
    main()
