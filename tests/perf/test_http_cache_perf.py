import json
import time
from pathlib import Path

import httpx

from fletplus.http import DiskCache


def _build_requests(total: int) -> list[httpx.Request]:
    requests: list[httpx.Request] = []
    for idx in range(total):
        requests.append(
            httpx.Request(
                "GET",
                f"https://example.org/items/{idx}",
                headers={"X-Item": str(idx)},
                content=f"payload-{idx}".encode(),
            )
        )
    return requests


def _build_responses(requests: list[httpx.Request]) -> list[httpx.Response]:
    responses: list[httpx.Response] = []
    for request in requests:
        responses.append(httpx.Response(200, headers={"X-Req": request.headers["X-Item"]}, content=request.content))
    return responses


def test_http_cache_microbenchmark(tmp_path: Path):
    cache = DiskCache(tmp_path, max_entries=600)
    requests = _build_requests(500)
    responses = _build_responses(requests)

    start = time.perf_counter()
    keys = [cache.build_key(request) for request in requests]
    build_time = time.perf_counter() - start

    start = time.perf_counter()
    for key, response in zip(keys, responses):
        cache.set(key, response)
    set_time = time.perf_counter() - start

    start = time.perf_counter()
    hits = [cache.get(key, request=req) for key, req in zip(keys, requests)]
    get_time = time.perf_counter() - start

    assert all(hit is not None for hit in hits)

    results = {
        "entries": len(requests),
        "build_key_ms": round(build_time * 1000, 3),
        "set_ms": round(set_time * 1000, 3),
        "get_ms": round(get_time * 1000, 3),
    }
    (tmp_path / "http_cache_timings.json").write_text(json.dumps(results, indent=2), "utf-8")
