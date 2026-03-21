# Main.py
import os
import ctypes
import ctypes.wintypes
import random

# Supported image extensions
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

# IDesktopWallpaper COM interface GUIDs
_CLSID_DesktopWallpaper = "{C2CF3110-460E-4fc1-B9D0-8A1C0C9CC4BD}"
_IID_IDesktopWallpaper  = "{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}"


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _str_to_guid(s):
    g = _GUID()
    ctypes.windll.ole32.CLSIDFromString(s, ctypes.byref(g))
    return g


def _set_wallpaper_primary_monitor(image_path):
    """Set wallpaper on primary monitor only via IDesktopWallpaper COM interface."""
    ole32 = ctypes.windll.ole32
    ole32.CoInitialize(None)

    clsid = _str_to_guid(_CLSID_DesktopWallpaper)
    iid   = _str_to_guid(_IID_IDesktopWallpaper)

    ppv = ctypes.c_void_p()
    hr = ole32.CoCreateInstance(
        ctypes.byref(clsid),
        None,
        4,  # CLSCTX_LOCAL_SERVER
        ctypes.byref(iid),
        ctypes.byref(ppv),
    )
    if hr != 0:
        print(f"IDesktopWallpaper CoCreateInstance failed: 0x{hr & 0xFFFFFFFF:08X}")
        return False

    # Vtable layout (after IUnknown's 3 methods):
    # [3] SetWallpaper(this, monitorID: LPWSTR, wallpaper: LPWSTR)
    # [4] GetWallpaper(this, monitorID: LPWSTR, wallpaper: LPWSTR*)
    # [5] GetMonitorDevicePathAt(this, monitorIndex: UINT, monitorID: LPWSTR*)
    # [6] GetMonitorDevicePathCount(this, count: UINT*)
    # [7] GetMonitorRECT(this, monitorID: LPWSTR, rect: RECT*)
    vtable = ctypes.cast(
        ctypes.cast(ppv, ctypes.POINTER(ctypes.c_void_p))[0],
        ctypes.POINTER(ctypes.c_void_p),
    )

    f_count = ctypes.WINFUNCTYPE(
        ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)
    )(vtable[6])

    f_path_at = ctypes.WINFUNCTYPE(
        ctypes.HRESULT, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)
    )(vtable[5])

    f_rect = ctypes.WINFUNCTYPE(
        ctypes.HRESULT, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(ctypes.wintypes.RECT)
    )(vtable[7])

    f_set = ctypes.WINFUNCTYPE(
        ctypes.HRESULT, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p
    )(vtable[3])

    count = ctypes.c_uint(0)
    f_count(ppv, ctypes.byref(count))

    if count.value == 0:
        print("IDesktopWallpaper: no monitors found")
        return False

    # Primary monitor is the one whose rect starts at (0, 0)
    primary_id = None
    for i in range(count.value):
        id_ptr = ctypes.c_void_p()
        if f_path_at(ppv, i, ctypes.byref(id_ptr)) != 0 or not id_ptr.value:
            continue
        monitor_id = ctypes.cast(id_ptr, ctypes.c_wchar_p).value
        rect = ctypes.wintypes.RECT()
        f_rect(ppv, monitor_id, ctypes.byref(rect))
        if rect.left == 0 and rect.top == 0:
            primary_id = monitor_id
            break

    if primary_id is None:
        # Fallback: use first monitor
        id_ptr = ctypes.c_void_p()
        if f_path_at(ppv, 0, ctypes.byref(id_ptr)) == 0 and id_ptr.value:
            primary_id = ctypes.cast(id_ptr, ctypes.c_wchar_p).value

    if not primary_id:
        return False

    hr = f_set(ppv, primary_id, image_path)
    if hr == 0:
        print(f"Set wallpaper on primary monitor: {os.path.basename(image_path)}")
        return True
    print(f"SetWallpaper failed: 0x{hr & 0xFFFFFFFF:08X}")
    return False


def is_valid_image_file(filename):
    """Check if a file has a valid image extension."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in VALID_IMAGE_EXTENSIONS


def change_wallpaper(image_path):
    if _set_wallpaper_primary_monitor(image_path):
        return True

    # Fallback: system-wide wallpaper change
    print("Falling back to SystemParametersInfoW")
    SPI_SETDESKWALLPAPER  = 20
    SPIF_UPDATEINIFILE    = 0x01
    SPIF_SENDWININICHANGE = 0x02
    try:
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, image_path,
            SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE,
        )
        return True
    except Exception as e:
        print(f"Error changing wallpaper: {e}")
        return False


def pick_image(folder_path):
    """Pick a random valid image file from the folder."""
    if not os.path.isdir(folder_path):
        raise ValueError(f"Invalid directory: {folder_path}")

    all_files = os.listdir(folder_path)
    image_files = [f for f in all_files if is_valid_image_file(f)]

    if not image_files:
        raise ValueError(f"No valid image files found in {folder_path}")

    filename = random.choice(image_files)
    return os.path.join(folder_path, filename)


def pick_and_change(folder_path):
    """Pick a random image from folder and set as wallpaper."""
    print(f"PickPath: {folder_path}")
    try:
        image_path = pick_image(folder_path)
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
