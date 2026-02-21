from __future__ import annotations

import sys
from typing import Sequence

from fletplus.utils.safe_subprocess import safe_run


def _run_py(args: Sequence[str], **kwargs):
    return safe_run([sys.executable, *args], **kwargs)


def test_safe_run_executes_python_and_captures_output() -> None:
    cp = _run_py(["-c", "print('ok')"], check=True, capture_output=True)
    assert cp.stdout is not None
    assert b"ok" in cp.stdout


def test_env_whitelist_applies_and_injects_custom_key() -> None:
    env = {"FOO": "BAR"}
    whitelist = ["FOO", "PATH", "SystemRoot", "WINDIR", "COMSPEC", "TEMP", "TMP", "HOME", "USERPROFILE", "PATHEXT"]
    cp = _run_py(
        ["-c", "import os; print(os.environ.get('FOO',''))"],
        check=True,
        capture_output=True,
        env=env,
        env_whitelist=whitelist,
    )
    assert cp.stdout is not None
    # On Windows stdout is bytes with \r\n; tolerate either newline variant.
    assert cp.stdout.strip() in {b"BAR", b"BAR\r"}
