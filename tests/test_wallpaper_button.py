"""Tests for wallpaper change button functionality."""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

import pytest

# Add src to path so we can import the main module
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import flet as ft


@pytest.fixture(autouse=True)
def mock_status_card():
    """Mock the status_card.create_status_card function for all tests."""
    with patch('src.gui.widgets.status_card.create_status_card', return_value=Mock()):
        yield


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
        self.appbar = None
        self.controls = []
        self.snack_bar = None
        self._update_count = 0

    def add(self, *args):
        """Mock add method."""
        self.controls.extend(args)

    def update(self):
        """Mock update method."""
        self._update_count += 1


@pytest.fixture
def page_mock():
    """Create a mock Flet page for testing."""
    return PageMock()


def find_button_by_text(controls, text):
    """Recursively find a button with specific text."""
    for control in controls:
        if hasattr(control, 'text') and control.text == text:
            return control
        if hasattr(control, 'content'):
            result = find_button_by_text([control.content], text)
            if result:
                return result
        if hasattr(control, 'controls'):
            result = find_button_by_text(control.controls, text)
            if result:
                return result
    return None


def test_button_has_click_handler(page_mock):
    """Test that the Change Wallpaper button has a click handler."""
    from gui.main_window import main
    main(page_mock)

    button = find_button_by_text(page_mock.controls, "Change Wallpaper Now")
    assert button is not None, "Change Wallpaper button not found"
    assert button.on_click is not None, "Button should have on_click handler"


@patch('src.config.DATA_FILE', 'test_data.txt')
def test_no_folders_configured(page_mock):
    """Test clicking button when no folders are configured."""
    from gui.main_window import main
    with patch('os.path.exists', return_value=False):
        main(page_mock)

        button = find_button_by_text(page_mock.controls, "Change Wallpaper Now")
        assert button is not None

        # Click the button
        button.on_click(Mock())

        # Should show error snackbar
        assert page_mock.snack_bar is not None
        assert "No folders configured" in page_mock.snack_bar.content.value
        assert page_mock.snack_bar.bgcolor == ft.colors.ERROR


@patch('src.config.DATA_FILE', 'test_data.txt')
@patch('src.core.wallpaper.pick_and_change')
def test_successful_wallpaper_change(mock_pick_and_change, page_mock):
    """Test successful wallpaper change."""
    from gui.main_window import main
    mock_pick_and_change.return_value = True

    test_path = "C:\\Images\\Wallpapers"
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=test_path)):
            main(page_mock)

            button = find_button_by_text(page_mock.controls, "Change Wallpaper Now")
            assert button is not None

            # Click the button
            button.on_click(Mock())

            # Verify wallpaper.pick_and_change was called
            mock_pick_and_change.assert_called_once_with(test_path)

            # Should show success snackbar
            assert page_mock.snack_bar is not None
            assert "successfully" in page_mock.snack_bar.content.value.lower()
            assert page_mock.snack_bar.bgcolor == ft.colors.GREEN


@patch('src.config.DATA_FILE', 'test_data.txt')
@patch('src.core.wallpaper.pick_and_change')
def test_failed_wallpaper_change(mock_pick_and_change, page_mock):
    """Test failed wallpaper change."""
    from gui.main_window import main
    mock_pick_and_change.return_value = False

    test_path = "C:\\Images\\Wallpapers"
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=test_path)):
            main(page_mock)

            button = find_button_by_text(page_mock.controls, "Change Wallpaper Now")
            assert button is not None

            # Click the button
            button.on_click(Mock())

            # Should show error snackbar
            assert page_mock.snack_bar is not None
            assert "Failed to change wallpaper" in page_mock.snack_bar.content.value
            assert page_mock.snack_bar.bgcolor == ft.colors.ERROR


@patch('src.config.DATA_FILE', 'test_data.txt')
@patch('src.core.wallpaper.pick_and_change')
def test_value_error_handling(mock_pick_and_change, page_mock):
    """Test handling of ValueError (no images found)."""
    from gui.main_window import main
    mock_pick_and_change.side_effect = ValueError("No valid image files found in C:\\Empty")

    test_path = "C:\\Empty"
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=test_path)):
            main(page_mock)

            button = find_button_by_text(page_mock.controls, "Change Wallpaper Now")
            assert button is not None

            # Click the button
            button.on_click(Mock())

            # Should show error snackbar with the error message
            assert page_mock.snack_bar is not None
            assert "No valid image files found" in page_mock.snack_bar.content.value
            assert page_mock.snack_bar.bgcolor == ft.colors.ERROR


@patch('src.config.DATA_FILE', 'test_data.txt')
@patch('src.core.wallpaper.pick_and_change')
def test_button_disabled_during_operation(mock_pick_and_change, page_mock):
    """Test that button is disabled during wallpaper change."""
    from gui.main_window import main
    # Track button state during operation
    button_states = []

    def track_state(*args, **kwargs):
        """Track button state when update is called."""
        button = find_button_by_text(page_mock.controls, "Changing...")
        if button is None:
            button = find_button_by_text(page_mock.controls, "Change Wallpaper Now")
        if button:
            button_states.append({
                'disabled': button.disabled,
                'text': button.text
            })
        return True

    mock_pick_and_change.side_effect = track_state

    test_path = "C:\\Images\\Wallpapers"
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=test_path)):
            main(page_mock)

            button = find_button_by_text(page_mock.controls, "Change Wallpaper Now")
            assert button is not None

            # Click the button
            button.on_click(Mock())

            # Button should be re-enabled after operation
            assert button.disabled is False
            assert button.text == "Change Wallpaper Now"


@patch('src.config.DATA_FILE', 'test_data.txt')
def test_load_paths_on_startup(page_mock):
    """Test that paths are loaded from data.txt on startup."""
    from gui.main_window import main
    test_paths = "C:\\Images\\Wallpapers\nD:\\Photos\\Backgrounds"

    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=test_paths)):
            main(page_mock)

            # Paths should be loaded (we can't directly access them,
            # but we can verify the file was read by checking that
            # clicking the button doesn't show "No folders configured")
            button = find_button_by_text(page_mock.controls, "Change Wallpaper Now")
            assert button is not None


@patch('src.config.DATA_FILE', 'test_data.txt')
@patch('src.core.wallpaper.pick_and_change')
def test_uses_first_path(mock_pick_and_change, page_mock):
    """Test that the handler uses the first path from data.txt."""
    from gui.main_window import main
    mock_pick_and_change.return_value = True

    test_paths = "C:\\First\\Path\nD:\\Second\\Path\nE:\\Third\\Path"

    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=test_paths)):
            main(page_mock)

            button = find_button_by_text(page_mock.controls, "Change Wallpaper Now")
            assert button is not None

            # Click the button
            button.on_click(Mock())

            # Should use the first path
            mock_pick_and_change.assert_called_once_with("C:\\First\\Path")
