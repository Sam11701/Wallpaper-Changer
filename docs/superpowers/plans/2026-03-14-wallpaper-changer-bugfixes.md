# Wallpaper Changer Bugfixes and Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all critical bugs, add validation, improve code quality, and add proper dependency management to the wallpaper-changer application.

**Architecture:** Refactor core wallpaper selection logic with proper validation, fix lambda closure issues in hotkey bindings, add input validation across the UI, and improve error handling throughout.

**Tech Stack:** Python 3.x, Tkinter, keyboard library, pystray, Pillow

---

## Chunk 1: Core Logic Fixes and Validation

### Task 1: Add Image File Validation and Path Handling

**Files:**
- Modify: `Main.py:21-31`
- Create: `tests/test_main.py`

- [ ] **Step 1: Create tests directory**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 2: Write failing test for image file validation**

```python
# tests/test_main.py
import os
import tempfile
import pytest
from Main import pick_image, is_valid_image_file

def test_is_valid_image_file_accepts_images():
    assert is_valid_image_file("photo.jpg") == True
    assert is_valid_image_file("image.png") == True
    assert is_valid_image_file("pic.jpeg") == True
    assert is_valid_image_file("wall.bmp") == True
    assert is_valid_image_file("background.gif") == True

def test_is_valid_image_file_rejects_non_images():
    assert is_valid_image_file("document.txt") == False
    assert is_valid_image_file("data.json") == False
    assert is_valid_image_file("script.py") == False
    assert is_valid_image_file("readme.md") == False

def test_pick_image_only_selects_valid_images(tmp_path):
    # Create test directory with mixed files
    (tmp_path / "image1.jpg").touch()
    (tmp_path / "image2.png").touch()
    (tmp_path / "notimage.txt").touch()
    (tmp_path / "data.json").touch()

    # Should only pick from valid images
    for _ in range(10):
        selected = pick_image(str(tmp_path))
        assert os.path.basename(selected) in ["image1.jpg", "image2.png"]

def test_pick_image_raises_on_empty_directory(tmp_path):
    with pytest.raises(ValueError, match="No valid image files found"):
        pick_image(str(tmp_path))

def test_pick_image_raises_on_no_images(tmp_path):
    (tmp_path / "document.txt").touch()
    (tmp_path / "data.json").touch()

    with pytest.raises(ValueError, match="No valid image files found"):
        pick_image(str(tmp_path))
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with import errors and test failures

- [ ] **Step 4: Replace Main.py with improved implementation**

Note: This is a full file rewrite. Use Write tool to replace the entire file.

```python
# Main.py
import os
import ctypes
import random

# Supported image extensions
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

def is_valid_image_file(filename):
    """Check if a file has a valid image extension."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in VALID_IMAGE_EXTENSIONS

def change_wallpaper(image_path):
    # Constants for setting the wallpaper
    SPI_SETDESKWALLPAPER = 20  # Action to change wallpaper
    SPIF_UPDATEINIFILE = 0x01  # Update user profile
    SPIF_SENDWININICHANGE = 0x02  # Notify change to system

    try:
        # Call Windows API to change wallpaper
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path,
                                                   SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE)
        return True
    except Exception as e:
        # Print error message if wallpaper change fails
        print(f"Error changing wallpaper: {e}")
        return False

def pick_image(folder_path):
    """Pick a random valid image file from the folder."""
    if not os.path.isdir(folder_path):
        raise ValueError(f"Invalid directory: {folder_path}")

    # Get all files in directory
    all_files = os.listdir(folder_path)

    # Filter for valid image files only
    image_files = [f for f in all_files if is_valid_image_file(f)]

    if not image_files:
        raise ValueError(f"No valid image files found in {folder_path}")

    # Pick random image and return full path
    filename = random.choice(image_files)
    return os.path.join(folder_path, filename)

def pick_and_change(folder_path):
    """Pick a random image from folder and set as wallpaper."""
    print(f"PickPath: {folder_path}")
    try:
        image_path = pick_image(folder_path)
        # Convert to absolute path for Windows API
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_main.py -v`
Expected: All 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add Main.py tests/test_main.py
git commit -m "fix: add image file validation and improve error handling

- Add is_valid_image_file() to filter non-image files
- Fix pick_image() to only select valid images
- Add proper error handling with ValueError for empty/invalid directories
- Use os.path.join() for cross-platform path handling
- Add comprehensive tests for image selection logic

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: UI Critical Bug Fixes

### Task 2: Fix Lambda Closure Bug in Hotkey Bindings

**Files:**
- Modify: `Tkinter/UIMain.py:333-344`
- Test: Manual testing with multiple hotkeys

- [ ] **Step 1: Fix the lambda closure bug**

In `Tkinter/UIMain.py`, find and replace the hotkey binding section (lines 333-344):

OLD CODE:
```python
for combo_str, path in hotkey_bindings["start"].items():
    print(f"Binding START hotkey: {combo_str} → {path}")
    keyboard.add_hotkey(combo_str, lambda k=combo_str: switch_path_by_hotkey(k))

for combo_str in hotkey_bindings["stop"]:
    keyboard.add_hotkey(combo_str, stop_auto_change_hotkey)

for combo_str in hotkey_bindings["change"]:
    keyboard.add_hotkey(combo_str, change_wallpaper_hotkey)

for combo_str in hotkey_bindings["show"]:
    keyboard.add_hotkey(combo_str, show_ui_hotkey)
```

NEW CODE (FIXED):
```python
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
```

- [ ] **Step 2: Test the fix manually**

1. Run the application
2. Add multiple "Start Auto-Change" hotkeys for different paths (e.g., Ctrl+1 for C:\Wallpapers\Nature, Ctrl+2 for C:\Wallpapers\Abstract)
3. Press Ctrl+1 → Expected: Update_label shows "Started auto-change from hotkey: ctrl+1" and wallpaper changes from Nature folder
4. Press Ctrl+2 → Expected: Update_label shows "Started auto-change from hotkey: ctrl+2" and wallpaper changes from Abstract folder
5. Verify each hotkey triggers the correct path, not all triggering the last path

Expected: Each hotkey correctly triggers its assigned path, confirming closure bug is fixed

- [ ] **Step 3: Commit**

```bash
git add Tkinter/UIMain.py
git commit -m "fix: resolve lambda closure bug in hotkey bindings

- Use closure factory to capture combo_str correctly
- Prevents all hotkeys from referencing the last value
- Each hotkey now properly triggers its assigned path

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Fix Wrong Variable Check in add_path

**Files:**
- Modify: `Tkinter/UIMain.py:118-127`

- [ ] **Step 1: Fix the variable check**

In `Tkinter/UIMain.py`, find and replace the add_path function (lines 118-126):

OLD CODE:
```python
def add_path(new_path, arr):
    if os.path.isdir(path):
        if new_path and new_path not in arr:
            arr.append(new_path)
            update_file(arr)
            Path_listbox.insert(END, new_path)
            Update_label['text'] = "Path Added"
    else:
        print("path not valid")
```

NEW CODE (FIXED):
```python
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
```

- [ ] **Step 2: Test the fix manually**

1. Run the application
2. Enter an invalid path in the Path_entry field (e.g., C:\NonExistent) and click "Add Path" → Expected: Update_label shows "Invalid directory path"
3. Clear the Path_entry field (leave it empty) and click "Add Path" → Expected: Update_label shows "No path provided"
4. Enter a valid path (e.g., C:\Wallpapers) and click "Add Path" → Expected: Update_label shows "Path Added" and path appears in listbox
5. Enter the same valid path again and click "Add Path" → Expected: Update_label shows "Path already exists"

Expected: Proper validation and feedback messages for all edge cases

- [ ] **Step 3: Commit**

```bash
git add Tkinter/UIMain.py
git commit -m "fix: check correct variable in add_path validation

- Check new_path parameter instead of global path variable
- Add proper validation messages for all edge cases
- Improve user feedback for invalid paths and duplicates

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: Fix Hotkey Overwrite Bug

**Files:**
- Modify: `Tkinter/Hotkey.py:136-150`

- [ ] **Step 1: Fix hotkey binding to append instead of overwrite**

In `Tkinter/Hotkey.py`, find and replace the action assignment section (lines 136-149):

OLD CODE:
```python
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
```

NEW CODE (FIXED):
```python
            elif action == "Stop Auto-Change":
                keyboard.add_hotkey(combo_str, hotkey_actions["stop"])
                if combo_str not in hotkey_bindings["stop"]:
                    hotkey_bindings["stop"].append(combo_str)
                hotkey_listbox.insert(END, f"[STOP] → {combo_str.replace('+', ' + ')}")

            elif action == "Change Wallpaper":
                keyboard.add_hotkey(combo_str, hotkey_actions["change"])
                if combo_str not in hotkey_bindings["change"]:
                    hotkey_bindings["change"].append(combo_str)
                hotkey_listbox.insert(END, f"[CHANGE] → {combo_str.replace('+', ' + ')}")

            elif action == "Show UI":
                keyboard.add_hotkey(combo_str, hotkey_actions["show"])
                if combo_str not in hotkey_bindings["show"]:
                    hotkey_bindings["show"].append(combo_str)
                hotkey_listbox.insert(END, f"[SHOW] → {combo_str.replace('+', ' + ')}")
```

Note: Keep the "Start Auto-Change (Path)" section above this unchanged:
        try:
            if action == "Start Auto-Change (Path)":
                if not path:
                    Update_label['text'] = "Path required for start hotkey"
                    return
                keyboard.add_hotkey(combo_str, lambda k=combo_str: hotkey_actions["start"](k))
                hotkey_bindings["start"][combo_str] = path
                folder_name = os.path.basename(path.rstrip("/\\"))
                hotkey_listbox.insert(END, f"[{folder_name}] → {combo_str.replace('+', ' + ')}")

            elif action == "Stop Auto-Change":
                keyboard.add_hotkey(combo_str, hotkey_actions["stop"])
                if combo_str not in hotkey_bindings["stop"]:
                    hotkey_bindings["stop"].append(combo_str)
                hotkey_listbox.insert(END, f"[STOP] → {combo_str.replace('+', ' + ')}")

            elif action == "Change Wallpaper":
                keyboard.add_hotkey(combo_str, hotkey_actions["change"])
                if combo_str not in hotkey_bindings["change"]:
                    hotkey_bindings["change"].append(combo_str)
                hotkey_listbox.insert(END, f"[CHANGE] → {combo_str.replace('+', ' + ')}")

            elif action == "Show UI":
                keyboard.add_hotkey(combo_str, hotkey_actions["show"])
                if combo_str not in hotkey_bindings["show"]:
                    hotkey_bindings["show"].append(combo_str)
                hotkey_listbox.insert(END, f"[SHOW] → {combo_str.replace('+', ' + ')}")

            save_hotkey_bindings()
            Update_label['text'] = f"{action} bound to {combo_str}"
        except Exception as e:
            Update_label['text'] = f"Failed to bind: {e}"
```

- [ ] **Step 2: Test multiple bindings**

1. Run the application
2. Start auto-change for any path to enable testing stop functionality
3. Open Hotkey Manager
4. Add first "Stop Auto-Change" hotkey (Ctrl+S) → Expected: Hotkey list shows "[STOP] → ctrl + s"
5. Add second "Stop Auto-Change" hotkey (Ctrl+X) → Expected: Hotkey list shows both "[STOP] → ctrl + s" and "[STOP] → ctrl + x"
6. Press Ctrl+S → Expected: Auto-change stops, Update_label shows "Auto-change stopped via hotkey"
7. Restart auto-change, press Ctrl+X → Expected: Auto-change stops, Update_label shows "Auto-change stopped via hotkey"
8. Repeat for "Change Wallpaper" (e.g., Ctrl+W, Ctrl+C) and "Show UI" (e.g., Ctrl+H, Ctrl+U)

Expected: All hotkeys are preserved in the list and functional when pressed

- [ ] **Step 3: Commit**

```bash
git add Tkinter/Hotkey.py
git commit -m "fix: append hotkeys instead of overwriting previous bindings

- Use append() instead of assignment for stop/change/show hotkeys
- Support multiple hotkeys per action type
- Add duplicate check before appending

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 3: Input Validation and Error Handling

### Task 5: Add Time Interval Input Validation

**Files:**
- Modify: `Tkinter/UIMain.py:48-70` and `72-97`

- [ ] **Step 1: Add input validation helper**

Add this function after the imports in `Tkinter/UIMain.py`:

```python
def validate_time_input(min_str, sec_str):
    """Validate and parse time inputs. Returns (minutes, seconds) or raises ValueError."""
    try:
        min_val = int(min_str) if min_str.strip() else 0
        sec_val = int(sec_str) if sec_str.strip() else 0
    except ValueError:
        raise ValueError("Time values must be valid numbers")

    if min_val < 0 or sec_val < 0:
        raise ValueError("Time values cannot be negative")

    if min_val == 0 and sec_val == 0:
        raise ValueError("Interval must be at least 1 second")

    if min_val > 1440:  # 24 hours
        raise ValueError("Interval cannot exceed 24 hours")

    return min_val, sec_val
```

- [ ] **Step 2: Update start_auto_change_for_path to use validation**

Replace `start_auto_change_for_path` function (lines 48-70):

```python
def start_auto_change_for_path(target_path):
    global interval_active, current_auto_path
    if not os.path.isdir(target_path):
        Update_label['text'] = "Invalid Directory"
        return

    current_auto_path = target_path
    interval_active = True

    try:
        min_val, sec_val = validate_time_input(min_entry.get(), sec_entry.get())
        interval_seconds = (min_val * 60) + sec_val
    except ValueError as e:
        Update_label['text'] = f"Invalid time: {e}"
        interval_active = False
        return

    Update_label['text'] = f"Auto-changing every {interval_seconds}s from {target_path}"

    def loop():
        if interval_active and os.path.isdir(current_auto_path):
            Main.pick_and_change(current_auto_path)
            threading.Timer(interval_seconds, loop).start()

    loop()
```

- [ ] **Step 3: Update start_interval_change to use validation**

Replace `start_interval_change` function (lines 72-97):

```python
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

    try:
        min_val, sec_val = validate_time_input(min_entry.get(), sec_entry.get())
        interval_seconds = (min_val * 60) + sec_val
    except ValueError as e:
        Update_label['text'] = f"Invalid time: {e}"
        return

    interval_active = True
    Update_label['text'] = f"Auto-changing every {interval_seconds}s"

    def loop():
        if interval_active:
            Main.pick_and_change(selected_path)
            threading.Timer(interval_seconds, loop).start()

    loop()
```

- [ ] **Step 4: Test input validation**

1. Run application
2. Try negative numbers in time fields → verify error message
3. Try text in time fields → verify error message
4. Try 0 minutes and 0 seconds → verify error message
5. Try valid input → verify it works

Expected: Clear error messages for invalid inputs

- [ ] **Step 5: Commit**

```bash
git add Tkinter/UIMain.py
git commit -m "fix: add input validation for time intervals

- Add validate_time_input() helper function
- Validate numeric input and prevent negative values
- Prevent zero-second intervals
- Add maximum interval limit (24 hours)
- Provide clear error messages for invalid input

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 6: Improve Error Handling for File Operations

**Files:**
- Modify: `Tkinter/UIMain.py:32-46` and `242-244`

- [ ] **Step 1: Add error handling to load_hotkey_bindings**

Replace `load_hotkey_bindings` function (lines 32-42):

```python
def load_hotkey_bindings():
    default = {"start": {}, "stop": [], "change": [], "show": []}
    if os.path.exists(HOTKEY_FILE):
        try:
            with open(HOTKEY_FILE, "r") as f:
                data = json.load(f)
                # Ensure all required keys exist
                for key in default:
                    if key not in data:
                        data[key] = default[key]
                print(f"Loaded hotkey bindings from {HOTKEY_FILE}")
                return data
        except json.JSONDecodeError as e:
            print(f"Error parsing {HOTKEY_FILE}: {e}. Using defaults.")
            # Backup corrupted file
            try:
                import shutil
                shutil.copy(HOTKEY_FILE, f"{HOTKEY_FILE}.backup")
                print(f"Backed up corrupted file to {HOTKEY_FILE}.backup")
            except Exception:
                pass
        except Exception as e:
            print(f"Error loading {HOTKEY_FILE}: {e}. Using defaults.")
    return default
```

- [ ] **Step 2: Add error handling to save_hotkey_bindings**

Replace `save_hotkey_bindings` function (lines 44-46):

```python
def save_hotkey_bindings():
    try:
        with open(HOTKEY_FILE, "w") as f:
            json.dump(hotkey_bindings, f, indent=4)
        print(f"Saved hotkey bindings to {HOTKEY_FILE}")
    except Exception as e:
        print(f"Error saving hotkey bindings: {e}")
        if Update_label:
            Update_label['text'] = f"Failed to save hotkeys: {e}"
```

- [ ] **Step 3: Add error handling to get_data and update_file**

Replace `get_data` function (lines 104-109):

```python
def get_data():
    try:
        with open("data.txt", "r") as f:
            data = f.read().splitlines()
            print(f"Loaded {len(data)} paths from data.txt")
            return data
    except FileNotFoundError:
        print("data.txt not found, starting fresh")
        return []
    except Exception as e:
        print(f"Error reading data.txt: {e}")
        return []
```

Replace `update_file` function (lines 242-244):

```python
def update_file(arr):
    try:
        with open("data.txt", "w") as f:
            f.writelines(line + '\n' for line in arr)
        print(f"Saved {len(arr)} paths to data.txt")
    except Exception as e:
        print(f"Error saving paths: {e}")
        Update_label['text'] = f"Failed to save paths: {e}"
```

- [ ] **Step 4: Test error handling**

1. Create an invalid JSON file (corrupted hotkeys.json)
2. Run application → verify it loads defaults and creates backup
3. Remove write permissions on data.txt (if possible)
4. Try adding path → verify error message appears

Expected: Graceful degradation with helpful error messages

- [ ] **Step 5: Commit**

```bash
git add Tkinter/UIMain.py
git commit -m "fix: improve error handling for file operations

- Add try-catch blocks for all file I/O operations
- Create backup of corrupted hotkeys.json file
- Provide informative error messages to user
- Gracefully fall back to defaults on errors
- Add logging for debugging file issues

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 4: Code Quality Improvements

### Task 7: Add Constants for Configuration

**Files:**
- Modify: `Tkinter/UIMain.py:19` (add constants section)

- [ ] **Step 1: Add constants at module level**

After the imports in `Tkinter/UIMain.py` (around line 14), add:

```python
# Configuration Constants
DATA_FILE = "data.txt"
HOTKEY_FILE = "hotkeys.json"
DEFAULT_INTERVAL_SECONDS = 60
MAX_INTERVAL_HOURS = 24
TRAY_ICON_SIZE = (64, 64)
```

- [ ] **Step 2: Replace hardcoded strings with constants**

Replace all occurrences:
- `"data.txt"` → `DATA_FILE` (in get_data and update_file)
- `"hotkeys.json"` → already uses `HOTKEY_FILE` variable
- `60` → `DEFAULT_INTERVAL_SECONDS` (in validation function)
- `1440` → `MAX_INTERVAL_HOURS * 60` (in validate_time_input)
- `(64, 64)` → `TRAY_ICON_SIZE` (in create_image)

Update the code:

```python
# In validate_time_input:
    if min_val > MAX_INTERVAL_HOURS * 60:
        raise ValueError(f"Interval cannot exceed {MAX_INTERVAL_HOURS} hours")

# In get_data:
    with open(DATA_FILE, "r") as f:

# In update_file:
    with open(DATA_FILE, "w") as f:

# In create_image:
    image = PILImage.new('RGB', TRAY_ICON_SIZE, color='gray')
```

- [ ] **Step 3: Verify no regressions**

Run application and test:
1. Load/save paths
2. Load/save hotkeys
3. Start intervals
4. Minimize to tray

Expected: All functionality works as before

- [ ] **Step 4: Commit**

```bash
git add Tkinter/UIMain.py
git commit -m "refactor: extract configuration constants

- Add module-level constants for file names and limits
- Replace hardcoded strings with named constants
- Improve maintainability and configurability
- Make limits visible and easy to adjust

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 8: Add Dependencies File

**Files:**
- Create: `requirements.txt`
- Create: `README.md` (update if exists)

- [ ] **Step 1: Create requirements.txt**

```python
# requirements.txt
keyboard>=0.13.5
pystray>=0.19.4
Pillow>=10.0.0
pytest>=7.4.0
```

- [ ] **Step 2: Update README with installation instructions**

Read the current README first, then update it to include:

```markdown
# Wallpaper-Changer

A Windows desktop application for automatically changing wallpapers at custom intervals with global hotkey support.

## Features

- Auto-change wallpapers from selected folders at custom intervals
- Global hotkey support for:
  - Starting auto-change for specific folders
  - Stopping auto-change
  - Manually changing wallpaper
  - Showing/hiding UI
- System tray integration
- Multiple folder management
- Customizable time intervals (minutes and seconds)

## Requirements

- Windows 10/11
- Python 3.7+

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd wallpaper-changer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python Tkinter/UIMain.py
```

### Adding Folders

1. Click "Browse" to select a folder containing wallpaper images
2. Or manually enter a path and click "Add Path"
3. Select a folder from the list and click "Change Wallpaper" to set immediately

### Auto-Change

1. Select a folder from the list
2. Set the interval (minutes and seconds)
3. Click "Start Auto-Change"
4. Click "Stop Auto-Change" to stop

### Hotkeys

1. Click "Manage Hotkeys" to open the hotkey configuration window
2. Select an action type:
   - **Start Auto-Change (Path)**: Switch to a specific folder's auto-change
   - **Stop Auto-Change**: Stop the current auto-change
   - **Change Wallpaper**: Manually change to next wallpaper
   - **Show UI**: Restore the UI from system tray
3. Click "Record Hotkey" and press your desired key combination
4. Click "Bind Hotkey" to save
5. Hotkeys work globally even when the app is minimized

### System Tray

- Minimize or close the window to send the app to system tray
- Right-click the tray icon to restore or exit

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
wallpaper-changer/
├── Main.py              # Core wallpaper changing logic
├── Tkinter/
│   ├── UIMain.py        # Main UI and application logic
│   └── Hotkey.py        # Hotkey management UI
├── tests/
│   └── test_main.py     # Unit tests
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Troubleshooting

**Hotkeys not working:**
- Ensure the application is running (check system tray)
- Try re-binding the hotkey
- Avoid conflicts with system hotkeys

**Wallpaper not changing:**
- Verify the folder contains valid image files (jpg, png, bmp, gif, etc.)
- Check the console output for error messages
- Ensure the folder path is valid and accessible

**Application crashes:**
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Ensure you're running on Windows (wallpaper changing uses Windows API)

## License

[Add your license here]
```

- [ ] **Step 3: Verify installation with fresh environment (optional)**

If you want to verify:
```bash
python -m venv test_env
test_env\Scripts\activate
pip install -r requirements.txt
python Tkinter/UIMain.py
```

Expected: Application runs without import errors

- [ ] **Step 4: Commit**

```bash
git add requirements.txt README.md
git commit -m "docs: add requirements.txt and update README

- Add requirements.txt with all Python dependencies
- Update README with installation instructions
- Add usage guide for all features
- Include troubleshooting section
- Document project structure

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 5: Additional Improvements and Testing

### Task 9: Add Timer Cancellation to Prevent Leaks

**Files:**
- Modify: `Tkinter/UIMain.py:48-70` and `72-97`

- [ ] **Step 1: Add timer tracking**

Add to global variables section (around line 16):

```python
active_timer = None  # Track active timer for cleanup
```

- [ ] **Step 2: Add timer cancellation to start_auto_change_for_path**

Update the function signature and add cancellation at the start (incremental change on top of Chunk 3):

Find:
```python
def start_auto_change_for_path(target_path):
    global interval_active, current_auto_path
```

Replace with:
```python
def start_auto_change_for_path(target_path):
    global interval_active, current_auto_path, active_timer

    # Cancel existing timer if any
    if active_timer:
        active_timer.cancel()
        active_timer = None
```

Then find the loop() function inside start_auto_change_for_path:
```python
    def loop():
        if interval_active and os.path.isdir(current_auto_path):
            Main.pick_and_change(current_auto_path)
            threading.Timer(interval_seconds, loop).start()
```

Replace with:
```python
    def loop():
        global active_timer
        if interval_active and os.path.isdir(current_auto_path):
            Main.pick_and_change(current_auto_path)
            active_timer = threading.Timer(interval_seconds, loop)
            active_timer.start()
```

- [ ] **Step 3: Add timer cancellation to start_interval_change**

Update the function signature and add cancellation at the start (incremental change on top of Chunk 3):

Find:
```python
def start_interval_change():
    global interval_thread, interval_active
```

Replace with:
```python
def start_interval_change():
    global interval_thread, interval_active, active_timer

    # Cancel existing timer if any
    if active_timer:
        active_timer.cancel()
        active_timer = None
```

Then find the loop() function inside start_interval_change:
```python
    def loop():
        if interval_active:
            Main.pick_and_change(selected_path)
            threading.Timer(interval_seconds, loop).start()
```

Replace with:
```python
    def loop():
        global active_timer
        if interval_active:
            Main.pick_and_change(selected_path)
            active_timer = threading.Timer(interval_seconds, loop)
            active_timer.start()
```

- [ ] **Step 4: Add timer cancellation to stop_interval_change**

Find:
```python
def stop_interval_change():
    global interval_active
    interval_active = False
    Update_label['text'] = "Auto-change stopped"
```

Replace with:
```python
def stop_interval_change():
    global interval_active, active_timer
    interval_active = False

    # Cancel active timer
    if active_timer:
        active_timer.cancel()
        active_timer = None

    Update_label['text'] = "Auto-change stopped"
```

- [ ] **Step 5: Test timer cancellation**

1. Start auto-change with short interval (5 seconds)
2. Wait for one change
3. Start again immediately
4. Verify no duplicate changes occur
5. Stop auto-change
6. Verify changes stop immediately

Expected: Clean timer management, no leaks

- [ ] **Step 6: Commit**

```bash
git add Tkinter/UIMain.py
git commit -m "fix: prevent timer leaks with proper cancellation

- Add active_timer tracking variable
- Cancel previous timer before starting new one
- Cancel timer in stop_interval_change
- Prevent accumulation of multiple timers
- Improve resource cleanup

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 10: Add .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore file**

```
# .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
test_env/

# Application data
data.txt
hotkeys.json
hotkeys.json.backup

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Distribution
dist/
build/
*.egg-info/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore for Python project

- Ignore Python cache and bytecode files
- Ignore user data files (data.txt, hotkeys.json)
- Ignore IDE and OS specific files
- Ignore test and distribution artifacts

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 11: Final Integration Testing

**Files:**
- Test: All components together

- [ ] **Step 1: Full application test**

Test checklist:
1. Launch application
2. Add multiple folders (valid and invalid paths)
3. Test "Browse" button
4. Test "Add Path" with manual entry
5. Test "Remove Path"
6. Test "Change Wallpaper" (single change)
7. Set custom interval and start auto-change
8. Test stop auto-change
9. Open hotkey manager
10. Record and bind hotkeys for all action types
11. Test all hotkeys work
12. Remove a hotkey
13. Minimize to tray
14. Test "Show UI" hotkey
15. Test other hotkeys while in tray
16. Restore from tray
17. Exit application
18. Relaunch and verify data persistence

- [ ] **Step 2: Edge case testing**

Test edge cases:
1. Empty folder (no images)
2. Folder with only non-image files
3. Invalid time inputs (negative, text, zero)
4. Very short interval (1 second)
5. Very long interval (1440 minutes)
6. Rapid start/stop cycles
7. Changing folders while auto-change is running

- [ ] **Step 3: Document any issues found**

If issues are found, create new tasks to fix them. Manual testing complete - no commit needed as no code changes were made during testing.

---

## Summary

This plan addresses all identified issues:

**Critical Bugs Fixed:**
1. ✅ Lambda closure bug in hotkey bindings
2. ✅ Wrong variable check in add_path
3. ✅ Hotkey overwrite bug (append vs assign)
4. ✅ Image file validation added

**Improvements Implemented:**
5. ✅ Path handling with os.path.join()
6. ✅ Empty directory handling
7. ✅ Timer leak prevention
8. ✅ Input validation for time intervals
9. ✅ Dependencies documented (requirements.txt)
10. ✅ Error handling for file operations
11. ✅ Configuration constants extracted
12. ✅ .gitignore added
13. ✅ README documentation
14. ✅ Unit tests for core logic

**Total Tasks:** 11 tasks across 5 chunks
**Estimated Time:** 2-3 hours for complete implementation and testing
**Test Coverage:** Unit tests for Main.py, manual testing for UI components
