import os
import ctypes

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

if __name__ == "__main__":
    # Provide the absolute path to the image file
    image_path = os.path.abspath("C:/MSI/MSI Center/New folder/DESKTOP/1847_106.jpg")  # Replace with the image path
    if change_wallpaper(image_path):
        print("Wallpaper changed successfully!")
    else:
        print("Failed to change wallpaper.")