import Main
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
import Hotkey

global path
interval_thread = None
interval_active = False
hotkey_bindings = {"start": {}, "stop": []}
HOTKEY_FILE = "hotkeys.json"
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
    default_bindings = {"start": {}, "stop": []}
    if os.path.exists(HOTKEY_FILE):
        try:
            with open(HOTKEY_FILE, "r") as f:
                data = json.load(f)
                data.setdefault("start", {})
                data.setdefault("stop", [])
                return data
        except Exception as e:
            print(f"Error loading hotkeys.json: {e}")
            return default_bindings
    return default_bindings

def save_hotkey_bindings():
    with open(HOTKEY_FILE, "w") as f:
        json.dump(hotkey_bindings, f, indent=4)

def start_auto_change_for_path(target_path):
    global interval_active, current_auto_path
    if not os.path.isdir(target_path):
        Update_label['text'] = "Invalid Directory"
        return

    current_auto_path = target_path
    interval_active = True

    min_val = int(min_entry.get()) if min_entry.get().isdigit() else 0
    sec_val = int(sec_entry.get()) if sec_entry.get().isdigit() else 0
    interval_seconds = (min_val * 60) + sec_val
    if interval_seconds == 0:
        interval_seconds = 60

    Update_label['text'] = f"Auto-changing every {interval_seconds}s from {target_path}"

    def loop():
        if interval_active and os.path.isdir(current_auto_path):
            Main.pick_and_change(current_auto_path)
            threading.Timer(interval_seconds, loop).start()

    loop()

def start_interval_change():
    global interval_thread, interval_active
    selected = Path_listbox.curselection()
    if not selected:
        Update_label['text'] = "No Path Selected"
        return

    selected_path = Path_listbox.get(selected[0])
    if not os.path.isdir(selected_path):
        Update_label['text'] = "Invalid Directory"
        return

    interval_active = True
    min_val = int(min_entry.get()) if min_entry.get().isdigit() else 0
    sec_val = int(sec_entry.get()) if sec_entry.get().isdigit() else 0
    interval_seconds = (min_val * 60) + sec_val
    if interval_seconds == 0:
        interval_seconds = 60  # fallback to 60s
    Update_label['text'] = f"Auto-changing every {interval_seconds}s"

    def loop():
        if interval_active:
            Main.pick_and_change(selected_path)
            threading.Timer(interval_seconds, loop).start()

    loop()

def stop_interval_change():
    global interval_active
    interval_active = False
    Update_label['text'] = "Auto-change stopped"

def get_data():
    try:
        with open("data.txt", "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

def browse_folder(arr):
    selected_folder = filedialog.askdirectory()
    if selected_folder:
        Path_entry.delete(0, END)
        add_path(selected_folder, arr)
        Update_label['text'] = "Folder selected"

def add_path(new_path, arr):
    if os.path.isdir(path):
        if new_path and new_path not in arr:
            arr.append(new_path)
            update_file(arr)
            Path_listbox.insert(END, new_path)
            Update_label['text'] = "Path Added"
    else:
        print("path not valid")

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
    path = hotkey_bindings["start"].get(key_combo)
    print(f"Hotkey Triggered: {key_combo} → {path}")
    if path and os.path.isdir(path):
        start_auto_change_for_path(path)
    else:
        Update_label['text'] = f"No valid path assigned to {key_combo}"

def stop_auto_change_hotkey():
    global interval_active
    interval_active = False
    print("Auto-change stopped via hotkey")
    Update_label['text'] = "Auto-change stopped via hotkey"

def create_image():
    # Simple blank image for icon; replace with a real icon if you have one
    image = PILImage.new('RGB', (64, 64), color='gray')
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
    with open("data.txt", "w") as f:
        f.writelines(line + '\n' for line in arr)

# GUI Setup
root = Tk()
root.title("Wallpaper Changer")
root.geometry("600x500")
root.protocol("WM_DELETE_WINDOW", minimize_to_tray)
root.bind("<Visibility>", handle_state_change)

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

Path_entry = ttk.Entry(right_frame, width=40)
Browse_button = ttk.Button(right_frame, text="Browse", command=lambda: browse_folder(data))
New_path_button = ttk.Button(right_frame, text="Add Path", command=lambda: add_path(get_path(), data))
Change_button = ttk.Button(right_frame, text="Change Wallpaper", command=lambda: change_wallpaper())
Remove_button = ttk.Button(right_frame, text="Remove Path", command=remove_path)
Close_button = ttk.Button(right_frame, text="Exit", command=exit)
Hotkey_manager_button = ttk.Button(
    right_frame,
    text="Manage Hotkeys",
    command=lambda: Hotkey.open_hotkey_window(
        root,
        Path_listbox,
        hotkey_bindings,
        switch_path_by_hotkey,
        stop_auto_change_hotkey,
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
Start_interval_button = ttk.Button(right_frame, text="Start Auto-Change", command=start_interval_change)
Stop_interval_button = ttk.Button(right_frame, text="Stop Auto-Change", command=stop_interval_change)



Path_entry.pack(pady=10)
Browse_button.pack(pady=5)
New_path_button.pack(pady=10)
Remove_button.pack(pady=10)
Change_button.pack(pady=10)
time_frame.pack(pady=10)
Start_interval_button.pack(pady=5)
Stop_interval_button.pack(pady=5)
Hotkey_manager_button.pack(pady=5)
Close_button.pack(pady=5)
Update_label.pack(pady=10)

data = get_data()
hotkey_bindings = load_hotkey_bindings()
for combo_str, path in hotkey_bindings["start"].items():
    print(f"Binding START hotkey: {combo_str} → {path}")
    keyboard.add_hotkey(combo_str, lambda k=combo_str: switch_path_by_hotkey(k))

for combo_str in hotkey_bindings["stop"]:
    print(f"Binding STOP hotkey: {combo_str}")
    keyboard.add_hotkey(combo_str, stop_auto_change_hotkey)
for item in data:
    Path_listbox.insert(END, item)

root.mainloop()
