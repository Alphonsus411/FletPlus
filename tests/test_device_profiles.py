import pytest

from fletplus.utils.device_profiles import (
    DeviceProfile,
    DEFAULT_DEVICE_PROFILES,
    get_device_profile,
    device_name,
    columns_for_width,
    iter_device_profiles,
)


def test_default_profiles_cover_common_ranges():
    assert device_name(320) == "mobile"
    assert device_name(700) == "tablet"
    assert device_name(1280) == "desktop"
    assert columns_for_width(350) == 4
    assert columns_for_width(980) == 8
    assert columns_for_width(1600) == 12


def test_iter_device_profiles_returns_sorted_sequence():
    names = [profile.name for profile in iter_device_profiles(DEFAULT_DEVICE_PROFILES)]
    assert names == ["mobile", "tablet", "desktop"]


def test_custom_profiles_override_defaults():
    profiles = (
        DeviceProfile("watch", min_width=0, max_width=299, columns=2),
        DeviceProfile("mobile", min_width=300, max_width=699, columns=4),
        DeviceProfile("desktop", min_width=700, max_width=None, columns=12),
    )
    assert get_device_profile(250, profiles).name == "watch"
    assert get_device_profile(450, profiles).columns == 4
    assert get_device_profile(1200, profiles).name == "desktop"


def test_get_device_profile_requires_profiles():
    with pytest.raises(ValueError):
        get_device_profile(100, profiles=())
