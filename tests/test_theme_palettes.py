import json
import pytest
from fletplus.themes.theme_manager import load_palette_from_file


def test_load_palette_from_file_invalid_mode(tmp_path):
    palette = {"light": {"primary": "#fff"}, "dark": {"primary": "#000"}}
    file_path = tmp_path / "palette.yaml"
    file_path.write_text(json.dumps(palette))

    with pytest.raises(ValueError):
        load_palette_from_file(str(file_path), "solarized")


def test_load_palette_from_file_nested_groups(tmp_path):
    palette = {"light": {"info": {"100": "#fff"}, "warning": {"200": "#eee"}}}
    file_path = tmp_path / "palette.json"
    file_path.write_text(json.dumps(palette))

    loaded = load_palette_from_file(str(file_path), "light")
    assert loaded["info_100"] == "#fff"
    assert loaded["warning_200"] == "#eee"


def test_load_palette_from_file_multiple_nested_groups(tmp_path):
    palette = {
        "dark": {
            "success": {"300": "#abc"},
            "error": {"800": "#def"},
        }
    }
    file_path = tmp_path / "palette.json"
    file_path.write_text(json.dumps(palette))

    loaded = load_palette_from_file(str(file_path), "dark")
    assert loaded["success_300"] == "#abc"
    assert loaded["error_800"] == "#def"
