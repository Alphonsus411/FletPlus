import pytest
from fletplus.themes.theme_manager import load_palette_from_file


def test_load_palette_from_file_invalid_mode(tmp_path):
    palette_yaml = """light:\n  primary: '#fff'\ndark:\n  primary: '#000'\n"""
    file_path = tmp_path / "palette.yaml"
    file_path.write_text(palette_yaml)

    with pytest.raises(ValueError):
        load_palette_from_file(str(file_path), "solarized")
