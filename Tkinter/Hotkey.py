import os
import threading
import time
from tkinter import *
from tkinter import ttk
import keyboard

def open_hotkey_window(root, Path_listbox, hotkey_bindings, switch_path_by_hotkey, stop_auto_change_hotkey, Update_label, save_hotkey_bindings):
    paths = [Path_listbox.get(i) for i in range(Path_listbox.size())]

    def start_hotkey_record():
        Update_label['text'] = "Recording... Press your key combination"
        hotkey_entry.delete(0, END)

        keys_down = set()
        combo_recorded = [False]

        def on_key_event(event):
            if event.event_type == 'down':
                keys_down.add(event.name)
            elif event.event_type == 'up':
                keys_down.discard(event.name)
                if not keys_down and not combo_recorded[0]:
                    # All keys released: finalize
                    ordered = sorted(set(keys_pressed), key=lambda k: (k not in ['ctrl', 'shift', 'alt'], k))
                    combo = '+'.join(ordered)
                    hotkey_entry.delete(0, END)
                    hotkey_entry.insert(0, combo)
                    Update_label['text'] = f"Hotkey detected: {combo}"
                    combo_recorded[0] = True
                    keyboard.unhook_all()

        keys_pressed = set()

        def record_keys(e):
            keys_pressed.add(e.name)

        keyboard.unhook_all()
        keyboard.hook(record_keys)
        keyboard.hook(on_key_event)

    hotkey_window = Toplevel(root)
    hotkey_window.title("Hotkey Manager")
    hotkey_window.geometry("600x500")

    Label(hotkey_window, text="Select Path:").pack(pady=5)

    path_combo = ttk.Combobox(hotkey_window, values=paths, state="readonly", width=40)
    path_combo.pack()
    path_combo.set(paths[0] if paths else "")

    Label(hotkey_window, text="Enter hotkey combo (e.g., Ctrl+Shift+1):").pack(pady=10)
    input_frame = Frame(hotkey_window)
    hotkey_entry = ttk.Entry(input_frame)
    hotkey_entry.pack(side=LEFT)

    record_button = ttk.Button(input_frame, text="Record Hotkey", command=start_hotkey_record)
    record_button.pack(side=LEFT)
    input_frame.pack(pady=5)

    # Display current hotkeys
    Label(hotkey_window, text="Assigned Hotkeys:").pack(pady=(15, 0))
    hotkey_listbox = Listbox(hotkey_window, width=50)
    hotkey_listbox.pack(pady=5)

    for combo_str, path in hotkey_bindings["start"].items():
        folder_name = os.path.basename(path.rstrip("/\\"))
        structure_path = combo_str.replace("+", " + ")
        hotkey_listbox.insert(END, f"[{folder_name}] → {structure_path}")
    for combo_str in hotkey_bindings["stop"]:
        structure_path = combo_str.replace("+", " + ")
        hotkey_listbox.insert(END, f"[STOP] → {structure_path}")

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

        # Remove existing stop hotkey (if any)
        if hotkey_bindings["stop"]:
            old_combo = hotkey_bindings["stop"][0]
            try:
                keyboard.remove_hotkey(old_combo)
            except:
                pass
            hotkey_bindings["stop"] = []

            # Also remove it from the listbox
            for i in range(hotkey_listbox.size()):
                if old_combo in hotkey_listbox.get(i):
                    hotkey_listbox.delete(i)
                    break

        # Add new stop hotkey
        try:
            keyboard.add_hotkey(combo_str, stop_auto_change_hotkey)
            hotkey_bindings["stop"].append(combo_str)
            save_hotkey_bindings()
            hotkey_listbox.insert(END, f"[STOP] {combo_str}")
            Update_label['text'] = f"Stop hotkey {combo_str} bound"
        except Exception as e:
            Update_label['text'] = f"Failed to bind: {e}"

    binding_frame = Frame(hotkey_window)
    bind_button = ttk.Button(binding_frame, text="Bind Hotkey", command=save_hotkey)
    remove_button = ttk.Button(binding_frame, text="Remove Hotkey", command=remove_selected_hotkey)
    bind_button.pack(side=LEFT)
    remove_button.pack(side=RIGHT)
    binding_frame.pack(pady=5)
    ttk.Button(binding_frame, text="Bind as Stop Hotkey", command=save_stop_hotkey).pack(pady=5)