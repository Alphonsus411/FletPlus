# tests/test_all.py

from tests.test_smart_table import test_smart_table_full_behavior
from tests.test_sidebar_admin import test_sidebar_admin_build_and_selection
from tests.test_responsive_grid import test_responsive_grid_builds_correctly
from tests.test_theme_manager import test_theme_manager_initialization_and_toggle
from tests.test_fletplus_app import test_fletplus_app_initialization_and_routing

def test_all_components():
    test_smart_table_full_behavior()
    test_sidebar_admin_build_and_selection()
    test_responsive_grid_builds_correctly()
    test_theme_manager_initialization_and_toggle()
    test_fletplus_app_initialization_and_routing()
