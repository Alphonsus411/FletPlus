# cython: language_level=3

cdef class DiskCache:
    cdef object directory
    cdef int max_entries
    cdef double max_age
    cdef bint has_ttl

    cdef object _path_for(self, str key)
    cdef bint _is_expired(self, double timestamp) except *
    cdef void _cleanup(self) except *

    cpdef str build_key(self, object request)
    cpdef object get(self, str key, object request=*)
    cpdef void set(self, str key, object response)
    cpdef void clear(self)
