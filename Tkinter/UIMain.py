import Main
import os
import pathlib
import threading
from tkinter import *
from tkinter import ttk

global path
interval_thread = None
interval_active = False

def get_path():
    global path
    new_path = Path_entry.get()
    p = pathlib.PureWindowsPath(new_path)
    path = p.as_posix()
    #print("Path:", path)
    return path

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
    interval_seconds = int(interval_entry.get()) if interval_entry.get().isdigit() else 60
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

def update_file(arr):
    with open("data.txt", "w") as f:
        f.writelines(line + '\n' for line in arr)

# GUI Setup
root = Tk()
root.title("Wallpaper Changer")
root.geometry("400x400")

main_frame = Frame(root)
main_frame.pack(fill=BOTH, expand=True)

left_frame = Frame(main_frame)
left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)

Path_listbox = Listbox(left_frame, height=20, width=30)
Path_listbox.pack(side=LEFT, fill=Y)

scrollbar = Scrollbar(left_frame, orient=VERTICAL)
scrollbar.config(command=Path_listbox.yview)
scrollbar.pack(side=RIGHT, fill=Y)
Path_listbox.config(yscrollcommand=scrollbar.set)

right_frame = Frame(main_frame)
right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

Path_entry = ttk.Entry(right_frame)
New_path_button = ttk.Button(right_frame, text="Add Path", command=lambda: add_path(get_path(), data))
Change_button = ttk.Button(right_frame, text="Change Wallpaper", command=lambda: change_wallpaper())
Remove_button = ttk.Button(right_frame, text="Remove Path", command=remove_path)
Update_label = ttk.Label(right_frame, text="")
interval_entry = ttk.Entry(right_frame)
interval_entry.insert(0, "60")
Start_interval_button = ttk.Button(right_frame, text="Start Auto-Change", command=start_interval_change)
Stop_interval_button = ttk.Button(right_frame, text="Stop Auto-Change", command=stop_interval_change)



Path_entry.pack(pady=10)
New_path_button.pack(pady=10)
Remove_button.pack(pady=10)
Change_button.pack(pady=10)
interval_entry.pack(pady=10)
Start_interval_button.pack(pady=5)
Stop_interval_button.pack(pady=5)
Update_label.pack(pady=10)

data = get_data()
for item in data:
    Path_listbox.insert(END, item)

root.mainloop()
