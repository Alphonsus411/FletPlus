# cython: language_level=3
"""Implementación optimizada en Cython para el caché de disco."""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import os
import stat
import time
import warnings
from pathlib import Path
from typing import Any

import httpx

cdef inline bytes _safe_bytes(object value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, memoryview):
        return bytes(value)
    if isinstance(value, str):
        return value.encode()
    return bytes(value)


cdef class DiskCache:
    """Caché persistente sencilla para respuestas HTTP.

    Al crear el directorio, intenta aplicar permisos restrictivos (``0o700``)
    y valida si es world-writable según ``world_writable_policy``. Con
    ``warn`` se crea un subdirectorio privado (``0700``) para mantener la
    compatibilidad, con ``error`` se falla de forma explícita y con ``ignore``
    se omite la validación.
    """

    def __init__(
        self,
        directory: str | os.PathLike[str],
        *,
        int max_entries=128,
        max_age: float | None = None,
        world_writable_policy: str = "error",
    ):
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
                    if world_writable_policy == "warn":
                        private_dir = self.directory / ".fletplus-cache-private"
                        private_dir.mkdir(parents=True, exist_ok=True)
                        try:
                            os.chmod(private_dir, 0o700)
                        except (PermissionError, NotImplementedError, OSError):
                            pass
                        warnings.warn(
                            "El directorio de caché "
                            f"'{self.directory}' es world-writable. "
                            f"Se usará el subdirectorio privado '{private_dir}'. "
                            "Configura world_writable_policy='error' para fallar "
                            "o 'ignore' para mantener el directorio original.",
                            RuntimeWarning,
                            stacklevel=2,
                        )
                        self.directory = private_dir
                    else:
                        message = (
                            "El directorio de caché "
                            f"'{self.directory}' es world-writable. "
                            "Configura world_writable_policy='warn' para usar "
                            "un subdirectorio privado o 'ignore' para "
                            "mantenerlo bajo tu responsabilidad."
                        )
                        if world_writable_policy == "error":
                            raise PermissionError(message)
                        warnings.warn(message, RuntimeWarning, stacklevel=2)
        self.max_entries = max_entries
        if max_age is None:
            self.has_ttl = False
            self.max_age = 0.0
        else:
            self.has_ttl = True
            self.max_age = max_age

    # ------------------------------------------------------------------
    cpdef str build_key(self, object request):
        cdef bytes body = _safe_bytes(request.content or b"")
        cdef list raw_headers = [(name.lower(), value) for name, value in request.headers.raw]
        raw_headers.sort()
        cdef object hasher = hashlib.sha256()
        hasher.update(request.method.encode("utf-8"))
        hasher.update(b"\n")
        hasher.update(str(request.url).encode("utf-8"))
        hasher.update(b"\n")
        for name, value in raw_headers:
            hasher.update(name)
            hasher.update(b":")
            hasher.update(value)
            hasher.update(b"\n")
        hasher.update(body)
        return hasher.hexdigest()

    # ------------------------------------------------------------------
    cdef object _path_for(self, str key):
        cdef str safe_key = key.replace("/", "_").replace("\\", "_")
        return self.directory / f"{safe_key}.json"

    # ------------------------------------------------------------------
    cdef bint _is_expired(self, double timestamp) except *:
        if not self.has_ttl:
            return False
        return (time.time() - timestamp) > self.max_age

    # ------------------------------------------------------------------
    cpdef object get(self, str key, object request=None):
        cdef object path = self._path_for(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text("utf-8"))
            timestamp = float(data["timestamp"])
            if self._is_expired(timestamp):
                with contextlib.suppress(OSError):
                    path.unlink(missing_ok=True)
                return None
            headers_data = data["headers"]
            content = base64.b64decode(data["content"])
        except Exception:
            with contextlib.suppress(OSError):
                path.unlink(missing_ok=True)
            return None

        cdef list header_items = []
        cdef object name
        cdef object value
        for name, value in headers_data:
            header_items.append((str(name).encode("latin-1"), str(value).encode("latin-1")))
        response = httpx.Response(
            int(data["status_code"]),
            headers=header_items,
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
        if not self.has_ttl:
            os.utime(path, None)
        return response

    # ------------------------------------------------------------------
    cpdef void set(self, str key, object response):
        cdef object path = self._path_for(key)
        cdef object tmp_path = f"{path}.tmp"
        cdef list headers = []
        cdef bytes name
        cdef bytes value
        for name, value in response.headers.raw:
            headers.append((name.decode("latin-1"), value.decode("latin-1")))
        entry: dict[str, Any] = {
            "status_code": response.status_code,
            "headers": headers,
            "content": base64.b64encode(response.content).decode("ascii"),
            "http_version": response.extensions.get("http_version"),
            "reason_phrase": response.reason_phrase,
            "timestamp": time.time(),
        }
        cdef bytes payload = json.dumps(entry, separators=(",", ":")).encode("utf-8")
        cdef int fd = -1
        try:
            fd = os.open(os.fspath(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as temp_file:
                fd = -1
                temp_file.write(payload)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(os.fspath(tmp_path), os.fspath(path))
            os.chmod(os.fspath(path), 0o600)
        finally:
            if fd != -1:
                os.close(fd)
            with contextlib.suppress(OSError):
                os.unlink(os.fspath(tmp_path))
        self._cleanup()

    # ------------------------------------------------------------------
    cdef void _cleanup(self) except *:
        cdef double cutoff
        cdef bint check_expiry = False
        if self.has_ttl:
            cutoff = time.time() - self.max_age
            check_expiry = True
        else:
            cutoff = 0.0
        files = sorted(self.directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        cdef int kept = 0
        cdef object file_path
        for file_path in files:
            if check_expiry:
                try:
                    data = json.loads(file_path.read_text("utf-8"))
                    timestamp = float(data["timestamp"])
                except Exception:
                    with contextlib.suppress(OSError):
                        file_path.unlink()
                    continue
                if timestamp < cutoff:
                    with contextlib.suppress(OSError):
                        file_path.unlink()
                    continue
            kept += 1
            if kept > self.max_entries:
                with contextlib.suppress(OSError):
                    file_path.unlink()

    # ------------------------------------------------------------------
    cpdef void clear(self):
        cdef object file
        for file in self.directory.glob("*.json"):
            with contextlib.suppress(OSError):
                file.unlink()
