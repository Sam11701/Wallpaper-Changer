import os
import ctypes
import random
from datetime import datetime, time, timedelta, date
import time

#ToDo
"""def repeat(interval=1):
    i = 0
    minut_to_run =[]
    minutes = 59
    while minutes >= 0:
       minut_to_run.append(minutes)
       minutes -= interval

    while i <= 1:
       t = datetime.now()
       my_time = t.strftime("%H:%M:%S.%f")

       if t.second >= 50 and t.minute in minut_to_run:
           print("my local time is", my_time)
           time.sleep(55)
           print("after sleep print time is", t)"""

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

def pick_and_change(folder_path):
    print("PickPath: "+folder_path)
    image_path = os.path.abspath(folder_path)  # Replace with the image path
    if change_wallpaper(pick_image(image_path)):
        print("Wallpaper changed successfully!")
    else:
        print("Failed to change wallpaper.")