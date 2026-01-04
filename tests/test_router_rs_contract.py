import pytest

from fletplus.router import router as router_mod

router_rs = pytest.importorskip("fletplus.router.router_rs")

if router_rs._normalize_path is None:  # pragma: no cover - entorno sin binario
    pytest.skip("backend Rust no disponible", allow_module_level=True)


@pytest.mark.parametrize(
    "path",
    [
        "",
        " ",
        "/",
        "//",
        " /users/ ",
        "/users//42/",
        "users/<name>/details",
        "//café//",
        "/emoji/😊/終/",
    ],
)
def test_normalize_path_equivalence(path: str):
    assert router_rs._normalize_path(path) == router_mod._normalize_path_py(path)


@pytest.mark.parametrize(
    "path",
    [
        "",
        "   ",
        "/",
        "/users/",
        "users/42",
        "//café//",
        "/emoji/😊/終/",
    ],
)
def test_normalize_path_string_equivalence(path: str):
    assert router_rs._normalize_path_string(path) == router_mod._normalize_path_string_py(path)


@pytest.mark.parametrize(
    "segment",
    [
        "users",
        "<user_id>",
        "<тест>",
        "<>",
        "< spaced >",
    ],
)
def test_parse_segment_equivalence(segment: str):
    assert router_rs._parse_segment(segment) == router_mod._parse_segment_py(segment)


@pytest.mark.parametrize(
    "base,segment",
    [
        ("/", "users"),
        ("/users/", "<id>"),
        ("/users/42", "details"),
        ("/emoji/😊", "終"),
        ("/prefixed", "/nested/path"),
        ("", "rooted"),
    ],
)
def test_join_paths_equivalence(base: str, segment: str):
    assert router_rs._join_paths(base, segment) == router_mod._join_paths_py(base, segment)
