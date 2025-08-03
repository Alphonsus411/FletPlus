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
