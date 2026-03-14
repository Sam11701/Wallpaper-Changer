# Main.py
import os
import ctypes
import random

# Supported image extensions
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

def is_valid_image_file(filename):
    """Check if a file has a valid image extension."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in VALID_IMAGE_EXTENSIONS

def change_wallpaper(image_path):
    # Constants for setting the wallpaper
    SPI_SETDESKWALLPAPER = 20  # Action to change wallpaper
    SPIF_UPDATEINIFILE = 0x01  # Update user profile
    SPIF_SENDWININICHANGE = 0x02  # Notify change to system

    try:
        # Call Windows API to change wallpaper
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path,
                                                   SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE)
        return True
    except Exception as e:
        # Print error message if wallpaper change fails
        print(f"Error changing wallpaper: {e}")
        return False

def pick_image(folder_path):
    """Pick a random valid image file from the folder."""
    if not os.path.isdir(folder_path):
        raise ValueError(f"Invalid directory: {folder_path}")

    # Get all files in directory
    all_files = os.listdir(folder_path)

    # Filter for valid image files only
    image_files = [f for f in all_files if is_valid_image_file(f)]

    if not image_files:
        raise ValueError(f"No valid image files found in {folder_path}")

    # Pick random image and return full path
    filename = random.choice(image_files)
    return os.path.join(folder_path, filename)

def pick_and_change(folder_path):
    """Pick a random image from folder and set as wallpaper."""
    print(f"PickPath: {folder_path}")
    try:
        image_path = pick_image(folder_path)
        # Convert to absolute path for Windows API
        abs_path = os.path.abspath(image_path)

        if change_wallpaper(abs_path):
            print(f"Wallpaper changed successfully to: {os.path.basename(abs_path)}")
            return True
        else:
            print("Failed to change wallpaper.")
            return False
    except ValueError as e:
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
