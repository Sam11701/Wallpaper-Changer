"""Main window for Wallpaper Changer using Flet framework."""
import os
import json
import threading
import keyboard
import pystray
import flet as ft
from PIL import Image as PILImage, ImageDraw
from src.core import wallpaper
from src.config import DATA_FILE, HOTKEY_FILE
from src.gui.widgets.path_list_item import create_path_list_item
from src.gui.hotkey_dialog import show_hotkey_dialog


def main(page: ft.Page):
    """Main entry point for Flet app."""
    # State
    current_paths = []
    selected_path = None  # Currently selected folder for wallpaper changes
    current_source = "No folder selected"
    timer_active = False
    timer_interval = 60  # Default 60 seconds
    active_timer = None
    hotkey_bindings = {"start": {}, "stop": [], "change": [], "show": []}
    tray_icon = None
    tray_icon_running = False
    is_maximized = False  # Track maximize/restore state for titlebar icon

    # Window configuration
    page.title = "Wallpaper Changer"
    page.window.frameless = True  # Remove default Windows frame
    page.window.title_bar_hidden = True  # Extra safety
    page.window.width = 800
    page.window.height = 640  # +40px for custom titlebar
    page.window.min_width = 600
    page.window.min_height = 540  # +40px for custom titlebar
    page.padding = 0  # Remove default padding for full-width titlebar

    # Theme configuration
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#8B5CF6",  # Soft purple
            secondary="#FF6B6B",  # Warm coral
            surface="#FFFFFF",  # White cards
            on_primary="#FFFFFF",  # White text on purple
            on_surface="#2D3748",  # Dark text on white
        ),
        use_material3=True,
    )
    page.bgcolor = "#FAFAFA"  # Off-white background

    # Status Cards Row (with refs for updates)
    source_card_value = ft.Ref[ft.Text]()
    timer_card_value = ft.Ref[ft.Text]()
    hotkeys_card_value = ft.Ref[ft.Text]()

    def create_updateable_status_card(icon: str, title: str, value: str, value_ref: ft.Ref):
        """Create status card with updateable value."""
        value_text = ft.Text(
            value,
            size=16,
            weight=ft.FontWeight.W_600,
            color="#2D3748",
            ref=value_ref,
        )
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(icon, size=32, color=ft.Colors.PRIMARY),
                        ft.Text(
                            title,
                            size=12,
                            weight=ft.FontWeight.W_400,
                            color="#718096",
                        ),
                        value_text,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=24,
            ),
            elevation=2,
        )

    status_cards = ft.ResponsiveRow(
        [
            ft.Container(
                content=create_updateable_status_card(
                    icon=ft.Icons.FOLDER_OUTLINED,
                    title="Current Source",
                    value=current_source,
                    value_ref=source_card_value,
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
            ft.Container(
                content=create_updateable_status_card(
                    icon=ft.Icons.TIMER_OUTLINED,
                    title="Timer",
                    value="Stopped",
                    value_ref=timer_card_value,
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
            ft.Container(
                content=create_updateable_status_card(
                    icon=ft.Icons.KEYBOARD_OUTLINED,
                    title="Hotkeys",
                    value="0 shortcuts active",
                    value_ref=hotkeys_card_value,
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            ),
        ],
        spacing=16,
    )

    # Quick Actions Section
    def update_timer_ui(is_active: bool, countdown: str = "Stopped"):
        """Update timer button and status card."""
        nonlocal timer_button

        if is_active:
            timer_button.content = ft.Text("Stop Timer")
            timer_button.icon = ft.Icons.STOP
            timer_button.style.bgcolor = {"": "#FF6B6B"}  # Coral
            timer_card_value.current.value = countdown
        else:
            timer_button.content = ft.Text("Start Timer")
            timer_button.icon = ft.Icons.PLAY_ARROW
            timer_button.style.bgcolor = {"": "#718096"}  # Gray
            timer_card_value.current.value = "Stopped"

        page.update()

    def timer_loop():
        """Timer loop that runs in background."""
        nonlocal current_source

        if timer_active and selected_path:
            # Pick and change wallpaper from selected folder
            try:
                if wallpaper.pick_and_change(selected_path):
                    current_source = os.path.basename(selected_path)
                    source_card_value.current.value = current_source
                    page.update()
            except Exception as e:
                print(f"Timer wallpaper change failed: {e}")

            # Schedule next iteration
            if timer_active:
                active_timer_ref = threading.Timer(timer_interval, timer_loop)
                active_timer_ref.start()

    def handle_timer_toggle(e):
        """Handle timer start/stop."""
        nonlocal timer_active, active_timer, timer_interval

        if not selected_path:
            page.show_dialog(
                ft.SnackBar(
                    ft.Text("No folder selected. Click a folder to select it."),
                    bgcolor=ft.Colors.ERROR,
                )
            )
            return

        timer_active = not timer_active

        if timer_active:
            # Calculate interval from inputs
            try:
                minutes = int(minutes_field.value) if minutes_field.value else 0
                seconds = int(seconds_field.value) if seconds_field.value else 0
                timer_interval = (minutes * 60) + seconds

                if timer_interval < 1:
                    timer_interval = 60
                    page.show_dialog(
                        ft.SnackBar(
                            ft.Text("Invalid interval, using default (60s)"),
                            bgcolor=ft.Colors.ORANGE,
                        )
                    )
                elif timer_interval > (24 * 3600):
                    timer_interval = 60
                    page.show_dialog(
                        ft.SnackBar(
                            ft.Text("Interval too long, using default (60s)"),
                            bgcolor=ft.Colors.ORANGE,
                        )
                    )
            except ValueError:
                timer_interval = 60
                page.show_dialog(
                    ft.SnackBar(
                        ft.Text("Invalid input, using default (60s)"),
                        bgcolor=ft.Colors.ORANGE,
                    )
                )

            # Start timer
            update_timer_ui(is_active=True, countdown=f"{timer_interval}s")
            page.show_dialog(
                ft.SnackBar(
                    ft.Text(f"Auto-change started ({timer_interval}s interval)"),
                    bgcolor=ft.Colors.BLUE,
                )
            )

            # Start timer loop
            active_timer = threading.Timer(timer_interval, timer_loop)
            active_timer.start()
        else:
            # Stop timer
            if active_timer:
                active_timer.cancel()
                active_timer = None

            update_timer_ui(is_active=False)
            page.show_dialog(
                ft.SnackBar(
                    ft.Text("Auto-change stopped"),
                    bgcolor=ft.Colors.BLUE,
                )
            )

        page.update()

    def load_paths():
        """Load paths from data.txt."""
        nonlocal current_paths, selected_path
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                current_paths = [line.strip() for line in f if line.strip()]
            # Auto-select first path on startup
            if current_paths and not selected_path:
                selected_path = current_paths[0]

    def load_hotkey_bindings():
        """Load hotkey bindings from file."""
        nonlocal hotkey_bindings
        default = {"start": {}, "stop": [], "change": [], "show": []}

        if os.path.exists(HOTKEY_FILE):
            try:
                with open(HOTKEY_FILE, "r") as f:
                    data = json.load(f)
                    for key in default:
                        if key not in data:
                            data[key] = default[key]
                    hotkey_bindings = data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading hotkeys: {e}")
                hotkey_bindings = default
        else:
            hotkey_bindings = default

    def save_hotkey_bindings(bindings: dict):
        """Save hotkey bindings to file."""
        nonlocal hotkey_bindings
        hotkey_bindings = bindings

        try:
            with open(HOTKEY_FILE, "w") as f:
                json.dump(hotkey_bindings, f, indent=4)

            # Update hotkeys card
            count = len(hotkey_bindings.get("start", {})) + \
                    len(hotkey_bindings.get("stop", [])) + \
                    len(hotkey_bindings.get("change", [])) + \
                    len(hotkey_bindings.get("show", []))
            hotkeys_card_value.current.value = f"{count} shortcuts active"
            page.update()
        except IOError as e:
            print(f"Error saving hotkeys: {e}")

    def switch_path_by_hotkey(key_combo: str):
        """Handle start hotkey press."""
        nonlocal current_source
        path = hotkey_bindings["start"].get(key_combo)
        if path and os.path.isdir(path):
            if not timer_active:
                # Start timer for this path
                current_paths.insert(0, path)  # Prioritize this path
                handle_timer_toggle(None)

    def stop_auto_change_hotkey():
        """Handle stop hotkey press."""
        if timer_active:
            handle_timer_toggle(None)

    def change_wallpaper_hotkey():
        """Handle change wallpaper hotkey press."""
        if current_paths:
            handle_change_wallpaper(None)

    def show_ui_hotkey():
        """Handle show UI hotkey press."""
        page.window.to_front()
        page.update()

    hotkey_actions = {
        "start": switch_path_by_hotkey,
        "stop": stop_auto_change_hotkey,
        "change": change_wallpaper_hotkey,
        "show": show_ui_hotkey,
    }

    def create_tray_image():
        """Create simple icon for system tray."""
        image = PILImage.new('RGB', (64, 64), color='gray')
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill='white')
        return image

    def on_tray_restore(icon, item):
        """Restore window from tray."""
        nonlocal tray_icon, tray_icon_running

        icon.stop()
        tray_icon = None
        tray_icon_running = False

        page.window.visible = True
        page.update()

    def on_tray_exit(icon, item):
        """Exit app from tray."""
        nonlocal tray_icon, tray_icon_running

        icon.stop()
        tray_icon = None
        tray_icon_running = False

        page.window.close()

    def minimize_to_tray():
        """Minimize window to system tray."""
        nonlocal tray_icon, tray_icon_running

        if tray_icon_running:
            return

        page.window.visible = False
        page.update()

        def run_tray():
            nonlocal tray_icon_running
            tray_icon_running = True
            tray_icon.run()
            tray_icon_running = False

        image = create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("Restore", on_tray_restore),
            pystray.MenuItem("Exit", on_tray_exit),
        )
        tray_icon = pystray.Icon("WallpaperChanger", image, "Wallpaper Changer", menu)

        threading.Thread(target=run_tray, daemon=True).start()

    def handle_change_wallpaper(e):
        """Handle manual wallpaper change."""
        nonlocal current_source

        if not selected_path:
            page.show_dialog(
                ft.SnackBar(
                    ft.Text("No folder selected. Click a folder to select it."),
                    bgcolor=ft.Colors.ERROR,
                )
            )
            return

        # Disable button, show loading
        change_now_button.disabled = True
        change_now_button.content = ft.Text("Changing...")
        page.update()

        try:
            if wallpaper.pick_and_change(selected_path):
                current_source = os.path.basename(selected_path)
                source_card_value.current.value = current_source
                page.show_dialog(
                    ft.SnackBar(
                        ft.Text("Wallpaper changed successfully"),
                        bgcolor=ft.Colors.GREEN,
                    )
                )
            else:
                page.show_dialog(
                    ft.SnackBar(
                        ft.Text("Failed to change wallpaper"),
                        bgcolor=ft.Colors.ERROR,
                    )
                )
        except ValueError as e:
            page.show_dialog(
                ft.SnackBar(
                    ft.Text(str(e)),
                    bgcolor=ft.Colors.ERROR,
                )
            )
        finally:
            change_now_button.disabled = False
            change_now_button.content = ft.Text("Change Wallpaper Now")
            page.update()

    # Load paths on startup
    load_paths()

    # Load and register hotkeys
    load_hotkey_bindings()

    # Register hotkeys
    for combo_str, path in hotkey_bindings.get("start", {}).items():
        try:
            keyboard.add_hotkey(
                combo_str,
                lambda c=combo_str: switch_path_by_hotkey(c)
            )
        except Exception as e:
            print(f"Failed to register hotkey {combo_str}: {e}")

    for combo_str in hotkey_bindings.get("stop", []):
        try:
            keyboard.add_hotkey(combo_str, stop_auto_change_hotkey)
        except Exception as e:
            print(f"Failed to register hotkey {combo_str}: {e}")

    for combo_str in hotkey_bindings.get("change", []):
        try:
            keyboard.add_hotkey(combo_str, change_wallpaper_hotkey)
        except Exception as e:
            print(f"Failed to register hotkey {combo_str}: {e}")

    for combo_str in hotkey_bindings.get("show", []):
        try:
            keyboard.add_hotkey(combo_str, show_ui_hotkey)
        except Exception as e:
            print(f"Failed to register hotkey {combo_str}: {e}")

    # Update hotkeys card
    count = len(hotkey_bindings.get("start", {})) + \
            len(hotkey_bindings.get("stop", [])) + \
            len(hotkey_bindings.get("change", [])) + \
            len(hotkey_bindings.get("show", []))
    hotkeys_card_value.current.value = f"{count} shortcuts active"

    change_now_button = ft.FilledButton(
        content=ft.Text("Change Wallpaper Now"),
        icon=ft.Icons.WALLPAPER,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PRIMARY,
            color=ft.Colors.ON_PRIMARY,
        ),
        height=50,
        on_click=handle_change_wallpaper,
    )

    timer_button = ft.FilledButton(
        content=ft.Text("Start Timer"),
        icon=ft.Icons.PLAY_ARROW,
        style=ft.ButtonStyle(
            bgcolor={"": "#718096"},  # Gray when stopped
            color=ft.Colors.WHITE,
        ),
        height=50,
        on_click=handle_timer_toggle,
    )

    quick_actions = ft.ResponsiveRow(
        [
            ft.Container(
                content=change_now_button,
                col={"xs": 12, "md": 6},
            ),
            ft.Container(
                content=timer_button,
                col={"xs": 12, "md": 6},
            ),
        ],
        spacing=16,
    )

    # Timer Configuration
    minutes_field = ft.TextField(
        label="Min",
        value="1",
        width=100,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=16,
        border_width=1,
        content_padding=ft.padding.all(12),
    )

    seconds_field = ft.TextField(
        label="Sec",
        value="0",
        width=100,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
        text_size=16,
        border_width=1,
        content_padding=ft.padding.all(12),
    )

    timer_config = ft.Container(
        content=ft.Column(
            [
                ft.Text("Timer Interval", size=14, weight=ft.FontWeight.W_600),
                ft.Row(
                    [
                        minutes_field,
                        seconds_field,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=16,
        border=ft.Border.all(1, "#E2E8F0"),
        border_radius=8,
    )

    # Paths Configuration
    paths_list = ft.Column(spacing=0)

    def handle_select_path(path: str):
        """Select a path as the active folder."""
        nonlocal selected_path, current_source
        selected_path = path
        current_source = os.path.basename(path) or path
        source_card_value.current.value = current_source
        refresh_paths_list()  # Refresh to update selection indicators

    def refresh_paths_list():
        """Refresh the paths list display."""
        paths_list.controls.clear()
        for path in current_paths:
            is_selected = (path == selected_path)
            paths_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.RADIO_BUTTON_CHECKED if is_selected else ft.Icons.RADIO_BUTTON_UNCHECKED,
                        color=ft.Colors.PRIMARY if is_selected else ft.Colors.ON_SURFACE_VARIANT
                    ),
                    title=ft.Text(path, size=14, weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.NORMAL),
                    trailing=ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.ERROR,
                        tooltip="Remove folder",
                        on_click=lambda e, p=path: handle_remove_path(p),
                    ),
                    selected=is_selected,
                    on_click=lambda e, p=path: handle_select_path(p),
                )
            )
        page.update()

    def handle_remove_path(path: str):
        """Remove a path from the list."""
        nonlocal current_paths, selected_path, current_source
        if path in current_paths:
            current_paths.remove(path)

            # If removed path was selected, update selection
            if path == selected_path:
                if current_paths:
                    # Select first remaining folder
                    selected_path = current_paths[0]
                    current_source = os.path.basename(selected_path) or selected_path
                    source_card_value.current.value = current_source
                else:
                    # No folders left
                    selected_path = None
                    current_source = "No folder selected"
                    source_card_value.current.value = current_source

            # Save to file
            with open(DATA_FILE, "w") as f:
                f.writelines(line + '\n' for line in current_paths)

            refresh_paths_list()

            page.show_dialog(
                ft.SnackBar(
                    ft.Text("Folder removed"),
                    bgcolor=ft.Colors.BLUE,
                )
            )

    def on_folder_selected(e):
        """Handle folder selection from file picker."""
        nonlocal current_paths
        if e.path:
            selected_path = e.path

            # Validate directory
            if not os.path.isdir(selected_path):
                page.show_dialog(
                    ft.SnackBar(
                        ft.Text("Invalid directory path"),
                        bgcolor=ft.Colors.ERROR,
                    )
                )
                return

            # Check for duplicates
            if selected_path in current_paths:
                page.show_dialog(
                    ft.SnackBar(
                        ft.Text("Folder already in list"),
                        bgcolor=ft.Colors.ORANGE,
                    )
                )
                return

            # Add to list
            current_paths.append(selected_path)

            # Save to file
            with open(DATA_FILE, "w") as f:
                f.writelines(line + '\n' for line in current_paths)

            refresh_paths_list()

            page.show_dialog(
                ft.SnackBar(
                    ft.Text("Folder added"),
                    bgcolor=ft.Colors.GREEN,
                )
            )

    # Create add folder dialog components
    add_path_input = ft.TextField(
        label="Folder Path",
        hint_text="Enter full path to wallpaper folder",
        expand=True,
    )

    def browse_folder(e):
        """Open Windows folder picker dialog."""
        try:
            # Try using win32com for modern dialog
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            folder = shell.BrowseForFolder(0, "Select Wallpaper Folder", 0x0040)  # BIF_NEWDIALOGSTYLE

            if folder:
                folder_path = folder.Self.Path
                add_path_input.value = folder_path
                page.update()
        except ImportError:
            # Fallback to tkinter if win32com not available
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder_path = filedialog.askdirectory(title="Select Wallpaper Folder")
            root.destroy()
            if folder_path:
                add_path_input.value = folder_path
                page.update()
        except Exception as ex:
            print(f"Folder browser error: {ex}")

    browse_button = ft.FilledButton(
        content=ft.Text("Browse..."),
        icon=ft.Icons.FOLDER_OPEN,
        on_click=browse_folder,
    )

    def close_add_dialog(e):
        """Close the add folder dialog."""
        print("Closing dialog")
        add_folder_dialog.open = False
        add_path_input.value = ""
        page.update()

    def submit_add_path(e):
        """Submit the new folder path."""
        print(f"Submitting path: {add_path_input.value}")
        if add_path_input.value and add_path_input.value.strip():
            folder_path = add_path_input.value.strip()

            # Validate directory
            if not os.path.isdir(folder_path):
                page.show_dialog(
                    ft.SnackBar(
                        ft.Text("Invalid directory path"),
                        bgcolor=ft.Colors.ERROR,
                    )
                )
                return

            # Check for duplicates
            if folder_path in current_paths:
                page.show_dialog(
                    ft.SnackBar(
                        ft.Text("Folder already in list"),
                        bgcolor=ft.Colors.ORANGE,
                    )
                )
                return

            # Add to list
            current_paths.append(folder_path)

            # Auto-select if no folder is selected
            if not selected_path:
                handle_select_path(folder_path)

            # Save to file
            with open(DATA_FILE, "w") as f:
                f.writelines(line + '\n' for line in current_paths)

            refresh_paths_list()

            # Close dialog and show success
            add_folder_dialog.open = False
            add_path_input.value = ""

            # Show success message
            page.show_dialog(
                ft.SnackBar(
                    ft.Text("Folder added"),
                    bgcolor=ft.Colors.GREEN,
                )
            )

    add_folder_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Add Wallpaper Folder"),
        content=ft.Column(
            [
                ft.Row(
                    [
                        add_path_input,
                        browse_button,
                    ],
                    spacing=8,
                ),
            ],
            tight=True,
            width=500,
        ),
        actions=[
            ft.TextButton(content=ft.Text("Cancel"), on_click=close_add_dialog),
            ft.TextButton(content=ft.Text("Add"), on_click=submit_add_path),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def handle_add_path(e):
        """Show dialog to add folder path."""
        print("=== handle_add_path called ===")
        if add_folder_dialog not in page.overlay:
            page.overlay.append(add_folder_dialog)
        add_folder_dialog.open = True
        page.update()
        print("Dialog opened")

    paths_section = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Wallpaper Folders",
                    size=14,
                    weight=ft.FontWeight.W_600,
                ),
                paths_list,
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ft.Colors.PRIMARY),
                    title=ft.Text("Add Folder"),
                    subtitle=ft.Text("Add a new wallpaper folder"),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                    on_click=lambda e: handle_add_path(e),
                ),
            ],
            spacing=8,
        ),
        padding=16,
        border=ft.Border.all(1, "#E2E8F0"),
        border_radius=8,
    )

    # Initialize paths list
    refresh_paths_list()

    # Hotkeys Section
    def open_hotkey_dialog(e):
        """Open hotkey management dialog."""
        show_hotkey_dialog(
            page=page,
            paths=current_paths,
            hotkey_bindings=hotkey_bindings,
            hotkey_actions=hotkey_actions,
            on_save=save_hotkey_bindings,
        )

    hotkeys_section = ft.Container(
        content=ft.ListTile(
            leading=ft.Icon(ft.Icons.KEYBOARD_OUTLINED, color=ft.Colors.PRIMARY),
            title=ft.Text("Manage Hotkeys", size=14, weight=ft.FontWeight.W_600),
            subtitle=ft.Text("Configure global keyboard shortcuts"),
            trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
            on_click=open_hotkey_dialog,
        ),
        border=ft.Border.all(1, "#E2E8F0"),
        border_radius=8,
    )

    # Window close handler
    def on_window_event(e):
        if e.data == "close":
            minimize_to_tray()

    page.on_window_event = on_window_event

    # Window control handlers
    def handle_minimize(e):
        """Minimize window to taskbar."""
        page.window.minimized = True
        page.update()

    def handle_maximize(e):
        """Toggle maximize/restore window state."""
        nonlocal maximize_button
        page.window.maximized = not page.window.maximized
        if page.window.maximized:
            maximize_button.icon = ft.Icons.FILTER_NONE
        else:
            maximize_button.icon = ft.Icons.CROP_SQUARE
        page.update()

    def handle_close(e):
        """Close window (minimize to tray)."""
        minimize_to_tray()

    # Custom titlebar
    maximize_button = ft.IconButton(
        icon=ft.Icons.CROP_SQUARE,
        icon_size=16,
        icon_color="#2D3748",
        tooltip="Maximize",
        on_click=handle_maximize,
        width=40,
        height=40,
        style=ft.ButtonStyle(
            overlay_color={
                ft.ControlState.HOVERED: "#E55A5A",
            },
        ),
    )

    custom_titlebar = ft.Row(
        [
            ft.WindowDragArea(
                content=ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "🎨",
                                size=18,
                                color="#2D3748",
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor="#FF6B6B",
                    height=40,
                    padding=ft.padding.only(left=12),
                ),
                expand=True,
                maximizable=True,
            ),
            ft.Container(
                content=ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.MINIMIZE,
                            icon_size=16,
                            icon_color="#2D3748",
                            tooltip="Minimize",
                            on_click=handle_minimize,
                            width=40,
                            height=40,
                            style=ft.ButtonStyle(
                                overlay_color={
                                    ft.ControlState.HOVERED: "#E55A5A",
                                },
                            ),
                        ),
                        maximize_button,
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=16,
                            icon_color="#2D3748",
                            tooltip="Close",
                            on_click=handle_close,
                            width=40,
                            height=40,
                            style=ft.ButtonStyle(
                                overlay_color={
                                    ft.ControlState.HOVERED: "#DC2626",
                                },
                            ),
                        ),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor="#FF6B6B",
                height=40,
                padding=ft.padding.only(right=4),
            ),
        ],
        spacing=0,
    )

    def resize_handle(edge, width=None, height=None, expand=False, cursor=ft.MouseCursor.RESIZE_COLUMN):
        def on_resize_start(e):
            page.run_task(page.window.start_resizing, edge)
        return ft.GestureDetector(
            content=ft.Container(width=width, height=height, expand=expand),
            on_tap_down=on_resize_start,
            mouse_cursor=cursor,
            expand=expand,
        )

    E = 5  # edge handle thickness in px

    main_content = ft.Column(
        [
            custom_titlebar,
            ft.ListView(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            [
                                status_cards,
                                quick_actions,
                                timer_config,
                                paths_section,
                                hotkeys_section,
                            ],
                            spacing=24,
                        ),
                        padding=24,
                    )
                ],
                expand=True,
            ),
        ],
        spacing=0,
        expand=True,
    )

    # Main layout with resize handles on all edges and corners
    page.add(
        ft.Column(
            [
                # Top edge + corners
                ft.Row(
                    [
                        resize_handle(ft.WindowResizeEdge.TOP_LEFT, width=E, height=E, cursor=ft.MouseCursor.RESIZE_UP_LEFT_DOWN_RIGHT),
                        resize_handle(ft.WindowResizeEdge.TOP, height=E, expand=True, cursor=ft.MouseCursor.RESIZE_ROW),
                        resize_handle(ft.WindowResizeEdge.TOP_RIGHT, width=E, height=E, cursor=ft.MouseCursor.RESIZE_UP_RIGHT_DOWN_LEFT),
                    ],
                    spacing=0,
                    height=E,
                ),
                # Middle: left handle | content | right handle
                ft.Row(
                    [
                        resize_handle(ft.WindowResizeEdge.LEFT, width=E, expand=False, cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT),
                        main_content,
                        resize_handle(ft.WindowResizeEdge.RIGHT, width=E, expand=False, cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT),
                    ],
                    spacing=0,
                    expand=True,
                ),
                # Bottom edge + corners
                ft.Row(
                    [
                        resize_handle(ft.WindowResizeEdge.BOTTOM_LEFT, width=E, height=E, cursor=ft.MouseCursor.RESIZE_UP_RIGHT_DOWN_LEFT),
                        resize_handle(ft.WindowResizeEdge.BOTTOM, height=E, expand=True, cursor=ft.MouseCursor.RESIZE_ROW),
                        resize_handle(ft.WindowResizeEdge.BOTTOM_RIGHT, width=E, height=E, cursor=ft.MouseCursor.RESIZE_UP_LEFT_DOWN_RIGHT),
                    ],
                    spacing=0,
                    height=E,
                ),
            ],
            spacing=0,
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)
