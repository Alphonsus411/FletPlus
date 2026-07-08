import flet as ft

from fletplus.utils.device_profiles import DeviceProfile
from fletplus.utils.viewport import (
    active_device_profile,
    safe_mobile_padding,
    safe_page_height,
    safe_page_size,
    safe_page_width,
    viewport_orientation,
    visual_density_for_page,
)


class DummyPage:
    def __init__(self, width=None, height=None):
        self.width = width
        self.height = height


def test_safe_page_size_normalizes_missing_values():
    page = DummyPage(width=None, height=-10)

    assert safe_page_width(page, fallback=375) == 375
    assert safe_page_height(page) == 0
    assert safe_page_size(page, fallback_width=375) == (375, 0)


def test_viewport_orientation_and_profile():
    page = DummyPage(width=390, height=844)

    assert viewport_orientation(page) == "portrait"
    assert active_device_profile(page).name == "mobile"
    assert visual_density_for_page(page) == "compact"


def test_visual_density_promotes_desktop_to_comfortable():
    page = DummyPage(width=1280, height=800)

    assert viewport_orientation(page) == "landscape"
    assert active_device_profile(page).name == "desktop"
    assert visual_density_for_page(page) == "comfortable"


def test_safe_mobile_padding_uses_custom_profiles():
    profiles = (DeviceProfile("mobile", 0, 499, 4), DeviceProfile("wide", 500, None, 12))
    page = DummyPage(width=700, height=500)

    padding = safe_mobile_padding(page, base=20, profiles=profiles)

    assert isinstance(padding, ft.Padding)
    assert padding.left == padding.right
    assert padding.top == padding.bottom
