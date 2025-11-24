import importlib
import sys
import types
from pathlib import Path


def test_disk_cache_import_error(monkeypatch):
    package_root = Path(__file__).resolve().parents[1] / "fletplus"

    with monkeypatch.context() as context:
        dummy_signal = type("DummySignal", (), {})

        context.setitem(sys.modules, "fletplus", types.ModuleType("fletplus"))
        sys.modules["fletplus"].__path__ = [str(package_root)]

        context.setitem(sys.modules, "fletplus.http", types.ModuleType("fletplus.http"))
        sys.modules["fletplus.http"].__path__ = [str(package_root / "http")]

        context.setitem(sys.modules, "fletplus.state", types.ModuleType("fletplus.state"))
        sys.modules["fletplus.state"].__path__ = [str(package_root / "state")]
        sys.modules["fletplus.state"].Signal = dummy_signal

        client = importlib.import_module("fletplus.http.client")

        context.setattr(client.importlib.util, "find_spec", lambda _: object())

        def _raise_import_error(*_args, **_kwargs):
            raise ImportError("boom")

        context.setattr(client.importlib, "import_module", _raise_import_error)

        reloaded = importlib.reload(client)
        assert reloaded.DiskCache is reloaded._PyDiskCache
