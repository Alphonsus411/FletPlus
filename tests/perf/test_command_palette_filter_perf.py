import time

from fletplus.components.command_palette import filter_commands


def test_filter_commands_large_list_fast():
    names = [f"cmd_{i}" for i in range(5000)]
    names[10] = "user_add"
    names[300] = "manage_user"
    start = time.perf_counter()
    indices = filter_commands(names, "user")
    elapsed = time.perf_counter() - start
    assert 10 in indices and 300 in indices
    assert elapsed < 1.0
