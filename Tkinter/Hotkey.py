from tkinter import *
from tkinter import ttk
import os

from tkinter import *
from tkinter import ttk
import keyboard

def open_hotkey_window(root, Path_listbox, hotkey_bindings, switch_path_by_hotkey, Update_label, save_hotkey_bindings):
    hotkey_window = Toplevel(root)
    hotkey_window.title("Hotkey Manager")
    hotkey_window.geometry("400x400")

    Label(hotkey_window, text="Selected Path:").pack(pady=5)

    selected = Path_listbox.curselection()
    selected_path = Path_listbox.get(selected[0]) if selected else ""
    path_label = Label(hotkey_window, text=selected_path or "No path selected")
    path_label.pack()

    Label(hotkey_window, text="Enter hotkey combo (e.g., ctrl+shift+1):").pack(pady=10)
    hotkey_entry = ttk.Entry(hotkey_window)
    hotkey_entry.pack()

    # Display current hotkeys
    Label(hotkey_window, text="Assigned Hotkeys:").pack(pady=(15, 0))
    hotkey_listbox = Listbox(hotkey_window, width=50)
    hotkey_listbox.pack(pady=5)

    for key, path in hotkey_bindings.items():
        hotkey_listbox.insert(END, f"{key} → {path}")

    def save_hotkey():
        combo_str = hotkey_entry.get().lower().strip()
        if not combo_str:
            Update_label['text'] = "Enter a hotkey combo"
            return
        if not selected:
            Update_label['text'] = "Select a path first"
            return

        path = Path_listbox.get(selected[0])
        hotkey_bindings[combo_str] = path

        try:
            keyboard.add_hotkey(combo_str, lambda: switch_path_by_hotkey(combo_str))
            save_hotkey_bindings()
            Update_label['text'] = f"Global hotkey {combo_str} bound to selected path"
        except Exception as e:
            Update_label['text'] = f"Failed to bind: {e}"
            return

        hotkey_listbox.insert(END, f"{combo_str} → {path}")
        hotkey_window.destroy()

    bind_button = ttk.Button(hotkey_window, text="Bind Hotkey", command=save_hotkey)
    bind_button.pack(pady=10)