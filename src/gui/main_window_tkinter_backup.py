"""
BACKUP: Original tkinter UI (deprecated, kept for reference during migration).
New Flet UI is in main_window.py
"""
import os
import pathlib
import pystray
import sys
from PIL import Image as PILImage, ImageDraw
import threading
import keyboard
import json
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from src.core import wallpaper
from src.gui import hotkey_manager
from src.config import (
    DATA_FILE,
    HOTKEY_FILE,
    DEFAULT_INTERVAL_SECONDS,
    MAX_INTERVAL_HOURS,
    TRAY_ICON_SIZE
)

def validate_time_input(min_str, sec_str):
    """Validate time interval inputs. Returns (valid, interval_seconds, error_msg)."""
    try:
        min_val = int(min_str) if min_str.isdigit() else 0
        sec_val = int(sec_str) if sec_str.isdigit() else 0
    except ValueError:
        return False, 0, "Invalid time format"

    if min_val < 0 or sec_val < 0:
        return False, 0, "Time values cannot be negative"

    interval_seconds = (min_val * 60) + sec_val

    if interval_seconds == 0:
        return False, 0, "Interval must be greater than zero"

    if interval_seconds > (MAX_INTERVAL_HOURS * 3600):
        return False, 0, f"Interval cannot exceed {MAX_INTERVAL_HOURS} hours"

    return True, interval_seconds, ""

global path
interval_thread = None
interval_active = False
active_timer = None
hotkey_bindings = {"start": {}, "stop": [], "change": [], "show": []}
current_auto_path = None
tray_icon = None
tray_icon_running = False
already_minimized = False

def get_path():
    global path
    new_path = Path_entry.get()
    p = pathlib.PureWindowsPath(new_path)
    path = p.as_posix()
    return path

def load_hotkey_bindings():
    default = {"start": {}, "stop": [], "change": [], "show": []}
    if os.path.exists(HOTKEY_FILE):
        try:
            with open(HOTKEY_FILE, "r") as f:
                data = json.load(f)
                for key in default:
                    if key not in data:
                        data[key] = default[key]
                print(data)
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading hotkey bindings: {e}")
            backup_file = f"{HOTKEY_FILE}.backup"
            try:
                if os.path.exists(HOTKEY_FILE):
                    os.rename(HOTKEY_FILE, backup_file)
                    print(f"Corrupted file backed up to {backup_file}")
            except Exception as backup_err:
                print(f"Failed to backup corrupted file: {backup_err}")
            return default
    return default

def save_hotkey_bindings():
    try:
        with open(HOTKEY_FILE, "w") as f:
            json.dump(hotkey_bindings, f, indent=4)
    except IOError as e:
        print(f"Error saving hotkey bindings: {e}")

def start_auto_change_for_path(target_path):
    global interval_active, current_auto_path, active_timer
    if not os.path.isdir(target_path):
        Update_label['text'] = "Invalid Directory"
        return

    if active_timer:
        active_timer.cancel()
        active_timer = None

    current_auto_path = target_path
    interval_active = True

    valid, interval_seconds, error_msg = validate_time_input(min_entry.get(), sec_entry.get())
    if not valid:
        interval_seconds = DEFAULT_INTERVAL_SECONDS
        Update_label['text'] = f"{error_msg}, using default {DEFAULT_INTERVAL_SECONDS}s"

    Update_label['text'] = f"Auto-changing every {interval_seconds}s from {target_path}"

    def loop():
        global active_timer
        if interval_active and os.path.isdir(current_auto_path):
            wallpaper.pick_and_change(current_auto_path)
            active_timer = threading.Timer(interval_seconds, loop)
            active_timer.start()

    loop()

def start_interval_change():
    global interval_thread, interval_active, active_timer
    selected = Path_listbox.curselection()
    if not selected:
        Update_label['text'] = "No Path Selected"
        return

    selected_path = Path_listbox.get(selected[0])
    if not os.path.isdir(selected_path):
        Update_label['text'] = "Invalid Directory"
        return

    if active_timer:
        active_timer.cancel()
        active_timer = None

    interval_active = True
    valid, interval_seconds, error_msg = validate_time_input(min_entry.get(), sec_entry.get())
    if not valid:
        interval_seconds = DEFAULT_INTERVAL_SECONDS
        Update_label['text'] = f"{error_msg}, using default {DEFAULT_INTERVAL_SECONDS}s"
    else:
        Update_label['text'] = f"Auto-changing every {interval_seconds}s"

    def loop():
        global active_timer
        if interval_active:
            wallpaper.pick_and_change(selected_path)
            active_timer = threading.Timer(interval_seconds, loop)
            active_timer.start()

    loop()

def stop_interval_change():
    global interval_active, active_timer
    if active_timer:
        active_timer.cancel()
        active_timer = None
    interval_active = False
    Update_label['text'] = "Auto-change stopped"

def get_data():
    try:
        with open(DATA_FILE, "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []
    except (IOError, UnicodeDecodeError) as e:
        print(f"Error reading data file: {e}")
        backup_file = f"{DATA_FILE}.backup"
        try:
            if os.path.exists(DATA_FILE):
                os.rename(DATA_FILE, backup_file)
                print(f"Corrupted file backed up to {backup_file}")
        except Exception as backup_err:
            print(f"Failed to backup corrupted file: {backup_err}")
        return []

def browse_folder(arr):
    selected_folder = filedialog.askdirectory()
    if selected_folder:
        Path_entry.delete(0, END)
        add_path(selected_folder, arr)
        Update_label['text'] = "Folder selected"

def add_path(new_path, arr):
    if not new_path:
        Update_label['text'] = "No path provided"
        return

    if not os.path.isdir(new_path):
        Update_label['text'] = "Invalid directory path"
        print(f"Path not valid: {new_path}")
        return

    if new_path in arr:
        Update_label['text'] = "Path already exists"
        return

    arr.append(new_path)
    update_file(arr)
    Path_listbox.insert(END, new_path)
    Update_label['text'] = "Path Added"

def remove_path():
    selected = Path_listbox.curselection()
    if selected:
        index = selected[0]
        path_to_remove = Path_listbox.get(index)
        Path_listbox.delete(index)
        if path_to_remove in data:
            data.remove(path_to_remove)
            update_file(data)
        Update_label['text'] = "Path Removed"

def change_wallpaper():
    selected = Path_listbox.curselection()
    if selected:
        index = selected[0]
        selected_path = Path_listbox.get(index)
        Main.pick_and_change(selected_path)
        Update_label['text'] = "Wallpaper Changed"
    else:
        Update_label['text'] = "No Path Selected"

def switch_path_by_hotkey(key_combo):
    global current_auto_path
    path = hotkey_bindings["start"].get(key_combo)
    if path and os.path.isdir(path):
        current_auto_path = path
        start_auto_change_for_path(path)
        Update_label['text'] = f"Started auto-change from hotkey: {key_combo}"
    else:
        Update_label['text'] = f"No valid path assigned to {key_combo}"

def stop_auto_change_hotkey():
    global interval_active
    interval_active = False
    print("Auto-change stopped via hotkey")
    Update_label['text'] = "Auto-change stopped via hotkey"

def change_wallpaper_hotkey():
    global current_auto_path
    if current_auto_path and os.path.isdir(current_auto_path):
        Main.pick_and_change(current_auto_path)
        Update_label['text'] = "Wallpaper changed via hotkey"
    else:
        Update_label['text'] = "No valid path for wallpaper change"

def show_ui_hotkey():
    global already_minimized
    already_minimized = False
    root.after(0, root.deiconify)
    Update_label['text'] = "UI restored via hotkey"

def create_image():
    # Simple blank image for icon; replace with a real icon if you have one
    image = PILImage.new('RGB', TRAY_ICON_SIZE, color='gray')
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill='white')
    return image

def on_tray_restore(icon, item):
    global tray_icon, tray_icon_running, already_minimized
    icon.stop()
    tray_icon = None
    tray_icon_running = False
    already_minimized = False
    root.after(0, root.deiconify)

def on_tray_exit(icon, item):
    global tray_icon, tray_icon_running, already_minimized
    icon.stop()
    tray_icon = None
    tray_icon_running = False
    already_minimized = False

    root.after(0, root.destroy)
    sys.exit(0)

def exit():
    tray_icon = None
    tray_icon_running = False
    already_minimized = False
    root.after(0, root.destroy)
    sys.exit(0)

def minimize_to_tray():
    global tray_icon, tray_icon_running

    if tray_icon_running:
        return  # Tray icon already active

    def run_tray():
        global tray_icon_running
        tray_icon_running = True
        tray_icon.run()
        tray_icon_running = False  # Reset when .run() exits

    root.withdraw()  # Hide the window
    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem("Restore", on_tray_restore),
        pystray.MenuItem("Exit", on_tray_exit)
    )
    tray_icon = pystray.Icon("WallpaperChanger", image, "Wallpaper Changer", menu)

    threading.Thread(target=run_tray, daemon=True).start()

def on_window_iconify(event):
    minimize_to_tray()

def handle_state_change(event):
    global already_minimized
    if root.state() == 'iconic' and not already_minimized:
        already_minimized = True
        minimize_to_tray()

def update_file(arr):
    try:
        with open(DATA_FILE, "w") as f:
            f.writelines(line + '\n' for line in arr)
    except IOError as e:
        print(f"Error writing data file: {e}")

# GUI Setup
root = Tk()
root.title("Wallpaper Changer")
root.geometry("600x500")
root.protocol("WM_DELETE_WINDOW", minimize_to_tray)
root.bind("<Visibility>", handle_state_change)
hotkey_actions = {
    "start": switch_path_by_hotkey,
    "stop": stop_auto_change_hotkey,
    "change": change_wallpaper_hotkey,
    "show": show_ui_hotkey,
}

main_frame = Frame(root)
main_frame.pack(fill=BOTH, expand=True)

left_frame = Frame(main_frame)
left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)
Path_listbox = Listbox(left_frame, height=20, width=50)
Path_listbox.pack(side=LEFT, fill=Y)
scrollbar = Scrollbar(left_frame, orient=VERTICAL)
scrollbar.config(command=Path_listbox.yview)
scrollbar.pack(side=RIGHT, fill=Y)
Path_listbox.config(yscrollcommand=scrollbar.set)

right_frame = Frame(main_frame)
right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

path_frame = Frame(right_frame)
path_frame.pack(pady=5)
Path_entry = ttk.Entry(path_frame, width=30)
Path_entry.pack(side=LEFT, padx=(0, 5))
Browse_button = ttk.Button(path_frame, text="Browse", command=lambda: browse_folder(data))
Browse_button.pack(side=RIGHT)

path_button_frame = Frame(right_frame)
path_button_frame.pack(pady=5)
Add_path_button = ttk.Button(path_button_frame, text="Add Path", command=lambda: add_path(get_path(), data))
Add_path_button.pack(side=LEFT, padx=(0, 5))
Remove_button = ttk.Button(path_button_frame, text="Remove Path", command=remove_path)
Remove_button.pack(side=LEFT)

Change_button = ttk.Button(right_frame, text="Change Wallpaper", command=change_wallpaper)
Change_button.pack(pady=5)

Close_button = ttk.Button(right_frame, text="Exit", command=exit)
Hotkey_manager_button = ttk.Button(
    right_frame,
    text="Manage Hotkeys",
    command=lambda: hotkey_manager.open_hotkey_window(
        root,
        Path_listbox,
        hotkey_bindings,
        hotkey_actions,
        Update_label,
        save_hotkey_bindings
    )
)
Update_label = ttk.Label(right_frame, text="")

time_frame = Frame(right_frame)
min_label = Label(time_frame, text="Minutes:")
min_label.pack(side=LEFT)
min_entry = ttk.Entry(time_frame, width=5)
min_entry.insert(0, "0")
min_entry.pack(side=LEFT, padx=(5, 15))
sec_label = Label(time_frame, text="Seconds:")
sec_label.pack(side=LEFT)

sec_entry = ttk.Entry(time_frame, width=5)
sec_entry.insert(0, "60")
sec_entry.pack(side=LEFT, padx=5)

interval_frame = Frame(right_frame)
interval_frame.pack(pady=5)
Start_interval_button = ttk.Button(interval_frame, text="Start Auto-Change", command=start_interval_change)
Start_interval_button.pack(side=LEFT, padx=(0, 5))
Stop_interval_button = ttk.Button(interval_frame, text="Stop Auto-Change", command=stop_interval_change)
Stop_interval_button.pack(side=LEFT)
time_frame.pack(pady=10)

Hotkey_manager_button.pack(pady=5)
Close_button.pack(pady=5)
Update_label.pack(pady=10)

data = get_data()
hotkey_bindings = load_hotkey_bindings()
for combo_str, path in hotkey_bindings["start"].items():
    print(f"Binding START hotkey: {combo_str} → {path}")
    # Create a closure factory to capture current value
    def make_hotkey_handler(key):
        return lambda: switch_path_by_hotkey(key)
    keyboard.add_hotkey(combo_str, make_hotkey_handler(combo_str))

for combo_str in hotkey_bindings["stop"]:
    keyboard.add_hotkey(combo_str, stop_auto_change_hotkey)

for combo_str in hotkey_bindings["change"]:
    keyboard.add_hotkey(combo_str, change_wallpaper_hotkey)

for combo_str in hotkey_bindings["show"]:
    keyboard.add_hotkey(combo_str, show_ui_hotkey)

for item in data:
    Path_listbox.insert(END, item)

root.mainloop()
