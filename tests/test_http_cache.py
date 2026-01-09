import time
from pathlib import Path

import httpx

from fletplus.http import DiskCache


def _make_request(url: str, *, body: bytes | str = b"", headers: dict[str, str] | None = None) -> httpx.Request:
    return httpx.Request("GET", url, headers=headers or {}, content=body)


def test_disk_cache_preserves_headers_and_reason(tmp_path: Path):
    cache = DiskCache(tmp_path)
    request = _make_request("https://example.org/data", headers={"X-Test": "1"})
    response = httpx.Response(
        201,
        headers={"X-Custom": "abc", "Set-Cookie": "a=b"},
        content=b"payload",
        request=request,
        extensions={"reason_phrase": b"CREATED"},
    )

    key = cache.build_key(request)
    cache.set(key, response)

    loaded = cache.get(key, request=request)
    assert loaded is not None
    assert loaded.status_code == 201
    assert loaded.headers["X-Custom"] == "abc"
    assert loaded.headers.get_list("Set-Cookie") == ["a=b"]
    assert loaded.reason_phrase == "CREATED"
    assert loaded.read() == b"payload"


def test_disk_cache_expiration(tmp_path: Path):
    cache = DiskCache(tmp_path, max_age=0.05)
    request = _make_request("https://example.org/expire")
    response = httpx.Response(200, content=b"expire-me", request=request)

    key = cache.build_key(request)
    cache.set(key, response)
    assert cache.get(key, request=request) is not None

    time.sleep(0.06)

    expired = cache.get(key, request=request)
    assert expired is None


def test_disk_cache_expiration_not_extended_by_reads(tmp_path: Path):
    cache = DiskCache(tmp_path, max_age=0.05)
    request = _make_request("https://example.org/expire-read")
    response = httpx.Response(200, content=b"expire-me", request=request)

    key = cache.build_key(request)
    cache.set(key, response)

    time.sleep(0.04)
    assert cache.get(key, request=request) is not None

    time.sleep(0.04)
    expired = cache.get(key, request=request)
    assert expired is None


def test_disk_cache_cleanup_limit(tmp_path: Path):
    cache = DiskCache(tmp_path, max_entries=3)
    requests = [_make_request(f"https://example.org/items/{idx}") for idx in range(6)]

    for req in requests:
        key = cache.build_key(req)
        cache.set(key, httpx.Response(200, content=bytes(str(req.url), "utf-8")))

    files = list(tmp_path.glob("*.json"))
    assert len(files) <= 3
