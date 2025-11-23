from types import MappingProxyType
from typing import Callable

ctypedef object Subscriber

cdef class _BaseSignal:
    cdef object _value
    cdef object _comparer
    cdef dict _subscribers
    cdef int _next_token

    cpdef object get(self)
    cdef bint _set_value(self, object value)
    cdef void _notify(self)

cdef class Signal(_BaseSignal):
    cpdef object set(self, object value)

cdef class DerivedSignal(_BaseSignal):
    cdef _BaseSignal _source
    cdef object _selector
    cdef object _unsubscribe

    cdef void _propagate(self, object source_value)

cdef class Store:
    cdef dict _signals
    cdef dict _children
    cdef Signal _root
    cdef object _create_snapshot(self)
    cdef void _sync_root(self)
    cdef void _link_child(self, str name, Signal signal)
