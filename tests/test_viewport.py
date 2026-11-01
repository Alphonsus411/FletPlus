import flet as ft
import pytest

from fletplus.utils.device_profiles import (
    EXTENDED_DEVICE_PROFILES,
    DeviceProfile,
    get_device_profile,
)
from fletplus.utils.viewport import (
    active_device_profile,
    orientation_from_size,
    safe_mobile_padding,
    safe_page_height,
    safe_page_size,
    safe_page_width,
    viewport_info,
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


def test_viewport_info_reuses_consistent_snapshot():
    page = DummyPage(width=420, height=900)

    info = viewport_info(page, padding_base=20)

    assert info.width == 420
    assert info.height == 900
    assert info.orientation == "portrait"
    assert info.profile.name == "mobile"
    assert info.density == "compact"
    assert info.padding.left == 15
    assert info.padding.top == 16
    assert info.padding.bottom == 20


@pytest.mark.parametrize(
    ("width", "height", "expected"),
    [
        (390, 844, "portrait"),
        (844, 390, "landscape"),
        (600, 600, "portrait"),
        (1024, 768, "landscape"),
    ],
)
def test_orientation_from_size_covers_portrait_and_landscape(width, height, expected):
    assert orientation_from_size(width, height) == expected
    page = DummyPage(width=width, height=height)
    assert viewport_orientation(page) == expected


@pytest.mark.parametrize(
    ("width", "expected_profile", "expected_columns"),
    [
        (320, "mobile", 4),
        (599, "mobile", 4),
        (600, "tablet", 8),
        (900, "tablet", 8),
        (1023, "tablet", 8),
        (1024, "desktop", 12),
        (1366, "desktop", 12),
    ],
)
def test_active_device_profile_covers_default_breakpoints(
    width, expected_profile, expected_columns
):
    page = DummyPage(width=width, height=800)

    profile = active_device_profile(page)

    assert profile.name == expected_profile
    assert profile.columns == expected_columns


@pytest.mark.parametrize(
    ("width", "expected_profile", "expected_columns"),
    [
        (1280, "desktop", 12),
        (1439, "desktop", 12),
        (1440, "large_desktop", 16),
        (1920, "large_desktop", 16),
    ],
)
def test_active_device_profile_supports_extended_large_desktop(
    width, expected_profile, expected_columns
):
    page = DummyPage(width=width, height=900)

    profile = active_device_profile(page, profiles=EXTENDED_DEVICE_PROFILES)

    assert profile.name == expected_profile
    assert profile.columns == expected_columns
    assert get_device_profile(width, EXTENDED_DEVICE_PROFILES) == profile


@pytest.mark.parametrize(
    ("width", "height", "expected_profile", "expected_orientation", "expected_density"),
    [
        (375, 812, "mobile", "portrait", "compact"),
        (820, 1180, "tablet", "portrait", "normal"),
        (1280, 800, "desktop", "landscape", "comfortable"),
        (1600, 900, "large_desktop", "landscape", "comfortable"),
    ],
)
def test_viewport_info_resolves_profiles_and_orientation(
    width, height, expected_profile, expected_orientation, expected_density
):
    page = DummyPage(width=width, height=height)

    info = viewport_info(page, profiles=EXTENDED_DEVICE_PROFILES)

    assert info.width == width
    assert info.height == height
    assert info.profile.name == expected_profile
    assert info.orientation == expected_orientation
    assert info.density == expected_density
