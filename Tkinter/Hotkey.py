import os
import threading
import time
from tkinter import *
from tkinter import ttk
import keyboard

def open_hotkey_window(root, Path_listbox, hotkey_bindings, hotkey_actions, Update_label, save_hotkey_bindings):
    paths = [Path_listbox.get(i) for i in range(Path_listbox.size())]

    def start_hotkey_record():
        Update_label['text'] = "Recording... Press your key combination"
        hotkey_entry.delete(0, END)

        keys_down = set()
        combo_recorded = [False]
        keys_pressed = set()
        record_hooks = []

        def normalize_key(key):
            replacements = {
                'add': 'equal',
                'plus': 'equal',
                '=': 'equal',
                'left shift': 'shift',
                'right shift': 'shift',
                'left ctrl': 'ctrl',
                'right ctrl': 'ctrl',
                'left alt': 'alt',
                'right alt': 'alt',
            }
            return replacements.get(key, key)

        def record_keys(e):
            keys_pressed.add(normalize_key(e.name))

        def on_key_event(event):
            if event.event_type == 'down':
                keys_down.add(normalize_key(event.name))
            elif event.event_type == 'up':
                keys_down.discard(normalize_key(event.name))
                if not keys_down and not combo_recorded[0]:
                    ordered = sorted(set(keys_pressed), key=lambda k: (k not in ['ctrl', 'shift', 'alt'], k))
                    combo = '+'.join(ordered)
                    combo = combo.replace("++", "+=")
                    hotkey_entry.delete(0, END)
                    hotkey_entry.insert(0, combo)
                    Update_label['text'] = f"Hotkey detected: {combo}"
                    combo_recorded[0] = True
                    for hook in record_hooks:
                        keyboard.unhook(hook)

        record_hooks.append(keyboard.hook(record_keys))
        record_hooks.append(keyboard.hook(on_key_event))

    hotkey_window = Toplevel(root)
    hotkey_window.title("Hotkey Manager")
    hotkey_window.geometry("600x500")

    Label(hotkey_window, text="Select Path:").pack(pady=5)

    path_combo = ttk.Combobox(hotkey_window, values=paths, state="readonly", width=40)
    path_combo.pack()
    path_combo.set(paths[0] if paths else "")

    Label(hotkey_window, text="Select Action:").pack(pady=(10, 2))

    action_combo = ttk.Combobox(hotkey_window, state="readonly", width=40)
    action_combo['values'] = ["Start Auto-Change (Path)", "Stop Auto-Change", "Change Wallpaper", "Show UI"]
    action_combo.current(0)
    action_combo.pack()

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
    for combo_str in hotkey_bindings["change"]:
        structure_path = combo_str.replace("+", " + ")
        hotkey_listbox.insert(END, f"[CHANGE] → {structure_path}")
    for combo_str in hotkey_bindings["show"]:
        structure_path = combo_str.replace("+", " + ")
        hotkey_listbox.insert(END, f"[SHOW] → {structure_path}")

    def save_hotkey():
        combo_str = hotkey_entry.get().lower().strip()
        action = action_combo.get()
        path = path_combo.get() if path_combo.get() else None

        if not combo_str:
            Update_label['text'] = "Press a hotkey combo"
            return

        # Unbind if already used in any category
        for section in ["start", "stop", "change", "show"]:
            if combo_str in hotkey_bindings.get(section, {} if section == "start" else []):
                try:
                    keyboard.remove_hotkey(combo_str)
                except:
                    pass
                if section == "start":
                    del hotkey_bindings["start"][combo_str]
                else:
                    hotkey_bindings[section].remove(combo_str)
                for i in range(hotkey_listbox.size()):
                    if combo_str in hotkey_listbox.get(i):
                        hotkey_listbox.delete(i)
                        break

        # Handle action assignment
        try:
            if action == "Start Auto-Change (Path)":
                if not path:
                    Update_label['text'] = "Path required for start hotkey"
                    return
                keyboard.add_hotkey(combo_str, lambda k=combo_str: hotkey_actions["start"](k))
                hotkey_bindings["start"][combo_str] = path
                hotkey_listbox.insert(END, f"[START] → {combo_str.replace('+', ' + ')}")

            elif action == "Stop Auto-Change":
                keyboard.add_hotkey(combo_str, hotkey_actions["stop"])
                hotkey_bindings["stop"] = [combo_str]  # Enforce single stop key
                hotkey_listbox.insert(END, f"[STOP] → {combo_str.replace('+', ' + ')}")

            elif action == "Change Wallpaper":
                keyboard.add_hotkey(combo_str, hotkey_actions["change"])
                hotkey_bindings["change"] = [combo_str]
                hotkey_listbox.insert(END, f"[CHANGE] → {combo_str.replace('+', ' + ')}")

            elif action == "Show UI":
                keyboard.add_hotkey(combo_str, hotkey_actions["show"])
                hotkey_bindings["show"] = [combo_str]
                hotkey_listbox.insert(END, f"[SHOW] → {combo_str.replace('+', ' + ')}")

            save_hotkey_bindings()
            Update_label['text'] = f"{action} bound to {combo_str}"
        except Exception as e:
            Update_label['text'] = f"Failed to bind: {e}"

    def remove_selected_hotkey():
        selection = hotkey_listbox.curselection()
        if not selection:
            Update_label['text'] = "No hotkey selected to remove"
            return

        entry = hotkey_listbox.get(selection[0])

        try:
            label, combo_str = entry.split("→")
            combo_str = combo_str.strip().replace(" + ", "+")  # normalize
            label = label.strip().strip("[]")
        except ValueError:
            Update_label['text'] = "Invalid format in hotkey list"
            return

        removed = False

        # Handle [STOP], [SHOW], [CHANGE], [START]
        label_map = {
            "STOP": "stop",
            "SHOW": "show",
            "CHANGE": "change",
        }
        action_key = label_map.get(label.upper())

        if action_key:
            if combo_str in hotkey_bindings[action_key]:
                hotkey_bindings[action_key].remove(combo_str)
                removed = True
        else:  # It's a START hotkey (label is folder name)
            for key, path in list(hotkey_bindings["start"].items()):
                if key == combo_str and os.path.basename(path.rstrip("/\\")) == label:
                    del hotkey_bindings["start"][key]
                    removed = True
                    break

        if removed:
            try:
                keyboard.remove_hotkey(combo_str)
            except:
                pass
            hotkey_listbox.delete(selection[0])
            save_hotkey_bindings()
            Update_label['text'] = f"Removed hotkey: {combo_str}"
        else:
            Update_label['text'] = f"Hotkey [{label}] not found"

    binding_frame = Frame(hotkey_window)
    bind_button = ttk.Button(binding_frame, text="Bind Hotkey", command=save_hotkey)
    remove_button = ttk.Button(binding_frame, text="Remove Hotkey", command=remove_selected_hotkey)
    bind_button.pack(side=LEFT)
    remove_button.pack(side=RIGHT)
    binding_frame.pack(pady=5)