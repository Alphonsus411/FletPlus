# cython: language_level=3
import flet as ft
from typing import Callable, Dict

from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle
from fletplus.utils.device_profiles import DeviceProfile


cdef class ResponsiveManager:
    cdef public object page
    cdef dict breakpoints
    cdef dict height_breakpoints
    cdef dict orientation_callbacks
    cdef dict device_callbacks
    cdef tuple device_profiles
    cdef tuple _width_bp_keys
    cdef tuple _height_bp_keys

    cdef object _current_width_bp
    cdef object _current_height_bp
    cdef object _current_orientation
    cdef object _current_device

    cdef dict _styles
    cdef dict _style_state

    cpdef void _apply_style(self, object control)
    cpdef dict _capture_base_attributes(self, object control)
    cpdef void _safe_setattr(self, object control, str attr, object value)
    cpdef void _handle_resize(self, object e=*)
