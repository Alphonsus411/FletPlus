import os
import pytest
from fletplus.utils.dragdrop import FileDropZone


def test_file_drop_zone_filters_by_extension_and_size(tmp_path):
    valid = tmp_path / "ok.txt"
    valid.write_text("data")
    invalid_ext = tmp_path / "bad.jpg"
    invalid_ext.write_text("x")
    large = tmp_path / "big.txt"
    large.write_bytes(b"x" * 2048)

    received = []

    zone = FileDropZone(
        allowed_extensions=[".txt"],
        max_size=1024,
        on_files=lambda files: received.extend(files),
    )

    result = zone.drop([str(valid), str(invalid_ext), str(large)])

    assert result == [str(valid)]
    assert received == [str(valid)]


def test_file_drop_zone_ignores_missing_paths(tmp_path):
    valid = tmp_path / "ok.txt"
    valid.write_text("data")
    missing = tmp_path / "missing.txt"

    zone = FileDropZone(allowed_extensions=[".txt"], max_size=1024)

    result = zone.drop([str(valid), str(missing)])

    assert result == [str(valid)]


def test_file_drop_zone_rejects_traversal_and_symlinks(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    inside = base / "inside.txt"
    inside.write_text("ok")
    outside = tmp_path / "outside.txt"
    outside.write_text("no")
    link = base / "link.txt"
    try:
        link.symlink_to(outside)
    except OSError as e:
        if getattr(e, "winerror", 0) == 1314:
            pytest.skip("Symlinks not allowed on Windows without admin/dev mode")
        raise

    zone = FileDropZone(allowed_extensions=[".txt"], base_directory=str(base))

    traversal = base / ".." / outside.name
    result = zone.drop([str(inside), str(traversal), str(link)])

    assert result == [str(inside.resolve())]
