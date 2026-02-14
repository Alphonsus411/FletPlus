import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_devtools_imports_without_websockets_and_fails_on_instantiation():
    script = """
import builtins
import importlib
import sys

real_import = builtins.__import__

def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == 'websockets' or name.startswith('websockets.'):
        raise ImportError("No module named 'websockets'")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = blocked_import

module = importlib.import_module('fletplus.devtools')
assert hasattr(module, 'DevToolsServer')

try:
    module.DevToolsServer()
except RuntimeError as exc:
    message = str(exc)
    assert 'websockets' in message
    assert 'pip install websockets' in message
else:
    raise AssertionError('DevToolsServer() debía fallar sin websockets')
"""

    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
