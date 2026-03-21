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

# Sentinel for "all monitors"
ALL_MONITORS = "ALL"


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


def _init_com():
    """Initialize IDesktopWallpaper COM interface.

    Returns (ppv, funcs) where funcs is a dict of bound vtable callables,
    or (None, None) on failure.
    """
    ole32 = ctypes.windll.ole32
    ole32.CoInitialize(None)

    clsid = _str_to_guid(_CLSID_DesktopWallpaper)
    iid   = _str_to_guid(_IID_IDesktopWallpaper)

    ppv = ctypes.c_void_p()
    hr = ole32.CoCreateInstance(
        ctypes.byref(clsid), None, 4,  # CLSCTX_LOCAL_SERVER
        ctypes.byref(iid), ctypes.byref(ppv),
    )
    if hr != 0:
        print(f"IDesktopWallpaper CoCreateInstance failed: 0x{hr & 0xFFFFFFFF:08X}")
        return None, None

    # IDesktopWallpaper vtable (after IUnknown's 3 slots):
    # [3] SetWallpaper(this, monitorID: LPWSTR, wallpaper: LPWSTR)
    # [4] GetWallpaper(this, monitorID: LPWSTR, wallpaper: LPWSTR*)
    # [5] GetMonitorDevicePathAt(this, monitorIndex: UINT, monitorID: LPWSTR*)
    # [6] GetMonitorDevicePathCount(this, count: UINT*)
    # [7] GetMonitorRECT(this, monitorID: LPWSTR, rect: RECT*)
    vtable = ctypes.cast(
        ctypes.cast(ppv, ctypes.POINTER(ctypes.c_void_p))[0],
        ctypes.POINTER(ctypes.c_void_p),
    )
    funcs = {
        'set': ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p
        )(vtable[3]),
        'path_at': ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)
        )(vtable[5]),
        'count': ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)
        )(vtable[6]),
        'rect': ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(ctypes.wintypes.RECT)
        )(vtable[7]),
    }
    return ppv, funcs


def _enum_monitors(ppv, funcs):
    """Return list of raw monitor dicts from an open COM session."""
    count = ctypes.c_uint(0)
    funcs['count'](ppv, ctypes.byref(count))
    monitors = []
    for i in range(count.value):
        id_ptr = ctypes.c_void_p()
        if funcs['path_at'](ppv, i, ctypes.byref(id_ptr)) != 0 or not id_ptr.value:
            continue
        monitor_id = ctypes.cast(id_ptr, ctypes.c_wchar_p).value
        rect = ctypes.wintypes.RECT()
        funcs['rect'](ppv, monitor_id, ctypes.byref(rect))
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        monitors.append({
            'id': monitor_id,
            'index': i,
            'is_primary': rect.left == 0 and rect.top == 0,
            'left': rect.left,
            'top': rect.top,
            'right': rect.right,
            'bottom': rect.bottom,
            'width': w,
            'height': h,
        })
    return monitors


def get_monitors():
    """Return list of monitor info dicts for use by the UI.

    Each dict has: id, index, is_primary, left, top, right, bottom, width, height.
    Returns [] if COM is unavailable.
    """
    ppv, funcs = _init_com()
    if ppv is None:
        return []
    return _enum_monitors(ppv, funcs)


def is_valid_image_file(filename):
    """Check if a file has a valid image extension."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in VALID_IMAGE_EXTENSIONS


def change_wallpaper(image_path, monitor_id=None):
    """Set wallpaper via IDesktopWallpaper COM interface.

    monitor_id=None  -> primary monitor only
    monitor_id=ALL_MONITORS -> every connected monitor
    monitor_id=<str> -> specific monitor by device path
    Falls back to SystemParametersInfoW if COM unavailable.
    """
    ppv, funcs = _init_com()

    if ppv is not None:
        monitors = _enum_monitors(ppv, funcs)

        if monitor_id == ALL_MONITORS:
            success = False
            for m in monitors:
                if funcs['set'](ppv, m['id'], image_path) == 0:
                    success = True
            if success:
                print(f"Set wallpaper on all monitors: {os.path.basename(image_path)}")
            return success

        # Resolve target monitor
        if monitor_id is None:
            target = next((m for m in monitors if m['is_primary']), None)
            if target is None and monitors:
                target = monitors[0]
        else:
            target = next((m for m in monitors if m['id'] == monitor_id), None)

        if target:
            hr = funcs['set'](ppv, target['id'], image_path)
            if hr == 0:
                label = "primary" if target['is_primary'] else f"monitor {target['index']+1}"
                print(f"Set wallpaper on {label}: {os.path.basename(image_path)}")
                return True
            print(f"SetWallpaper failed: 0x{hr & 0xFFFFFFFF:08X}")
            return False

    # Fallback: system-wide via Win32
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


def pick_and_change(folder_path, monitor_id=None):
    """Pick a random image from folder and set as wallpaper."""
    print(f"PickPath: {folder_path}")
    try:
        image_path = pick_image(folder_path)
        abs_path = os.path.abspath(image_path)

        if change_wallpaper(abs_path, monitor_id=monitor_id):
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
