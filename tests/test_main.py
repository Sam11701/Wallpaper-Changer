# tests/test_main.py
import os
import tempfile
import pytest
from src.core.wallpaper import pick_image, is_valid_image_file

def test_is_valid_image_file_accepts_images():
    assert is_valid_image_file("photo.jpg") == True
    assert is_valid_image_file("image.png") == True
    assert is_valid_image_file("pic.jpeg") == True
    assert is_valid_image_file("wall.bmp") == True
    assert is_valid_image_file("background.gif") == True

def test_is_valid_image_file_rejects_non_images():
    assert is_valid_image_file("document.txt") == False
    assert is_valid_image_file("data.json") == False
    assert is_valid_image_file("script.py") == False
    assert is_valid_image_file("readme.md") == False

def test_pick_image_only_selects_valid_images(tmp_path):
    # Create test directory with mixed files
    (tmp_path / "image1.jpg").touch()
    (tmp_path / "image2.png").touch()
    (tmp_path / "notimage.txt").touch()
    (tmp_path / "data.json").touch()

    # Should only pick from valid images
    for _ in range(10):
        selected = pick_image(str(tmp_path))
        assert os.path.basename(selected) in ["image1.jpg", "image2.png"]

def test_pick_image_raises_on_empty_directory(tmp_path):
    with pytest.raises(ValueError, match="No valid image files found"):
        pick_image(str(tmp_path))

def test_pick_image_raises_on_no_images(tmp_path):
    (tmp_path / "document.txt").touch()
    (tmp_path / "data.json").touch()

    with pytest.raises(ValueError, match="No valid image files found"):
        pick_image(str(tmp_path))
