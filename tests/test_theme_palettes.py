import json
import pytest
from fletplus.themes.theme_manager import load_palette_from_file


def test_load_palette_from_file_invalid_mode(tmp_path):
    palette = {"light": {"primary": "#fff"}, "dark": {"primary": "#000"}}
    file_path = tmp_path / "palette.yaml"
    file_path.write_text(json.dumps(palette))

    with pytest.raises(ValueError):
        load_palette_from_file(str(file_path), "solarized")
