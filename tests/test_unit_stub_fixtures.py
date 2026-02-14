from __future__ import annotations

import importlib


def test_state_stub_fixture_is_opt_in(use_state_stub):
    state_module = importlib.import_module("fletplus.state.state")
    signal = state_module.Signal(10)

    assert not hasattr(state_module, "__file__")
    assert signal.get() == 10


def test_responsive_manager_stub_fixture_is_opt_in(use_responsive_manager_stub):
    module = importlib.import_module("fletplus.utils.responsive_manager")
    manager = module.ResponsiveManager(page=object())

    assert not hasattr(module, "__file__")
    assert manager is not None
