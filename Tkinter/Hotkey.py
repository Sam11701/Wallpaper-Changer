import os
from tkinter import *
from tkinter import ttk
import keyboard

def open_hotkey_window(root, Path_listbox, hotkey_bindings, switch_path_by_hotkey, stop_auto_change_hotkey, Update_label, save_hotkey_bindings):
    paths = [Path_listbox.get(i) for i in range(Path_listbox.size())]

    hotkey_window = Toplevel(root)
    hotkey_window.title("Hotkey Manager")
    hotkey_window.geometry("400x400")

    Label(hotkey_window, text="Select Path:").pack(pady=5)

    path_combo = ttk.Combobox(hotkey_window, values=paths, state="readonly", width=40)
    path_combo.pack()
    path_combo.set(paths[0] if paths else "")

    Label(hotkey_window, text="Enter hotkey combo (e.g., ctrl+shift+1):").pack(pady=10)
    hotkey_entry = ttk.Entry(hotkey_window)
    hotkey_entry.pack()

    # Display current hotkeys
    Label(hotkey_window, text="Assigned Hotkeys:").pack(pady=(15, 0))
    hotkey_listbox = Listbox(hotkey_window, width=50)
    hotkey_listbox.pack(pady=5)

    for combo_str, path in hotkey_bindings["start"].items():
        folder_name = os.path.basename(path.rstrip("/\\"))
        hotkey_listbox.insert(END, f"{combo_str} → {folder_name}")
    for combo_str in hotkey_bindings["stop"]:
        hotkey_listbox.insert(END, f"[STOP] {combo_str}")

    def save_hotkey():
        combo_str = hotkey_entry.get().lower().strip()
        if not combo_str:
            Update_label['text'] = "Enter a hotkey combo"
            return
        path = path_combo.get()
        if not path:
            Update_label['text'] = "No path selected"
            return
        hotkey_bindings["start"][combo_str] = path

        try:
            keyboard.add_hotkey(combo_str, lambda: switch_path_by_hotkey(combo_str))
            save_hotkey_bindings()
            Update_label['text'] = f"Global hotkey {combo_str} bound to selected path"
        except Exception as e:
            Update_label['text'] = f"Failed to bind: {e}"
            return

        folder_name = os.path.basename(path.rstrip("/\\"))
        hotkey_listbox.insert(END, f"{combo_str} → {folder_name}")
        hotkey_window.destroy()

    def remove_selected_hotkey():
        selection = hotkey_listbox.curselection()
        if not selection:
            Update_label['text'] = "No hotkey selected to remove"
            return

        entry = hotkey_listbox.get(selection[0])
        combo_str = entry.split("→")[0].strip().replace("[STOP] ", "")

        removed = False
        if combo_str in hotkey_bindings["start"]:
            del hotkey_bindings["start"][combo_str]
            removed = True
        elif combo_str in hotkey_bindings["stop"]:
            hotkey_bindings["stop"].remove(combo_str)
            removed = True

        if removed:
            try:
                keyboard.remove_hotkey(combo_str)
            except:
                pass  # ignore if not bound
            hotkey_listbox.delete(selection[0])
            save_hotkey_bindings()
            Update_label['text'] = f"Removed hotkey: {combo_str}"
        else:
            Update_label['text'] = f"Hotkey {combo_str} not found"

    def save_stop_hotkey():
        combo_str = hotkey_entry.get().lower().strip()
        if not combo_str:
            Update_label['text'] = "Enter a hotkey combo"
            return

        if combo_str in hotkey_bindings["stop"]:
            Update_label['text'] = f"{combo_str} already bound as stop hotkey"
            return

        try:
            keyboard.add_hotkey(combo_str, stop_auto_change_hotkey)
            hotkey_bindings["stop"].append(combo_str)
            save_hotkey_bindings()
            hotkey_listbox.insert(END, f"[STOP] {combo_str}")
            Update_label['text'] = f"Stop hotkey {combo_str} bound"
        except Exception as e:
            Update_label['text'] = f"Failed to bind: {e}"

    bind_button = ttk.Button(hotkey_window, text="Bind Hotkey", command=save_hotkey)
    remove_button = ttk.Button(hotkey_window, text="Remove Hotkey", command=remove_selected_hotkey)
    bind_button.pack(pady=5)
    remove_button.pack(pady=5)
    ttk.Button(hotkey_window, text="Bind as Stop Hotkey", command=save_stop_hotkey).pack(pady=5)