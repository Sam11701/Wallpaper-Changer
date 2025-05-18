import os
import ctypes
import random

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
    filename = random.choice(os.listdir(folder_path))
    return folder_path+"/"+filename

if __name__ == "__main__":
    image_path = os.path.abspath("C:/MSI/MSI Center/New folder/DESKTOP")  # Replace with the image path
    if change_wallpaper(pick_image(image_path)):
        print("Wallpaper changed successfully!")
    else:
        print("Failed to change wallpaper.")