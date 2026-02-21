from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Sequence


def _resolve_executable(executable: str) -> str:
    if os.path.isabs(executable) and Path(executable).exists():
        return executable
    resolved = shutil.which(executable)
    if not resolved:
        raise FileNotFoundError(executable)
    return resolved


def _ensure_cwd(cwd: str | os.PathLike[str] | None) -> str | None:
    if cwd is None:
        return None
    p = Path(cwd)
    if not p.exists() or not p.is_dir():
        raise FileNotFoundError(str(p))
    return str(p)


def _normalize_args(args: Sequence[str]) -> list[str]:
    if not isinstance(args, (list, tuple)) or not args:
        raise ValueError("args")
    norm = [str(a) for a in args]
    norm[0] = _resolve_executable(norm[0])
    return norm


def _inject_powershell_flags(args: list[str]) -> list[str]:
    exe = os.path.basename(args[0]).lower()
    if exe in {"powershell", "pwsh"} and "-NoProfile" not in args:
        return [args[0], "-NoProfile"] + args[1:]
    return args


def _filter_env(base: Mapping[str, str] | None, whitelist: Sequence[str] | None) -> Mapping[str, str] | None:
    if whitelist is None:
        return dict(base) if base is not None else None
    base_env = os.environ if base is None else base
    allowed = {k: v for k, v in base_env.items() if k in set(whitelist)}
    return allowed


def safe_run(
    args: Sequence[str],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
    env_whitelist: Sequence[str] | None = None,
    check: bool = False,
    timeout: float | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    norm = _normalize_args(args)
    norm = _inject_powershell_flags(norm)
    effective_cwd = _ensure_cwd(cwd)
    effective_env = _filter_env(env if env is not None else os.environ, env_whitelist)
    return subprocess.run(
        norm,
        cwd=effective_cwd,
        env=effective_env,
        check=check,
        timeout=timeout,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
    )


def safe_popen(
    args: Sequence[str],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
    env_whitelist: Sequence[str] | None = None,
) -> subprocess.Popen:
    norm = _normalize_args(args)
    norm = _inject_powershell_flags(norm)
    effective_cwd = _ensure_cwd(cwd)
    effective_env = _filter_env(env if env is not None else os.environ, env_whitelist)
    return subprocess.Popen(
        norm,
        cwd=effective_cwd,
        env=effective_env,
    )
