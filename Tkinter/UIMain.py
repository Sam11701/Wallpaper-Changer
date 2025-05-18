import Main
import os
import pathlib
from tkinter import *
from tkinter import ttk

global path
path = "C:/"

def get_path():
    global path
    new_path = Path_entry.get()
    p = pathlib.PureWindowsPath(new_path)
    path = p.as_posix()
    print("Path:", path)
    Update_label['text'] = "Path Updated"
    return path

def get_data():
    try:
        with open("data.txt", "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

def add_path(new_path, arr):
    if os.path.isdir(path):
        if new_path not in arr:
            arr.append(new_path)
            update_file(arr)
    else:
        print("path not valid")

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
New_path_button = ttk.Button(right_frame, text="Set Path", command=lambda: add_path(get_path(), data))
Change_button = ttk.Button(right_frame, text="Change Wallpaper", command=lambda: Main.pick_and_change(path))
Update_label = ttk.Label(right_frame, text="")

Path_entry.pack(pady=10)
New_path_button.pack(pady=10)
Change_button.pack(pady=10)
Update_label.pack(pady=10)

data = get_data()
for item in data:
    Path_listbox.insert(END, item)

root.mainloop()
