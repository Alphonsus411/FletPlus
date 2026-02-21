#!/usr/bin/env python3
"""Valida que workflow/docs/config estén sincronizados con la matriz de Flet."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO_ROOT))

from tools.flet_version_matrix_config import FLET_MATRIX_MINORS


def main() -> int:
    if len(FLET_MATRIX_MINORS) != 2:
        print(
            "ERROR: FLET_MATRIX_MINORS debe contener exactamente baseline y target.",
            file=sys.stderr,
        )
        return 1

    baseline_minor, target_minor = FLET_MATRIX_MINORS
    cmd = [
        sys.executable,
        str(REPO_ROOT / "tools" / "update_flet_target.py"),
        "--check",
        "--baseline-minor",
        baseline_minor,
        "--target-minor",
        target_minor,
    ]

    completed = subprocess.run(cmd, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
