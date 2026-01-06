"""Implementación en Python puro del caché de disco."""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx

try:  # pragma: no cover - acelerador opcional
    from .disk_cache_pr import build_key as _build_key_rs, cleanup as _cleanup_rs
except Exception:  # pragma: no cover - fallback limpio
    _build_key_rs = None
    _cleanup_rs = None


class DiskCache:
    """Caché persistente sencilla para respuestas HTTP."""

    def __init__(self, directory: str | os.PathLike[str], *, max_entries: int = 128, max_age: float | None = None) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self.max_age = max_age

    # ------------------------------------------------------------------
    def build_key(self, request: httpx.Request) -> str:
        if _build_key_rs is not None:
            try:
                return _build_key_rs(request)
            except Exception:
                pass

        body = request.content or b""
        if isinstance(body, str):
            body = body.encode()
        elif not isinstance(body, (bytes, bytearray, memoryview)):
            body = bytes(body)
        raw_headers = [(name.lower(), value) for name, value in request.headers.raw]
        raw_headers.sort()
        hasher = hashlib.sha256()
        hasher.update(request.method.encode("utf-8"))
        hasher.update(b"\n")
        hasher.update(str(request.url).encode("utf-8"))
        hasher.update(b"\n")
        for name, value in raw_headers:
            hasher.update(name)
            hasher.update(b":")
            hasher.update(value)
            hasher.update(b"\n")
        hasher.update(memoryview(body))
        return hasher.hexdigest()

    # ------------------------------------------------------------------
    def _path_for(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.directory / f"{safe_key}.json"

    # ------------------------------------------------------------------
    def _is_expired(self, timestamp: float) -> bool:
        if self.max_age is None:
            return False
        return (time.time() - timestamp) > self.max_age

    # ------------------------------------------------------------------
    def get(self, key: str, *, request: httpx.Request | None = None) -> httpx.Response | None:
        path = self._path_for(key)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text("utf-8"))
            timestamp = float(data["timestamp"])
            if self._is_expired(timestamp):
                path.unlink(missing_ok=True)
                return None
            headers_data = data["headers"]
            content = base64.b64decode(data["content"])
        except Exception:
            path.unlink(missing_ok=True)
            return None

        headers = [
            (str(name).encode("latin-1"), str(value).encode("latin-1"))
            for name, value in headers_data
        ]
        response = httpx.Response(
            int(data["status_code"]),
            headers=headers,
            content=content,
            request=request,
            extensions={},
        )
        http_version = data.get("http_version")
        reason_phrase = data.get("reason_phrase")
        if http_version:
            response.extensions["http_version"] = http_version
        if reason_phrase:
            response.extensions["reason_phrase"] = str(reason_phrase).encode("ascii", "ignore")
        os.utime(path, None)
        return response

    # ------------------------------------------------------------------
    def set(self, key: str, response: httpx.Response) -> None:
        path = self._path_for(key)
        headers = [
            (name.decode("latin-1"), value.decode("latin-1"))
            for name, value in response.headers.raw
        ]
        entry: dict[str, Any] = {
            "status_code": response.status_code,
            "headers": headers,
            "content": base64.b64encode(response.content).decode("ascii"),
            "http_version": response.extensions.get("http_version"),
            "reason_phrase": response.reason_phrase,
            "timestamp": time.time(),
        }
        path.write_text(json.dumps(entry, separators=(",", ":")), "utf-8")
        self._cleanup()

    # ------------------------------------------------------------------
    def _cleanup(self) -> None:
        if _cleanup_rs is not None:
            try:
                _cleanup_rs(str(self.directory), self.max_entries, self.max_age)
                return
            except Exception:
                pass

        if self.max_age is not None:
            cutoff = time.time() - self.max_age
        else:
            cutoff = None
        files = sorted(self.directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        kept = 0
        for file_path in files:
            if cutoff is not None and file_path.stat().st_mtime < cutoff:
                with contextlib.suppress(OSError):
                    file_path.unlink()
                continue
            kept += 1
            if kept > self.max_entries:
                with contextlib.suppress(OSError):
                    file_path.unlink()

    # ------------------------------------------------------------------
    def clear(self) -> None:
        for file in self.directory.glob("*.json"):
            with contextlib.suppress(OSError):
                file.unlink()
