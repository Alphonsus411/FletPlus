"""Implementación en Python puro del caché de disco."""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import os
import stat
import time
import tempfile
import warnings
from pathlib import Path
from typing import Any, Literal

import httpx

try:  # pragma: no cover - acelerador opcional
    from .disk_cache_pr import build_key as _build_key_rs, cleanup as _cleanup_rs
except Exception:  # pragma: no cover - fallback limpio
    _build_key_rs = None
    _cleanup_rs = None


class DiskCache:
    """Caché persistente sencilla para respuestas HTTP.

    Al crear el directorio, intenta aplicar permisos restrictivos (``0o700``)
    y valida si es world-writable según ``world_writable_policy``.
    """

    def __init__(
        self,
        directory: str | os.PathLike[str],
        *,
        max_entries: int = 128,
        max_age: float | None = None,
        world_writable_policy: Literal["warn", "error", "ignore"] = "warn",
    ) -> None:
        if not isinstance(max_entries, int) or isinstance(max_entries, bool) or max_entries < 1:
            raise ValueError("max_entries debe ser un entero mayor o igual a 1.")
        if max_age is not None:
            if not isinstance(max_age, (int, float)) or isinstance(max_age, bool) or max_age <= 0:
                raise ValueError("max_age debe ser None o un número positivo.")
        if world_writable_policy not in {"warn", "error", "ignore"}:
            raise ValueError("world_writable_policy debe ser 'warn', 'error' o 'ignore'.")
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        if os.name == "posix":
            try:
                os.chmod(self.directory, 0o700)
            except (PermissionError, NotImplementedError, OSError):
                pass
            if world_writable_policy != "ignore":
                try:
                    mode = self.directory.stat().st_mode
                except OSError:
                    mode = None
                if mode is not None and mode & stat.S_IWOTH:
                    message = (
                        "El directorio de caché "
                        f"'{self.directory}' es world-writable. "
                        "Usa permisos restrictivos o ajusta world_writable_policy."
                    )
                    if world_writable_policy == "error":
                        raise PermissionError(message)
                    warnings.warn(message, RuntimeWarning, stacklevel=2)
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
            expires_at = data.get("expires_at")
            if expires_at is not None and float(expires_at) <= time.time():
                path.unlink(missing_ok=True)
                return None
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
    def set(self, key: str, response: httpx.Response, *, expires_at: float | None = None) -> None:
        """Guarda la respuesta en disco con escritura atómica segura para concurrencia."""
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
            "expires_at": expires_at,
        }
        payload = json.dumps(entry, separators=(",", ":"))
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                delete=False,
                dir=self.directory,
            ) as fh:
                tmp_path = Path(fh.name)
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, path)
            os.chmod(path, 0o600)
        finally:
            if tmp_path is not None:
                with contextlib.suppress(OSError):
                    tmp_path.unlink()
        self._cleanup()

    # ------------------------------------------------------------------
    def _cleanup(self) -> None:
        if _cleanup_rs is not None:
            try:
                _cleanup_rs(str(self.directory), self.max_entries, self.max_age)
                return
            except Exception:
                pass

        cutoff = (time.time() - self.max_age) if self.max_age is not None else None
        files: list[tuple[Path, float]] = []
        # Orden por recencia: usamos mtime actualizado en hits.
        for path in self.directory.glob("*.json"):
            try:
                mtime = path.stat().st_mtime
            except (FileNotFoundError, OSError):
                continue
            if cutoff is not None:
                try:
                    data = json.loads(path.read_text("utf-8"))
                    timestamp = float(data["timestamp"])
                except Exception:
                    with contextlib.suppress(OSError):
                        path.unlink()
                    continue
                if timestamp < cutoff:
                    with contextlib.suppress(OSError):
                        path.unlink()
                    continue
            files.append((path, mtime))
        files.sort(key=lambda item: item[1], reverse=True)
        kept = 0
        for file_path, _mtime in files:
            kept += 1
            if kept > self.max_entries:
                with contextlib.suppress(OSError):
                    file_path.unlink()

    # ------------------------------------------------------------------
    def clear(self) -> None:
        for file in self.directory.glob("*.json"):
            with contextlib.suppress(OSError):
                file.unlink()
