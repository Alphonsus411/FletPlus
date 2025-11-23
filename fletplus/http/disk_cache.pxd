# cython: language_level=3
from pathlib import Path
import httpx

cdef class DiskCache:
    cdef Path directory
    cdef int max_entries
    cdef double max_age
    cdef bint has_ttl

    cpdef str build_key(self, httpx.Request request)
    cpdef httpx.Response | None get(self, str key, *, httpx.Request | None request=*)
    cpdef void set(self, str key, httpx.Response response)
    cpdef void clear(self)
