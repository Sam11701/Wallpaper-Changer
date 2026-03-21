"""Tests for the Flet app skeleton."""
import sys
from pathlib import Path

import flet as ft
import pytest

# Add src to path so we can import the main module
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from gui.main_window import main


def test_app_configuration(page_mock):
    """Test that the app configures the page correctly."""
    main(page_mock)

    # Verify window configuration
    assert page_mock.title == "Wallpaper Changer"
    assert page_mock.window_width == 800
    assert page_mock.window_height == 600
    assert page_mock.window_min_width == 600
    assert page_mock.window_min_height == 500


def test_app_theme_configuration(page_mock):
    """Test that the app applies the correct theme."""
    main(page_mock)

    # Verify theme is set
    assert page_mock.theme is not None
    assert page_mock.theme.use_material3 is True

    # Verify color scheme
    color_scheme = page_mock.theme.color_scheme
    assert color_scheme.primary == "#8B5CF6"  # Soft purple
    assert color_scheme.secondary == "#FF6B6B"  # Warm coral
    assert color_scheme.surface == "#FFFFFF"  # White cards
    assert color_scheme.on_primary == "#FFFFFF"  # White text on purple
    assert color_scheme.on_surface == "#2D3748"  # Dark text on white


def test_app_background_color(page_mock):
    """Test that the app sets the correct background color."""
    main(page_mock)

    # Verify background color
    assert page_mock.bgcolor == "#FAFAFA"  # Off-white background


def test_app_content(page_mock):
    """Test that the app adds content to the page."""
    main(page_mock)

    # Verify that content was added
    assert len(page_mock.controls) > 0


@pytest.fixture
def page_mock():
    """Create a mock Flet page for testing."""
    page = PageMock()
    return page


class PageMock:
    """Mock Flet Page for testing."""

    def __init__(self):
        self.title = None
        self.window_width = None
        self.window_height = None
        self.window_min_width = None
        self.window_min_height = None
        self.theme = None
        self.bgcolor = None
        self.controls = []

    def add(self, *args):
        """Mock add method."""
        self.controls.extend(args)
